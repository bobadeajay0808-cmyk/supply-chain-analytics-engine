# ==============================================================================
# SCRIPT: Supply Chain Synthetic Data Generator
# PURPOSE: Creates a relational star schema (3 Dimension tables, 2 Fact tables)
#          with real-world operational problems (late shipments, stockouts, etc.)
# ==============================================================================

# Import necessary libraries
import numpy as np                      # For numerical arrays and probability distributions
import pandas as pd                     # For data manipulation and exporting to CSV
from datetime import datetime, timedelta # For managing dates, lead times, and timestamps
from faker import Faker                 # To generate realistic company names and codes

# Initialize Faker and set random seeds
# Setting seeds ensures the exact same "random" data is generated every time you run it
fake = Faker()
np.random.seed(42)
Faker.seed(42)

# ==============================================================================
# GLOBAL PARAMETERS (Configuration)
# ==============================================================================
NUM_PRODUCTS = 60                       # Total distinct product SKUs
NUM_SUPPLIERS = 12                      # Total vendor/supplier companies
NUM_WAREHOUSES = 4                      # Number of regional distribution hubs
NUM_ORDERS = 15000                      # Number of customer/store orders in 2025
START_DATE = datetime(2025, 1, 1)       # Project timeline start
END_DATE = datetime(2025, 12, 31)       # Project timeline end
DATE_RANGE_DAYS = (END_DATE - START_DATE).days  # 364 days available for orders

# ==============================================================================
# SECTION 1: DIMENSION TABLE - WAREHOUSES (dim_warehouses)
# Purpose: Static list of distribution centers holding inventory.
# ==============================================================================
warehouse_data = [
    {"warehouse_id": "WH-01", "warehouse_name": "North Logistics Hub", "location": "Chicago, IL", "capacity_units": 150000},
    {"warehouse_id": "WH-02", "warehouse_name": "Pacific Gateway DC", "location": "Los Angeles, CA", "capacity_units": 180000},
    {"warehouse_id": "WH-03", "warehouse_name": "Southeast Distribution Center", "location": "Atlanta, GA", "capacity_units": 120000},
    {"warehouse_id": "WH-04", "warehouse_name": "Northeast Fulfillment Hub", "location": "Newark, NJ", "capacity_units": 100000},
]
dim_warehouses = pd.DataFrame(warehouse_data)

# ==============================================================================
# SECTION 2: DIMENSION TABLE - SUPPLIERS (dim_suppliers)
# Purpose: Vendors providing goods. Each has an agreed contract lead time and 
#          a hidden 'delay_risk_score' to simulate unreliable vendors.
# ==============================================================================
supplier_ids = [f"SUP-{100 + i}" for i in range(NUM_SUPPLIERS)]
supplier_names = [fake.company() + " Logistics" for _ in range(NUM_SUPPLIERS)]
countries = ["USA", "China", "Germany", "Mexico", "Vietnam", "India"]

dim_suppliers = pd.DataFrame({
    "supplier_id": supplier_ids,
    "supplier_name": supplier_names,
    # Assign countries with realistic supply chain distribution weights
    "country": np.random.choice(countries, size=NUM_SUPPLIERS, p=[0.35, 0.20, 0.15, 0.15, 0.10, 0.05]),
    # Standard agreed time (in days) the supplier promises to take to ship goods
    "contract_lead_time_days": np.random.choice([7, 10, 14, 21, 30], size=NUM_SUPPLIERS),
    # Service Level Agreement benchmark (e.g., 95% on-time target)
    "sla_target_rate": np.random.choice([0.95, 0.98, 0.99], size=NUM_SUPPLIERS),
    # Risk factor (0.08 to 0.40): Probability this vendor will run late. Used later in orders.
    "delay_risk_score": np.random.uniform(0.08, 0.40, size=NUM_SUPPLIERS).round(2)
})

