"""
SUPPLY CHAIN RISK INTELLIGENCE PLATFORM - DATA GENERATOR
Simulates a fictional global electronics & auto-components manufacturer.
Generates realistic, CONNECTED data (not random) across all 18 tables.
Outputs one CSV per table, ready for SQL Server BULK INSERT.
"""

import numpy as np
import pandas as pd
from faker import Faker
from datetime import date, timedelta
import random

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

OUT_DIR = "/home/claude/supply_chain_project/data"
START_DATE = date(2022, 1, 1)
END_DATE = date(2024, 12, 31)
ALL_MONTHS = pd.date_range(START_DATE, END_DATE, freq="MS").date.tolist()

# ------------------------------------------------------------------
# 1. COUNTRIES
# Real countries, grouped into regions. Some are deliberately marked
# as higher baseline risk (matches real-world sourcing hot spots),
# so later risk scores and delays have something real to correlate with.
# ------------------------------------------------------------------
COUNTRY_DATA = [
    # (name, region, currency, base_risk)
    ("China", "East Asia", "CNY", 42),
    ("Taiwan", "East Asia", "TWD", 48),
    ("Vietnam", "Southeast Asia", "VND", 38),
    ("India", "South Asia", "INR", 40),
    ("South Korea", "East Asia", "KRW", 20),
    ("Japan", "East Asia", "JPY", 15),
    ("Thailand", "Southeast Asia", "THB", 35),
    ("Malaysia", "Southeast Asia", "MYR", 28),
    ("Indonesia", "Southeast Asia", "IDR", 45),
    ("Philippines", "Southeast Asia", "PHP", 42),
    ("Bangladesh", "South Asia", "BDT", 55),
    ("Mexico", "North America", "MXN", 33),
    ("United States", "North America", "USD", 12),
    ("Canada", "North America", "CAD", 10),
    ("Germany", "Europe", "EUR", 14),
    ("Poland", "Europe", "PLN", 22),
    ("Netherlands", "Europe", "EUR", 12),
    ("United Kingdom", "Europe", "GBP", 20),
    ("Turkey", "Europe", "TRY", 52),
    ("Brazil", "South America", "BRL", 40),
    ("South Africa", "Africa", "ZAR", 48),
    ("Egypt", "Africa", "EGP", 50),
    ("Nigeria", "Africa", "NGN", 58),
    ("United Arab Emirates", "Middle East", "AED", 25),
    ("Saudi Arabia", "Middle East", "SAR", 30),
]
countries = pd.DataFrame(COUNTRY_DATA, columns=["country_name", "region", "currency_code", "base_risk_score"])
countries.insert(0, "country_id", range(1, len(countries) + 1))
countries.to_csv(f"{OUT_DIR}/countries.csv", index=False)

def country_ids_by_region():
    return countries.groupby("region")["country_id"].apply(list).to_dict()

# ------------------------------------------------------------------
# 2. SUPPLIERS (100)
# Weighted so more suppliers sit in the classic electronics-manufacturing
# countries (China, Taiwan, Vietnam, South Korea, Malaysia) - realistic.
# ------------------------------------------------------------------
N_SUPPLIERS = 100
supplier_country_weights = countries.set_index("country_id")["country_name"].map(
    lambda n: 5 if n in ["China", "Taiwan", "Vietnam", "South Korea", "Malaysia"] else
              3 if n in ["India", "Thailand", "Mexico", "Indonesia"] else 1
)
supplier_country_weights = supplier_country_weights / supplier_country_weights.sum()

supplier_countries = np.random.choice(countries["country_id"], size=N_SUPPLIERS, p=supplier_country_weights.values)

