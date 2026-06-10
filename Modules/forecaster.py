"""
forecaster.py
-------------
Expense forecasting module.
Uses NumPy linear regression to predict next month's expenses.
Also forecasts category-wise spending.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

os.makedirs("Charts", exist_ok=True)


def get_monthly_expenses(df):
    """
    Returns a sorted list of monthly total expenses.
    """
    expenses = df[df["type"] == "expense"]
    monthly  = expenses.groupby("month_year")["amount"].sum().reset_index()
    monthly.columns = ["month_year", "total_expense"]

    monthly["sort_key"] = pd.to_datetime(monthly["month_year"], format="%b %Y")
    monthly = monthly.sort_values("sort_key").reset_index(drop=True)
    return monthly


def linear_regression_forecast(values):
    """
    Pure NumPy linear regression.
    Given a list of values [y1, y2, y3 ...], predicts the next value.

    Formula:
        y = mx + c
        m = (n*sum(xy) - sum(x)*sum(y)) / (n*sum(x^2) - sum(x)^2)
        c = (sum(y) - m*sum(x)) / n
    """
    n = len(values)
    x = np.arange(1, n + 1, dtype=float)
    y = np.array(values, dtype=float)

    sum_x  = np.sum(x)
    sum_y  = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x ** 2)

    m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    c = (sum_y - m * sum_x) / n

    next_x   = n + 1
    predicted = m * next_x + c

    return round(predicted, 2), round(m, 2), round(c, 2)


def forecast_total_expense(df):
    """
    Predict next month's total expense using linear regression.
    Returns predicted amount and trend info.
    """
    monthly  = get_monthly_expenses(df)
    values   = monthly["total_expense"].tolist()
    pred, m, c = linear_regression_forecast(values)

    avg = np.mean(values)
    if m > 0:
        trend = "INCREASING"
        trend_icon = "↑"
    elif m < 0:
        trend = "DECREASING"
        trend_icon = "↓"
    else:
        trend = "STABLE"
        trend_icon = "→"

    return {
        "predicted"  : max(pred, 0),   # expenses can't be negative
        "slope"      : m,
        "trend"      : trend,
        "trend_icon" : trend_icon,
        "avg_expense": round(avg, 2),
        "months_data": len(values)
    }


def forecast_category_wise(df):
    """
    Predict next month's expense for each category.
    Returns a DataFrame with category forecasts.
    """
    expenses = df[df["type"] == "expense"]

    # Get monthly totals per category
    cat_monthly = expenses.groupby(["month_year", "category"])["amount"].sum().reset_index()
    cat_monthly["sort_key"] = pd.to_datetime(cat_monthly["month_year"], format="%b %Y")
    cat_monthly = cat_monthly.sort_values("sort_key")

    results = []
    for category in cat_monthly["category"].unique():
        cat_data = cat_monthly[cat_monthly["category"] == category]["amount"].tolist()

        if len(cat_data) < 2:
            # Not enough data — use average
            predicted = round(np.mean(cat_data), 2)
            trend = "STABLE"
        else:
            predicted, slope, _ = linear_regression_forecast(cat_data)
            predicted = max(predicted, 0)
            trend = "UP" if slope > 0 else ("DOWN" if slope < 0 else "STABLE")

        results.append({
            "Category" : category,
            "Avg/Month": round(np.mean(cat_data), 2),
            "Predicted": predicted,
            "Trend"    : trend,
            "Icon"     : "↑" if trend == "UP" else ("↓" if trend == "DOWN" else "→")
        })

    result_df = pd.DataFrame(results)
    result_df  = result_df.sort_values("Predicted", ascending=False).reset_index(drop=True)
    return result_df


def print_forecast_report(df):
    """
    Pretty-print the full forecast report.
    """
    total_forecast = forecast_total_expense(df)
    cat_forecast   = forecast_category_wise(df)

    print("\n" + "="*55)
    print("       🔮 NEXT MONTH EXPENSE FORECAST")
    print("="*55)
    print(f"  Based on last {total_forecast['months_data']} months of data")
    print(f"  Method: Linear Regression (NumPy)\n")
    print(f"  Current Avg Monthly Expense : ₹{total_forecast['avg_expense']:>10,.2f}")
    print(f"  Predicted Next Month        : ₹{total_forecast['predicted']:>10,.2f}")
    print(f"  Expense Trend               : {total_forecast['trend_icon']} {total_forecast['trend']}")
    print("="*55)

    if total_forecast["trend"] == "INCREASING":
        print("  ⚠️  Warning: Expenses are rising month over month.")
        print("      Consider cutting discretionary spending.")
    elif total_forecast["trend"] == "DECREASING":
        print("  ✅ Good news: Expenses are trending downward!")
    else:
        print("  ➡️  Expenses are stable. Keep maintaining this.")

    print("\n" + "="*55)
    print("    📂 CATEGORY-WISE FORECAST (Next Month)")
    print("="*55)
    print(f"  {'Category':<15} {'Avg/Month':>10} {'Predicted':>10}  Trend")
    print("-"*55)

    for _, row in cat_forecast.iterrows():
        diff = row["Predicted"] - row["Avg/Month"]
        diff_str = f"+₹{diff:,.0f}" if diff > 0 else f"-₹{abs(diff):,.0f}"
        print(f"  {row['Category']:<15} ₹{row['Avg/Month']:>9,.0f} ₹{row['Predicted']:>9,.0f}  {row['Icon']} ({diff_str})")

    print("-"*55)
    print(f"  {'TOTAL':<15} ₹{cat_forecast['Avg/Month'].sum():>9,.0f} ₹{cat_forecast['Predicted'].sum():>9,.0f}")
    print("="*55)


def plot_forecast_chart(df):
    """
    Line chart showing past expenses + forecast point.
    Saved as Charts/forecast.png
    """
    monthly        = get_monthly_expenses(df)
    total_forecast = forecast_total_expense(df)

    months  = monthly["month_year"].tolist()
    actuals = monthly["total_expense"].tolist()

    # Regression line
    x    = np.arange(1, len(actuals) + 1, dtype=float)
    pred_val, m, c = linear_regression_forecast(actuals)
    reg_line = m * x + c

    # Next month label
    last_date  = pd.to_datetime(months[-1], format="%b %Y")
    next_month = (last_date + pd.DateOffset(months=1)).strftime("%b %Y")

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    all_months = months + [next_month]
    x_all      = list(range(len(all_months)))

    # Actual line
    ax.plot(x_all[:len(actuals)], actuals, color="#45B7D1",
            linewidth=2.5, marker="o", markersize=8, label="Actual Expense", zorder=3)

    # Regression trend line (extended to forecast point)
    full_x     = np.arange(1, len(actuals) + 2)
    full_reg   = m * full_x + c
    ax.plot(x_all, full_reg, color="#FFEAA7", linewidth=1.5,
            linestyle="--", label="Trend Line", alpha=0.7)

    # Forecast point
    ax.scatter([len(actuals)], [pred_val], color="#FF6B6B",
               s=150, zorder=5, label=f"Forecast: ₹{pred_val:,.0f}")
    ax.annotate(f"  ₹{pred_val:,.0f}\n  (Forecast)",
                (len(actuals), pred_val),
                color="#FF6B6B", fontsize=10, fontweight="bold",
                xytext=(10, 10), textcoords="offset points")

    # Dashed connector from last actual to forecast
    ax.plot([len(actuals)-1, len(actuals)], [actuals[-1], pred_val],
            color="#FF6B6B", linestyle=":", linewidth=1.5, alpha=0.8)

    # Shaded forecast zone
    ax.axvspan(len(actuals) - 0.5, len(actuals) + 0.5,
               alpha=0.08, color="#FF6B6B", label="Forecast Zone")

    # Labels on actual points
    for i, amt in enumerate(actuals):
        ax.annotate(f"₹{amt/1000:.1f}k", (i, amt),
                    textcoords="offset points", xytext=(0, 10),
                    color="white", fontsize=8, ha="center")

    ax.set_xticks(x_all)
    ax.set_xticklabels(all_months, color="white", fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"₹{v/1000:.0f}k"))
    ax.tick_params(colors="white")
    ax.yaxis.set_tick_params(labelcolor="white")
    ax.set_title("Expense Forecast — Next Month Prediction", color="white",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Month", color="white", fontsize=11)
    ax.set_ylabel("Expense (₹)", color="white", fontsize=11)
    ax.legend(facecolor="#2e2e3e", labelcolor="white", fontsize=10)
    ax.grid(axis="y", color="#333355", linestyle="--", linewidth=0.7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

    plt.tight_layout()
    path = "Charts/forecast.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"\n  Forecast chart saved -> Charts/forecast.png")


def run_forecaster(df):
    """Main function — call this from main.py"""
    print_forecast_report(df)
    plot_forecast_chart(df)
    print("\n  Forecasting complete!")


# -------------------------------------------------------
# Quick test
# -------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from Modules.loader import load_data
    df = load_data("Data/expenses.csv")
    run_forecaster(df)