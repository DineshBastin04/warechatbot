/* =====================================================================================
   Warehouse Performance Agent - TEST SCENARIOS  (insert)
   -------------------------------------------------------------------------------------
   RUN ON A TEST / NON-PRODUCTION COPY OF THE WAREHOUSE DATABASE ONLY.

   HOW TO USE
     1. Set @scenario below (0-11) to the situation you want to test.
     2. Run this script, then click "Run analysis now" on the Warehouse Performance dashboard.
     3. Compare what the agents report with "Expected" in the list below
        (docs/examples/wpa_test_scenarios.md has the full expected results).
     4. Run wpa_test_data_cleanup.sql before trying the next scenario
        (this script stops if test data is already there).

   SCENARIOS - every scenario has the same 5 weeks of normal history; only TODAY differs
     0  NORMAL DAY         nothing goes wrong                        -> all normal, no alert email
     1  TWO PROBLEMS       LAK1 from 09:00: a picker is absent AND the label printer fails
                                                                     -> label printer #1, short of pickers #2
     2  STAFF SHORTAGE     LAK1 from 09:00: 2 of the 4 pickers are absent
                                                                     -> not enough people on Picking
     3  PRINTER FAILURE    LAK1 from 09:00: label printer fails for half of the shipments
                                                                     -> label printer exceptions slowing Shipping
     4  STOCK SHORTAGE     LAK1 from 09:00: a third of the orders cannot be picked (short picks)
                                                                     -> short picks / stock problem
     5  LOW DEMAND         LAK1 from 09:00: 40% fewer orders come in -> fewer orders coming in (not a warehouse fault)
     6  SLOW SHIPPING      LAK1 from 09:00: same people, half the shipments run 2.5 h late,
                           nothing is logged                         -> slower work per person, no recorded cause
     7  SYSTEM STOPPED     both warehouses from 11:00: picks and shipments stop being recorded
                                                                     -> warehouse system not recording
     8  BIGGER ORDERS      LAK1 from 09:00: orders are 3x bigger, so a third are not picked yet
                                                                     -> bigger orders than usual
     9  REWORK             LAK1 from 09:00: a third of shipments are reversed (unshipped)
                                                                     -> work being undone (reversals)
    10  SHORT STOPPAGE     both warehouses 10:00-12:00: all work stops, then catches up
                                                                     -> problem window 10:00-12:00, no one working
    11  BUSY DAY           LAK1 from 09:00: 45% more orders, all handled
                                                                     -> better than normal, no alert email

   What it creates (every row is tagged so wpa_test_data_cleanup.sql can remove it):
     * dbo.t_order          - orders 'WPATEST-...' with customer_id 'WPATEST'
     * dbo.t_tran_log       - picks (301), shipments (340), short picks (376), unships (341),
                              control_number 'WPATEST-...', employees 'WPATST...'
     * dbo.t_exception_log  - exceptions with control_number 'WPATEST-...', employees 'WPATST...'

   People (employee_id):
         ATH1: pickers WPATSTAP1..WPATSTAP5, shippers WPATSTAS1..WPATSTAS3
         LAK1: pickers WPATSTLP1..WPATSTLP4, shippers WPATSTLS1..WPATSTLS3

   Normal history (all scenarios): the last 35 days, Monday-Saturday, 06:00-19:59;
     ATH1 ~20 orders/hour, LAK1 ~15 orders/hour; created -> picked +40 min -> shipped +2 h;
     each day each warehouse has 0-2 short picks, 0-1 unships and 0-2 routine
     "Putaway Location Override" exceptions. Nothing is created after the current time.

   Notes
     * Run it in the afternoon (after 13:00) on a Monday-Saturday, so several hours of
       "today" exist after the problem starts.
     * t_order has the trigger tr_as_aw_order. It copies orders into t_as_aw_order_candidate
       only when the carrier is in the auto-wave profile; these rows use carrier = NULL,
       so the trigger does nothing with them. t_tran_log and t_exception_log have no triggers.
     * GETDATE() is used as "now": the database server and the app must use the same
       local time (both are IST in this environment).
   ===================================================================================== */
SET NOCOUNT ON;
SET XACT_ABORT ON;

DECLARE @scenario int         = 1;           -- <<< CHOOSE THE SCENARIO HERE (0-11)

