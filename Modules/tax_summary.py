"""
tax_summary.py
--------------
HomeFi — Year-end Tax Summary (Indian IT Filing)
Identifies tax-relevant expenses: Rent (HRA), Healthcare (80D),
Education (80E), and summarises income for ITR.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime


CHARTS_DIR  = "Charts"
REPORTS_DIR = "Reports"
os.makedirs(CHARTS_DIR,  exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


# ── Tax rules (FY 2024-25) ────────────────────────────────────────────────
TAX_SLABS_NEW = [
    (300000,   0.00),
    (600000,   0.05),
    (900000,   0.10),
    (1200000,  0.15),
    (1500000,  0.20),
    (float("inf"), 0.30),
]

STANDARD_DEDUCTION = 75000     # New regime FY2024-25

DEDUCTION_RULES = {
    "80C":  {"limit": 150000, "categories": ["Education"],
             "label": "80C — Education / ELSS / PPF / LIC"},
    "80D":  {"limit":  25000, "categories": ["Healthcare"],
             "label": "80D — Medical Insurance / Health"},
    "HRA":  {"limit": None,   "categories": ["Rent"],
             "label": "HRA — House Rent Allowance"},
}


def _compute_tax_new_regime(taxable_income):
    """Compute tax under new regime (FY 2024-25)."""
    tax   = 0
    prev  = 0
    for slab, rate in TAX_SLABS_NEW:
        if taxable_income <= prev:
            break
        taxable_in_slab = min(taxable_income, slab) - prev
        tax  += taxable_in_slab * rate
        prev  = slab
    # 4% cess
    cess = tax * 0.04
    return tax, cess, tax + cess


def _section_header(title):
    print("\n" + "═" * 55)
    print(f"  {title}")
    print("═" * 55)


def run_tax_summary(df):
    """Full tax summary report — CLI output + text file."""
    df = df.copy()

    # Filter to selected financial year
    years_available = sorted(df["date"].dt.year.unique())
    print("\n  Available years in your data:")
    for i, y in enumerate(years_available, 1):
        print(f"    {i}. FY {y}-{str(y+1)[-2:]}")

    choice = input(f"\n  Select year (1-{len(years_available)}): ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(years_available)):
        print("  [!] Invalid choice.")
        return

    year  = years_available[int(choice) - 1]
    fy_df = df[df["date"].dt.year == year]

    inc_df  = fy_df[fy_df["type"] == "income"]
    exp_df  = fy_df[fy_df["type"] == "expense"]

    total_income  = inc_df["amount"].sum()
    total_expense = exp_df["amount"].sum()
    net_savings   = total_income - total_expense

    # ── Income breakdown ──────────────────────────────────────────────
    _section_header(f"INCOME SUMMARY — FY {year}-{str(year+1)[-2:]}")
    income_by_cat = inc_df.groupby("category")["amount"].sum()
    for cat, amt in income_by_cat.items():
        pct = amt / total_income * 100 if total_income > 0 else 0
        print(f"  {cat:<20} Rs. {amt:>10,.0f}   ({pct:.1f}%)")
    print(f"  {'─'*45}")
    print(f"  {'TOTAL INCOME':<20} Rs. {total_income:>10,.0f}")

    # ── Deductions ────────────────────────────────────────────────────
    _section_header("TAX DEDUCTIONS (OLD REGIME)")
    deduction_totals = {}
    for key, rule in DEDUCTION_RULES.items():
        cats   = rule["categories"]
        amt    = exp_df[exp_df["category"].isin(cats)]["amount"].sum()
        limit  = rule["limit"]
        claimable = min(amt, limit) if limit else amt
        deduction_totals[key] = claimable
        flag = "✅" if claimable > 0 else "⬜"
        limit_str = f"(Limit: Rs.{limit:,.0f})" if limit else "(No cap)"
        print(f"  {flag} {rule['label']}")
        print(f"     Spent: Rs.{amt:,.0f}  |  Claimable: Rs.{claimable:,.0f}  {limit_str}")

    total_deductions = sum(deduction_totals.values())
    print(f"\n  {'─'*45}")
    print(f"  Total Deductions (80C+80D+HRA) : Rs. {total_deductions:,.0f}")

    # ── Tax calculation ───────────────────────────────────────────────
    _section_header("ESTIMATED TAX LIABILITY")

    # Old regime
    taxable_old = max(0, total_income - total_deductions - STANDARD_DEDUCTION)
    tax_old, cess_old, total_old = _compute_tax_new_regime(taxable_old)

    # New regime
    taxable_new = max(0, total_income - STANDARD_DEDUCTION)
    tax_new, cess_new, total_new = _compute_tax_new_regime(taxable_new)

    print(f"\n  Standard Deduction (both regimes) : Rs. {STANDARD_DEDUCTION:,.0f}")
    print(f"\n  ┌{'─'*50}┐")
    print(f"  │{'OLD REGIME':^50}│")
    print(f"  ├{'─'*50}┤")
    print(f"  │  Gross Income          : Rs. {total_income:>14,.0f}       │")
    print(f"  │  Less: Deductions      : Rs. {total_deductions:>14,.0f}       │")
    print(f"  │  Less: Std. Deduction  : Rs. {STANDARD_DEDUCTION:>14,.0f}       │")
    print(f"  │  Taxable Income        : Rs. {taxable_old:>14,.0f}       │")
    print(f"  │  Income Tax            : Rs. {tax_old:>14,.0f}       │")
    print(f"  │  Cess (4%)             : Rs. {cess_old:>14,.0f}       │")
    print(f"  │  TOTAL TAX PAYABLE     : Rs. {total_old:>14,.0f}       │")
    print(f"  └{'─'*50}┘")

    print(f"\n  ┌{'─'*50}┐")
    print(f"  │{'NEW REGIME (Default FY2024-25)':^50}│")
    print(f"  ├{'─'*50}┤")
    print(f"  │  Gross Income          : Rs. {total_income:>14,.0f}       │")
    print(f"  │  Less: Std. Deduction  : Rs. {STANDARD_DEDUCTION:>14,.0f}       │")
    print(f"  │  Taxable Income        : Rs. {taxable_new:>14,.0f}       │")
    print(f"  │  Income Tax            : Rs. {tax_new:>14,.0f}       │")
    print(f"  │  Cess (4%)             : Rs. {cess_new:>14,.0f}       │")
    print(f"  │  TOTAL TAX PAYABLE     : Rs. {total_new:>14,.0f}       │")
    print(f"  └{'─'*50}┘")

    if total_old < total_new:
        print(f"\n  💡 OLD REGIME saves you Rs. {total_new - total_old:,.0f} — consider it!")
    elif total_new < total_old:
        print(f"\n  💡 NEW REGIME saves you Rs. {total_old - total_new:,.0f} — new regime is better.")
    else:
        print("\n  Both regimes result in the same tax.")

    # ── Category breakdown ────────────────────────────────────────────
    _section_header("EXPENSE CATEGORY BREAKDOWN")
    cat_totals = exp_df.groupby("category")["amount"].sum().sort_values(ascending=False)
    print(f"  {'Category':<20} {'Amount':>12}  {'% of Expenses':>14}")
    print(f"  {'─'*50}")
    for cat, amt in cat_totals.items():
        pct = amt / total_expense * 100 if total_expense > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"  {cat:<20} Rs.{amt:>10,.0f}  {pct:>6.1f}%  {bar}")
    print(f"  {'─'*50}")
    print(f"  {'TOTAL':<20} Rs.{total_expense:>10,.0f}")

    # ── Save text report ──────────────────────────────────────────────
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORTS_DIR, f"tax_summary_FY{year}_{ts}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"HomeFi Tax Summary — FY {year}-{str(year+1)[-2:]}\n")
        f.write(f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n")
        f.write("=" * 55 + "\n\n")
        f.write(f"Total Income   : Rs. {total_income:,.0f}\n")
        f.write(f"Total Expenses : Rs. {total_expense:,.0f}\n")
        f.write(f"Net Savings    : Rs. {net_savings:,.0f}\n\n")
        f.write("DEDUCTIONS (Old Regime)\n")
        for key, claimable in deduction_totals.items():
            f.write(f"  {DEDUCTION_RULES[key]['label']}: Rs. {claimable:,.0f}\n")
        f.write(f"\nOld Regime Tax : Rs. {total_old:,.0f}\n")
        f.write(f"New Regime Tax : Rs. {total_new:,.0f}\n")
    print(f"\n  [OK] Tax report saved: {report_path}")

    # ── Chart ─────────────────────────────────────────────────────────
    _make_tax_chart(total_income, total_expense, net_savings,
                    total_old, total_new, deduction_totals, year)


def _make_tax_chart(income, expense, savings, tax_old, tax_new,
                    deductions, year):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor="#1a1a2e")

    # Left: Income vs Expense vs Savings bar
    ax1 = axes[0]
    ax1.set_facecolor("#16213e")
    labels = ["Income", "Expenses", "Savings"]
    values = [income, expense, savings]
    colors = ["#00d4aa", "#e63946", "#2dc653"]
    bars   = ax1.bar(labels, values, color=colors, edgecolor="#1a1a2e", width=0.5)
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + income * 0.01,
                 f"Rs.{val:,.0f}", ha="center", color="white", fontsize=9, fontweight="bold")
    ax1.set_title(f"Financial Overview\nFY {year}-{str(year+1)[-2:]}",
                  color="#00d4aa", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Amount (Rs.)", color="#888888")
    ax1.tick_params(colors="white")
    ax1.spines[:].set_color("#333333")
    ax1.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"Rs.{x/1000:.0f}K")
    )

    # Right: Old vs New regime tax
    ax2 = axes[1]
    ax2.set_facecolor("#16213e")
    reg_labels = [f"Old Regime\n(with deductions)", f"New Regime\n(default)"]
    reg_vals   = [tax_old, tax_new]
    reg_colors = ["#f4a261", "#00d4aa"]
    bars2 = ax2.bar(reg_labels, reg_vals, color=reg_colors, edgecolor="#1a1a2e", width=0.4)
    for bar, val in zip(bars2, reg_vals):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(reg_vals) * 0.02,
                 f"Rs.{val:,.0f}", ha="center", color="white", fontsize=10, fontweight="bold")
    ax2.set_title(f"Tax Comparison\nFY {year}-{str(year+1)[-2:]}",
                  color="#00d4aa", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Tax Payable (Rs.)", color="#888888")
    ax2.tick_params(colors="white")
    ax2.spines[:].set_color("#333333")
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"Rs.{x/1000:.0f}K")
    )

    plt.suptitle("HomeFi — Year-End Tax Summary", color="white",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()

    out = os.path.join(CHARTS_DIR, f"tax_summary_{year}.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close()
    print(f"  [OK] Chart saved: {out}")


if __name__ == "__main__":
    from loader import load_data
    df = load_data("Data/expenses.csv")
    run_tax_summary(df)