suppliers = pd.DataFrame({
    "supplier_id": range(1, N_SUPPLIERS + 1),
    "supplier_name": [fake.company() + random.choice([" Electronics", " Components", " Manufacturing", " Industries", " Co."]) for _ in range(N_SUPPLIERS)],
    "country_id": supplier_countries,
    "reliability_score": np.round(np.clip(np.random.normal(78, 12, N_SUPPLIERS), 30, 99), 1),
    "onboarded_date": [fake.date_between(date(2015, 1, 1), date(2023, 1, 1)) for _ in range(N_SUPPLIERS)],
})
# Lower reliability slightly for suppliers in higher base-risk countries - realistic correlation
risk_lookup = countries.set_index("country_id")["base_risk_score"]
suppliers["reliability_score"] = np.round(
    np.clip(suppliers["reliability_score"] - suppliers["country_id"].map(risk_lookup) * 0.15, 25, 99), 1
)
suppliers.to_csv(f"{OUT_DIR}/suppliers.csv", index=False)

# ------------------------------------------------------------------
# 3. FACTORIES (40) - our own manufacturing sites
# ------------------------------------------------------------------
N_FACTORIES = 40
factory_country_weights = supplier_country_weights  # similar geographic logic
factory_countries = np.random.choice(countries["country_id"], size=N_FACTORIES, p=factory_country_weights.values)
factory_cities = [fake.city() for _ in range(N_FACTORIES)]

factories = pd.DataFrame({
    "factory_id": range(1, N_FACTORIES + 1),
    "factory_name": [f"{city} Assembly Plant" for city in factory_cities],
    "country_id": factory_countries,
    "capacity_units_per_month": np.random.randint(20000, 300000, N_FACTORIES),
})
factories.to_csv(f"{OUT_DIR}/factories.csv", index=False)

# ------------------------------------------------------------------
# 4. PRODUCTS (60) - electronics & auto-components catalog
# ------------------------------------------------------------------
PRODUCT_CATALOG = {
    "Semiconductors": ["Microcontroller Unit", "Power Management IC", "Memory Chip", "Sensor IC", "RF Transceiver Chip"],
    "Connectors & Cables": ["USB-C Connector", "Wiring Harness", "Fiber Optic Cable", "Board-to-Board Connector", "HDMI Cable Assembly"],
    "Batteries & Power": ["Lithium-Ion Battery Cell", "Battery Management System", "DC-DC Converter", "Power Adapter", "Capacitor Bank"],
    "Sensors": ["Proximity Sensor", "Temperature Sensor", "Pressure Sensor", "LIDAR Module", "Accelerometer"],
    "Displays & Optics": ["LCD Display Panel", "OLED Module", "Camera Lens Assembly", "Touchscreen Panel", "LED Backlight Unit"],
    "Auto Components": ["Electronic Control Unit", "Brake Sensor Module", "Fuel Injector", "Airbag Control Module", "Dashboard Display Unit"],
}
products_list = []
pid = 1
for category, items in PRODUCT_CATALOG.items():
    for item in items:
        for variant in ["Standard", "Pro", "Compact"]:
            if pid > 60:
                break
            products_list.append((pid, f"{item} - {variant}", category,
                                   round(np.random.uniform(1.5, 450), 2),
                                   round(np.random.uniform(0.02, 8.5), 2)))
            pid += 1
products = pd.DataFrame(products_list, columns=["product_id", "product_name", "category", "unit_price", "unit_weight_kg"])
products.to_csv(f"{OUT_DIR}/products.csv", index=False)
N_PRODUCTS = len(products)

# ------------------------------------------------------------------
# 5. WAREHOUSES (25) - finished goods storage, near demand centers
# ------------------------------------------------------------------
N_WAREHOUSES = 25
wh_country_weights = countries.set_index("country_id")["country_name"].map(
    lambda n: 4 if n in ["United States", "Germany", "United Kingdom", "China", "Netherlands"] else
              2 if n in ["Mexico", "Poland", "India", "Japan"] else 1
)
wh_country_weights = wh_country_weights / wh_country_weights.sum()
wh_countries = np.random.choice(countries["country_id"], size=N_WAREHOUSES, p=wh_country_weights.values)

