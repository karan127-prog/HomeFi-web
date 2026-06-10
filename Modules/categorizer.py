"""
categorizer.py
--------------
Category-wise expense breakdown.
Generates pie chart and bar chart saved in Charts/ folder.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# Make sure Charts folder exists
os.makedirs("Charts", exist_ok=True)

# Colors for each category (Indian-friendly palette)
CATEGORY_COLORS = {
    "Food"         : "#FF6B6B",
    "Rent"         : "#4ECDC4",
    "Utilities"    : "#45B7D1",
    "Transport"    : "#96CEB4",
    "Entertainment": "#FFEAA7",
    "Healthcare"   : "#DDA0DD",
    "Education"    : "#98D8C8",
    "Clothing"     : "#F7DC6F",
    "EMI"          : "#E8A0BF",
    "Savings"      : "#82E0AA",
    "Other"        : "#AEB6BF"
}


def get_category_breakdown(df):
    """
    Returns a DataFrame with category-wise total expense,
    percentage share, and average per month.
    """
    expenses = df[df["type"] == "expense"]
    total_expense = expenses["amount"].sum()
    num_months = df["month_year"].nunique()

    breakdown = expenses.groupby("category")["amount"].sum().reset_index()
    breakdown.columns = ["Category", "Total Spent"]
    breakdown["% Share"] = (breakdown["Total Spent"] / total_expense * 100).round(2)
    breakdown["Avg/Month"] = (breakdown["Total Spent"] / num_months).round(2)
    breakdown = breakdown.sort_values("Total Spent", ascending=False).reset_index(drop=True)

    return breakdown


def print_category_breakdown(df):
    """Pretty-print the category-wise breakdown table."""
    breakdown = get_category_breakdown(df)

    print("\n" + "="*60)
    print("         🗂️  CATEGORY-WISE EXPENSE BREAKDOWN")
    print("="*60)
    print(f"  {'Category':<15} {'Total Spent':>12} {'% Share':>9} {'Avg/Month':>12}")
    print("-"*60)

    for _, row in breakdown.iterrows():
        bar = "█" * int(row["% Share"] / 2)  # visual bar
        print(f"  {row['Category']:<15} ₹{row['Total Spent']:>10,.0f}  {row['% Share']:>6.1f}%  ₹{row['Avg/Month']:>9,.0f}")
        print(f"  {'':15} {bar}")

    print("-"*60)
    top = breakdown.iloc[0]
    print(f"  🔴 Highest spend : {top['Category']} (₹{top['Total Spent']:,.0f} | {top['% Share']}%)")
    low = breakdown.iloc[-1]
    print(f"  🟢 Lowest spend  : {low['Category']} (₹{low['Total Spent']:,.0f} | {low['% Share']}%)")
    print("="*60)


def plot_pie_chart(df):
    """
    Generate and save a pie chart of category-wise expenses.
    Saved as Charts/category_pie.png
    """
    breakdown = get_category_breakdown(df)

    categories = breakdown["Category"].tolist()
    amounts    = breakdown["Total Spent"].tolist()
    colors     = [CATEGORY_COLORS.get(cat, "#AEB6BF") for cat in categories]

    # Explode the top category slightly
    explode = [0.05 if i == 0 else 0 for i in range(len(categories))]

    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    wedges, texts, autotexts = ax.pie(
        amounts,
        labels=None,
        autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
        colors=colors,
        explode=explode,
        startangle=140,
        wedgeprops={"edgecolor": "#1e1e2e", "linewidth": 2}
    )

    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(9)
        autotext.set_fontweight("bold")

    # Legend
    legend_labels = [f"{cat}  ₹{amt:,.0f}" for cat, amt in zip(categories, amounts)]
    legend = ax.legend(
        wedges, legend_labels,
        title="Category",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=9,
        title_fontsize=10,
        facecolor="#2e2e3e",
        labelcolor="white"
    )
    legend.get_title().set_color("white")

    ax.set_title("💸 Where is Your Money Going?", color="white", fontsize=14, fontweight="bold", pad=20)

    plt.tight_layout()
    path = "Charts/category_pie.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"\n  📊 Pie chart saved → {path}")


def plot_category_bar(df):
    """
    Generate and save a horizontal bar chart of category-wise expenses.
    Saved as Charts/category_bar.png
    """
    breakdown = get_category_breakdown(df)
    categories = breakdown["Category"].tolist()
    amounts    = breakdown["Total Spent"].tolist()
    colors     = [CATEGORY_COLORS.get(cat, "#AEB6BF") for cat in categories]

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    bars = ax.barh(categories[::-1], amounts[::-1], color=colors[::-1],
                   edgecolor="#1e1e2e", height=0.6)

    # Value labels on bars
    for bar, amt in zip(bars, amounts[::-1]):
        ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
                f"₹{amt:,.0f}", va="center", color="white", fontsize=9)

    ax.set_xlabel("Amount Spent (₹)", color="white", fontsize=11)
    ax.set_title("📊 Category-wise Total Expenses", color="white", fontsize=14, fontweight="bold")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")
    ax.set_xlim(0, max(amounts) * 1.25)
    ax.xaxis.set_tick_params(labelcolor="white")

    plt.tight_layout()
    path = "Charts/category_bar.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  📊 Bar chart saved  → {path}")


def run_categorizer(df):
    """Main function — call this from main.py"""
    print_category_breakdown(df)
    plot_pie_chart(df)
    plot_category_bar(df)
    print("\n  ✅ Category analysis complete!")


# -------------------------------------------------------
# Quick test
# -------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from Modules.loader import load_data
    df = load_data("Data/expenses.csv")
    run_categorizer(df)