"""
recommender.py
--------------
Smart recommendation engine.
Analyzes spending patterns and gives personalized saving tips.
Rule-based system — no ML needed, pure Python logic.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

os.makedirs("Charts", exist_ok=True)


# -------------------------------------------------------
# RECOMMENDATION RULES (thresholds as % of total expense)
# -------------------------------------------------------
RULES = {
    "Food"         : {"warn": 20, "danger": 30, "tip": "Cook at home more often. Avoid ordering food daily. Weekly meal prep saves up to ₹2000/month."},
    "Entertainment": {"warn": 8,  "danger": 15, "tip": "Limit OTT subscriptions to 1-2. Share plans with family. Set a fixed monthly fun budget."},
    "Clothing"     : {"warn": 8,  "danger": 15, "tip": "Avoid impulse buying. Wait 48 hours before any clothing purchase above ₹1000."},
    "Transport"    : {"warn": 10, "danger": 18, "tip": "Use public transport when possible. Carpool with colleagues. Combine errands into single trips."},
    "Healthcare"   : {"warn": 8,  "danger": 15, "tip": "Get a health insurance policy to reduce out-of-pocket costs. Regular checkups prevent costly treatments."},
    "Utilities"    : {"warn": 6,  "danger": 12, "tip": "Switch off appliances when not in use. LED bulbs save up to 30% on electricity bills."},
    "Education"    : {"warn": 10, "danger": 18, "tip": "Use free resources like YouTube, NPTEL, or Coursera free tier before paid courses."},
}

SAVINGS_RATE_TIPS = {
    "excellent" : (30, "Your savings rate is excellent! Consider investing surplus in mutual funds or SIPs."),
    "good"      : (20, "Good savings rate! Try to increase it by 5% by cutting one discretionary category."),
    "average"   : (10, "Average savings rate. Identify your top 2 expense categories and cut each by 10%."),
    "poor"      : (0,  "Low savings rate — urgent action needed! Track every rupee and eliminate non-essential expenses."),
}


def get_spending_percentages(df):
    """Returns each category's % share of total expenses."""
    expenses      = df[df["type"] == "expense"]
    total_expense = expenses["amount"].sum()
    cat_totals    = expenses.groupby("category")["amount"].sum()
    percentages   = (cat_totals / total_expense * 100).round(2)
    return percentages


def get_savings_rate(df):
    """Returns overall savings rate %."""
    total_income  = df[df["type"] == "income"]["amount"].sum()
    total_expense = df[df["type"] == "expense"]["amount"].sum()
    net_savings   = total_income - total_expense
    return round((net_savings / total_income * 100), 2) if total_income > 0 else 0


