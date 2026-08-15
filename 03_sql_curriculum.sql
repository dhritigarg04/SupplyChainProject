/* ================================================================
   STEP 5: SQL CURRICULUM
   Supply Chain Risk Intelligence Platform
   Beginner -> Intermediate -> Advanced
   Every query answers a real business question. Read the comments -
   they explain WHY the query is written the way it is, not just what
   it does.
   ================================================================ */

USE SupplyChainRiskDB;
GO


/* ================================================================
   PART 1: BEGINNER SQL
   Single tables, simple filters, sorting, basic joins.
   ================================================================ */

-- Q1: Which countries are riskiest right now?
-- Just a sort - the simplest possible business question.
SELECT country_name, region, base_risk_score
FROM countries
ORDER BY base_risk_score DESC;


-- Q2: How many suppliers do we have in each country?
-- Your first JOIN - combining two tables so the count means something.
SELECT c.country_name, COUNT(s.supplier_id) AS supplier_count
FROM countries c
JOIN suppliers s ON c.country_id = s.country_id
GROUP BY c.country_name
ORDER BY supplier_count DESC;


-- Q3: Which shipments are currently delayed?
-- WHERE turns "all the data" into "just the problem."
SELECT shipment_id, ship_date, delay_days, delay_reason
FROM shipments
WHERE delay_days > 0
ORDER BY delay_days DESC;


-- Q4: What's our average delay, broken down by reason?
-- GROUP BY + AVG answers "why" instead of just "what."
SELECT delay_reason, COUNT(*) AS num_shipments, AVG(delay_days) AS avg_delay
FROM shipments
WHERE delay_days > 0
GROUP BY delay_reason
ORDER BY avg_delay DESC;


-- Q5: Which suppliers have the worst reliability?
-- A simple threshold filter - your "risky supplier" question in 4 lines.
SELECT supplier_name, reliability_score, country_id
FROM suppliers
WHERE reliability_score < 60
ORDER BY reliability_score ASC;


/* ================================================================
   PART 2: INTERMEDIATE SQL
   Multi-table joins, subqueries, CASE statements, HAVING, date logic.
   ================================================================ */

-- Q6: Which suppliers, with their country name AND country risk score,
-- are both unreliable AND sitting in a risky country?
-- Three tables joined together - this is the "connect the dots" query
-- an analyst writes when a single table isn't enough to see the picture.
SELECT
    s.supplier_name,
    c.country_name,
    s.reliability_score,
    c.base_risk_score
FROM suppliers s
JOIN countries c ON s.country_id = c.country_id
WHERE s.reliability_score < 65 AND c.base_risk_score > 45
ORDER BY c.base_risk_score DESC, s.reliability_score ASC;


-- Q7: Categorize every shipment into a risk bucket using CASE.
-- CASE is how you turn a raw number into a business label -
-- "12 days late" means nothing to an exec, "Critical Delay" does.
SELECT
    shipment_id,
    delay_days,
    CASE
        WHEN delay_days = 0 THEN 'On Time'
        WHEN delay_days BETWEEN 1 AND 3 THEN 'Minor Delay'
        WHEN delay_days BETWEEN 4 AND 10 THEN 'Significant Delay'
        ELSE 'Critical Delay'
    END AS delay_category
FROM shipments;


-- Q8: Which products currently have LOW inventory relative to their
-- reorder point, right now (most recent snapshot per product/warehouse)?
-- Subquery in the FROM clause: first find the latest snapshot date per
-- product+warehouse, THEN join back to get the actual stock numbers.
-- This pattern (subquery to find "the latest X", then join) is one of
-- the most common things you'll write in real analyst work.
SELECT
    i.product_id,
    i.warehouse_id,
    i.stock_quantity,
    i.reorder_point
FROM inventory i
JOIN (
    SELECT product_id, warehouse_id, MAX(snapshot_date) AS latest_date
    FROM inventory
    GROUP BY product_id, warehouse_id
) latest ON i.product_id = latest.product_id
        AND i.warehouse_id = latest.warehouse_id
        AND i.snapshot_date = latest.latest_date
