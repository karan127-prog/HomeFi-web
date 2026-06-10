"""
analyzer.py
-----------
Core financial analysis module.
Calculates income, expenses, savings, and savings rate — overall and month-wise.
"""

import pandas as pd
import numpy as np


def get_overall_summary(df):
    """
    Calculate total income, total expenses, net savings, and savings rate.
    Returns a dictionary with all values.
    """
    total_income   = df[df["type"] == "income"]["amount"].sum()
    total_expense  = df[df["type"] == "expense"]["amount"].sum()
    net_savings    = total_income - total_expense
    savings_rate   = (net_savings / total_income * 100) if total_income > 0 else 0

    return {
        "total_income"  : round(total_income, 2),
        "total_expense" : round(total_expense, 2),
        "net_savings"   : round(net_savings, 2),
        "savings_rate"  : round(savings_rate, 2)
    }


def get_monthly_summary(df):
    """
    Month-wise breakdown of income, expenses, and savings.
    Returns a DataFrame sorted by date.
    """
    # Group by month_year
    income_monthly  = df[df["type"] == "income"].groupby("month_year")["amount"].sum()
    expense_monthly = df[df["type"] == "expense"].groupby("month_year")["amount"].sum()

    # Combine into one DataFrame
    monthly = pd.DataFrame({
        "Income" : income_monthly,
        "Expense": expense_monthly
    }).fillna(0)

    monthly["Savings"]      = monthly["Income"] - monthly["Expense"]
    monthly["Savings Rate"] = (monthly["Savings"] / monthly["Income"] * 100).round(2)

    # Sort by actual date order (not alphabetically)
    monthly = monthly.reset_index()
    monthly["sort_key"] = pd.to_datetime(monthly["month_year"], format="%b %Y")
    monthly = monthly.sort_values("sort_key").drop(columns="sort_key")
    monthly = monthly.set_index("month_year")

    return monthly


def get_avg_monthly_expense(df):
    """Returns the average monthly expense across all months."""
    monthly = get_monthly_summary(df)
    return round(monthly["Expense"].mean(), 2)


def get_avg_monthly_income(df):
    """Returns the average monthly income across all months."""
    monthly = get_monthly_summary(df)
    return round(monthly["Income"].mean(), 2)


def get_highest_expense_month(df):
    """Returns the month with the highest expenses."""
    monthly = get_monthly_summary(df)
    month = monthly["Expense"].idxmax()
    amount = monthly.loc[month, "Expense"]
    return month, round(amount, 2)


def get_best_savings_month(df):
    """Returns the month with the best savings."""
    monthly = get_monthly_summary(df)
    month = monthly["Savings"].idxmax()
    amount = monthly.loc[month, "Savings"]
    return month, round(amount, 2)


def print_overall_summary(df):
    """Pretty-print the overall financial summary."""
    s = get_overall_summary(df)

    print("\n" + "="*45)
    print("       💰 OVERALL FINANCIAL SUMMARY")
    print("="*45)
    print(f"  Total Income   : ₹{s['total_income']:>10,.2f}")
    print(f"  Total Expenses : ₹{s['total_expense']:>10,.2f}")
    print(f"  Net Savings    : ₹{s['net_savings']:>10,.2f}")
    print(f"  Savings Rate   :  {s['savings_rate']:>9.2f}%")
    print("="*45)

    # Savings health indicator
    rate = s["savings_rate"]
    if rate >= 30:
        print("  🟢 Excellent savings rate! Keep it up.")
    elif rate >= 20:
        print("  🟡 Good savings rate. Can be improved.")
    elif rate >= 10:
        print("  🟠 Average savings rate. Try to cut expenses.")
    else:
        print("  🔴 Low savings rate! Needs attention.")
    print("="*45)


def print_monthly_summary(df):
    """Pretty-print month-wise income, expense, savings table."""
    monthly = get_monthly_summary(df)

    print("\n" + "="*65)
    print("              📅 MONTH-WISE SUMMARY")
    print("="*65)
    print(f"  {'Month':<12} {'Income':>10} {'Expense':>10} {'Savings':>10} {'Rate':>8}")
    print("-"*65)

    for month, row in monthly.iterrows():
        indicator = "🟢" if row["Savings Rate"] >= 20 else ("🟡" if row["Savings Rate"] >= 10 else "🔴")
        print(f"  {month:<12} ₹{row['Income']:>9,.0f} ₹{row['Expense']:>9,.0f} ₹{row['Savings']:>9,.0f} {row['Savings Rate']:>6.1f}% {indicator}")

    print("-"*65)
    high_month, high_amt = get_highest_expense_month(df)
    best_month, best_amt = get_best_savings_month(df)
    print(f"  📈 Avg Monthly Income  : ₹{get_avg_monthly_income(df):,.2f}")
    print(f"  📉 Avg Monthly Expense : ₹{get_avg_monthly_expense(df):,.2f}")
    print(f"  🔴 Highest Expense Month : {high_month} (₹{high_amt:,.0f})")
    print(f"  🟢 Best Savings Month    : {best_month} (₹{best_amt:,.0f})")
    print("="*65)


# -------------------------------------------------------
# Quick test
# -------------------------------------------------------
if __name__ == "__main__":
    from loader import load_data
    df = load_data("Data/expenses.csv")
    print_overall_summary(df)
    print_monthly_summary(df)
