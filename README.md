# Supply Chain Intelligence & Inventory Optimization Engine

An end-to-end data analytics and business intelligence pipeline modeling logistics fulfillment, vendor SLA compliance, warehouse inventory risk, and working capital optimization using **Python**, **MySQL**, and **Power BI**.

---

## Executive Summary
In global supply chain networks, poor vendor reliability and inventory imbalances directly drive unfulfilled orders, stockouts of high-margin SKUs, and inflated inventory carrying costs. 

This project simulates 15,000 logistics orders and 12,480 warehouse inventory snapshots across an enterprise distribution network to evaluate operational bottlenecks and optimize replenishment cycles.

---

## Business Problems Solved
* **Vendor Reliability Tracking:** Identifying suppliers causing repeated delivery overruns and failing contractual On-Time In-Full (OTIF) service level agreements (SLAs).
* **Stockout & Safety Stock Prevention:** Detecting critical inventory dips across distribution centers before they result in lost sales.
* **Working Capital Optimization:** Quantifying annual carrying costs tied up in overstocked warehouses to free up cash flow.

---

## Data Architecture & Schema
The project is built on a relational **Star Schema** within MySQL, designed for direct ingestion and high-performance querying in Power BI:

* **`dim_warehouses`**: Regional distribution hubs, geographic locations, and capacity thresholds.
* **`dim_suppliers`**: Supplier details, country of origin, baseline lead times, and contractual SLA targets.
* **`dim_products`**: 60 SKUs categorized by operational margin, unit cost, price, and standard production turnaround.
* **`fact_orders_fulfillment`**: 15,000 shipment transaction records tracking promised vs. actual delivery dates, quantity variances, and OTIF flags.
* **`fact_inventory_snapshot`**: 12,480 weekly stock audit records tracking on-hand inventory, safety stock targets, reorder points, and holding rates.

---

## Core KPIs & Analytical Measures

| Metric | Business Definition | Formula / Implementation |
| :--- | :--- | :--- |
| **OTIF Rate %** | Percentage of customer orders delivered on time and fully fulfilled | $\frac{\text{Orders (Actual Date} \le \text{Promised Date AND Shipped} = \text{Ordered)}}{\text{Total Orders}} \times 100$ |
| **Average Delay Days** | Mean duration of delivery overruns across delayed shipments | $\text{Average}(\text{Actual Delivery Date} - \text{Promised Delivery Date})$ |
| **Below Safety Stock Alert** | SKUs requiring immediate purchase order generation | $\text{Count of records where } 0 < \text{Stock on Hand} \le \text{Safety Stock}$ |
| **Stockout Incidents** | Zero-inventory audit events creating immediate revenue loss | $\text{Count of records where } \text{Stock on Hand} = 0$ |
| **Annual Carrying Cost** | Capital tied up in holding physical stock across fulfillment hubs | $\sum(\text{Stock on Hand} \times \text{Unit Cost} \times 20\% \text{ Holding Rate})$ |

---

## Repository Structure

```text
supply-chain-analytics-engine/
│
├── data/
│   ├── dim_warehouses.csv
│   ├── dim_suppliers.csv
│   ├── dim_products.csv
│   ├── fact_orders_fulfillment.csv
│   └── fact_inventory_snapshot.csv
│
├── sql/
│   ├── schema_ddl.sql          # Table definitions, data types, and primary keys
│   └── analytics_queries.sql   # OTIF analysis, supplier scorecard, and carrying cost queries
│
├── scripts/
│   └── generate_data.py        # Python script injecting delays, partial fulfillments, and stockouts
│
├── dashboard/
│   ├── Supply_Chain_Fulfillment_Analytics.pbix # Interactive Power BI reporting suite
│   └── dashboard_preview.pdf                   # Static visual report export
│
└── README.md                   # Project architecture and business insights\

Key SQL Insights Extracted
Vendor Bottlenecks: Certain international suppliers demonstrated actual OTIF delivery rates under 70%, consistently breaching contractual 95% SLA benchmarks and driving downstream stockouts.

Carrying Cost Distribution: Analysis of warehouse capacity revealed inventory concentration imbalances, with specific hubs exceeding 80% capacity utilization in slow-moving categories.

Safety Stock Buffer Risks: Automated reorder triggers flagged recurring stock depletion events in high-turnover product lines.

Dashboard Architecture (Power BI)
Page 1: Executive Logistics Overview

Top-line KPI cards for OTIF %, Total Orders, Average Overrun Days, and Stockout Counts.

Monthly delivery performance trends evaluating delivery consistency across time.

Supplier scorecard ranking vendors by SLA compliance.

Page 2: Inventory Health & Stockout Tracker

Warehouse storage utilization comparing current stock to maximum capacity limits.

Reorder alert table isolating SKUs operating below minimum safety thresholds.

Category-level risk heatmaps highlighting exposure to stock depletion.

Tech Stack
Data Synthesis: Python (pandas, numpy, Faker)

Relational Database: MySQL (DDL, CTEs, Aggregations, Window Logic)

Business Intelligence: Microsoft Power BI Desktop (DAX, Star Schema Modeling)
