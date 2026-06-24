"""
Supply Chain Risk Data Generator
---------------------------------
Author: Kumar Aditya
Purpose: Generates a realistic 12-month synthetic dataset for a fictional
         mid-size German manufacturer. Used to build the Power BI
         risk dashboard in this repo.

I modelled this after the kind of data I worked with at Spirka Technologies —
obviously anonymised and randomised, but structurally similar (delivery
windows, supplier reliability, warehouse fill rates, backorder counts).

Run this before opening the Power BI file to get fresh data:
    python generate_data.py

Outputs:
    data/supply_chain_data.csv     - main transaction-level dataset
    data/supplier_scorecard.csv    - supplier-level aggregates
    data/risk_flags.csv            - flagged incidents for drill-through
"""

import csv
import random
import os
from datetime import date, timedelta

random.seed(42)  # reproducible output — important for the demo screenshots

# ── Configuration ─────────────────────────────────────────────────────────────

START_DATE = date(2024, 1, 1)
END_DATE   = date(2024, 12, 31)

SUPPLIERS = [
    # (name, country, reliability_base, lead_time_days, disruption_risk)
    # reliability_base = baseline on-time delivery rate (0–1)
    # disruption_risk  = chance of a bad month with late shipments
    ("Müller Stahl GmbH",          "Germany",     0.94, 5,  0.04),
    ("Koch Kunststoffe KG",        "Germany",     0.91, 6,  0.06),
    ("Baltic Freight Partners",    "Poland",      0.87, 8,  0.10),
    ("Sächsische Metallwerk AG",   "Germany",     0.96, 4,  0.03),
    ("Eastern Auto Parts s.r.o.",  "Czech Rep.",  0.83, 10, 0.14),
    ("NordSee Logistics GmbH",     "Germany",     0.89, 7,  0.07),
    ("Vistula Components Sp.",     "Poland",      0.80, 11, 0.16),
    ("Rheinland Technik GmbH",     "Germany",     0.93, 5,  0.04),
    ("Prag Precision Parts s.r.o.","Czech Rep.",  0.85, 9,  0.12),
    ("Bremen Handel AG",           "Germany",     0.90, 6,  0.05),
]

PRODUCT_CATEGORIES = [
    "Raw Materials", "Mechanical Components", "Electronic Parts",
    "Packaging", "Fasteners & Fixings", "Seals & Gaskets",
    "Surface Treatments", "Assembly Kits"
]

WAREHOUSES = ["Berlin Main", "Hamburg Hub", "München South", "Leipzig Cross-dock"]

DISRUPTION_CAUSES = [
    "Port congestion", "Supplier capacity issue", "Quality hold",
    "Transport delay", "Customs clearance", "Weather / force majeure",
    "Demand spike", "IT system issue", "Supplier insolvency risk",
    "Short shipment"
]


def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def generate_transactions():
    """Generate order-level records across the full year."""
    rows = []
    order_id = 10001

    for supplier_data in SUPPLIERS:
        name, country, reliability, lead_time, disrupt_risk = supplier_data

        # vary the number of orders per supplier (bigger suppliers = more orders)
        n_orders = random.randint(60, 180)

        # simulate one or two bad months for disruption-prone suppliers
        bad_months = set()
        for _ in range(12):
            if random.random() < disrupt_risk:
                bad_months.add(random.randint(1, 12))

        for _ in range(n_orders):
            order_date = random_date(START_DATE, END_DATE)
            month = order_date.month

            # adjust on-time rate for bad months
            effective_reliability = reliability * (0.55 if month in bad_months else 1.0)
            on_time = random.random() < effective_reliability

            planned_lead = lead_time + random.randint(-1, 2)
            actual_lead  = planned_lead if on_time else planned_lead + random.randint(2, 12)

            qty_ordered   = random.randint(50, 2000)
            qty_received  = qty_ordered if random.random() > 0.07 else int(qty_ordered * random.uniform(0.7, 0.97))
            short_shipped = qty_ordered - qty_received

            unit_price = round(random.uniform(0.80, 340.0), 2)
            order_value = round(qty_ordered * unit_price, 2)

            defect_rate = round(max(0, random.gauss(0.018, 0.015)), 4)  # ~1.8% average defect rate
            defect_qty  = int(qty_received * defect_rate)

            category  = random.choice(PRODUCT_CATEGORIES)
            warehouse = random.choice(WAREHOUSES)

            rows.append({
                "order_id":        order_id,
                "order_date":      order_date.strftime("%Y-%m-%d"),
                "month":           month,
                "quarter":         f"Q{(month-1)//3 + 1}",
                "supplier_name":   name,
                "supplier_country":country,
                "product_category":category,
                "receiving_warehouse": warehouse,
                "qty_ordered":     qty_ordered,
                "qty_received":    qty_received,
                "short_shipped":   short_shipped,
                "unit_price_eur":  unit_price,
                "order_value_eur": order_value,
                "planned_lead_days": planned_lead,
                "actual_lead_days":  actual_lead,
                "on_time_delivery":  1 if on_time else 0,
                "days_late":       max(0, actual_lead - planned_lead),
                "defect_qty":      defect_qty,
                "defect_rate":     defect_rate,
            })
            order_id += 1

    return rows


