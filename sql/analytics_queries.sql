SET GLOBAL local_infile = 1;

CREATE DATABASE IF NOT EXISTS supply_chain_db;
USE supply_chain_db;

-- 2. Drop existing tables if re-running
DROP TABLE IF EXISTS fact_orders_fulfillment;
DROP TABLE IF EXISTS fact_inventory_snapshot;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_suppliers;
DROP TABLE IF EXISTS dim_warehouses;

-- 3. Warehouses Table
CREATE TABLE dim_warehouses (
    warehouse_id VARCHAR(10) PRIMARY KEY,
    warehouse_name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    capacity_units INT NOT NULL
);

-- 4. Suppliers Table
CREATE TABLE dim_suppliers (
    supplier_id VARCHAR(15) PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    country VARCHAR(50) NOT NULL,
    contract_lead_time_days INT NOT NULL,
    sla_target_rate DECIMAL(4, 2) NOT NULL
);

-- 5. Products Table
CREATE TABLE dim_products (
    product_id VARCHAR(15) PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    unit_cost DECIMAL(10, 2) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    lead_time_days INT NOT NULL
);

-- 6. Orders Fulfillment Table
CREATE TABLE fact_orders_fulfillment (
    order_id VARCHAR(20) PRIMARY KEY,
    order_date DATE NOT NULL,
    product_id VARCHAR(15) NOT NULL,
    warehouse_id VARCHAR(10) NOT NULL,
    supplier_id VARCHAR(15) NOT NULL,
    order_quantity INT NOT NULL,
    shipped_quantity INT NOT NULL,
    promised_delivery_date DATE NOT NULL,
    actual_delivery_date DATE NOT NULL,
    fulfillment_status VARCHAR(30) NOT NULL,
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
    FOREIGN KEY (warehouse_id) REFERENCES dim_warehouses(warehouse_id),
    FOREIGN KEY (supplier_id) REFERENCES dim_suppliers(supplier_id)
);

-- 7. Weekly Inventory Snapshot Table
CREATE TABLE fact_inventory_snapshot (
    snapshot_id INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    product_id VARCHAR(15) NOT NULL,
    warehouse_id VARCHAR(10) NOT NULL,
    stock_on_hand INT NOT NULL,
    safety_stock_level INT NOT NULL,
    reorder_point INT NOT NULL,
    annual_holding_rate DECIMAL(4, 2) NOT NULL,
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
    FOREIGN KEY (warehouse_id) REFERENCES dim_warehouses(warehouse_id)
);

show tables;

USE supply_chain_db;

SELECT 'dim_warehouses' AS table_name, COUNT(*) AS record_count FROM dim_warehouses
UNION ALL
SELECT 'dim_suppliers', COUNT(*) FROM dim_suppliers
UNION ALL
SELECT 'dim_products', COUNT(*) FROM dim_products
UNION ALL
SELECT 'fact_orders_fulfillment', COUNT(*) FROM fact_orders_fulfillment
UNION ALL
SELECT 'fact_inventory_snapshot', COUNT(*) FROM fact_inventory_snapshot;


SELECT 
    s.supplier_id,
    s.supplier_name,
    s.country,
    COUNT(f.order_id) AS total_shipments,
    SUM(CASE WHEN f.fulfillment_status = 'OTIF' THEN 1 ELSE 0 END) AS successful_otif_orders,
    ROUND(SUM(CASE WHEN f.fulfillment_status = 'OTIF' THEN 1 ELSE 0 END) * 100.0 / COUNT(f.order_id), 2) AS actual_otif_pct,
    ROUND(s.sla_target_rate * 100, 0) AS contract_sla_target_pct,
    ROUND(AVG(DATEDIFF(f.actual_delivery_date, f.promised_delivery_date)), 1) AS avg_delay_days
FROM dim_suppliers s
JOIN fact_orders_fulfillment f ON s.supplier_id = f.supplier_id
GROUP BY s.supplier_id, s.supplier_name, s.country, s.sla_target_rate
ORDER BY actual_otif_pct ASC;


SELECT 
    w.warehouse_name,
    p.product_name,
    p.category,
    inv.snapshot_date,
    inv.stock_on_hand,
    inv.safety_stock_level,
    inv.reorder_point,
    CASE 
        WHEN inv.stock_on_hand = 0 THEN 'CRITICAL: Stockout'
        WHEN inv.stock_on_hand <= inv.safety_stock_level THEN 'HIGH RISK: Below Safety Stock'
        WHEN inv.stock_on_hand <= inv.reorder_point THEN 'WARNING: Reorder Triggered'
        ELSE 'OPTIMAL'
    END AS replenishment_status
FROM fact_inventory_snapshot inv
JOIN dim_products p ON inv.product_id = p.product_id
JOIN dim_warehouses w ON inv.warehouse_id = w.warehouse_id
WHERE inv.stock_on_hand <= inv.reorder_point
ORDER BY inv.stock_on_hand ASC;


SELECT 
    w.warehouse_name,
    w.capacity_units,
    SUM(inv.stock_on_hand) AS current_stock_units,
    ROUND(SUM(inv.stock_on_hand * p.unit_cost), 2) AS total_inventory_value_usd,
    ROUND(SUM(inv.stock_on_hand * p.unit_cost * inv.annual_holding_rate), 2) AS estimated_annual_holding_cost_usd
FROM fact_inventory_snapshot inv
JOIN dim_warehouses w ON inv.warehouse_id = w.warehouse_id
JOIN dim_products p ON inv.product_id = p.product_id
WHERE inv.snapshot_date = (SELECT MAX(snapshot_date) FROM fact_inventory_snapshot)
GROUP BY w.warehouse_name, w.capacity_units
ORDER BY estimated_annual_holding_cost_usd DESC;