warehouses = pd.DataFrame({
    "warehouse_id": range(1, N_WAREHOUSES + 1),
    "warehouse_name": [f"{fake.city()} Distribution Center" for _ in range(N_WAREHOUSES)],
    "country_id": wh_countries,
    "capacity_units": np.random.randint(50000, 500000, N_WAREHOUSES),
})
warehouses.to_csv(f"{OUT_DIR}/warehouses.csv", index=False)

# ------------------------------------------------------------------
# 6. PORTS (30) - real-sounding major ports per region
# ------------------------------------------------------------------
PORT_NAMES = {
    "China": ["Port of Shanghai", "Port of Shenzhen", "Port of Ningbo"],
    "Taiwan": ["Port of Kaohsiung"],
    "Vietnam": ["Port of Ho Chi Minh City", "Port of Hai Phong"],
    "India": ["Port of Mumbai", "Port of Chennai"],
    "South Korea": ["Port of Busan"],
    "Japan": ["Port of Yokohama"],
    "Thailand": ["Port of Laem Chabang"],
    "Malaysia": ["Port Klang"],
    "Indonesia": ["Port of Tanjung Priok"],
    "Philippines": ["Port of Manila"],
    "Bangladesh": ["Port of Chittagong"],
    "Mexico": ["Port of Veracruz", "Port of Manzanillo"],
    "United States": ["Port of Los Angeles", "Port of Long Beach", "Port of Savannah"],
    "Canada": ["Port of Vancouver"],
    "Germany": ["Port of Hamburg"],
    "Poland": ["Port of Gdansk"],
    "Netherlands": ["Port of Rotterdam"],
    "United Kingdom": ["Port of Felixstowe"],
    "Turkey": ["Port of Istanbul"],
    "Brazil": ["Port of Santos"],
    "South Africa": ["Port of Durban"],
    "Egypt": ["Port of Alexandria"],
    "Nigeria": ["Port of Lagos"],
    "United Arab Emirates": ["Port of Jebel Ali"],
    "Saudi Arabia": ["Port of Jeddah"],
}
country_name_to_id = countries.set_index("country_name")["country_id"].to_dict()
port_rows = []
port_id = 1
for cname, plist in PORT_NAMES.items():
    for pname in plist:
        port_rows.append((port_id, pname, country_name_to_id[cname], round(np.random.uniform(10, 70), 1)))
        port_id += 1
ports = pd.DataFrame(port_rows, columns=["port_id", "port_name", "country_id", "avg_congestion_score"])
# bump congestion score for ports in higher-risk countries - realistic correlation
ports["avg_congestion_score"] = np.round(
    np.clip(ports["avg_congestion_score"] + ports["country_id"].map(risk_lookup) * 0.25, 5, 95), 1
)
ports.to_csv(f"{OUT_DIR}/ports.csv", index=False)
N_PORTS = len(ports)

print("Reference tables done:")
print(f"  countries: {len(countries)}, suppliers: {len(suppliers)}, factories: {len(factories)}")
print(f"  products: {len(products)}, warehouses: {len(warehouses)}, ports: {len(ports)}")

# ------------------------------------------------------------------
# 7. SUPPLIER_PRODUCTS - each supplier makes 3-8 of our products
# ------------------------------------------------------------------
sp_rows = []
sp_id = 1
for sid in suppliers["supplier_id"]:
    n_products = random.randint(3, 8)
    chosen_products = np.random.choice(products["product_id"], size=n_products, replace=False)
    for pid_ in chosen_products:
        base_price = float(products.loc[products["product_id"] == pid_, "unit_price"].iloc[0])
        sp_rows.append((
            sp_id, sid, pid_,
            round(base_price * np.random.uniform(0.4, 0.75), 2),  # supplier cost is a fraction of sell price
            int(np.random.choice([7, 10, 14, 21, 30, 45], p=[0.1, 0.2, 0.25, 0.2, 0.15, 0.1]))
        ))
        sp_id += 1
