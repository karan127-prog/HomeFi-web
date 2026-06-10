"""
goals.py
--------
Savings goal tracker module.
User sets savings goals (e.g. Laptop ₹80,000).
Tracks progress and estimates months to reach each goal.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import json
import os

os.makedirs("Charts", exist_ok=True)
os.makedirs("Data",   exist_ok=True)

GOALS_FILE = "Data/goals.json"

# -------------------------------------------------------
# DEFAULT SAMPLE GOALS — user can change via main menu
# -------------------------------------------------------
DEFAULT_GOALS = [
    {"name": "Emergency Fund",  "target": 100000, "saved": 0,     "priority": "High"},
    {"name": "Laptop",          "target": 80000,  "saved": 15000, "priority": "Medium"},
    {"name": "Vacation Trip",   "target": 50000,  "saved": 5000,  "priority": "Low"},
    {"name": "Bike Down Payment","target":30000,  "saved": 10000, "priority": "High"},
]


def load_goals():
    """Load goals from JSON file, or return defaults."""
    if os.path.exists(GOALS_FILE):
        with open(GOALS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_GOALS.copy()


def save_goals(goals):
    """Save goals to JSON file."""
    with open(GOALS_FILE, "w") as f:
        json.dump(goals, f, indent=4)
    print(f"  ✅ Goals saved to {GOALS_FILE}")


def get_avg_monthly_savings(df):
    """Calculate average monthly net savings from transaction data."""
    income_m  = df[df["type"] == "income"].groupby("month_year")["amount"].sum()
    expense_m = df[df["type"] == "expense"].groupby("month_year")["amount"].sum()

    monthly = pd.DataFrame({"Income": income_m, "Expense": expense_m}).fillna(0)
    monthly["Savings"] = monthly["Income"] - monthly["Expense"]

    return round(monthly["Savings"].mean(), 2)


def calculate_goal_progress(goals, monthly_savings):
    """
    For each goal, calculate:
    - % progress
    - remaining amount
    - months to complete (ETA)
    - status
    """
    results = []
    for goal in goals:
        target    = goal["target"]
        saved     = goal["saved"]
        remaining = max(target - saved, 0)
        progress  = min((saved / target * 100), 100) if target > 0 else 0

        if monthly_savings > 0 and remaining > 0:
            # Distribute savings proportionally by priority
            priority_weight = {"High": 0.5, "Medium": 0.3, "Low": 0.2}
            weight     = priority_weight.get(goal.get("priority", "Medium"), 0.3)
            allocated  = monthly_savings * weight
            months_eta = remaining / allocated if allocated > 0 else float("inf")
        elif remaining == 0:
            months_eta = 0
        else:
            months_eta = float("inf")

        if progress >= 100:
            status = "COMPLETED"
            icon   = "✅"
        elif progress >= 75:
            status = "ALMOST THERE"
            icon   = "🟢"
        elif progress >= 50:
            status = "HALFWAY"
            icon   = "🟡"
        elif progress >= 25:
            status = "IN PROGRESS"
            icon   = "🟠"
        else:
            status = "JUST STARTED"
            icon   = "🔴"

        results.append({
            "Name"      : goal["name"],
            "Target"    : target,
            "Saved"     : saved,
            "Remaining" : remaining,
            "Progress%" : round(progress, 1),
            "ETA Months": round(months_eta, 1) if months_eta != float("inf") else "N/A",
            "Priority"  : goal.get("priority", "Medium"),
            "Status"    : status,
            "Icon"      : icon
        })

    return pd.DataFrame(results)


def print_goals_report(df):
    """Pretty-print all savings goals with progress and ETA."""
    goals          = load_goals()
    monthly_savings = get_avg_monthly_savings(df)
    report         = calculate_goal_progress(goals, monthly_savings)

    print("\n" + "="*68)
    print("            🎯 SAVINGS GOALS TRACKER")
    print("="*68)
    print(f"  Avg Monthly Savings Available : ₹{monthly_savings:,.2f}\n")

    for _, row in report.iterrows():
        bar_filled = int(row["Progress%"] / 5)
        bar_empty  = 20 - bar_filled
        progress_bar = "█" * bar_filled + "░" * bar_empty

        eta_str = f"{row['ETA Months']} months" if row["ETA Months"] != "N/A" else "Need more savings"

        print(f"  {row['Icon']}  {row['Name']} [{row['Priority']} Priority]")
        print(f"     Target  : ₹{row['Target']:>10,.0f}")
        print(f"     Saved   : ₹{row['Saved']:>10,.0f}  ({row['Progress%']}%)")
        print(f"     Remaining: ₹{row['Remaining']:>9,.0f}")
        print(f"     Progress: [{progress_bar}] {row['Progress%']}%")
        print(f"     ETA     : {eta_str}  |  Status: {row['Status']}")
        print()

    print("-"*68)
    total_target = report["Target"].sum()
    total_saved  = report["Saved"].sum()
    overall_pct  = (total_saved / total_target * 100) if total_target > 0 else 0
    print(f"  📊 Total Target : ₹{total_target:>10,.0f}")
    print(f"  📊 Total Saved  : ₹{total_saved:>10,.0f}  ({overall_pct:.1f}%)")
    print(f"  📊 Still Needed : ₹{total_target - total_saved:>10,.0f}")
    print("="*68)


def plot_goals_chart(df):
    """
    Horizontal progress bar chart for all goals.
    Saved as Charts/goals_progress.png
    """
    goals           = load_goals()
    monthly_savings = get_avg_monthly_savings(df)
    report          = calculate_goal_progress(goals, monthly_savings)

    names     = report["Name"].tolist()
    targets   = report["Target"].tolist()
    saved     = report["Saved"].tolist()
    progress  = report["Progress%"].tolist()

    priority_colors = {"High": "#FF6B6B", "Medium": "#FFEAA7", "Low": "#82E0AA"}
    bar_colors = [priority_colors.get(p, "#45B7D1") for p in report["Priority"].tolist()]

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    y = range(len(names))

    # Background bar (target)
    ax.barh(y, targets, color="#2e2e4e", height=0.5, edgecolor="#444")

    # Progress bar (saved)
    bars = ax.barh(y, saved, color=bar_colors, height=0.5, edgecolor="#1e1e2e")

    # Labels
    for i, (bar, pct, tgt, sav, eta) in enumerate(
            zip(bars, progress, targets, saved, report["ETA Months"].tolist())):
        # Progress % inside bar
        ax.text(max(sav - 500, 200), i, f"{pct}%",
                va="center", color="#1e1e2e", fontsize=9, fontweight="bold")
        # Target amount at end
        ax.text(tgt + tgt * 0.02, i, f"₹{tgt/1000:.0f}k",
                va="center", color="white", fontsize=8)
        # ETA label
        eta_label = f"{eta}mo" if eta != "N/A" else "∞"
        ax.text(sav + tgt * 0.02, i + 0.28, f"ETA: {eta_label}",
                va="center", color="#aaaacc", fontsize=7)

    ax.set_yticks(list(y))
    ax.set_yticklabels(names, color="white", fontsize=11)
    ax.set_xlabel("Amount (₹)", color="white", fontsize=11)
    ax.set_title("Savings Goals Progress", color="white", fontsize=14,
                 fontweight="bold", pad=15)
    ax.tick_params(colors="white")
    ax.xaxis.set_tick_params(labelcolor="white")
    ax.set_xlim(0, max(targets) * 1.2)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"₹{v/1000:.0f}k"))
    ax.grid(axis="x", color="#333355", linestyle="--", linewidth=0.7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

    legend_patches = [
        mpatches.Patch(color="#FF6B6B", label="High Priority"),
        mpatches.Patch(color="#FFEAA7", label="Medium Priority"),
        mpatches.Patch(color="#82E0AA", label="Low Priority"),
        mpatches.Patch(color="#2e2e4e", label="Remaining Target"),
    ]
    ax.legend(handles=legend_patches, facecolor="#2e2e3e",
              labelcolor="white", fontsize=9, loc="lower right")

    plt.tight_layout()
    path = "Charts/goals_progress.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"\n  Goals chart saved -> Charts/goals_progress.png")


def add_goal_interactive():
    """Interactive CLI to add a new savings goal."""
    print("\n" + "="*45)
    print("       ➕ ADD NEW SAVINGS GOAL")
    print("="*45)

    try:
        name     = input("  Goal Name       : ").strip()
        target   = float(input("  Target Amount ₹ : ").strip())
        saved    = float(input("  Already Saved ₹ : ").strip() or "0")
        priority = input("  Priority (High/Medium/Low) [Medium]: ").strip().capitalize() or "Medium"
        if priority not in ["High", "Medium", "Low"]:
            priority = "Medium"

        goals = load_goals()
        goals.append({"name": name, "target": target, "saved": saved, "priority": priority})
        save_goals(goals)
        print(f"\n  ✅ Goal '{name}' added successfully!")

    except ValueError:
        print("  ❌ Invalid input. Goal not added.")


def update_savings_interactive():
    """Update how much has been saved toward a goal."""
    goals = load_goals()

    print("\n" + "="*45)
    print("       💰 UPDATE GOAL SAVINGS")
    print("="*45)

    for i, g in enumerate(goals):
        print(f"  {i+1}. {g['name']} — Saved: ₹{g['saved']:,} / ₹{g['target']:,}")

    try:
        choice = int(input("\n  Select goal number: ").strip()) - 1
        if 0 <= choice < len(goals):
            amount = float(input(f"  New saved amount for '{goals[choice]['name']}' ₹: ").strip())
            goals[choice]["saved"] = amount
            save_goals(goals)
            print(f"  ✅ Updated '{goals[choice]['name']}' saved amount to ₹{amount:,}")
        else:
            print("  ❌ Invalid selection.")
    except ValueError:
        print("  ❌ Invalid input.")


def run_goals(df):
    """Main function — call this from main.py"""
    print_goals_report(df)
    plot_goals_chart(df)
    print("\n  Goals tracking complete!")


# -------------------------------------------------------
# Quick test
# -------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from Modules.loader import load_data
    df = load_data("Data/expenses.csv")
    run_goals(df)