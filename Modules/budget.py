"""
budget.py
---------
Budget management module.
User sets monthly budget per category.
Alerts generated if spending exceeds budget.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import json

os.makedirs("Charts", exist_ok=True)

# -------------------------------------------------------
# DEFAULT MONTHLY BUDGETS (in Rupees)
# User can change these values anytime
# -------------------------------------------------------
DEFAULT_BUDGETS = {
    "Food"         : 5000,
    "Rent"         : 9000,
    "Utilities"    : 2000,
    "Transport"    : 2000,
    "Entertainment": 1500,
    "Healthcare"   : 2000,
    "Education"    : 3000,
    "Clothing"     : 2000,
    "EMI"          : 4000,
    "Savings"      : 5000,
    "Other"        : 1000
}

BUDGET_FILE = "Data/budgets.json"


def load_budgets():
    """
    Load budgets from JSON file if it exists,
    otherwise return default budgets.
    """
    if os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_BUDGETS.copy()


def save_budgets(budgets):
    """Save budgets to JSON file for persistence."""
    os.makedirs("Data", exist_ok=True)
    with open(BUDGET_FILE, "w") as f:
        json.dump(budgets, f, indent=4)
    print(f"  ✅ Budgets saved to {BUDGET_FILE}")


def set_budget_interactive():
    """
    Interactive CLI to let user set/update budgets.
    """
    budgets = load_budgets()

    print("\n" + "="*50)
    print("       💼 SET MONTHLY BUDGETS")
    print("="*50)
    print("  (Press Enter to keep current value)\n")

    for category, current in budgets.items():
        try:
            user_input = input(f"  {category:<15} [Current: ₹{current:,}] → ₹ ").strip()
            if user_input:
                budgets[category] = float(user_input)
        except ValueError:
            print(f"  ⚠️  Invalid input for {category}, keeping ₹{current:,}")

    save_budgets(budgets)
    print("\n  ✅ All budgets updated!")
    return budgets


def get_monthly_category_spend(df):
    """
    Returns average monthly spending per category (expenses only).
    """
    expenses   = df[df["type"] == "expense"]
    num_months = df["month_year"].nunique()

    monthly_avg = expenses.groupby("category")["amount"].sum() / num_months
    return monthly_avg.round(2)


def check_budget_alerts(df):
    """
    Compare actual avg monthly spend vs budget.
    Returns a DataFrame with status for each category.
    """
    budgets    = load_budgets()
    actual_avg = get_monthly_category_spend(df)

    results = []
    for category, budget in budgets.items():
        actual = actual_avg.get(category, 0)
        diff   = actual - budget
        usage  = (actual / budget * 100) if budget > 0 else 0

        if usage >= 100:
            status = "EXCEEDED"
            icon   = "🔴"
        elif usage >= 80:
            status = "WARNING"
            icon   = "🟡"
        elif usage >= 60:
            status = "MODERATE"
            icon   = "🟠"
        else:
            status = "GOOD"
            icon   = "🟢"

        results.append({
            "Category" : category,
            "Budget"   : budget,
            "Actual"   : round(actual, 2),
            "Diff"     : round(diff, 2),
            "Usage %"  : round(usage, 2),
            "Status"   : status,
            "Icon"     : icon
        })

    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values("Usage %", ascending=False).reset_index(drop=True)
    return result_df


def print_budget_report(df):
    """
    Pretty-print the budget vs actual report with alerts.
    """
    report = check_budget_alerts(df)

    print("\n" + "="*72)
    print("              💼 BUDGET vs ACTUAL REPORT (Monthly Avg)")
    print("="*72)
    print(f"  {'Category':<15} {'Budget':>9} {'Actual':>9} {'Diff':>10} {'Usage':>7}  Status")
    print("-"*72)

    exceeded = []
    warning  = []

    for _, row in report.iterrows():
        diff_str = f"+₹{row['Diff']:,.0f}" if row["Diff"] > 0 else f"-₹{abs(row['Diff']):,.0f}"
        print(f"  {row['Category']:<15} ₹{row['Budget']:>8,.0f} ₹{row['Actual']:>8,.0f} {diff_str:>10}  {row['Usage %']:>5.1f}%  {row['Icon']} {row['Status']}")

        if row["Status"] == "EXCEEDED":
            exceeded.append(row["Category"])
        elif row["Status"] == "WARNING":
            warning.append(row["Category"])

    print("="*72)

    # Alerts section
    if exceeded:
        print(f"\n  🚨 BUDGET EXCEEDED in: {', '.join(exceeded)}")
        print("     Action needed — review these categories!")
    if warning:
        print(f"\n  ⚠️  NEAR LIMIT in: {', '.join(warning)}")
        print("     Be careful for rest of the month.")
    if not exceeded and not warning:
        print("\n  ✅ All categories are within budget. Great job!")

    # Total budget health
    total_budget = report["Budget"].sum()
    total_actual = report["Actual"].sum()
    overall_usage = (total_actual / total_budget * 100)
    print(f"\n  📊 Total Budget : ₹{total_budget:,.0f}/month")
    print(f"  📊 Total Actual : ₹{total_actual:,.0f}/month")
    print(f"  📊 Overall Usage: {overall_usage:.1f}%")
    print("="*72)


def plot_budget_chart(df):
    """
    Horizontal grouped bar chart: Budget vs Actual per category.
    Saved as Charts/budget_vs_actual.png
    """
    report     = check_budget_alerts(df)
    categories = report["Category"].tolist()
    budgets    = report["Budget"].tolist()
    actuals    = report["Actual"].tolist()
    colors     = []

    for _, row in report.iterrows():
        if row["Status"] == "EXCEEDED":
            colors.append("#FF6B6B")
        elif row["Status"] == "WARNING":
            colors.append("#FFEAA7")
        elif row["Status"] == "MODERATE":
            colors.append("#F39C12")
        else:
            colors.append("#82E0AA")

    y      = range(len(categories))
    height = 0.35

    fig, ax = plt.subplots(figsize=(11, 7))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    bars_b = ax.barh([i + height/2 for i in y], budgets,  height=height,
                     color="#45B7D1", label="Budget", edgecolor="#1e1e2e")
    bars_a = ax.barh([i - height/2 for i in y], actuals, height=height,
                     color=colors, label="Actual", edgecolor="#1e1e2e")

    # Labels
    for bar in bars_b:
        ax.text(bar.get_width() + 100, bar.get_y() + bar.get_height()/2,
                f"₹{bar.get_width():,.0f}", va="center", color="#45B7D1", fontsize=8)
    for bar in bars_a:
        ax.text(bar.get_width() + 100, bar.get_y() + bar.get_height()/2,
                f"₹{bar.get_width():,.0f}", va="center", color="white", fontsize=8)

    ax.set_yticks(list(y))
    ax.set_yticklabels(categories, color="white", fontsize=10)
    ax.set_xlabel("Amount (₹)", color="white", fontsize=11)
    ax.set_title("Budget vs Actual Spending (Monthly Avg)", color="white",
                 fontsize=14, fontweight="bold", pad=15)
    ax.tick_params(colors="white")
    ax.xaxis.set_tick_params(labelcolor="white")
    ax.set_xlim(0, max(max(budgets), max(actuals)) * 1.3)
    ax.grid(axis="x", color="#333355", linestyle="--", linewidth=0.7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

    legend_patches = [
        mpatches.Patch(color="#45B7D1", label="Budget"),
        mpatches.Patch(color="#82E0AA", label="Actual (Good)"),
        mpatches.Patch(color="#FFEAA7", label="Actual (Warning)"),
        mpatches.Patch(color="#FF6B6B", label="Actual (Exceeded)"),
    ]
    ax.legend(handles=legend_patches, facecolor="#2e2e3e",
              labelcolor="white", fontsize=9, loc="lower right")

    plt.tight_layout()
    path = "Charts/budget_vs_actual.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"\n  Budget chart saved -> Charts/budget_vs_actual.png")


def run_budget(df):
    """Main function — call this from main.py"""
    print_budget_report(df)
    plot_budget_chart(df)
    print("\n  Budget analysis complete!")


# -------------------------------------------------------
# Quick test
# -------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from Modules.loader import load_data
    df = load_data("Data/expenses.csv")
    run_budget(df)