supplier_products = pd.DataFrame(sp_rows, columns=["supplier_product_id", "supplier_id", "product_id", "unit_cost", "avg_lead_time_days"])
supplier_products.to_csv(f"{OUT_DIR}/supplier_products.csv", index=False)

# ------------------------------------------------------------------
# 8. FACTORY_SUPPLIERS - each factory buys from 4-10 suppliers
# ------------------------------------------------------------------
fs_rows = []
fs_id = 1
for fid in factories["factory_id"]:
    n_suppliers = random.randint(4, 10)
    chosen = np.random.choice(suppliers["supplier_id"], size=n_suppliers, replace=False)
    for sid in chosen:
        fs_rows.append((fs_id, fid, sid))
        fs_id += 1
factory_suppliers = pd.DataFrame(fs_rows, columns=["factory_supplier_id", "factory_id", "supplier_id"])
factory_suppliers.to_csv(f"{OUT_DIR}/factory_suppliers.csv", index=False)

# ------------------------------------------------------------------
# 9. PRODUCT_FACTORIES - each product made at 1-3 factories
# ------------------------------------------------------------------
pf_rows = []
pf_id = 1
for pid_ in products["product_id"]:
    n_factories = random.randint(1, 3)
    chosen = np.random.choice(factories["factory_id"], size=n_factories, replace=False)
    for fid in chosen:
        pf_rows.append((pf_id, pid_, fid))
        pf_id += 1
product_factories = pd.DataFrame(pf_rows, columns=["product_factory_id", "product_id", "factory_id"])
product_factories.to_csv(f"{OUT_DIR}/product_factories.csv", index=False)

print("Bridge tables done:")
print(f"  supplier_products: {len(supplier_products)}, factory_suppliers: {len(factory_suppliers)}, product_factories: {len(product_factories)}")

# ------------------------------------------------------------------
# 10. POLITICAL_RISK_INDEX - monthly score per country
# One country (Bangladesh) gets a deliberate "crisis arc" in 2023 -
# this becomes the centerpiece story used in Steps 5-9 later.
# ------------------------------------------------------------------
CRISIS_COUNTRY = "Bangladesh"
CRISIS_MONTHS = pd.date_range("2023-06-01", "2023-11-01", freq="MS").date.tolist()

pri_rows = []
pri_id = 1
for _, row in countries.iterrows():
    base = row["base_risk_score"]
    for m in ALL_MONTHS:
        noise = np.random.normal(0, 4)
        score = base + noise
        if row["country_name"] == CRISIS_COUNTRY and m in CRISIS_MONTHS:
            # risk ramps up then partially recovers - a real story arc
            step = CRISIS_MONTHS.index(m)
            bump = [10, 22, 35, 30, 18, 8][step]
            score += bump
        pri_rows.append((pri_id, row["country_id"], m, round(float(np.clip(score, 2, 99)), 1)))
        pri_id += 1
political_risk_index = pd.DataFrame(pri_rows, columns=["political_risk_id", "country_id", "month_year", "risk_score"])
political_risk_index.to_csv(f"{OUT_DIR}/political_risk_index.csv", index=False)

# ------------------------------------------------------------------
# 11. WEATHER_EVENTS - storms/floods, weighted toward monsoon/typhoon
# season (Jun-Oct) in South/Southeast Asia - realistic seasonality.
# ------------------------------------------------------------------
weather_rows = []
w_id = 1
storm_prone = countries[countries["region"].isin(["Southeast Asia", "South Asia", "East Asia"])]["country_id"].tolist()
N_WEATHER = 5200
for _ in range(N_WEATHER):
    cid = int(np.random.choice(countries["country_id"]))
    month_bias = countries.loc[countries["country_id"] == cid, "region"].iloc[0] in ["Southeast Asia", "South Asia"]
    month = np.random.choice(range(6, 11)) if (month_bias and random.random() < 0.6) else np.random.choice(range(1, 13))
    year = random.choice([2022, 2023, 2024])
    day = random.randint(1, 28)
    event_date = date(year, int(month), day)
    event_type = np.random.choice(["Storm", "Typhoon", "Flood", "Heatwave", "Fog Delay"],
                                   p=[0.3, 0.2, 0.25, 0.15, 0.1])
    severity = round(float(np.clip(np.random.normal(45, 20), 5, 99)), 1)
    country_ports = ports[ports["country_id"] == cid]["port_id"].tolist()
    port_id_val = int(random.choice(country_ports)) if country_ports and random.random() < 0.7 else None
    weather_rows.append((w_id, cid, port_id_val, event_date, event_type, severity))
    w_id += 1
