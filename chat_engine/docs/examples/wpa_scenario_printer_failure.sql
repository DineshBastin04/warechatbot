/* Warehouse Performance Agent - ONE TEST SCENARIO: label printer failure
   Run in the TEST database (WPA_TestDB), after 13:00, Monday-Saturday.
   5 weeks of normal history for ATH1 and LAK1; TODAY in LAK1 from 09:00 the label
   printer fails for half of the shipments and every failure is logged.
   Then click "Run analysis now". Expected: Needs attention - orders shipped down in LAK1
   from 09:00; #1 'Label printer communication error' exceptions slowing Shipping (High). */
SET NOCOUNT ON;
SET XACT_ABORT ON;

DECLARE @now      datetime    = GETDATE();
DECLARE @today    datetime    = CAST(CAST(@now AS date) AS datetime);
DECLARE @wh_ok    varchar(10) = 'ATH1';
DECLARE @wh_bad   varchar(10) = 'LAK1';
DECLARE @bad_from datetime    = DATEADD(hour, 9, @today);

IF EXISTS (SELECT 1 FROM dbo.t_order WHERE order_number LIKE 'WPATEST-%')
    THROW 50001, 'Test data already exists - run the cleanup query first.', 1;

IF OBJECT_ID('tempdb..#wpa_orders') IS NOT NULL DROP TABLE #wpa_orders;
IF OBJECT_ID('tempdb..#wpa_days')   IS NOT NULL DROP TABLE #wpa_days;
IF OBJECT_ID('tempdb..#wpa_exc')    IS NOT NULL DROP TABLE #wpa_exc;
IF OBJECT_ID('tempdb..#wpa_tran')   IS NOT NULL DROP TABLE #wpa_tran;
CREATE TABLE #wpa_orders (wh_id varchar(10), order_number varchar(30), k int, created datetime,
                          picked datetime NULL, shipped datetime NULL, qty int, picker varchar(10), shipper varchar(10));
CREATE TABLE #wpa_days (wh_id varchar(10), tag char(1), day0 datetime);
CREATE TABLE #wpa_exc  (wh_id varchar(10), at datetime, tran_type varchar(5), description varchar(100),
                        employee_id varchar(10), control varchar(30));
CREATE TABLE #wpa_tran (wh_id varchar(10), at datetime, tran_type varchar(3), description varchar(50),
                        employee_id varchar(10), control varchar(30), item_number varchar(30), qty int);

-- 1. operating days: the last 35 days, Monday-Saturday
;WITH n AS (SELECT TOP (100) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS i FROM sys.all_objects)
INSERT INTO #wpa_days (wh_id, tag, day0)
SELECT w.wh_id, w.tag, DATEADD(day, -n.i, @today)
FROM n CROSS JOIN (SELECT @wh_ok AS wh_id, 'A' AS tag UNION ALL SELECT @wh_bad, 'L') AS w
WHERE n.i <= 35 AND DATEDIFF(day, '19000107', DATEADD(day, -n.i, @today)) % 7 <> 0;

-- 2. orders 06:00-19:59: ATH1 ~20/hour (5 pickers, 3 shippers), LAK1 ~15/hour (4 pickers, 3 shippers)
;WITH n AS (SELECT TOP (100) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS i FROM sys.all_objects),
w AS (SELECT @wh_ok AS wh_id, 20 AS per_hour, 5 AS pickers, 3 AS shippers UNION ALL SELECT @wh_bad, 15, 4, 3),
slots AS (
    SELECT w.wh_id, dd.tag, w.pickers, w.shippers, dd.day0, h.i AS hr,
           w.per_hour + (ABS(CHECKSUM(w.wh_id, dd.day0)) % 3) - 1 AS cnt
    FROM w JOIN #wpa_days AS dd ON dd.wh_id = w.wh_id CROSS JOIN n AS h
    WHERE h.i BETWEEN 6 AND 19)
INSERT INTO #wpa_orders (wh_id, order_number, k, created, picked, shipped, qty, picker, shipper)
SELECT s.wh_id,
       'WPATEST-' + s.wh_id + '-' + CONVERT(varchar(6), s.day0, 12) + '-'
           + RIGHT('0' + CAST(s.hr AS varchar(2)), 2) + RIGHT('0' + CAST(k.i AS varchar(2)), 2),
       k.i,
       DATEADD(minute, (k.i * 60) / s.cnt, DATEADD(hour, s.hr, s.day0)),
       DATEADD(minute, 40 + (k.i * 60) / s.cnt, DATEADD(hour, s.hr, s.day0)),
       DATEADD(minute, 120 + (k.i % 7) + (k.i * 60) / s.cnt, DATEADD(hour, s.hr, s.day0)),
       2 + (k.i % 3),
       'WPATST' + s.tag + 'P' + CAST(k.i % s.pickers + 1 AS varchar(2)),
       'WPATST' + s.tag + 'S' + CAST(k.i % s.shippers + 1 AS varchar(2))
FROM slots AS s JOIN n AS k ON k.i < s.cnt;

-- 3. TODAY'S PROBLEM: in LAK1 from 09:00 the label printer fails for half of the shipments
INSERT INTO #wpa_exc (wh_id, at, tran_type, description, employee_id, control)
SELECT wh_id, shipped, '990', 'Label printer communication error', shipper, order_number
FROM #wpa_orders
WHERE wh_id = @wh_bad AND created >= @today AND shipped >= @bad_from AND shipped <= @now AND k % 2 = 1;

UPDATE #wpa_orders SET shipped = NULL
WHERE wh_id = @wh_bad AND created >= @today AND shipped >= @bad_from AND k % 2 = 1;

