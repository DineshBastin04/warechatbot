/* =====================================================================================
   Warehouse Performance Agent - TEST DATA  (cleanup)
   Removes ONLY the rows created by wpa_test_data_insert.sql (this version and the
   previous one): tagged control_number / order_number 'WPATEST-...' AND a test employee
   ('WPATEST' or 'WPATST...') or test customer.
   ===================================================================================== */
SET NOCOUNT ON;
SET XACT_ABORT ON;

-- preview what will be removed
SELECT 't_order' AS table_name, COUNT(*) AS rows_to_delete
FROM dbo.t_order WHERE order_number LIKE 'WPATEST-%' AND customer_id = 'WPATEST'
UNION ALL
SELECT 't_tran_log', COUNT(*)
FROM dbo.t_tran_log WHERE control_number LIKE 'WPATEST-%' AND (employee_id = 'WPATEST' OR employee_id LIKE 'WPATST%')
UNION ALL
SELECT 't_exception_log', COUNT(*)
FROM dbo.t_exception_log WHERE control_number LIKE 'WPATEST-%' AND employee_id LIKE 'WPATST%';

BEGIN TRANSACTION;
DELETE FROM dbo.t_exception_log WHERE control_number LIKE 'WPATEST-%' AND employee_id LIKE 'WPATST%';
DELETE FROM dbo.t_tran_log      WHERE control_number LIKE 'WPATEST-%' AND (employee_id = 'WPATEST' OR employee_id LIKE 'WPATST%');
DELETE FROM dbo.t_order         WHERE order_number LIKE 'WPATEST-%' AND customer_id = 'WPATEST';
COMMIT TRANSACTION;

-- afterwards: click "Re-scan database" on the Warehouse Performance dashboard