weather_events = pd.DataFrame(weather_rows, columns=["weather_event_id", "country_id", "port_id", "event_date", "event_type", "severity_score"])
weather_events.to_csv(f"{OUT_DIR}/weather_events.csv", index=False)

# ------------------------------------------------------------------
# 12. NEWS_EVENTS - templated headlines w/ sentiment (own wording,
# not copied from any real source), tied to countries/suppliers.
# ------------------------------------------------------------------
NEWS_TEMPLATES_NEG = [
    "Labor strike disrupts factory operations in {loc}",
    "Port congestion worsens amid staffing shortages in {loc}",
    "New tariffs announced affecting exporters in {loc}",
    "Currency volatility raises costs for manufacturers in {loc}",
    "Regulatory crackdown targets manufacturing sector in {loc}",
    "Fuel shortage disrupts logistics networks in {loc}",
]
NEWS_TEMPLATES_POS = [
    "Government announces infrastructure investment in {loc}",
    "New trade agreement expected to boost exports from {loc}",
    "Manufacturing output rises as demand strengthens in {loc}",
    "Port expansion project completed ahead of schedule in {loc}",
]
news_rows = []
n_id = 1
N_NEWS = 6000
for _ in range(N_NEWS):
    cid = int(np.random.choice(countries["country_id"]))
    cname = countries.loc[countries["country_id"] == cid, "country_name"].iloc[0]
    is_crisis_window = (cname == CRISIS_COUNTRY)
    neg_prob = 0.75 if is_crisis_window else 0.4
    is_neg = random.random() < neg_prob
    template = random.choice(NEWS_TEMPLATES_NEG if is_neg else NEWS_TEMPLATES_POS)
    headline = template.format(loc=cname)
    sentiment = round(float(np.random.uniform(-0.95, -0.2)) if is_neg else float(np.random.uniform(0.2, 0.9)), 2)
    year = random.choice([2022, 2023, 2024])
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    supplier_id_val = None
    if random.random() < 0.4:
        same_country_suppliers = suppliers[suppliers["country_id"] == cid]["supplier_id"].tolist()
        if same_country_suppliers:
            supplier_id_val = int(random.choice(same_country_suppliers))
    news_rows.append((n_id, cid, supplier_id_val, date(year, month, day), headline, sentiment))
    n_id += 1
news_events = pd.DataFrame(news_rows, columns=["news_event_id", "country_id", "supplier_id", "event_date", "headline", "sentiment_score"])
news_events.to_csv(f"{OUT_DIR}/news_events.csv", index=False)

# ------------------------------------------------------------------
# 13. FUEL_PRICES - by region/month, gentle upward-then-down trend
# (mirrors real 2022 energy price spike, for realism)
# ------------------------------------------------------------------
regions = countries["region"].unique().tolist()
fuel_rows = []
f_id = 1
for region in regions:
    for i, m in enumerate(ALL_MONTHS):
        # trend: spike through 2022, gradual decline through 2024
        trend = 90 + 25 * np.sin(i / 6) + (15 if m.year == 2022 else 0)
        price = round(float(np.clip(trend + np.random.normal(0, 5), 55, 140)), 2)
        fuel_rows.append((f_id, region, m, price))
        f_id += 1
