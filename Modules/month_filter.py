"""
month_filter.py
---------------
HomeFi — Filter analysis to a specific month.
Shows income, expenses, savings, category breakdown for one month.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


CHARTS_DIR = "Charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

COLORS = ["#00d4aa", "#f4a261", "#e63946", "#457b9d",
          "#2dc653", "#9b5de5", "#f15bb5", "#fee440",
          "#00bbf9", "#fb5607", "#8338ec", "#3a86ff"]


def _available_months(df):
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")
    months = sorted(df["month"].unique())
    return months


def _filter_df(df, period):
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")
    return df[df["month"] == period]


def _print_month_summary(mdf, period):
    income  = mdf[mdf["type"] == "income"]["amount"].sum()
    expense = mdf[mdf["type"] == "expense"]["amount"].sum()
    savings = income - expense
    rate    = (savings / income * 100) if income > 0 else 0

    print(f"\n  {'─'*48}")
    print(f"  MONTHLY REPORT — {str(period).upper()}")
    print(f"  {'─'*48}")
    print(f"  Total Income   : Rs. {income:>10,.2f}")
    print(f"  Total Expenses : Rs. {expense:>10,.2f}")
    print(f"  Net Savings    : Rs. {savings:>10,.2f}")

    if rate >= 30:
        badge = "🟢 Excellent"
    elif rate >= 20:
        badge = "🟡 Good"
    elif rate >= 10:
        badge = "🟠 Average"
    else:
        badge = "🔴 Low"

    print(f"  Savings Rate   : {rate:>9.1f}%  {badge}")
    print(f"  {'─'*48}")

    # Category breakdown
    exp_df = mdf[mdf["type"] == "expense"]
    if exp_df.empty:
        print("  No expenses recorded this month.")
        return income, expense, savings, rate

    cat_totals = exp_df.groupby("category")["amount"].sum().sort_values(ascending=False)
    print(f"\n  {'Category':<18} {'Amount':>10}  {'Share':>6}  Bar")
    print(f"  {'─'*55}")
    for cat, amt in cat_totals.items():
        pct  = (amt / expense * 100) if expense > 0 else 0
        bar  = "█" * int(pct / 5)
        print(f"  {cat:<18} Rs.{amt:>8,.0f}  {pct:>5.1f}%  {bar}")

    # Transactions list
    print(f"\n  {'─'*48}")
    print(f"  ALL TRANSACTIONS ({str(period)})")
    print(f"  {'─'*48}")
    print(f"  {'Date':<12} {'Type':<10} {'Category':<15} {'Amount':>10}  Description")
    print(f"  {'─'*70}")
    for _, row in mdf.sort_values("date").iterrows():
        sign = "-" if row["type"] == "expense" else "+"
        print(f"  {str(row['date'].date()):<12} {row['type']:<10} "
              f"{row['category']:<15} {sign}Rs.{row['amount']:>7,.0f}  "
              f"{str(row.get('description',''))[:20]}")

    return income, expense, savings, rate


def _make_month_chart(mdf, period):
    """Pie chart of category expenses for the selected month."""
    exp_df = mdf[mdf["type"] == "expense"]
    if exp_df.empty:
        return

    cat_totals = exp_df.groupby("category")["amount"].sum().sort_values(ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6),
                             facecolor="#1a1a2e")

    # ── Pie ───────────────────────────────────────────
    ax1 = axes[0]
    ax1.set_facecolor("#1a1a2e")
    wedge_props = {"linewidth": 2, "edgecolor": "#1a1a2e"}
    wedges, texts, autotexts = ax1.pie(
        cat_totals.values,
        labels=cat_totals.index,
        autopct="%1.1f%%",
        colors=COLORS[:len(cat_totals)],
        wedgeprops=wedge_props,
        startangle=140,
    )
    for t in texts:
        t.set_color("white")
        t.set_fontsize(9)
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(8)

    ax1.set_title(f"Expense Breakdown\n{str(period)}",
                  color="#00d4aa", fontsize=13, fontweight="bold", pad=15)

    # ── Bar ───────────────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor("#16213e")
    bars = ax2.barh(cat_totals.index[::-1],
                    cat_totals.values[::-1],
                    color=COLORS[:len(cat_totals)][::-1],
                    edgecolor="#1a1a2e", linewidth=0.5)

    for bar, val in zip(bars, cat_totals.values[::-1]):
        ax2.text(bar.get_width() + max(cat_totals.values) * 0.01,
                 bar.get_y() + bar.get_height() / 2,
                 f"Rs.{val:,.0f}", va="center", color="white", fontsize=8)

    ax2.set_title(f"Category Amounts\n{str(period)}",
                  color="#00d4aa", fontsize=13, fontweight="bold")
    ax2.set_xlabel("Amount (Rs.)", color="#888888")
    ax2.tick_params(colors="white")
    ax2.spines[:].set_color("#333333")
    ax2.set_xlim(0, max(cat_totals.values) * 1.22)

    plt.suptitle(f"HomeFi — Monthly Analysis: {str(period)}",
                 color="white", fontsize=15, fontweight="bold", y=1.01)
    plt.tight_layout()

    out = os.path.join(CHARTS_DIR, f"month_{str(period)}.png")
    plt.savefig(out, dpi=150, bbox_inches="tight",
                facecolor="#1a1a2e")
    plt.close()
    print(f"\n  [OK] Chart saved: {out}")


def run_month_filter(df):
    """Interactive month filter — user picks a month, sees full analysis."""
    months = _available_months(df)

    print("\n  Available months in your data:")
    for i, m in enumerate(months, 1):
        print(f"    {i:>2}. {m}")

    choice = input(f"\n  Select month (1-{len(months)}): ").strip()

    if not choice.isdigit() or not (1 <= int(choice) <= len(months)):
        print("  [!] Invalid choice.")
        return

    period = months[int(choice) - 1]
    mdf    = _filter_df(df, period)

    _print_month_summary(mdf, period)
    _make_month_chart(mdf, period)


if __name__ == "__main__":
    from loader import load_data
    df = load_data("Data/expenses.csv")
    run_month_filter(df)