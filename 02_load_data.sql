/* ============================================================
   LOAD CSV DATA INTO SQL SERVER
   File: 02_load_data.sql
   Run this AFTER 01_create_schema.sql

   IMPORTANT: Update the file path below to wherever you copied
   the CSV folder on your machine, e.g. 'C:\SupplyChainData\'
   ============================================================ */

USE SupplyChainRiskDB;
GO

DECLARE @path NVARCHAR(500) = 'C:\SupplyChainData\';  -- <-- CHANGE THIS

/* Loading order matters: parent tables (countries) must load
   before any table that has a foreign key pointing to them. */

BULK INSERT countries
FROM 'C:\SupplyChainData\countries.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT suppliers
FROM 'C:\SupplyChainData\suppliers.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT factories
FROM 'C:\SupplyChainData\factories.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT products
FROM 'C:\SupplyChainData\products.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT warehouses
FROM 'C:\SupplyChainData\warehouses.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT ports
FROM 'C:\SupplyChainData\ports.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT supplier_products
FROM 'C:\SupplyChainData\supplier_products.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT factory_suppliers
FROM 'C:\SupplyChainData\factory_suppliers.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT product_factories
FROM 'C:\SupplyChainData\product_factories.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT political_risk_index
FROM 'C:\SupplyChainData\political_risk_index.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT weather_events
FROM 'C:\SupplyChainData\weather_events.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT news_events
FROM 'C:\SupplyChainData\news_events.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT fuel_prices
FROM 'C:\SupplyChainData\fuel_prices.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT purchase_orders
FROM 'C:\SupplyChainData\purchase_orders.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT shipments
FROM 'C:\SupplyChainData\shipments.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT customer_orders
FROM 'C:\SupplyChainData\customer_orders.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT inventory
FROM 'C:\SupplyChainData\inventory.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

BULK INSERT returns
FROM 'C:\SupplyChainData\returns.csv'
WITH (FORMAT='CSV', FIRSTROW=2, CODEPAGE='65001', TABLOCK);

/* Quick check that everything loaded */
SELECT 'countries' AS table_name, COUNT(*) AS row_count FROM countries
UNION ALL SELECT 'suppliers', COUNT(*) FROM suppliers
UNION ALL SELECT 'factories', COUNT(*) FROM factories
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'warehouses', COUNT(*) FROM warehouses
UNION ALL SELECT 'ports', COUNT(*) FROM ports
UNION ALL SELECT 'supplier_products', COUNT(*) FROM supplier_products
UNION ALL SELECT 'factory_suppliers', COUNT(*) FROM factory_suppliers
UNION ALL SELECT 'product_factories', COUNT(*) FROM product_factories
UNION ALL SELECT 'political_risk_index', COUNT(*) FROM political_risk_index
UNION ALL SELECT 'weather_events', COUNT(*) FROM weather_events
UNION ALL SELECT 'news_events', COUNT(*) FROM news_events
UNION ALL SELECT 'fuel_prices', COUNT(*) FROM fuel_prices
UNION ALL SELECT 'purchase_orders', COUNT(*) FROM purchase_orders
UNION ALL SELECT 'shipments', COUNT(*) FROM shipments
UNION ALL SELECT 'customer_orders', COUNT(*) FROM customer_orders
UNION ALL SELECT 'inventory', COUNT(*) FROM inventory
UNION ALL SELECT 'returns', COUNT(*) FROM returns;