fuel_prices = pd.DataFrame(fuel_rows, columns=["fuel_price_id", "region", "month_year", "price_per_barrel"])
fuel_prices.to_csv(f"{OUT_DIR}/fuel_prices.csv", index=False)

print("Risk tables done:")
print(f"  political_risk_index: {len(political_risk_index)}, weather_events: {len(weather_events)}")
print(f"  news_events: {len(news_events)}, fuel_prices: {len(fuel_prices)}")

# ------------------------------------------------------------------
# Helper lookups used to make delays REAL rather than random
# ------------------------------------------------------------------
supplier_country_lookup = suppliers.set_index("supplier_id")["country_id"]
port_country_lookup = ports.set_index("port_id")["country_id"]
ports_by_country = ports.groupby("country_id")["port_id"].apply(list).to_dict()
pri_lookup = political_risk_index.set_index(["country_id", "month_year"])["risk_score"].to_dict()
weather_by_country_month = {}
for _, w in weather_events.iterrows():
    key = (w["country_id"], date(w["event_date"].year if hasattr(w["event_date"], "year") else w["event_date"].year, 1, 1))
for _, w in weather_events.iterrows():
    d = w["event_date"]
    key = (w["country_id"], date(d.year, d.month, 1))
    weather_by_country_month.setdefault(key, []).append(w["severity_score"])

def month_key(d):
    return date(d.year, d.month, 1)

def get_political_risk(country_id, d):
    return pri_lookup.get((country_id, month_key(d)), 30)

def get_weather_severity(country_id, d):
    vals = weather_by_country_month.get((country_id, month_key(d)), [])
    return max(vals) if vals else 0

# ------------------------------------------------------------------
# 14. PURCHASE_ORDERS (~70,000) - real orders against supplier_products
# ------------------------------------------------------------------
N_PO = 70000
po_rows = []
sp_sample = supplier_products.sample(N_PO, replace=True, random_state=1).reset_index(drop=True)
order_dates = [fake.date_between(START_DATE, END_DATE) for _ in range(N_PO)]

for i in range(N_PO):
    sp = sp_sample.iloc[i]
    od = order_dates[i]
    lead = int(sp["avg_lead_time_days"])
    expected = od + timedelta(days=lead)
    qty = int(np.random.choice([50, 100, 250, 500, 1000, 2500], p=[0.25, 0.25, 0.2, 0.15, 0.1, 0.05]))
    # status depends on whether expected date has passed relative to our data horizon
    if expected > END_DATE:
        status = np.random.choice(["Pending", "Shipped"], p=[0.4, 0.6])
    else:
        status = np.random.choice(["Received", "Delayed"], p=[0.85, 0.15])
    po_rows.append((i + 1, int(sp["supplier_id"]), int(sp["product_id"]), od, expected, qty, status))

purchase_orders = pd.DataFrame(po_rows, columns=["po_id", "supplier_id", "product_id", "order_date", "expected_date", "quantity", "status"])
purchase_orders.to_csv(f"{OUT_DIR}/purchase_orders.csv", index=False)

# ------------------------------------------------------------------
# 15. SHIPMENTS (~70,000, one per PO) - delay_days is DRIVEN by
# political risk + weather severity + port congestion, not random.
# This is the key table for later ML delay-prediction work.
# ------------------------------------------------------------------
warehouse_ids = warehouses["warehouse_id"].tolist()
port_congestion_lookup = ports.set_index("port_id")["avg_congestion_score"]

