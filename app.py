"""
app.py
------
HomeFi Web — Flask entry point
Run: python app.py
Then open: http://127.0.0.1:5000
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
from types import SimpleNamespace
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file

sys.path.append(os.path.join(os.path.dirname(__file__), "Modules"))
from loader import load_data
from report_generator import generate_report
from excel_exporter import export_to_excel

app = Flask(__name__)
DATA_FILE   = os.path.join("Data", "expenses.csv")
CHARTS_DIR  = "Charts"
REPORTS_DIR = "Reports"
os.makedirs(CHARTS_DIR,  exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def get_df():
    return load_data(DATA_FILE)


def collect_report_data(df):
    inc_df = df[df["type"] == "income"].copy()
    exp_df = df[df["type"] == "expense"].copy()

    total_income  = inc_df["amount"].sum()
    total_expense = exp_df["amount"].sum()
    net_savings   = total_income - total_expense
    savings_rate  = (net_savings / total_income * 100) if total_income > 0 else 0

    exp_df["month"] = exp_df["date"].dt.to_period("M")
    inc_df["month"] = inc_df["date"].dt.to_period("M")
    monthly_exp = exp_df.groupby("month")["amount"].sum()
    monthly_inc = inc_df.groupby("month")["amount"].sum()
    monthly_sav = monthly_inc.subtract(monthly_exp, fill_value=0)

    summary = {
        "total_income":  float(total_income),
        "total_expense": float(total_expense),
        "net_savings":   float(net_savings),
        "savings_rate":  round(float(savings_rate), 1),
        "months":        int(monthly_exp.shape[0]),
        "best_month":    str(monthly_sav.idxmax()) if not monthly_sav.empty else "N/A",
        "worst_month":   str(monthly_exp.idxmax()) if not monthly_exp.empty else "N/A",
    }

    if len(monthly_exp) >= 2:
        x = np.arange(len(monthly_exp))
        y = monthly_exp.values
        m_slope, b = np.polyfit(x, y, 1)
        predicted = float(m_slope * len(monthly_exp) + b)
        trend = "increasing" if m_slope > 50 else ("decreasing" if m_slope < -50 else "stable")
    else:
        m_slope, predicted, trend = 0.0, float(total_expense), "stable"

    forecast_data = {
        "predicted_expense": predicted,
        "trend":             trend,
        "monthly_change":    float(m_slope),
    }

    goals = []
    goals_path = os.path.join("Data", "goals.json")
    if os.path.exists(goals_path):
        with open(goals_path) as f:
            raw_goals = json.load(f)
        avg_sav = float(monthly_sav.mean()) if not monthly_sav.empty else 0
        for g in raw_goals:
            target    = g.get("target", 0)
            saved     = g.get("current_savings", 0)
            remaining = max(0, target - saved)
            eta = f"{int(remaining / avg_sav)} months" if avg_sav > 0 else "N/A"
            goals.append({"name": g.get("name", "Goal"), "target": target,
                          "saved": saved, "eta": eta})

    tips = []
    thresholds = {"Food": 25, "Entertainment": 10, "Shopping": 15, "Travel": 10}
    cat_totals = exp_df.groupby("category")["amount"].sum()
    for cat, amt in cat_totals.items():
        pct   = (amt / total_expense * 100) if total_expense > 0 else 0
        limit = thresholds.get(cat, 30)
        if pct > limit:
            tips.append(f"{cat} is {pct:.1f}% of expenses — aim below {limit}%.")
    if savings_rate < 20:
        tips.append(f"Savings rate {savings_rate:.1f}% — target at least 20%.")
    if not tips:
        tips.append("Excellent discipline! Consider investing the surplus.")

    return summary, forecast_data, goals, tips


def generate_all_charts(df):
    import matplotlib
    matplotlib.use("Agg")
    from categorizer import run_categorizer
    # from trends      import run_trends
    from budget      import run_budget
    from forecaster  import run_forecaster
    from goals       import run_goals
    from recommender import run_recommender
    run_categorizer(df)
    # run_trends(df)
    run_budget(df)
    run_forecaster(df)
    run_goals(df)
    run_recommender(df)


@app.route("/")
def dashboard():
    df  = get_df()
    inc = df[df["type"] == "income"]["amount"].sum()
    exp = df[df["type"] == "expense"]["amount"].sum()
    sav = inc - exp
    rate = round((sav / inc * 100) if inc > 0 else 0, 1)

    exp_df = df[df["type"] == "expense"].copy()
    exp_df["month"] = exp_df["date"].dt.to_period("M")
    monthly_exp = exp_df.groupby("month")["amount"].sum()

    inc_df = df[df["type"] == "income"].copy()
    inc_df["month"] = inc_df["date"].dt.to_period("M")
    monthly_inc = inc_df.groupby("month")["amount"].sum()
    monthly_sav = monthly_inc.subtract(monthly_exp, fill_value=0)

    all_months = sorted(set(monthly_inc.index) | set(monthly_exp.index))

    top_cat = (df[df["type"] == "expense"]
               .groupby("category")["amount"].sum()
               .idxmax()) if not df[df["type"] == "expense"].empty else "N/A"

    recent_df = df.sort_values("date", ascending=False).head(10)
    recent = []
    for _, row in recent_df.iterrows():
        recent.append({
            "date":        str(row["date"].date()),
            "category":    row["category"],
            "description": str(row.get("description", "")),
            "type":        row["type"],
            "amount":      row["amount"],
        })

    cat = df[df["type"] == "expense"].groupby("category")["amount"].sum().sort_values(ascending=False)

    summary = SimpleNamespace(
        total_income  = inc,
        total_expense = exp,
        net_savings   = sav,
        savings_rate  = rate,
        months        = df["date"].dt.to_period("M").nunique(),
        records       = len(df),
        best_month    = str(monthly_sav.idxmax()) if not monthly_sav.empty else "N/A",
        worst_month   = str(monthly_exp.idxmax()) if not monthly_exp.empty else "N/A",
        top_cat       = top_cat,
    )

    return render_template(
        "dashboard.html",
        summary     = summary,
        recent      = recent,
        months      = [str(m) for m in all_months],
        incomes     = [float(monthly_inc.get(m, 0)) for m in all_months],
        expenses    = [float(monthly_exp.get(m, 0)) for m in all_months],
        savings     = [float(monthly_sav.get(m, 0)) for m in all_months],
        cat_names   = list(cat.index),
        cat_amounts = [float(v) for v in cat.values],
    )


@app.route("/api/categories")
def api_categories():
    df  = get_df()
    cat = df[df["type"] == "expense"].groupby("category")["amount"].sum().sort_values(ascending=False)
    return jsonify({"labels": list(cat.index), "values": [float(v) for v in cat.values]})


@app.route("/api/trends")
def api_trends():
    df  = get_df()
    df2 = df.copy()
    df2["month"] = df2["date"].dt.to_period("M")
    inc    = df2[df2["type"] == "income"].groupby("month")["amount"].sum()
    exp    = df2[df2["type"] == "expense"].groupby("month")["amount"].sum()
    months = sorted(set(inc.index) | set(exp.index))
    return jsonify({
        "months":  [str(m) for m in months],
        "income":  [float(inc.get(m, 0)) for m in months],
        "expense": [float(exp.get(m, 0)) for m in months],
        "savings": [float(inc.get(m, 0) - exp.get(m, 0)) for m in months],
    })


@app.route("/api/forecast")
def api_forecast():
    df     = get_df()
    exp_df = df[df["type"] == "expense"].copy()
    exp_df["month"] = exp_df["date"].dt.to_period("M")
    monthly = exp_df.groupby("month")["amount"].sum()
    values  = [float(v) for v in monthly.values]
    months  = [str(m) for m in monthly.index]

    if len(values) >= 2:
        x = np.arange(len(values))
        m_s, b     = np.polyfit(x, values, 1)
        predicted  = float(m_s * len(values) + b)
        trend      = "increasing" if m_s > 50 else ("decreasing" if m_s < -50 else "stable")
        trend_line = [float(m_s * i + b) for i in range(len(values) + 1)]
    else:
        predicted, trend, trend_line = (values[-1] if values else 0), "stable", values

    return jsonify({"months": months, "values": values,
                    "trend_line": trend_line, "predicted": predicted, "trend": trend})


@app.route("/api/budget")
def api_budget():
    df      = get_df()
    actuals = df[df["type"] == "expense"].groupby("category")["amount"].sum().to_dict()
    budgets = {}
    budgets_path = os.path.join("Data", "budgets.json")
    if os.path.exists(budgets_path):
        with open(budgets_path) as f:
            budgets = json.load(f)
    cats = list(set(list(actuals.keys()) + list(budgets.keys())))
    return jsonify({
        "categories": cats,
        "actual":     [float(actuals.get(c, 0)) for c in cats],
        "budget":     [float(budgets.get(c, 0)) for c in cats],
    })


@app.route("/api/goals")
def api_goals():
    goals_path = os.path.join("Data", "goals.json")
    if not os.path.exists(goals_path):
        return jsonify([])
    with open(goals_path) as f:
        goals = json.load(f)

    df     = get_df()
    exp_df = df[df["type"] == "expense"].copy()
    exp_df["month"] = exp_df["date"].dt.to_period("M")
    inc_df = df[df["type"] == "income"].copy()
    inc_df["month"] = inc_df["date"].dt.to_period("M")
    monthly_sav = (inc_df.groupby("month")["amount"].sum()
                   .subtract(exp_df.groupby("month")["amount"].sum(), fill_value=0))
    avg_sav = float(monthly_sav.mean()) if not monthly_sav.empty else 0

    result = []
    for g in goals:
        target    = g.get("target", 0)
        saved     = g.get("current_savings", 0)
        pct       = min(100, (saved / target * 100)) if target > 0 else 0
        remaining = max(0, target - saved)
        result.append({
            "name":     g.get("name", "Goal"),
            "target":   target,
            "saved":    saved,
            "pct":      round(pct, 1),
            "priority": g.get("priority", "medium"),
            "eta":      f"{int(remaining / avg_sav)} months" if avg_sav > 0 else "N/A",
        })
    return jsonify(result)


@app.route("/add", methods=["GET", "POST"])
def add_expense():
    categories = ["Food", "Rent", "EMI", "Entertainment", "Shopping",
                  "Travel", "Utilities", "Healthcare", "Education",
                  "Salary", "Freelance", "Other"]
    if request.method == "POST":
        date  = request.form.get("date") or datetime.now().strftime("%Y-%m-%d")
        cat   = request.form.get("category")
        etype = request.form.get("type")
        amt   = request.form.get("amount")
        desc  = request.form.get("description") or cat
        with open(DATA_FILE, "a") as f:
            f.write(f"\n{date},{cat},{etype},{amt},{desc}")
        return redirect(url_for("dashboard"))
    return render_template("add.html", categories=categories,
                           today=datetime.now().strftime("%Y-%m-%d"))


@app.route("/download-pdf")
def download_pdf():
    df = get_df()
    print("[*] Generating charts...")
    generate_all_charts(df)
    print("[*] Collecting data...")
    summary, forecast_data, goals, tips = collect_report_data(df)
    print("[*] Building PDF...")
    pdf_path = generate_report(
        summary       = summary,
        forecast_data = forecast_data,
        goals         = goals,
        tips          = tips,
        charts_dir    = CHARTS_DIR,
        reports_dir   = REPORTS_DIR,
    )
    print(f"[OK] PDF: {pdf_path}")
    return send_file(pdf_path, as_attachment=True)


@app.route("/download-excel")
def download_excel():
    df   = get_df()
    path = export_to_excel(df)
    return send_file(path, as_attachment=True)

@app.route("/categories")
def categories():
    return render_template("categories.html")

@app.route("/trends")
def trends():
    return render_template("trends.html")

@app.route("/budget")
def budget():
    return render_template("budget.html")

@app.route("/forecast")
def forecast():
    return render_template("forecast.html")

@app.route("/goals")
def goals():
    return render_template("goals.html")

@app.route("/recommendations")
def recommendations():
    return render_template("recommendations.html")



if __name__ == "__main__":
    app.run(debug=True)