WHERE i.stock_quantity < i.reorder_point;


-- Q9: Which countries have MORE than 3 unreliable suppliers?
-- HAVING filters on a GROUP BY result - different from WHERE, which
-- can only filter individual rows before grouping happens.
SELECT
    c.country_name,
    COUNT(s.supplier_id) AS unreliable_supplier_count
FROM countries c
JOIN suppliers s ON c.country_id = s.country_id
WHERE s.reliability_score < 65
GROUP BY c.country_name
HAVING COUNT(s.supplier_id) > 3
ORDER BY unreliable_supplier_count DESC;


-- Q10: Monthly shipment volume and average delay, using DATE functions.
-- DATEFROMPARTS + YEAR/MONTH let you roll daily data up into months -
-- essential for any trend chart in the dashboard later.
SELECT
    DATEFROMPARTS(YEAR(ship_date), MONTH(ship_date), 1) AS ship_month,
    COUNT(*) AS total_shipments,
    AVG(delay_days) AS avg_delay_days
FROM shipments
GROUP BY DATEFROMPARTS(YEAR(ship_date), MONTH(ship_date), 1)
ORDER BY ship_month;


/* ================================================================
   PART 3: ADVANCED SQL
   CTEs, window functions, ranking, views, stored procedures,
   indexes/optimization, and transactions.
   ================================================================ */

-- Q11: CTE (Common Table Expression) - find the riskiest supplier
-- PER COUNTRY, then join back to get full details.
-- A CTE is basically a "temporary named result" you can reference
-- like a table, in the SAME query - makes complex logic readable
-- instead of nesting subqueries five levels deep.
WITH SupplierRisk AS (
    SELECT
        supplier_id,
        supplier_name,
        country_id,
        reliability_score,
        ROW_NUMBER() OVER (PARTITION BY country_id ORDER BY reliability_score ASC) AS risk_rank
    FROM suppliers
)
SELECT sr.supplier_name, c.country_name, sr.reliability_score
FROM SupplierRisk sr
JOIN countries c ON sr.country_id = c.country_id
WHERE sr.risk_rank = 1  -- the single riskiest supplier in each country
ORDER BY sr.reliability_score ASC;


-- Q12: Window function - running total of shipment delays over time.
-- SUM() OVER (ORDER BY ...) calculates a running total WITHOUT
-- collapsing your rows the way GROUP BY would - you keep every row
-- AND get the cumulative number. This is exactly what a trend line
-- with a cumulative total needs in Power BI later.
SELECT
    shipment_id,
    ship_date,
    delay_days,
    SUM(delay_days) OVER (ORDER BY ship_date ROWS UNBOUNDED PRECEDING) AS running_total_delay_days
FROM shipments
ORDER BY ship_date;


-- Q13: RANK vs DENSE_RANK - rank suppliers by reliability, showing
-- both, so ties are handled two different ways.
-- RANK leaves gaps after ties (1,1,3); DENSE_RANK doesn't (1,1,2).
-- Knowing the difference matters the first time two suppliers tie
-- and your report shows a confusing gap in the ranking numbers.
SELECT
    supplier_name,
    reliability_score,
    RANK() OVER (ORDER BY reliability_score DESC) AS rank_with_gaps,
    DENSE_RANK() OVER (ORDER BY reliability_score DESC) AS rank_no_gaps
FROM suppliers;


-- Q14: Recursive CTE - build a simple calendar of months between two
-- dates. Useful whenever you need every month to appear in a report,
-- even months with ZERO activity (otherwise those months just vanish
-- from your charts, which is misleading).
WITH MonthSeries AS (
    SELECT CAST('2022-01-01' AS DATE) AS month_start
    UNION ALL
    SELECT DATEADD(MONTH, 1, month_start)
    FROM MonthSeries
    WHERE month_start < '2024-12-01'
)
SELECT month_start
FROM MonthSeries
OPTION (MAXRECURSION 100);  -- safety limit, since recursive CTEs can loop forever if written wrong