ship_rows = []
for i, po in purchase_orders.iterrows():
    supplier_country = int(supplier_country_lookup[po["supplier_id"]])
    country_ports = ports_by_country.get(supplier_country)
    if not country_ports:
        # land-locked-ish fallback: nearest region port
        region = countries.loc[countries["country_id"] == supplier_country, "region"].iloc[0]
        region_countries = countries[countries["region"] == region]["country_id"].tolist()
        fallback_ports = ports[ports["country_id"].isin(region_countries)]["port_id"].tolist()
        origin_port = random.choice(fallback_ports) if fallback_ports else int(ports["port_id"].sample(1).iloc[0])
    else:
        origin_port = random.choice(country_ports)

    dest_warehouse = random.choice(warehouse_ids)
    ship_date = po["order_date"] + timedelta(days=random.randint(2, 7))  # processing time
    base_transit = random.randint(10, 40)

    political_risk = get_political_risk(supplier_country, ship_date)
    weather_sev = get_weather_severity(supplier_country, ship_date)
    congestion = float(port_congestion_lookup.get(origin_port, 30))

    # Zero-inflated delay model: most shipments are on time. Delays only
    # kick in when risk signals are genuinely elevated - so a real crisis
    # (like the Bangladesh arc) produces a visible spike against a calm baseline.
    elevated = (political_risk > 55) or (weather_sev > 50) or (congestion > 68)
    if not elevated:
        delay_days = 0 if random.random() < 0.96 else int(np.random.poisson(1.2))
    else:
        severity_factor = (
            max(0, political_risk - 55) * 0.3 +
            max(0, weather_sev - 50) * 0.25 +
            max(0, congestion - 68) * 0.2
        )
        delay_days = int(np.random.poisson(max(1, severity_factor))) if random.random() < 0.7 else 0

    expected_arrival = ship_date + timedelta(days=base_transit)
    actual_arrival = expected_arrival + timedelta(days=delay_days) if ship_date <= END_DATE else None

    if delay_days == 0:
        delay_reason = "None"
    elif weather_sev > 50 and weather_sev >= political_risk:
        delay_reason = "Weather"
    elif congestion > 55:
        delay_reason = "Port Congestion"
    elif political_risk > 50:
        delay_reason = "Political"
    else:
        delay_reason = "Operational"

    ship_rows.append((
        i + 1, int(po["po_id"]), origin_port, dest_warehouse, ship_date,
        expected_arrival, actual_arrival, delay_days, delay_reason
    ))

shipments = pd.DataFrame(ship_rows, columns=[
    "shipment_id", "po_id", "origin_port_id", "destination_warehouse_id",
    "ship_date", "expected_arrival_date", "actual_arrival_date", "delay_days", "delay_reason"
])
shipments.to_csv(f"{OUT_DIR}/shipments.csv", index=False)

print("Purchase orders + shipments done:")
print(f"  purchase_orders: {len(purchase_orders)}, shipments: {len(shipments)}")
print(f"  avg delay_days: {shipments['delay_days'].mean():.2f}, pct delayed: {(shipments['delay_days']>0).mean()*100:.1f}%")

# ------------------------------------------------------------------
# 16. CUSTOMER_ORDERS (~120,000) - demand for finished products
# Fulfillment rate dips slightly for products tied to delayed shipments
# in the same month, so stockouts trace back to real causes later.
# ------------------------------------------------------------------
N_CUST_ORDERS = 145000
co_products = np.random.choice(products["product_id"], size=N_CUST_ORDERS)
co_warehouses = np.random.choice(warehouse_ids, size=N_CUST_ORDERS)
co_dates = [fake.date_between(START_DATE, END_DATE) for _ in range(N_CUST_ORDERS)]

# monthly delay-rate per product, used to influence fulfillment realistically
shipments_with_product = shipments.merge(purchase_orders[["po_id", "product_id"]], on="po_id")
shipments_with_product["order_month"] = shipments_with_product["ship_date"].apply(month_key)
delay_rate_by_product_month = shipments_with_product.groupby(["product_id", "order_month"])["delay_days"].apply(lambda x: (x > 3).mean()).to_dict()