DECLARE @now      datetime    = GETDATE();
DECLARE @today    datetime    = CAST(CAST(@now AS date) AS datetime);
DECLARE @days     int         = 35;          -- days of history
DECLARE @wh_ok    varchar(10) = 'ATH1';      -- healthy warehouse
DECLARE @wh_bad   varchar(10) = 'LAK1';      -- warehouse with problems today
DECLARE @bad_from datetime    = DATEADD(hour, 9, @today);    -- problems start 09:00 today
DECLARE @stop_at  datetime    = DATEADD(hour, 11, @today);   -- scenario 7: recording stops 11:00
DECLARE @out_from datetime    = DATEADD(hour, 10, @today);   -- scenario 10: stoppage 10:00-12:00
DECLARE @out_to   datetime    = DATEADD(hour, 12, @today);

IF @scenario NOT BETWEEN 0 AND 11
    THROW 50002, '@scenario must be a number from 0 to 11.', 1;

IF EXISTS (SELECT 1 FROM dbo.t_order WHERE order_number LIKE 'WPATEST-%')
    OR EXISTS (SELECT 1 FROM dbo.t_tran_log WHERE control_number LIKE 'WPATEST-%'
                                              AND (employee_id = 'WPATEST' OR employee_id LIKE 'WPATST%'))
    OR EXISTS (SELECT 1 FROM dbo.t_exception_log WHERE control_number LIKE 'WPATEST-%')
    THROW 50001, 'Warehouse Performance Agent test data already exists - run wpa_test_data_cleanup.sql first.', 1;

IF OBJECT_ID('tempdb..#wpa_orders') IS NOT NULL DROP TABLE #wpa_orders;
IF OBJECT_ID('tempdb..#wpa_days') IS NOT NULL DROP TABLE #wpa_days;
IF OBJECT_ID('tempdb..#wpa_exc') IS NOT NULL DROP TABLE #wpa_exc;
IF OBJECT_ID('tempdb..#wpa_tran') IS NOT NULL DROP TABLE #wpa_tran;
CREATE TABLE #wpa_orders (
    wh_id        varchar(10) NOT NULL,
    order_number varchar(30) NOT NULL,
    k            int         NOT NULL,
    created      datetime    NOT NULL,
    picked       datetime    NULL,
    shipped      datetime    NULL,
    qty          int         NOT NULL,
    picker       varchar(10) NOT NULL,
    shipper      varchar(10) NOT NULL
);
CREATE TABLE #wpa_days (wh_id varchar(10) NOT NULL, tag char(1) NOT NULL, day0 datetime NOT NULL);
CREATE TABLE #wpa_exc (
    wh_id        varchar(10)  NOT NULL,
    at           datetime     NOT NULL,
    tran_type    varchar(5)   NOT NULL,
    description  varchar(100) NOT NULL,
    employee_id  varchar(10)  NOT NULL,
    control      varchar(30)  NOT NULL
);
CREATE TABLE #wpa_tran (                         -- every t_tran_log row, staged before writing
    wh_id        varchar(10)  NOT NULL,
    at           datetime     NOT NULL,
    tran_type    varchar(3)   NOT NULL,
    description  varchar(50)  NOT NULL,
    employee_id  varchar(10)  NOT NULL,
    control      varchar(30)  NOT NULL,
    item_number  varchar(30)  NOT NULL,
    qty          int          NOT NULL
);

;WITH n AS (
    SELECT TOP (100) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS i
    FROM sys.all_objects
),
d AS (                                           -- operating days: Monday-Saturday
    SELECT DATEADD(day, -i, @today) AS day0
    FROM n
    WHERE i <= @days AND DATEDIFF(day, '19000107', DATEADD(day, -i, @today)) % 7 <> 0
)
INSERT INTO #wpa_days (wh_id, tag, day0)
SELECT w.wh_id, w.tag, d.day0
FROM d CROSS JOIN (SELECT @wh_ok AS wh_id, 'A' AS tag UNION ALL SELECT @wh_bad, 'L') AS w;

;WITH n AS (
    SELECT TOP (100) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS i
    FROM sys.all_objects
),
w AS (                                           -- volume and team sizes per warehouse
    SELECT @wh_ok AS wh_id, 20 AS per_hour, 5 AS pickers, 3 AS shippers
    UNION ALL SELECT @wh_bad, 15, 4, 3
),
slots AS (                                       -- per warehouse/day volume varies +/-1 per hour
    SELECT w.wh_id, dd.tag, w.pickers, w.shippers, dd.day0, h.i AS hr,
           w.per_hour + (ABS(CHECKSUM(w.wh_id, dd.day0)) % 3) - 1
           + CASE WHEN @scenario = 11 AND w.wh_id = @wh_bad AND dd.day0 = @today AND h.i >= 9
                  THEN 7 ELSE 0 END AS cnt       -- scenario 11: 45% more orders from 09:00
    FROM w JOIN #wpa_days AS dd ON dd.wh_id = w.wh_id
    CROSS JOIN n AS h
    WHERE h.i BETWEEN 6 AND 19
)
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
FROM slots AS s
JOIN n AS k ON k.i < s.cnt;