# ==============================================================================
# SECTION 3: DIMENSION TABLE - PRODUCTS (dim_products)
# Purpose: Catalog of SKUs with procurement costs, sale prices, and manufacturing lead times.
# ==============================================================================
categories = ["Electronics", "Industrial Tools", "Office Automation", "Safety Gear", "Raw Consumables"]
product_ids = [f"SKU-{1000 + i}" for i in range(NUM_PRODUCTS)]

products = []
for pid in product_ids:
    category = np.random.choice(categories)
    # Unit cost to manufacture or buy the item ($15 to $450)
    unit_cost = round(np.random.uniform(15.0, 450.0), 2)
    # Profit markup between 25% and 85%
    markup = np.random.uniform(1.25, 1.85)
    unit_price = round(unit_cost * markup, 2)
    # Internal turnaround days
    lead_time = int(np.random.choice([5, 8, 12, 18, 25]))
    
    products.append({
        "product_id": pid,
        "product_name": f"{category} Model {fake.bothify(text='??-###').upper()}",
        "category": category,
        "unit_cost": unit_cost,
        "unit_price": unit_price,
        "lead_time_days": lead_time
    })
dim_products = pd.DataFrame(products)

# ==============================================================================
# SECTION 4: FACT TABLE - ORDERS & FULFILLMENT (fact_orders_fulfillment)
# Purpose: Logs 15,000 shipment transactions. Injects delays based on supplier risk
#          and short-shipments (partial deliveries) to calculate OTIF.
# ==============================================================================
order_list = []
# Create quick-lookup dictionaries for supplier lead time and risk probability
supplier_risk_map = dict(zip(dim_suppliers["supplier_id"], dim_suppliers["delay_risk_score"]))
supplier_lead_map = dict(zip(dim_suppliers["supplier_id"], dim_suppliers["contract_lead_time_days"]))

for i in range(1, NUM_ORDERS + 1):
    order_id = f"ORD-{20250000 + i}"
    # Randomly assign a product, supplier, and warehouse for this transaction
    prod = dim_products.sample(n=1).iloc[0]
    supp_id = np.random.choice(dim_suppliers["supplier_id"])
    wh_id = np.random.choice(dim_warehouses["warehouse_id"])
    
    # Generate an order date within 2025 (leaving 35 days buffer at end of year for delivery)
    random_day = np.random.randint(0, DATE_RANGE_DAYS - 35)
    order_date = START_DATE + timedelta(days=random_day)
    
    # Calculate promised delivery date = order date + agreed supplier lead time
    contract_lead = supplier_lead_map[supp_id]
    promised_delivery_date = order_date + timedelta(days=int(contract_lead))
    
    # Determine if this shipment gets delayed using a binomial distribution (coin flip based on supplier risk)
    delay_risk = supplier_risk_map[supp_id]
    is_delayed = np.random.binomial(1, delay_risk)
    
    if is_delayed:
        # If delayed, add random exponential delay (typically 1 to 10+ days late)
        delay_days = int(np.random.exponential(scale=5)) + 1
        actual_delivery_date = promised_delivery_date + timedelta(days=delay_days)
    else:
        # If on time, delivery happens slightly early or exactly on target date
        variance = int(np.random.choice([-2, -1, 0, 0, 0]))
        actual_delivery_date = promised_delivery_date + timedelta(days=variance)
    
    # Quantity ordered by customer
    order_quantity = int(np.random.choice([10, 25, 50, 100, 250, 500], p=[0.25, 0.30, 0.20, 0.15, 0.08, 0.02]))
    
    # Inject partial shipment issue (8% chance warehouse was short on stock and shipped incomplete order)
    partial_shipment = np.random.binomial(1, 0.08)
    if partial_shipment:
        shipped_quantity = int(order_quantity * np.random.uniform(0.60, 0.95))
    else:
        shipped_quantity = order_quantity
        
    # OTIF (On-Time In-Full) evaluation logic
    is_on_time = actual_delivery_date <= promised_delivery_date
    is_in_full = shipped_quantity == order_quantity
    
    if is_on_time and is_in_full:
        fulfillment_status = "OTIF"                      # Best case: delivered on time and complete
    elif not is_on_time and is_in_full:
        fulfillment_status = "Delayed - Full"            # Complete order, but delivered late
    elif is_on_time and not is_in_full:
        fulfillment_status = "On-Time - Partial"         # Arrived on time, but missing items
    else:
        fulfillment_status = "Delayed - Partial"         # Worst case: late and missing items
        
    order_list.append({
        "order_id": order_id,
        "order_date": order_date.strftime("%Y-%m-%d"),
        "product_id": prod["product_id"],
        "warehouse_id": wh_id,
        "supplier_id": supp_id,
        "order_quantity": order_quantity,
        "shipped_quantity": shipped_quantity,
        "promised_delivery_date": promised_delivery_date.strftime("%Y-%m-%d"),
        "actual_delivery_date": actual_delivery_date.strftime("%Y-%m-%d"),
        "fulfillment_status": fulfillment_status
    })