co_rows = []
for i in range(N_CUST_ORDERS):
    pid_ = int(co_products[i])
    od = co_dates[i]
    qty = int(np.random.choice([5, 10, 25, 50, 100], p=[0.35, 0.3, 0.2, 0.1, 0.05]))
    disruption_rate = delay_rate_by_product_month.get((pid_, month_key(od)), 0.05)
    fulfilled_prob = max(0.55, 1 - disruption_rate * 0.8)
    fulfilled = 1 if random.random() < fulfilled_prob else 0
    co_rows.append((i + 1, pid_, int(co_warehouses[i]), od, qty, fulfilled))

customer_orders = pd.DataFrame(co_rows, columns=["order_id", "product_id", "warehouse_id", "order_date", "quantity", "fulfilled"])
customer_orders.to_csv(f"{OUT_DIR}/customer_orders.csv", index=False)

# ------------------------------------------------------------------
# 17. INVENTORY (~54,000) - monthly snapshot per product x warehouse
# Stock dips when disruption rate for that product/month was high.
# ------------------------------------------------------------------
inv_rows = []
inv_id = 1
for pid_ in products["product_id"]:
    base_stock = int(np.random.randint(500, 5000))
    reorder_point = int(base_stock * 0.25)
    stock = base_stock
    for m in ALL_MONTHS:
        disruption = delay_rate_by_product_month.get((pid_, m), 0.05)
        demand_draw = int(np.random.normal(base_stock * 0.12, base_stock * 0.03))
        incoming = int(base_stock * 0.12 * (1 - disruption * 0.6))
        stock = max(0, stock - demand_draw + incoming)
        for wid in np.random.choice(warehouse_ids, size=min(9, len(warehouse_ids)), replace=False):
            inv_rows.append((inv_id, pid_, int(wid), m, int(stock * np.random.uniform(0.7, 1.3)), reorder_point))
            inv_id += 1
inventory = pd.DataFrame(inv_rows, columns=["inventory_id", "product_id", "warehouse_id", "snapshot_date", "stock_quantity", "reorder_point"])
inventory.to_csv(f"{OUT_DIR}/inventory.csv", index=False)

# ------------------------------------------------------------------
# 18. RETURNS (~4% of fulfilled customer orders)
# ------------------------------------------------------------------
fulfilled_orders = customer_orders[customer_orders["fulfilled"] == 1]
returned_sample = fulfilled_orders.sample(frac=0.04, random_state=2)
return_reasons = ["Defective Unit", "Wrong Item Shipped", "Customer Changed Mind", "Damaged in Transit", "Quality Issue"]

ret_rows = []
for i, (_, order) in enumerate(returned_sample.iterrows()):
    return_date = order["order_date"] + timedelta(days=random.randint(3, 30))
    ret_rows.append((i + 1, int(order["order_id"]), return_date, random.choice(return_reasons), random.randint(1, int(order["quantity"]))))

returns = pd.DataFrame(ret_rows, columns=["return_id", "order_id", "return_date", "reason", "quantity"])
returns.to_csv(f"{OUT_DIR}/returns.csv", index=False)

print("Transaction tables done:")
print(f"  customer_orders: {len(customer_orders)}, inventory: {len(inventory)}, returns: {len(returns)}")

# ------------------------------------------------------------------
# FINAL SUMMARY
# ------------------------------------------------------------------
all_tables = {
    "countries": countries, "suppliers": suppliers, "factories": factories,
    "products": products, "warehouses": warehouses, "ports": ports,
    "supplier_products": supplier_products, "factory_suppliers": factory_suppliers,
    "product_factories": product_factories, "political_risk_index": political_risk_index,
    "weather_events": weather_events, "news_events": news_events, "fuel_prices": fuel_prices,
    "purchase_orders": purchase_orders, "shipments": shipments,
    "customer_orders": customer_orders, "inventory": inventory, "returns": returns,
}
total_rows = sum(len(df) for df in all_tables.values())
print("\n=== TOTAL ROW COUNT ACROSS ALL 18 TABLES ===")
for name, df in all_tables.items():
    print(f"  {name}: {len(df):,}")
print(f"\nTOTAL: {total_rows:,} rows")