def generate_recommendations(df):
    """
    Core engine — generates a list of recommendation objects.
    Each has: type, category, severity, message, potential_saving.
    """
    recommendations = []
    percentages     = get_spending_percentages(df)
    savings_rate    = get_savings_rate(df)
    total_expense   = df[df["type"] == "expense"]["amount"].sum()
    num_months      = df["month_year"].nunique()
    avg_monthly_exp = total_expense / num_months

    # --- Rule 1: Category overspending ---
    for category, thresholds in RULES.items():
        if category not in percentages:
            continue

        pct = percentages[category]

        if pct >= thresholds["danger"]:
            severity = "HIGH"
            icon     = "🔴"
            excess   = pct - thresholds["warn"]
            potential_save = round((excess / 100) * avg_monthly_exp * 0.5, 0)
            msg = (f"{category} is {pct:.1f}% of your expenses — "
                   f"well above the {thresholds['danger']}% danger threshold.\n"
                   f"     Tip: {thresholds['tip']}\n"
                   f"     Potential saving: ₹{potential_save:,.0f}/month if reduced by 50%")

        elif pct >= thresholds["warn"]:
            severity = "MEDIUM"
            icon     = "🟡"
            excess   = pct - thresholds["warn"]
            potential_save = round((excess / 100) * avg_monthly_exp * 0.3, 0)
            msg = (f"{category} is {pct:.1f}% of your expenses — "
                   f"above the {thresholds['warn']}% warning threshold.\n"
                   f"     Tip: {thresholds['tip']}\n"
                   f"     Potential saving: ₹{potential_save:,.0f}/month if trimmed slightly")
        else:
            continue  # Category is within safe limits

        recommendations.append({
            "icon"           : icon,
            "severity"       : severity,
            "category"       : category,
            "message"        : msg,
            "potential_save" : potential_save
        })

    # --- Rule 2: Savings rate advice ---
    for level, (threshold, tip) in SAVINGS_RATE_TIPS.items():
        if savings_rate >= threshold:
            icon = "✅" if level == "excellent" else ("🟡" if level == "good" else ("🟠" if level == "average" else "🔴"))
            recommendations.append({
                "icon"           : icon,
                "severity"       : "INFO",
                "category"       : "Savings Rate",
                "message"        : f"Your savings rate is {savings_rate:.1f}%.\n     Tip: {tip}",
                "potential_save" : 0
            })
            break

    # --- Rule 3: Increasing expense trend ---
    monthly_exp_df = df[df["type"] == "expense"].groupby("month_year")["amount"].sum().reset_index()
    monthly_exp_df["sort_key"] = pd.to_datetime(monthly_exp_df["month_year"], format="%b %Y")
    monthly_exp_df = monthly_exp_df.sort_values("sort_key")
    values = monthly_exp_df["amount"].values

    if len(values) >= 3:
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        if slope > 500:
            recommendations.append({
                "icon"           : "📈",
                "severity"       : "HIGH",
                "category"       : "Expense Trend",
                "message"        : (f"Your expenses are increasing by ₹{slope:,.0f}/month on average.\n"
                                    f"     Tip: Review last 3 months to find what's driving the increase.\n"
                                    f"     Focus on categories that grew most month-over-month."),
                "potential_save" : round(slope * 3, 0)
            })

    # --- Rule 4: No investment/savings category found ---
    categories = df["category"].unique()
    if "Savings" not in categories:
        recommendations.append({
            "icon"           : "💰",
            "severity"       : "HIGH",
            "category"       : "No Savings Recorded",
            "message"        : ("No savings transactions found!\n"
                                "     Tip: Follow the 50-30-20 rule — 50% needs, 30% wants, 20% savings.\n"
                                "     Start a SIP of even ₹500/month to build the habit."),
            "potential_save" : 0
        })

    # --- Rule 5: High EMI burden ---
    if "Other" in percentages and percentages["Other"] > 15:
        recommendations.append({
            "icon"           : "🏦",
            "severity"       : "MEDIUM",
            "category"       : "EMI / Loans",
            "message"        : ("EMI or loan payments are consuming a large portion of income.\n"
                                "     Tip: Try to prepay loans when possible. Avoid taking new EMIs.\n"
                                "     EMIs should not exceed 30-35% of monthly income."),
            "potential_save" : 0
        })

    # Sort by severity
    order = {"HIGH": 0, "MEDIUM": 1, "INFO": 2}
    recommendations.sort(key=lambda r: order.get(r["severity"], 3))

    return recommendations