-- 4. the normal background every day: 0-2 routine exceptions, 0-2 short picks, some unships
;WITH n AS (SELECT 0 AS i UNION ALL SELECT 1)
INSERT INTO #wpa_exc (wh_id, at, tran_type, description, employee_id, control)
SELECT dd.wh_id, DATEADD(minute, ABS(CHECKSUM(dd.wh_id, dd.day0, n.i, 'ex')) % 780, DATEADD(hour, 7, dd.day0)),
       '101', 'Putaway Location Override', 'WPATST' + dd.tag + 'P1',
       'WPATEST-EX-' + dd.wh_id + '-' + CONVERT(varchar(6), dd.day0, 12) + '-' + CAST(n.i AS varchar(1))
FROM #wpa_days AS dd CROSS JOIN n
WHERE n.i < ABS(CHECKSUM(dd.wh_id, dd.day0, 'excount')) % 3;

;WITH n AS (SELECT 0 AS i UNION ALL SELECT 1)
INSERT INTO #wpa_tran (wh_id, at, tran_type, description, employee_id, control, item_number, qty)
SELECT dd.wh_id, DATEADD(minute, ABS(CHECKSUM(dd.wh_id, dd.day0, n.i, 'sp')) % 780, DATEADD(hour, 7, dd.day0)),
       '376', 'Short Pick Close', 'WPATST' + dd.tag + 'P1',
       'WPATEST-SP-' + dd.wh_id + '-' + CONVERT(varchar(6), dd.day0, 12) + '-' + CAST(n.i AS varchar(1)),
       'WPATEST-ITEM' + CAST(ABS(CHECKSUM(dd.wh_id, dd.day0, n.i)) % 20 AS varchar(3)), 0
FROM #wpa_days AS dd CROSS JOIN n
WHERE n.i < ABS(CHECKSUM(dd.wh_id, dd.day0, 'spcount')) % 3;

INSERT INTO #wpa_tran (wh_id, at, tran_type, description, employee_id, control, item_number, qty)
SELECT dd.wh_id, DATEADD(minute, ABS(CHECKSUM(dd.wh_id, dd.day0, 'rv')) % 780, DATEADD(hour, 7, dd.day0)),
       '341', 'Unship (reversal)', 'WPATST' + dd.tag + 'S1',
       'WPATEST-RV-' + dd.wh_id + '-' + CONVERT(varchar(6), dd.day0, 12), 'WPATEST-ITEM', 1
FROM #wpa_days AS dd
WHERE ABS(CHECKSUM(dd.wh_id, dd.day0, 'rvcount')) % 7 IN (1, 3, 5);

-- 5. picks and shipments
INSERT INTO #wpa_tran (wh_id, at, tran_type, description, employee_id, control, item_number, qty)
SELECT wh_id, picked, '301', 'Picking (pick)', picker, order_number, 'WPATEST-ITEM', qty FROM #wpa_orders WHERE picked IS NOT NULL
UNION ALL
SELECT wh_id, shipped, '340', 'Shipping', shipper, order_number, 'WPATEST-ITEM', qty FROM #wpa_orders WHERE shipped IS NOT NULL;

-- 6. nothing may exist after "now"
DELETE FROM #wpa_orders WHERE created > @now;
UPDATE #wpa_orders SET picked = NULL, shipped = NULL WHERE picked > @now;
UPDATE #wpa_orders SET shipped = NULL WHERE shipped > @now;
DELETE FROM #wpa_tran WHERE at > @now;
DELETE FROM #wpa_exc  WHERE at > @now;

-- 7. write
BEGIN TRANSACTION;
INSERT INTO dbo.t_order (wh_id, order_number, customer_id, customer_name, order_date, date_picked,
                         actual_ship_date, status, carrier, backorder, partial_order_flag, total_nbr_lines)
SELECT wh_id, order_number, 'WPATEST', 'WPA TEST DATA', created, picked, shipped,
       CASE WHEN shipped IS NOT NULL THEN 'S' ELSE 'N' END, NULL, 'N', 'N', 1
FROM #wpa_orders;

INSERT INTO dbo.t_tran_log (tran_type, description, start_tran_date, start_tran_time, end_tran_date, end_tran_time,
                            employee_id, control_number, line_number, wh_id, location_id, item_number, uom, tran_qty)
SELECT tran_type, description, at, at, at, at, employee_id, control, '1', wh_id, 'WPATEST', item_number, 'EA', qty
FROM #wpa_tran;

INSERT INTO dbo.t_exception_log (tran_type, description, exception_date, exception_time, employee_id, wh_id,
                                 location_id, item_number, quantity, control_number)
SELECT tran_type, description, CAST(CAST(at AS date) AS datetime),
       DATEADD(second, DATEDIFF(second, CAST(CAST(at AS date) AS datetime), at), CAST('19000101' AS datetime)),
       employee_id, wh_id, 'WPATEST', NULL, 0, control
FROM #wpa_exc;
COMMIT TRANSACTION;

-- what was created today
SELECT wh_id,
       SUM(CASE WHEN created >= @today THEN 1 ELSE 0 END)                         AS orders_today,
       SUM(CASE WHEN created >= @today AND shipped IS NOT NULL THEN 1 ELSE 0 END) AS shipped_today,
       (SELECT COUNT(*) FROM #wpa_exc e WHERE e.wh_id = o.wh_id AND e.tran_type = '990') AS printer_errors_today
FROM #wpa_orders AS o GROUP BY wh_id;

DROP TABLE #wpa_orders; DROP TABLE #wpa_days; DROP TABLE #wpa_exc; DROP TABLE #wpa_tran;