-- Q15: VIEW - save a common business definition so everyone in the
-- company queries "revenue at risk" the same way, instead of every
-- analyst writing their own slightly-different version.
GO
CREATE OR ALTER VIEW vw_ShipmentRiskSummary AS
SELECT
    sh.shipment_id,
    sh.ship_date,
    sh.delay_days,
    sh.delay_reason,
    po.product_id,
    p.product_name,
    p.unit_price,
    po.quantity,
    (p.unit_price * po.quantity) AS order_value,
    c.country_name AS origin_country,
    c.base_risk_score AS origin_country_risk
FROM shipments sh
JOIN purchase_orders po ON sh.po_id = po.po_id
JOIN products p ON po.product_id = p.product_id
JOIN ports pt ON sh.origin_port_id = pt.port_id
JOIN countries c ON pt.country_id = c.country_id;
GO

-- Now anyone can just query the view like a normal table:
SELECT TOP 20 * FROM vw_ShipmentRiskSummary ORDER BY delay_days DESC;


-- Q16: STORED PROCEDURE - reusable business logic with a parameter.
-- Instead of pasting this query everywhere, you call the procedure
-- with whatever risk threshold you want, any time, from Power BI,
-- Python, or another script.
GO
CREATE OR ALTER PROCEDURE sp_GetHighRiskSuppliers
    @RiskThreshold DECIMAL(5,2)
AS
BEGIN
    SET NOCOUNT ON;  -- stops SQL Server sending "rows affected" messages that clutter output

    SELECT
        s.supplier_name,
        c.country_name,
        s.reliability_score,
        c.base_risk_score
    FROM suppliers s
    JOIN countries c ON s.country_id = c.country_id
    WHERE c.base_risk_score > @RiskThreshold
    ORDER BY c.base_risk_score DESC;
END;
GO

-- Call it like this:
EXEC sp_GetHighRiskSuppliers @RiskThreshold = 45;


-- Q17: TRANSACTION - safely update data with a rollback safety net.
-- If ANYTHING inside a transaction fails, the whole thing undoes
-- itself - critical when you're updating multiple related tables
-- and a half-finished update would leave your data inconsistent.
BEGIN TRANSACTION;

BEGIN TRY
    UPDATE suppliers
    SET reliability_score = reliability_score - 5
    WHERE supplier_id IN (
        SELECT supplier_id FROM suppliers
        WHERE country_id = (SELECT country_id FROM countries WHERE country_name = 'Bangladesh')
    );

    COMMIT TRANSACTION;
    PRINT 'Update succeeded and was committed.';
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    PRINT 'Something went wrong - all changes were undone.';
END CATCH;


-- Q18: INDEX + query plan check - proving WHY the indexes from
-- Step 3 matter. Run this, then look at the "Execution Plan" tab
-- in SSMS (Query menu -> Include Actual Execution Plan) - you should
-- see it using an Index Seek, not a slow full Table Scan.
SELECT shipment_id, delay_days
FROM shipments
WHERE ship_date BETWEEN '2023-06-01' AND '2023-09-01';


-- Q19: Dynamic SQL - build and run a query where part of it (like the
-- column to sort by) is decided at runtime, not hardcoded.
-- Used carefully - dynamic SQL can be a security risk (SQL injection)
-- if you ever plug in raw user text instead of a controlled value
-- like this.
DECLARE @SortColumn NVARCHAR(50) = 'reliability_score';
DECLARE @SQL NVARCHAR(MAX);

SET @SQL = N'SELECT supplier_name, ' + QUOTENAME(@SortColumn) +
           N' FROM suppliers ORDER BY ' + QUOTENAME(@SortColumn) + N' DESC';

EXEC sp_executesql @SQL;


/* ================================================================
   END OF STEP 5
   You now have: filtering, joins, subqueries, CASE, GROUP BY/HAVING,
   CTEs, recursive CTEs, window functions, ranking, views, stored
   procedures, transactions, and dynamic SQL - all tied to real
   business questions from the platform.
   ================================================================ */