def print_recommendations(df):
    """Pretty-print all recommendations."""
    recs         = generate_recommendations(df)
    savings_rate = get_savings_rate(df)
    percentages  = get_spending_percentages(df)

    print("\n" + "="*65)
    print("       💡 PERSONALIZED SAVING RECOMMENDATIONS")
    print("="*65)
    print(f"  Total recommendations: {len(recs)}\n")

    total_potential = 0
    for i, rec in enumerate(recs, 1):
        print(f"  {i}. {rec['icon']}  [{rec['severity']}] {rec['category']}")
        print(f"     {rec['message']}")
        if rec["potential_save"] > 0:
            print(f"     💵 Potential monthly saving: ₹{rec['potential_save']:,.0f}")
            total_potential += rec["potential_save"]
        print()

    print("-"*65)
    if total_potential > 0:
        print(f"  💰 Total potential monthly savings : ₹{total_potential:,.0f}")
        print(f"  💰 Annualized potential savings    : ₹{total_potential * 12:,.0f}")
    print("="*65)

    # Final 50-30-20 check
    print("\n" + "="*65)
    print("       📐 50-30-20 RULE CHECK")
    print("="*65)
    total_income = df[df["type"] == "income"]["amount"].sum()
    num_months   = df["month_year"].nunique()
    avg_income   = total_income / num_months

    needs_cats  = ["Rent", "Utilities", "Food", "Healthcare", "Transport", "EMI", "Other"]
    wants_cats  = ["Entertainment", "Clothing", "Education"]
    savings_cats= ["Savings"]

    needs_amt   = df[(df["type"]=="expense") & (df["category"].isin(needs_cats))]["amount"].sum() / num_months
    wants_amt   = df[(df["type"]=="expense") & (df["category"].isin(wants_cats))]["amount"].sum() / num_months
    savings_amt = df[(df["type"]=="expense") & (df["category"].isin(savings_cats))]["amount"].sum() / num_months

    def rule_icon(actual_pct, target_pct):
        return "✅" if actual_pct <= target_pct + 5 else "❌"

    needs_pct   = needs_amt / avg_income * 100
    wants_pct   = wants_amt / avg_income * 100
    savings_pct = savings_amt / avg_income * 100

    print(f"  {'Category':<12} {'Ideal':>8} {'Actual':>10}  Status")
    print(f"  {'-'*45}")
    print(f"  {'Needs':<12} {'50%':>8} {needs_pct:>9.1f}%  {rule_icon(needs_pct, 50)}")
    print(f"  {'Wants':<12} {'30%':>8} {wants_pct:>9.1f}%  {rule_icon(wants_pct, 30)}")
    print(f"  {'Savings':<12} {'20%':>8} {savings_pct:>9.1f}%  {rule_icon(savings_pct, 20)}")
    print("="*65)


def plot_recommendation_chart(df):
    """
    Radar/spider chart showing spending health across categories.
    Saved as Charts/spending_health.png
    """
    percentages = get_spending_percentages(df)
    categories  = list(RULES.keys())
    actual_pcts = [percentages.get(cat, 0) for cat in categories]
    warn_pcts   = [RULES[cat]["warn"] for cat in categories]
    danger_pcts = [RULES[cat]["danger"] for cat in categories]

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    x      = range(len(categories))
    width  = 0.28

    bars_a = ax.bar([i - width   for i in x], actual_pcts, width=width, color="#45B7D1", label="Actual %",  edgecolor="#1e1e2e")
    bars_w = ax.bar([i           for i in x], warn_pcts,   width=width, color="#FFEAA7", label="Warning %", edgecolor="#1e1e2e", alpha=0.7)
    bars_d = ax.bar([i + width   for i in x], danger_pcts, width=width, color="#FF6B6B", label="Danger %",  edgecolor="#1e1e2e", alpha=0.7)

    # Value labels
    for bar in bars_a:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"{bar.get_height():.1f}%", ha="center", color="white", fontsize=8)

    ax.set_xticks(list(x))
    ax.set_xticklabels(categories, color="white", fontsize=10, rotation=15)
    ax.set_ylabel("% of Total Expense", color="white", fontsize=11)
    ax.set_title("Spending Health — Actual vs Warning vs Danger Levels",
                 color="white", fontsize=13, fontweight="bold", pad=15)
    ax.tick_params(colors="white")
    ax.yaxis.set_tick_params(labelcolor="white")
    ax.legend(facecolor="#2e2e3e", labelcolor="white", fontsize=10)
    ax.grid(axis="y", color="#333355", linestyle="--", linewidth=0.7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

    plt.tight_layout()
    path = "Charts/spending_health.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"\n  Spending health chart saved -> Charts/spending_health.png")


def run_recommender(df):
    """Main function — call this from main.py"""
    print_recommendations(df)
    plot_recommendation_chart(df)
    print("\n  Recommendations complete!")


# -------------------------------------------------------
# Quick test
# -------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from Modules.loader import load_data
    df = load_data("Data/expenses.csv")
    run_recommender(df)