fact_orders_fulfillment = pd.DataFrame(order_list)

# ==============================================================================
# SECTION 5: FACT TABLE - WEEKLY INVENTORY SNAPSHOTS (fact_inventory_snapshot)
# Purpose: Tracks weekly stock counts across every warehouse and SKU to measure
#          holding costs, reorder alerts, and out-of-stock events.
# ==============================================================================
# Generate weekly Monday dates for all 52 weeks in 2025
snapshot_dates = pd.date_range(start=START_DATE, end=END_DATE, freq="W-MON")

inventory_snapshots = []
for s_date in snapshot_dates:
    s_date_str = s_date.strftime("%Y-%m-%d")
    for wh_id in dim_warehouses["warehouse_id"]:
        for prod_id in dim_products["product_id"]:
            # Set baseline warehouse targets
            safety_stock = int(np.random.choice([30, 50, 80, 120]))
            reorder_point = int(safety_stock * np.random.uniform(1.8, 2.4))
            
            # Simulate stock status: 82% normal, 12% dangerously low, 6% total stockout (0 units)
            stock_state = np.random.choice(["normal", "low", "stockout"], p=[0.82, 0.12, 0.06])
            if stock_state == "stockout":
                stock_on_hand = 0
            elif stock_state == "low":
                stock_on_hand = int(np.random.uniform(1, safety_stock))
            else:
                stock_on_hand = int(np.random.uniform(reorder_point, reorder_point * 2.5))
                
            unit_holding_cost_rate = 0.20  # Industry standard 20% annual inventory carrying cost
            
            inventory_snapshots.append({
                "snapshot_date": s_date_str,
                "product_id": prod_id,
                "warehouse_id": wh_id,
                "stock_on_hand": stock_on_hand,
                "safety_stock_level": safety_stock,
                "reorder_point": reorder_point,
                "annual_holding_rate": unit_holding_cost_rate
            })

fact_inventory_snapshot = pd.DataFrame(inventory_snapshots)

# ==============================================================================
# SECTION 6: CSV EXPORT
# Purpose: Saves the data structures as standard CSV files for SQL and Power BI import.
# ==============================================================================
dim_warehouses.to_csv("dim_warehouses.csv", index=False)
# Drop internal simulation column 'delay_risk_score' so the exported supplier file is clean
dim_suppliers.drop(columns=["delay_risk_score"]).to_csv("dim_suppliers.csv", index=False)
dim_products.to_csv("dim_products.csv", index=False)
fact_orders_fulfillment.to_csv("fact_orders_fulfillment.csv", index=False)
fact_inventory_snapshot.to_csv("fact_inventory_snapshot.csv", index=False)

# Print execution summary to verify counts
print("Data generation complete. Exported 5 CSV files:")
print(f" - dim_warehouses.csv: {len(dim_warehouses)} rows")
print(f" - dim_suppliers.csv: {len(dim_suppliers)} rows")
print(f" - dim_products.csv: {len(dim_products)} rows")
print(f" - fact_orders_fulfillment.csv: {len(fact_orders_fulfillment)} rows")
print(f" - fact_inventory_snapshot.csv: {len(fact_inventory_snapshot)} rows")