/* ------------------------------------------------------------------ today's scenario */

IF @scenario = 1            -- TWO PROBLEMS: picker WPATSTLP4 absent + label printer fails for a third
BEGIN
    UPDATE #wpa_orders SET picked = NULL, shipped = NULL
    WHERE wh_id = @wh_bad AND created >= @today AND picked >= @bad_from AND picker = 'WPATSTLP4';

    INSERT INTO #wpa_exc (wh_id, at, tran_type, description, employee_id, control)
    SELECT wh_id, shipped, '990', 'Label printer communication error', shipper, order_number
    FROM #wpa_orders
    WHERE wh_id = @wh_bad AND created >= @today AND shipped >= @bad_from AND shipped <= @now AND (k / 3) % 3 = 1;

    UPDATE #wpa_orders SET shipped = NULL
    WHERE wh_id = @wh_bad AND created >= @today AND shipped >= @bad_from AND (k / 3) % 3 = 1;
END;

IF @scenario = 2            -- STAFF SHORTAGE: pickers WPATSTLP3 and WPATSTLP4 absent
    UPDATE #wpa_orders SET picked = NULL, shipped = NULL
    WHERE wh_id = @wh_bad AND created >= @today AND picked >= @bad_from
      AND picker IN ('WPATSTLP3', 'WPATSTLP4');

IF @scenario = 3            -- PRINTER FAILURE: half of the shipments fail, each failure logged
BEGIN
    INSERT INTO #wpa_exc (wh_id, at, tran_type, description, employee_id, control)
    SELECT wh_id, shipped, '990', 'Label printer communication error', shipper, order_number
    FROM #wpa_orders
    WHERE wh_id = @wh_bad AND created >= @today AND shipped >= @bad_from AND shipped <= @now AND k % 2 = 1;

    UPDATE #wpa_orders SET shipped = NULL
    WHERE wh_id = @wh_bad AND created >= @today AND shipped >= @bad_from AND k % 2 = 1;
END;

IF @scenario = 4            -- STOCK SHORTAGE: a third of the orders hit an empty location (3 items)
BEGIN
    INSERT INTO #wpa_tran (wh_id, at, tran_type, description, employee_id, control, item_number, qty)
    SELECT wh_id, picked, '376', 'Short Pick Close', picker, order_number,
           'WPATEST-SKU' + CAST(k % 3 + 1 AS varchar(2)), 0
    FROM #wpa_orders
    WHERE wh_id = @wh_bad AND created >= @today AND picked >= @bad_from AND picked <= @now AND (k / 3) % 3 = 1;

    UPDATE #wpa_orders SET picked = NULL, shipped = NULL
    WHERE wh_id = @wh_bad AND created >= @today AND picked >= @bad_from AND (k / 3) % 3 = 1;
END;

IF @scenario = 5            -- LOW DEMAND: 40% of the orders never arrive
    DELETE FROM #wpa_orders
    WHERE wh_id = @wh_bad AND created >= @bad_from AND k % 5 IN (1, 3);

IF @scenario = 6            -- SLOW SHIPPING: half of the shipments run 2.5 hours late, nothing logged
    UPDATE #wpa_orders SET shipped = DATEADD(minute, 150, shipped)
    WHERE wh_id = @wh_bad AND created >= @today AND shipped >= @bad_from AND k % 2 = 0;

IF @scenario = 7            -- SYSTEM STOPPED: no picks / shipments recorded from 11:00, both warehouses
BEGIN
    UPDATE #wpa_orders SET picked = NULL, shipped = NULL WHERE created >= @today AND picked >= @stop_at;
    UPDATE #wpa_orders SET shipped = NULL WHERE created >= @today AND shipped >= @stop_at;
END;

