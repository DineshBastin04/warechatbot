/* =====================================================================================
   Warehouse Performance Agent - CHECK QUERIES (read-only, SELECT only)
   Run these after wpa_test_data_insert.sql to see, by hand, the same numbers the
   agents report. Each one compares LAK1 today from 09:00 with the same hours on the
   same weekday in the previous 5 weeks (that is what "normally" means in the report).
   ===================================================================================== */

-- 1. Is the test data there?
SELECT 't_order' AS table_name, COUNT(*) AS test_rows
FROM dbo.t_order WHERE order_number LIKE 'WPATEST-%' AND customer_id = 'WPATEST'
UNION ALL
SELECT 't_tran_log', COUNT(*)
FROM dbo.t_tran_log WHERE control_number LIKE 'WPATEST-%' AND (employee_id = 'WPATEST' OR employee_id LIKE 'WPATST%')
UNION ALL
SELECT 't_exception_log', COUNT(*)
FROM dbo.t_exception_log WHERE control_number LIKE 'WPATEST-%' AND employee_id LIKE 'WPATST%';


-- 2. Staffing and work per person (Investigator: "Fewer people" / "Slower work per person")
--    Expect today: Picking people_per_hour 3 (other days 4), per_person about the same,
--                  Shipping people_per_hour 3 (other days 3), per_person about half.
WITH per_hour AS (
    SELECT CAST(start_tran_date AS date)    AS day,
           DATEPART(hour, start_tran_time)  AS hr,
           tran_type,
           MIN(description)                 AS activity,
           COUNT(*)                         AS work_done,
           COUNT(DISTINCT employee_id)      AS people
    FROM dbo.t_tran_log
    WHERE wh_id = 'LAK1'
      AND tran_type IN ('301', '340')
      AND start_tran_date >= DATEADD(day, -35, CAST(GETDATE() AS date))
      AND DATEPART(weekday, start_tran_date) = DATEPART(weekday, GETDATE())
      AND DATEPART(hour, start_tran_time) >= 9
      AND DATEPART(hour, start_tran_time) <  DATEPART(hour, GETDATE())
    GROUP BY CAST(start_tran_date AS date), DATEPART(hour, start_tran_time), tran_type
)
SELECT activity, day,
       SUM(work_done)                                   AS work_done,
       CAST(AVG(people * 1.0) AS decimal(6, 1))         AS people_per_hour,
       CAST(SUM(work_done) * 1.0 / SUM(people) AS decimal(6, 1)) AS per_person_per_hour
FROM per_hour
GROUP BY activity, day
ORDER BY activity, day DESC;


-- 3. Exceptions by type (Investigator: "Exceptions logged by the warehouse system")
--    Expect today: about 25-30 'Label printer communication error' (990), other days none.
SELECT CAST(exception_date AS date) AS day, tran_type, MIN(description) AS exception, COUNT(*) AS exceptions
FROM dbo.t_exception_log
WHERE wh_id = 'LAK1'
  AND exception_date >= DATEADD(day, -35, CAST(GETDATE() AS date))
  AND DATEPART(weekday, exception_date) = DATEPART(weekday, GETDATE())
  AND DATEPART(hour, exception_time) >= 9
  AND DATEPART(hour, exception_time) <  DATEPART(hour, GETDATE())
GROUP BY CAST(exception_date AS date), tran_type
ORDER BY day DESC, exceptions DESC;


-- 4. Short picks (Investigator: "Stock and location problems")
--    Expect today: 0-2, same as other days -> ruled out.
--    (After the optional stock test in 6: about 12 today, on two items.)
SELECT CAST(start_tran_date AS date) AS day, COUNT(*) AS short_picks,
       COUNT(DISTINCT item_number) AS items
FROM dbo.t_tran_log
WHERE wh_id = 'LAK1' AND tran_type = '376'
  AND start_tran_date >= DATEADD(day, -35, CAST(GETDATE() AS date))
  AND DATEPART(weekday, start_tran_date) = DATEPART(weekday, GETDATE())
  AND DATEPART(hour, start_tran_time) >= 9
  AND DATEPART(hour, start_tran_time) <  DATEPART(hour, GETDATE())
GROUP BY CAST(start_tran_date AS date)
ORDER BY day DESC;


-- 5. Incoming orders and units per order (Investigator: "Fewer orders" / "Bigger orders")
--    Expect today: about the same as other days -> both ruled out.
SELECT CAST(o.order_date AS date) AS day,
       COUNT(*) AS orders_received,
       CAST((SELECT SUM(t.tran_qty) FROM dbo.t_tran_log t
             WHERE t.wh_id = 'LAK1' AND t.tran_type = '301'
               AND CAST(t.start_tran_date AS date) = CAST(o.order_date AS date)
               AND DATEPART(hour, t.start_tran_time) >= 9
               AND DATEPART(hour, t.start_tran_time) < DATEPART(hour, GETDATE()))
            / NULLIF(SUM(CASE WHEN o.date_picked IS NOT NULL
                               AND DATEPART(hour, o.date_picked) >= 9
                               AND DATEPART(hour, o.date_picked) < DATEPART(hour, GETDATE()) THEN 1 END), 0)
            AS decimal(6, 2)) AS units_per_order_picked
FROM dbo.t_order o
WHERE o.wh_id = 'LAK1'
  AND o.order_date >= DATEADD(day, -35, CAST(GETDATE() AS date))
  AND DATEPART(weekday, o.order_date) = DATEPART(weekday, GETDATE())
  AND DATEPART(hour, o.order_date) >= 9
  AND DATEPART(hour, o.order_date) <  DATEPART(hour, GETDATE())
GROUP BY CAST(o.order_date AS date)
ORDER BY day DESC;


/* -------------------------------------------------------------------------------------
   6. OPTIONAL extra test - a stock problem (this one WRITES; test database only).
      Adds 12 short picks in LAK1 today between 10:00 and 12:59 on two items.
      Then click "Run analysis now": the Investigator should report short picks above
      normal and name WPATEST-ITEM7 and WPATEST-ITEM42; the Advisor adds
      "Check stock in LAK1 for these items ...". Removed by wpa_test_data_cleanup.sql.
   ------------------------------------------------------------------------------------- */
/*
INSERT INTO dbo.t_tran_log (tran_type, description, start_tran_date, start_tran_time, end_tran_date, end_tran_time,
                            employee_id, control_number, line_number, wh_id, location_id, item_number, uom, tran_qty)
SELECT '376', 'Short Pick Close', x.at, x.at, x.at, x.at, 'WPATSTLP1',
       'WPATEST-SPX-' + CAST(x.i AS varchar(2)), '1', 'LAK1', 'WPATEST',
       CASE WHEN x.i % 3 = 0 THEN 'WPATEST-ITEM42' ELSE 'WPATEST-ITEM7' END, 'EA', 0
FROM (SELECT v.i, DATEADD(minute, 10 + v.i * 14, DATEADD(hour, 10, CAST(CAST(GETDATE() AS date) AS datetime))) AS at
      FROM (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11)) AS v(i)) AS x
WHERE x.at <= GETDATE();
*/
