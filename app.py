"""
app.py
------
HomeFi Web — Flask entry point with Supabase database
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
from types import SimpleNamespace
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file
from supabase import create_client

sys.path.append(os.path.join(os.path.dirname(__file__), "Modules"))
from excel_exporter import export_to_excel

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mhdhhyynritbuhpurdii.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1oZGhoeXlucml0YnVocHVyZGlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODExNjc0MTUsImV4cCI6MjA5Njc0MzQxNX0.L9ob_H7C9uFql9eIeT6-P9EIkfeRyw7bOmvk0Hm88_g")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

os.makedirs("Charts",  exist_ok=True)
os.makedirs("Reports", exist_ok=True)


def get_df():
    """Load expenses from Supabase — always returns clean DataFrame with datetime dates"""
    try:
        response = supabase.table("expenses").select("*").execute()
        data = response.data
    except Exception:
        data = []
    if not data:
        return pd.DataFrame(columns=["date","category","type","amount","description"])
    df = pd.DataFrame(data)
    df["date"]   = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df = df.dropna(subset=["date"])
    return df


def add_month_col(df):
    """Safely add month period column"""
    df = df.copy()
    df["date"]  = pd.to_datetime(df["date"], errors="coerce")
    df["month"] = df["date"].dt.to_period("M")
    return df


# ── Page routes ────────────────────────────────────────────────────────────────
@app.route("/")
def dashboard():
    df  = get_df()
    inc = df[df["type"] == "income"]["amount"].sum()
    exp = df[df["type"] == "expense"]["amount"].sum()
    sav = inc - exp
    rate = round((sav / inc * 100) if inc > 0 else 0, 1)

    exp_df = add_month_col(df[df["type"] == "expense"])
    inc_df = add_month_col(df[df["type"] == "income"])

    monthly_exp = exp_df.groupby("month")["amount"].sum()
    monthly_inc = inc_df.groupby("month")["amount"].sum()
    monthly_sav = monthly_inc.subtract(monthly_exp, fill_value=0)
    all_months  = sorted(set(monthly_inc.index) | set(monthly_exp.index))

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

    df_months = add_month_col(df)
    summary = SimpleNamespace(
        total_income  = inc,
        total_expense = exp,
        net_savings   = sav,
        savings_rate  = rate,
        months        = df_months["month"].nunique(),
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


@app.route("/categories")
def categories():   return render_template("categories.html")

@app.route("/trends")
def trends():       return render_template("trends.html")

@app.route("/budget")
def budget():       return render_template("budget.html")

@app.route("/forecast")
def forecast():     return render_template("forecast.html")

@app.route("/goals")
def goals():        return render_template("goals.html")

@app.route("/recommendations")
def recommendations(): return render_template("recommendations.html")


# ── API routes ─────────────────────────────────────────────────────────────────
@app.route("/api/categories")
def api_categories():
    df  = get_df()
    cat = df[df["type"] == "expense"].groupby("category")["amount"].sum().sort_values(ascending=False)
    return jsonify({"labels": list(cat.index), "values": [float(v) for v in cat.values]})


@app.route("/api/trends")
def api_trends():
    df  = get_df()
    df2 = add_month_col(df)
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
    exp_df = add_month_col(df[df["type"] == "expense"])
    monthly = exp_df.groupby("month")["amount"].sum()
    values  = [float(v) for v in monthly.values]
    months  = [str(m) for m in monthly.index]

    if len(values) >= 2:
        x          = np.arange(len(values))
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
        goals_data = json.load(f)

    df     = get_df()
    df2    = add_month_col(df)
    inc_m  = df2[df2["type"] == "income"].groupby("month")["amount"].sum()
    exp_m  = df2[df2["type"] == "expense"].groupby("month")["amount"].sum()
    monthly_sav = inc_m.subtract(exp_m, fill_value=0)
    avg_sav = float(monthly_sav.mean()) if not monthly_sav.empty else 0

    result = []
    for g in goals_data:
        target    = g.get("target", 0)
        saved     = g.get("current_savings", 0)
        pct       = min(100, (saved / target * 100)) if target > 0 else 0
        remaining = max(0, target - saved)
        result.append({
            "name":     g.get("name", "Goal"),
            "target":   target,
            "saved":    saved,
            "pct":      round(pct, 1),
            "priority": g.get("priority", "Medium"),
            "eta":      f"{int(remaining / avg_sav)} months" if avg_sav > 0 else "N/A",
        })
    return jsonify(result)


# ── Add expense ────────────────────────────────────────────────────────────────
@app.route("/add", methods=["GET", "POST"])
def add_expense():
    categories = ["Food", "Rent", "EMI", "Entertainment", "Shopping",
                  "Travel", "Utilities", "Healthcare", "Education",
                  "Salary", "Freelance", "Other"]
    if request.method == "POST":
        date  = request.form.get("date") or datetime.now().strftime("%Y-%m-%d")
        cat   = request.form.get("category")
        etype = request.form.get("type")
        amt   = float(request.form.get("amount"))
        desc  = request.form.get("description") or cat
        supabase.table("expenses").insert({
            "date": date, "category": cat,
            "type": etype, "amount": amt, "description": desc
        }).execute()
        return redirect(url_for("dashboard"))

    return render_template("add.html", categories=categories,
                           today=datetime.now().strftime("%Y-%m-%d"))


@app.route("/download-excel")
def download_excel():
    df   = get_df()
    path = export_to_excel(df)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))