IF @scenario = 8            -- BIGGER ORDERS: 8-10 units instead of 2-4; a third not picked yet
BEGIN
    UPDATE #wpa_orders SET qty = 8 + (k % 3)
    WHERE wh_id = @wh_bad AND created >= @today AND picked >= @bad_from;
    UPDATE #wpa_orders SET picked = NULL, shipped = NULL
    WHERE wh_id = @wh_bad AND created >= @today AND picked >= @bad_from AND k % 3 = 0;
END;

IF @scenario = 9            -- REWORK: a third of shipments are reversed 20 minutes later
BEGIN
    INSERT INTO #wpa_tran (wh_id, at, tran_type, description, employee_id, control, item_number, qty)
    SELECT wh_id, shipped, '340', 'Shipping', shipper, order_number, 'WPATEST-ITEM', qty
    FROM #wpa_orders
    WHERE wh_id = @wh_bad AND created >= @today AND shipped >= @bad_from AND (k / 3) % 3 = 1
    UNION ALL
    SELECT wh_id, DATEADD(minute, 20, shipped), '341', 'Unship (reversal)', shipper, order_number, 'WPATEST-ITEM', qty
    FROM #wpa_orders
    WHERE wh_id = @wh_bad AND created >= @today AND shipped >= @bad_from AND (k / 3) % 3 = 1;

    UPDATE #wpa_orders SET shipped = NULL        -- not shipped in t_order; the 340 row is already staged
    WHERE wh_id = @wh_bad AND created >= @today AND shipped >= @bad_from AND (k / 3) % 3 = 1;
END;

IF @scenario = 10           -- SHORT STOPPAGE: nothing happens 10:00-12:00 in both warehouses
BEGIN
    UPDATE #wpa_orders SET picked = DATEADD(minute, k % 30, @out_to)
    WHERE created >= @today AND picked >= @out_from AND picked < @out_to;
    UPDATE #wpa_orders SET shipped = DATEADD(minute, 30 + k % 30, @out_to)
    WHERE created >= @today AND shipped >= @out_from AND shipped < @out_to;
    UPDATE #wpa_orders SET shipped = DATEADD(minute, 30, picked)
    WHERE created >= @today AND shipped < DATEADD(minute, 30, picked);
END;

/* ------------------------------------------------------------------ normal background, every day */

-- 0-2 routine putaway-override exceptions per warehouse per day
;WITH n AS (SELECT 0 AS i UNION ALL SELECT 1)
INSERT INTO #wpa_exc (wh_id, at, tran_type, description, employee_id, control)
SELECT dd.wh_id,
       DATEADD(minute, ABS(CHECKSUM(dd.wh_id, dd.day0, n.i, 'ex')) % 780, DATEADD(hour, 7, dd.day0)),
       '101', 'Putaway Location Override', 'WPATST' + dd.tag + 'P1',
       'WPATEST-EX-' + dd.wh_id + '-' + CONVERT(varchar(6), dd.day0, 12) + '-' + CAST(n.i AS varchar(1))
FROM #wpa_days AS dd CROSS JOIN n
WHERE n.i < ABS(CHECKSUM(dd.wh_id, dd.day0, 'excount')) % 3;

-- 0-2 short picks per warehouse per day
;WITH n AS (SELECT 0 AS i UNION ALL SELECT 1)
INSERT INTO #wpa_tran (wh_id, at, tran_type, description, employee_id, control, item_number, qty)
SELECT dd.wh_id,
       DATEADD(minute, ABS(CHECKSUM(dd.wh_id, dd.day0, n.i, 'sp')) % 780, DATEADD(hour, 7, dd.day0)),
       '376', 'Short Pick Close', 'WPATST' + dd.tag + 'P1',
       'WPATEST-SP-' + dd.wh_id + '-' + CONVERT(varchar(6), dd.day0, 12) + '-' + CAST(n.i AS varchar(1)),
       'WPATEST-ITEM' + CAST(ABS(CHECKSUM(dd.wh_id, dd.day0, n.i)) % 20 AS varchar(3)), 0
FROM #wpa_days AS dd CROSS JOIN n
WHERE n.i < ABS(CHECKSUM(dd.wh_id, dd.day0, 'spcount')) % 3;

-- 0-1 unships per warehouse per day (so reversals have a normal level to compare with)
INSERT INTO #wpa_tran (wh_id, at, tran_type, description, employee_id, control, item_number, qty)
SELECT dd.wh_id,
       DATEADD(minute, ABS(CHECKSUM(dd.wh_id, dd.day0, 'rv')) % 780, DATEADD(hour, 7, dd.day0)),
       '341', 'Unship (reversal)', 'WPATST' + dd.tag + 'S1',
       'WPATEST-RV-' + dd.wh_id + '-' + CONVERT(varchar(6), dd.day0, 12), 'WPATEST-ITEM', 1
