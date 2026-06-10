"""
trends.py
---------
Monthly trend analysis module.
Shows how income, expenses, and savings changed over time.
Generates line charts saved in Charts/ folder.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

os.makedirs("Charts", exist_ok=True)


def get_monthly_trends(df):
    """
    Returns month-wise income, expense, savings as a sorted DataFrame.
    """
    income_m  = df[df["type"] == "income"].groupby("month_year")["amount"].sum()
    expense_m = df[df["type"] == "expense"].groupby("month_year")["amount"].sum()

    monthly = pd.DataFrame({"Income": income_m, "Expense": expense_m}).fillna(0)
    monthly["Savings"]      = monthly["Income"] - monthly["Expense"]
    monthly["Savings Rate"] = (monthly["Savings"] / monthly["Income"] * 100).round(2)

    monthly = monthly.reset_index()
    monthly["sort_key"] = pd.to_datetime(monthly["month_year"], format="%b %Y")
    monthly = monthly.sort_values("sort_key").reset_index(drop=True)

    return monthly


def print_trend_analysis(df):
    """
    Print month-wise trend with change indicators (↑ ↓ →).
    Shows whether spending went up or down compared to last month.
    """
    monthly = get_monthly_trends(df)

    print("\n" + "="*65)
    print("          📈 MONTHLY EXPENSE TREND ANALYSIS")
    print("="*65)
    print(f"  {'Month':<12} {'Expense':>10} {'Change':>10} {'Trend':>8} {'Savings Rate':>14}")
    print("-"*65)

    for i, row in monthly.iterrows():
        if i == 0:
            change_str = "    —"
            trend_icon = "  —"
        else:
            prev_expense = monthly.loc[i - 1, "Expense"]
            curr_expense = row["Expense"]
            change = curr_expense - prev_expense
            pct    = (change / prev_expense * 100) if prev_expense > 0 else 0

            if change > 0:
                trend_icon = "  ↑ UP"
                change_str = f"+₹{change:,.0f}"
            elif change < 0:
                trend_icon = "  ↓ DOWN"
                change_str = f"-₹{abs(change):,.0f}"
            else:
                trend_icon = "  → SAME"
                change_str = "  ₹0"

        rate_val = row["Savings Rate"]
        rate_bar = "█" * int(min(rate_val, 100) / 5) if rate_val != float('inf') and rate_val == rate_val else ""
        print(f"  {row['month_year']:<12} ₹{row['Expense']:>9,.0f} {change_str:>10} {trend_icon:<10} {row['Savings Rate']:>6.1f}%  {rate_bar}")

    print("-"*65)

    # Summary insights
    max_exp_idx = monthly["Expense"].idxmax()
    min_exp_idx = monthly["Expense"].idxmin()
    max_sav_idx = monthly["Savings"].idxmax()

    print(f"  🔴 Most expensive month  : {monthly.loc[max_exp_idx, 'month_year']} (₹{monthly.loc[max_exp_idx, 'Expense']:,.0f})")
    print(f"  🟢 Least expensive month : {monthly.loc[min_exp_idx, 'month_year']} (₹{monthly.loc[min_exp_idx, 'Expense']:,.0f})")
    print(f"  💰 Best savings month    : {monthly.loc[max_sav_idx, 'month_year']} (₹{monthly.loc[max_sav_idx, 'Savings']:,.0f})")

    # Overall trend
    first_exp = monthly.iloc[0]["Expense"]
    last_exp  = monthly.iloc[-1]["Expense"]
    if last_exp > first_exp:
        print(f"  📊 Overall Trend: Expenses are INCREASING over time ⚠️")
    elif last_exp < first_exp:
        print(f"  📊 Overall Trend: Expenses are DECREASING over time ✅")
    else:
        print(f"  📊 Overall Trend: Expenses are STABLE ➡️")

    print("="*65)


def plot_income_expense_trend(df):
    """
    Line chart: Income vs Expense vs Savings over months.
    Saved as Charts/trend_line.png
    """
    monthly = get_monthly_trends(df)
    months  = monthly["month_year"].tolist()
    x       = range(len(months))

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    # Plot lines
    ax.plot(x, monthly["Income"],  color="#82E0AA", linewidth=2.5, marker="o", markersize=7, label="Income")
    ax.plot(x, monthly["Expense"], color="#FF6B6B", linewidth=2.5, marker="o", markersize=7, label="Expense")
    ax.plot(x, monthly["Savings"], color="#45B7D1", linewidth=2.5, marker="o", markersize=7, label="Savings", linestyle="--")

    # Fill area between income and expense
    ax.fill_between(x, monthly["Income"], monthly["Expense"],
                    where=(monthly["Income"] >= monthly["Expense"]),
                    alpha=0.15, color="#82E0AA", label="Surplus")
    ax.fill_between(x, monthly["Income"], monthly["Expense"],
                    where=(monthly["Income"] < monthly["Expense"]),
                    alpha=0.15, color="#FF6B6B", label="Deficit")

    # Data labels
    for i, row in monthly.iterrows():
        ax.annotate(f"₹{row['Income']/1000:.0f}k",  (i, row["Income"]),
                    textcoords="offset points", xytext=(0, 10), color="#82E0AA", fontsize=8, ha="center")
        ax.annotate(f"₹{row['Expense']/1000:.0f}k", (i, row["Expense"]),
                    textcoords="offset points", xytext=(0, -15), color="#FF6B6B", fontsize=8, ha="center")

    # Styling
    ax.set_xticks(x)
    ax.set_xticklabels(months, color="white", fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _: f"₹{val/1000:.0f}k"))
    ax.tick_params(colors="white")
    ax.yaxis.set_tick_params(labelcolor="white")
    ax.set_title("Monthly Income vs Expense vs Savings", color="white", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Month", color="white", fontsize=11)
    ax.set_ylabel("Amount (₹)", color="white", fontsize=11)
    ax.legend(facecolor="#2e2e3e", labelcolor="white", fontsize=10)
    ax.grid(axis="y", color="#333355", linestyle="--", linewidth=0.7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

    plt.tight_layout()
    path = "Charts/trend_line.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"\n  Line chart saved   -> Charts/trend_line.png")


def plot_savings_rate_trend(df):
    """
    Bar chart showing savings rate % each month.
    Saved as Charts/savings_rate.png
    """
    monthly = get_monthly_trends(df)
    months  = monthly["month_year"].tolist()
    rates   = monthly["Savings Rate"].tolist()
    colors  = ["#82E0AA" if r >= 20 else ("#FFEAA7" if r >= 10 else "#FF6B6B") for r in rates]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    bars = ax.bar(months, rates, color=colors, edgecolor="#1e1e2e", width=0.5)

    # Value labels on top of bars
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{rate:.1f}%", ha="center", color="white", fontsize=10, fontweight="bold")

    # 20% reference line (healthy savings rate)
    ax.axhline(y=20, color="#FFD700", linestyle="--", linewidth=1.5, label="20% target")
    ax.text(len(months) - 0.5, 21, "Target 20%", color="#FFD700", fontsize=9)

    ax.set_title("Monthly Savings Rate (%)", color="white", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Month", color="white", fontsize=11)
    ax.set_ylabel("Savings Rate (%)", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.yaxis.set_tick_params(labelcolor="white")
    ax.xaxis.set_tick_params(labelcolor="white")
    ax.set_ylim(0, max(rates) + 10)
    ax.grid(axis="y", color="#333355", linestyle="--", linewidth=0.7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

    plt.tight_layout()
    path = "Charts/savings_rate.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Savings rate chart -> Charts/savings_rate.png")


def run_trends(df):
    """Main function — call this from main.py"""
    print_trend_analysis(df)
    plot_income_expense_trend(df)
    plot_savings_rate_trend(df)
    print("\n  Trend analysis complete!")


# -------------------------------------------------------
# Quick test
# -------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from Modules.loader import load_data
    df = load_data("Data/expenses.csv")
    run_trends(df)