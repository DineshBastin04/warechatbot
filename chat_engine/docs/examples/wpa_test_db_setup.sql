/* =====================================================================================
   Warehouse Performance Agent - TEST DATABASE  (setup)
   -------------------------------------------------------------------------------------
   Adds empty copies of the three tables the test scenarios use to the CURRENT database,
   so scenario testing never touches ISN_db. Column names and types are copied from
   ISN_db (only the columns the agent and the scenarios use; no triggers, no data).
   Tables that already exist are left alone.

   1. Select the test database first (the database drop-down in SSMS, or USE <name>).
      For a brand-new database run this once, then select it:
          CREATE DATABASE WPA_TestDB;
   2. Run this script.
   3. In the app's Workspace Manager, connect a workspace to that database.
   4. Load scenarios with wpa_test_data_insert.sql, or let wpa_scenario_runner.py do it.
   To remove the tables afterwards:
          DROP TABLE dbo.t_order, dbo.t_tran_log, dbo.t_exception_log;
   ===================================================================================== */
IF DB_NAME() IN ('ISN_db', 'master', 'model', 'msdb', 'tempdb')
BEGIN
    RAISERROR('Select the TEST database first - this script must not run in ISN_db or a system database. Nothing was created.', 16, 1);
    SET NOEXEC ON;           -- every batch below is skipped (THROW alone would only stop this batch)
END;
GO
IF OBJECT_ID('dbo.t_order') IS NULL
CREATE TABLE dbo.t_order (
    wh_id                varchar(10)      NOT NULL,
    order_number         varchar(30)      NOT NULL,
    customer_id          varchar(15)      NULL,
    customer_name        varchar(100)     NULL,
    order_date           datetime         NOT NULL,
    date_picked          datetime         NULL,
    actual_ship_date     datetime         NULL,
    status               varchar(20)      NOT NULL,
    carrier              varchar(30)      NULL,
    backorder            char(1)          NOT NULL,
    partial_order_flag   char(1)          NOT NULL,
    total_nbr_lines      int              NULL,
    CONSTRAINT pk_t_order PRIMARY KEY (wh_id, order_number)
);
GO
IF OBJECT_ID('dbo.t_tran_log') IS NULL
CREATE TABLE dbo.t_tran_log (
    tran_log_id          bigint IDENTITY(1,1) NOT NULL CONSTRAINT pk_t_tran_log PRIMARY KEY,
    tran_type            varchar(3)       NOT NULL,
    description          varchar(50)      NULL,
    start_tran_date      datetime         NOT NULL,
    start_tran_time      datetime         NOT NULL,
    end_tran_date        datetime         NULL,
    end_tran_time        datetime         NULL,
    employee_id          varchar(10)      NOT NULL,
    control_number       varchar(30)      NULL,
    line_number          varchar(5)       NULL,
    wh_id                varchar(10)      NOT NULL,
    location_id          varchar(50)      NULL,
    item_number          varchar(30)      NULL,
    uom                  varchar(10)      NULL,
    tran_qty             float            NOT NULL
);
GO
IF OBJECT_ID('dbo.t_exception_log') IS NULL
CREATE TABLE dbo.t_exception_log (
    exception_id         bigint IDENTITY(1,1) NOT NULL CONSTRAINT pk_t_exception_log PRIMARY KEY,
    tran_type            varchar(5)       NOT NULL,
    description          varchar(100)     NULL,
    exception_date       datetime         NULL,
    exception_time       datetime         NULL,
    employee_id          varchar(10)      NULL,
    wh_id                varchar(10)      NOT NULL,
    location_id          varchar(50)      NULL,
    item_number          varchar(30)      NULL,
    quantity             float            NULL,
    control_number       varchar(30)      NULL
);
GO
-- the agent's queries filter by date: index the timestamps it reads
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_t_tran_log_start')
    CREATE INDEX ix_t_tran_log_start ON dbo.t_tran_log (start_tran_date, wh_id, tran_type);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_t_order_date')
    CREATE INDEX ix_t_order_date ON dbo.t_order (order_date);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_t_exception_log_date')
    CREATE INDEX ix_t_exception_log_date ON dbo.t_exception_log (exception_date);
GO
SELECT DB_NAME() AS database_name, name AS table_name FROM sys.tables ORDER BY name;
GO
SET NOEXEC OFF;
