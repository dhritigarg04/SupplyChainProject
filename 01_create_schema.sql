/* ============================================================
   SUPPLY CHAIN RISK INTELLIGENCE PLATFORM
   Database: SQL Server
   File: 01_create_schema.sql
   Purpose: Creates all tables, keys, and indexes for the project
   ============================================================ */

CREATE DATABASE SupplyChainRiskDB;
GO

USE SupplyChainRiskDB;
GO

/* ============================================================
   SECTION 1: CORE REFERENCE TABLES
   These hold the basic "who and what" of the business.
   Almost every other table points back to these.
   ============================================================ */

-- Every supplier, factory, port, and risk event happens IN a country.
-- This is the anchor table for all geography-based risk analysis.
CREATE TABLE countries (
    country_id      INT IDENTITY(1,1) PRIMARY KEY,
    country_name    VARCHAR(100) NOT NULL,
    region          VARCHAR(50),        -- e.g. 'Southeast Asia', 'Europe'
    currency_code   VARCHAR(10),        -- e.g. 'USD', 'EUR'
    base_risk_score DECIMAL(5,2)        -- baseline political/instability score
);

-- Companies we buy raw materials or components from.
CREATE TABLE suppliers (
    supplier_id     INT IDENTITY(1,1) PRIMARY KEY,
    supplier_name   VARCHAR(150) NOT NULL,
    country_id      INT NOT NULL,
    reliability_score DECIMAL(5,2),     -- 0-100, calculated from history
    onboarded_date  DATE,
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

-- Places where our products are physically manufactured.
CREATE TABLE factories (
    factory_id      INT IDENTITY(1,1) PRIMARY KEY,
    factory_name    VARCHAR(150) NOT NULL,
    country_id      INT NOT NULL,
    capacity_units_per_month INT,
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

-- The actual products the company sells.
CREATE TABLE products (
    product_id      INT IDENTITY(1,1) PRIMARY KEY,
    product_name    VARCHAR(150) NOT NULL,
    category        VARCHAR(80),
    unit_price      DECIMAL(10,2),
    unit_weight_kg  DECIMAL(6,2)
);

-- Storage locations for finished goods before they reach customers.
CREATE TABLE warehouses (
    warehouse_id    INT IDENTITY(1,1) PRIMARY KEY,
    warehouse_name  VARCHAR(150) NOT NULL,
    country_id      INT NOT NULL,
    capacity_units  INT,
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

-- Shipping ports used to move goods between countries.
CREATE TABLE ports (
    port_id         INT IDENTITY(1,1) PRIMARY KEY,
    port_name       VARCHAR(150) NOT NULL,
    country_id      INT NOT NULL,
    avg_congestion_score DECIMAL(5,2),  -- how often this port is backed up
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);


/* ============================================================
   SECTION 2: RELATIONSHIP (BRIDGE) TABLES
   These exist because one supplier can supply many products,
   one factory can use many suppliers, etc. (many-to-many links)
   ============================================================ */

-- Which supplier provides which product/material.
CREATE TABLE supplier_products (
    supplier_product_id INT IDENTITY(1,1) PRIMARY KEY,
    supplier_id     INT NOT NULL,
    product_id      INT NOT NULL,
    unit_cost       DECIMAL(10,2),
    avg_lead_time_days INT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Which factory buys from which supplier.
CREATE TABLE factory_suppliers (
    factory_supplier_id INT IDENTITY(1,1) PRIMARY KEY,
    factory_id      INT NOT NULL,
    supplier_id     INT NOT NULL,
    FOREIGN KEY (factory_id) REFERENCES factories(factory_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- Which factory makes which product.
CREATE TABLE product_factories (
    product_factory_id INT IDENTITY(1,1) PRIMARY KEY,
    product_id      INT NOT NULL,
    factory_id      INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (factory_id) REFERENCES factories(factory_id)
);


/* ============================================================
   SECTION 3: TRANSACTION TABLES
   These are the "action" tables — this is where most of your
   300k+ rows will live, and where SQL practice really happens.
   ============================================================ */

-- When the company orders raw material from a supplier.
CREATE TABLE purchase_orders (
    po_id           INT IDENTITY(1,1) PRIMARY KEY,
    supplier_id     INT NOT NULL,
    product_id      INT NOT NULL,
    order_date      DATE NOT NULL,
    expected_date   DATE,
    quantity        INT,
    status          VARCHAR(30),   -- 'Pending','Shipped','Delayed','Received'
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- A shipment moving goods from a factory/port to a warehouse.
-- This is the "glue" table that risk events attach to.
CREATE TABLE shipments (
    shipment_id     INT IDENTITY(1,1) PRIMARY KEY,
    po_id           INT NULL,
    origin_port_id  INT NOT NULL,
    destination_warehouse_id INT NOT NULL,
    ship_date       DATE NOT NULL,
    expected_arrival_date DATE,
    actual_arrival_date DATE NULL,
    delay_days      INT DEFAULT 0,
    delay_reason    VARCHAR(100) NULL,  -- 'Weather','Port Congestion','Political','None'
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id),
    FOREIGN KEY (origin_port_id) REFERENCES ports(port_id),
    FOREIGN KEY (destination_warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- Customer demand — orders that need to be fulfilled from stock.
CREATE TABLE customer_orders (
    order_id        INT IDENTITY(1,1) PRIMARY KEY,
    product_id      INT NOT NULL,
    warehouse_id    INT NOT NULL,
    order_date      DATE NOT NULL,
    quantity        INT,
    fulfilled       BIT DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- Stock levels of each product at each warehouse, tracked over time.
-- This is what your demand forecasting / shortage prediction ML uses.
CREATE TABLE inventory (
    inventory_id    INT IDENTITY(1,1) PRIMARY KEY,
    product_id      INT NOT NULL,
    warehouse_id    INT NOT NULL,
    snapshot_date   DATE NOT NULL,
    stock_quantity  INT,
    reorder_point   INT,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- Product returns, linked back to the original customer order.
CREATE TABLE returns (
    return_id       INT IDENTITY(1,1) PRIMARY KEY,
    order_id        INT NOT NULL,
    return_date     DATE,
    reason          VARCHAR(100),
    quantity        INT,
    FOREIGN KEY (order_id) REFERENCES customer_orders(order_id)
);


/* ============================================================
   SECTION 4: RISK & SIGNAL TABLES
   These make it a "risk intelligence" platform instead of a
   plain operations database. They feed the risk scores and ML.
   ============================================================ */

-- Bad weather at a port/country on a given date.
CREATE TABLE weather_events (
    weather_event_id INT IDENTITY(1,1) PRIMARY KEY,
    country_id      INT NOT NULL,
    port_id         INT NULL,
    event_date      DATE NOT NULL,
    event_type      VARCHAR(50),    -- 'Storm','Flood','Heatwave', etc.
    severity_score  DECIMAL(5,2),   -- 0-100
    FOREIGN KEY (country_id) REFERENCES countries(country_id),
    FOREIGN KEY (port_id) REFERENCES ports(port_id)
);

-- News headlines tagged to a country/supplier, with sentiment.
-- This is where the NLP/sentiment analysis work plugs in.
CREATE TABLE news_events (
    news_event_id   INT IDENTITY(1,1) PRIMARY KEY,
    country_id      INT NULL,
    supplier_id     INT NULL,
    event_date      DATE NOT NULL,
    headline        VARCHAR(300),
    sentiment_score DECIMAL(5,2),   -- -1 (very negative) to +1 (very positive)
    FOREIGN KEY (country_id) REFERENCES countries(country_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- Monthly political/instability risk score per country.
CREATE TABLE political_risk_index (
    political_risk_id INT IDENTITY(1,1) PRIMARY KEY,
    country_id      INT NOT NULL,
    month_year      DATE NOT NULL,   -- store as first-of-month
    risk_score      DECIMAL(5,2),
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

-- Fuel prices by region/month — affects shipping cost and delay risk.
-- NOTE: region is just a text label here (e.g. 'Europe'), not a foreign key,
-- because "region" isn't a unique/primary key over in countries.
-- We'll join on the region NAME when we need to connect this to countries.
CREATE TABLE fuel_prices (
    fuel_price_id   INT IDENTITY(1,1) PRIMARY KEY,
    region          VARCHAR(50) NOT NULL,
    month_year      DATE NOT NULL,
    price_per_barrel DECIMAL(8,2)
);


/* ============================================================
   SECTION 5: INDEXES
   These speed up the joins and filters we'll use constantly
   in Steps 5-8 (SQL practice, dashboards, ML feature building).
   ============================================================ */

CREATE INDEX idx_suppliers_country ON suppliers(country_id);
CREATE INDEX idx_factories_country ON factories(country_id);
CREATE INDEX idx_warehouses_country ON warehouses(country_id);
CREATE INDEX idx_ports_country ON ports(country_id);

CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_po_date ON purchase_orders(order_date);

CREATE INDEX idx_shipments_origin ON shipments(origin_port_id);
CREATE INDEX idx_shipments_dest ON shipments(destination_warehouse_id);
CREATE INDEX idx_shipments_date ON shipments(ship_date);

CREATE INDEX idx_orders_product ON customer_orders(product_id);
CREATE INDEX idx_orders_date ON customer_orders(order_date);

CREATE INDEX idx_inventory_snapshot ON inventory(product_id, warehouse_id, snapshot_date);

CREATE INDEX idx_weather_country_date ON weather_events(country_id, event_date);
CREATE INDEX idx_news_country_date ON news_events(country_id, event_date);
CREATE INDEX idx_political_country_month ON political_risk_index(country_id, month_year);