def generate_supplier_scorecard(transactions):
    """Roll up transaction data to supplier level for the scorecard view."""
    from collections import defaultdict
    agg = defaultdict(lambda: {
        "total_orders": 0, "on_time": 0, "total_value": 0,
        "total_defects": 0, "total_received": 0, "total_days_late": 0,
        "late_orders": 0, "country": ""
    })

    for t in transactions:
        s = t["supplier_name"]
        agg[s]["total_orders"]   += 1
        agg[s]["on_time"]        += t["on_time_delivery"]
        agg[s]["total_value"]    += t["order_value_eur"]
        agg[s]["total_defects"]  += t["defect_qty"]
        agg[s]["total_received"] += t["qty_received"]
        agg[s]["total_days_late"] += t["days_late"]
        if not t["on_time_delivery"]:
            agg[s]["late_orders"] += 1
        agg[s]["country"] = t["supplier_country"]

    rows = []
    for supplier, d in agg.items():
        otd_rate    = round(d["on_time"] / d["total_orders"] * 100, 1) if d["total_orders"] else 0
        defect_rate = round(d["total_defects"] / d["total_received"] * 100, 2) if d["total_received"] else 0
        avg_delay   = round(d["total_days_late"] / d["late_orders"], 1) if d["late_orders"] else 0.0
        spend       = round(d["total_value"], 2)

        # Simple composite risk score: lower OTD + higher defects + higher avg_delay = higher risk
        # Scaled 1–10; I'm treating OTD as the biggest factor
        risk_score = round(
            (1 - otd_rate / 100) * 5 +
            min(defect_rate / 2, 2.5) +
            min(avg_delay / 10, 2.5),
            1
        )
        risk_label = (
            "High"   if risk_score >= 6 else
            "Medium" if risk_score >= 3 else
            "Low"
        )

        rows.append({
            "supplier_name":    supplier,
            "country":          d["country"],
            "total_orders":     d["total_orders"],
            "otd_rate_pct":     otd_rate,
            "avg_delay_days":   avg_delay,
            "defect_rate_pct":  defect_rate,
            "annual_spend_eur": spend,
            "risk_score":       risk_score,
            "risk_label":       risk_label,
        })

    # sort by risk score descending so the dashboard's default sort makes sense
    rows.sort(key=lambda x: x["risk_score"], reverse=True)
    return rows


def generate_risk_flags(transactions):
    """
    Pull out individual orders that meet flag criteria.
    These feed the 'Incidents' drill-through page in Power BI.
    """
    flags = []
    for t in transactions:
        reasons = []
        if t["days_late"] >= 7:
            reasons.append(f"Late delivery ({t['days_late']} days)")
        if t["defect_rate"] > 0.05:
            reasons.append(f"High defect rate ({t['defect_rate']*100:.1f}%)")
        if t["short_shipped"] > 0 and t["short_shipped"] / t["qty_ordered"] > 0.10:
            reasons.append(f"Short shipment ({t['short_shipped']} units, {t['short_shipped']/t['qty_ordered']*100:.0f}%)")

        if reasons:
            cause = random.choice(DISRUPTION_CAUSES)
            flags.append({
                "order_id":       t["order_id"],
                "order_date":     t["order_date"],
                "supplier_name":  t["supplier_name"],
                "flag_reason":    " | ".join(reasons),
                "disruption_cause": cause,
                "estimated_impact_eur": round(
                    t["order_value_eur"] * random.uniform(0.03, 0.18), 2
                ),
            })

    return flags


def write_csv(rows, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved: {filepath}  ({len(rows)} rows)")


if __name__ == "__main__":
    print("\nGenerating supply chain dataset...")
    transactions = generate_transactions()
    scorecard    = generate_supplier_scorecard(transactions)
    risk_flags   = generate_risk_flags(transactions)

    write_csv(transactions, "data/supply_chain_data.csv")
    write_csv(scorecard,    "data/supplier_scorecard.csv")
    write_csv(risk_flags,   "data/risk_flags.csv")

    print(f"\nSummary:")
    print(f"  Total orders generated : {len(transactions)}")
    print(f"  Risk flags raised      : {len(risk_flags)}")
    print(f"  Suppliers tracked      : {len(scorecard)}")
    print(f"\nDone. Load the CSV files into Power BI — see dashboard_guide.md for setup steps.\n")