FROM #wpa_days AS dd
WHERE ABS(CHECKSUM(dd.wh_id, dd.day0, 'rvcount')) % 7 IN (1, 3, 5);   -- (CHECKSUM here is always even: no % 2)

-- scenario 7: the background activity is not recorded after 11:00 either
IF @scenario = 7
    DELETE FROM #wpa_tran WHERE at >= @stop_at AND at >= @today;

/* ------------------------------------------------------------------ picks and shipments */
INSERT INTO #wpa_tran (wh_id, at, tran_type, description, employee_id, control, item_number, qty)
SELECT wh_id, picked, '301', 'Picking (pick)', picker, order_number, 'WPATEST-ITEM', qty
FROM #wpa_orders WHERE picked IS NOT NULL
UNION ALL
SELECT wh_id, shipped, '340', 'Shipping', shipper, order_number, 'WPATEST-ITEM', qty
FROM #wpa_orders WHERE shipped IS NOT NULL;

-- nothing may exist after "now"
DELETE FROM #wpa_orders WHERE created > @now;
UPDATE #wpa_orders SET picked = NULL, shipped = NULL WHERE picked > @now;
UPDATE #wpa_orders SET shipped = NULL WHERE shipped > @now;
DELETE FROM #wpa_tran WHERE at > @now;
DELETE FROM #wpa_exc WHERE at > @now;

/* ------------------------------------------------------------------ write */
BEGIN TRANSACTION;

INSERT INTO dbo.t_order (wh_id, order_number, customer_id, customer_name, order_date, date_picked,
                         actual_ship_date, status, carrier, backorder, partial_order_flag, total_nbr_lines)
SELECT wh_id, order_number, 'WPATEST', 'WPA TEST DATA', created, picked, shipped,
       CASE WHEN shipped IS NOT NULL THEN 'S' ELSE 'N' END, NULL, 'N', 'N', 1
FROM #wpa_orders;

INSERT INTO dbo.t_tran_log (tran_type, description, start_tran_date, start_tran_time, end_tran_date, end_tran_time,
                            employee_id, control_number, line_number, wh_id, location_id, item_number, uom, tran_qty)
SELECT tran_type, description, at, at, at, at, employee_id, control, '1', wh_id,
       'WPATEST', item_number, 'EA', qty
FROM #wpa_tran;

INSERT INTO dbo.t_exception_log (tran_type, description, exception_date, exception_time, employee_id, wh_id,
                                 location_id, item_number, quantity, control_number)
SELECT tran_type, description,
       CAST(CAST(at AS date) AS datetime),
       DATEADD(second, DATEDIFF(second, CAST(CAST(at AS date) AS datetime), at), CAST('19000101' AS datetime)),
       employee_id, wh_id, 'WPATEST', NULL, 0, control
FROM #wpa_exc;

COMMIT TRANSACTION;

/* ------------------------------------------------------------------ what was created */
SELECT @scenario AS scenario,
       CASE @scenario WHEN 0 THEN 'Normal day' WHEN 1 THEN 'Two problems' WHEN 2 THEN 'Staff shortage'
                      WHEN 3 THEN 'Printer failure' WHEN 4 THEN 'Stock shortage' WHEN 5 THEN 'Low demand'
                      WHEN 6 THEN 'Slow shipping' WHEN 7 THEN 'System stopped recording'
                      WHEN 8 THEN 'Bigger orders' WHEN 9 THEN 'Rework (unships)'
                      WHEN 10 THEN 'Short stoppage' WHEN 11 THEN 'Busy day' END AS scenario_name,
       @now AS created_at;

SELECT o.wh_id,
       SUM(CASE WHEN o.created >= @today THEN 1 ELSE 0 END)                        AS orders_today,
       SUM(CASE WHEN o.created >= @today AND o.picked  IS NOT NULL THEN 1 ELSE 0 END) AS picked_today,
       SUM(CASE WHEN o.created >= @today AND o.shipped IS NOT NULL THEN 1 ELSE 0 END) AS shipped_today,
       COUNT(*)                                                                     AS orders_total
FROM #wpa_orders AS o
GROUP BY o.wh_id;

DROP TABLE #wpa_orders;
DROP TABLE #wpa_days;
DROP TABLE #wpa_exc;
DROP TABLE #wpa_tran;
