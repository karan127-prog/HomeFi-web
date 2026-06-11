"""
app.py
------
HomeFi Web — Flask entry point with Supabase + Multi-user login
Run: python app.py
Then open: http://127.0.0.1:5000
"""
import os
import json
import hashlib
import secrets
import numpy as np
import pandas as pd
from datetime import datetime
from flask import (Flask, render_template, jsonify, request,
                   redirect, url_for, session, flash)
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)   # sessions ke liye

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://mhdhhyynritbuhpurdii.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1oZGhoeXlucml0YnVocHVyZGlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODExNjc0MTUsImV4cCI6MjA5Njc0MzQxNX0.L9ob_H7C9uFql9eIeT6-P9EIkfeRyw7bOmvk0Hm88_g"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Auth helpers ──────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user():
    return session.get("username")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ── Data helpers ──────────────────────────────────────────────────────────────
def get_df():
    user = get_current_user()
    if not user:
        return pd.DataFrame(columns=["date","category","type","amount","description"])
    response = supabase.table("expenses").select("*").eq("user_id", user).execute()
    data = response.data
    if not data:
        return pd.DataFrame(columns=["date","category","type","amount","description"])
    df = pd.DataFrame(data)
    df["date"]   = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df = df.dropna(subset=["date"])
    return df

def add_month_col(df, col="date"):
    df = df.copy()
    df[col] = pd.to_datetime(df[col], errors="coerce")
    df["month"] = df[col].dt.to_period("M")
    return df

def safe_json(obj):
    if isinstance(obj, (np.integer,)):  return int(obj)
    if isinstance(obj, (np.floating,)): return float(obj)
    if isinstance(obj, np.ndarray):     return obj.tolist()
    return str(obj)

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET","POST"])
def login():
    if get_current_user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username","").strip().lower()
        password = request.form.get("password","")
        result = supabase.table("users").select("*").eq("username", username).execute()
        if result.data and result.data[0]["password_hash"] == hash_password(password):
            session["username"] = username
            session["name"]     = result.data[0]["name"]
            return redirect(url_for("dashboard"))
        flash("Galat username ya password!", "error")
    return render_template("login.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if get_current_user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name     = request.form.get("name","").strip()
        username = request.form.get("username","").strip().lower()
        password = request.form.get("password","")
        if not name or not username or not password:
            flash("Saare fields fill karo!")
            return render_template("signup.html")
        existing = supabase.table("users").select("username").eq("username", username).execute()
        if existing.data:
            flash("Ye username already le liya gaya hai!")
            return render_template("signup.html")
        supabase.table("users").insert({
            "username": username,
            "name": name,
            "password_hash": hash_password(password)
        }).execute()
        flash(f"Account ban gaya! Ab login karo.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── Main routes ───────────────────────────────────────────────────────────────
@app.route("/")
@login_required
def dashboard():
    df = get_df()
    if df.empty:
        stats = dict(total_income=0, total_expense=0, net_savings=0,
                     savings_rate=0, num_transactions=0, months=0,
                     monthly_labels=[], monthly_exp=[], monthly_inc=[])
        return render_template("dashboard.html", stats=stats,
                               username=get_current_user(), name=session.get("name",""))

    exp_df = add_month_col(df[df["type"]=="expense"].copy())
    inc_df = add_month_col(df[df["type"]=="income"].copy())

    monthly_exp = exp_df.groupby("month")["amount"].sum()
    monthly_inc = inc_df.groupby("month")["amount"].sum()
    all_months  = sorted(set(monthly_exp.index) | set(monthly_inc.index))

    total_income  = float(df[df["type"]=="income"]["amount"].sum())
    total_expense = float(df[df["type"]=="expense"]["amount"].sum())
    net_savings   = total_income - total_expense
    savings_rate  = round((net_savings/total_income)*100, 1) if total_income else 0
    months_count  = pd.to_datetime(df["date"], errors="coerce").dt.to_period("M").nunique()

    stats = dict(
        total_income=total_income, total_expense=total_expense,
        net_savings=net_savings, savings_rate=savings_rate,
        num_transactions=len(df), months=int(months_count),
        monthly_labels=[str(m) for m in all_months],
        monthly_exp=[float(monthly_exp.get(m,0)) for m in all_months],
        monthly_inc=[float(monthly_inc.get(m,0)) for m in all_months],
    )
    return render_template("dashboard.html", stats=stats,
                           username=get_current_user(), name=session.get("name",""))

@app.route("/add", methods=["GET","POST"])
@login_required
def add_entry():
    if request.method == "POST":
        supabase.table("expenses").insert({
            "date":        request.form["date"],
            "category":    request.form["category"],
            "type":        request.form["type"],
            "amount":      float(request.form["amount"]),
            "description": request.form.get("description",""),
            "user_id":     get_current_user()
        }).execute()
        return redirect(url_for("dashboard"))
    return render_template("add.html")

@app.route("/categories")
@login_required
def categories(): return render_template("categories.html")

@app.route("/trends")
@login_required
def trends(): return render_template("trends.html")

@app.route("/budget")
@login_required
def budget(): return render_template("budget.html")

@app.route("/forecast")
@login_required
def forecast(): return render_template("forecast.html")

@app.route("/goals")
@login_required
def goals(): return render_template("goals.html")

@app.route("/recommendations")
@login_required
def recommendations(): return render_template("recommendations.html")

# ── API routes ────────────────────────────────────────────────────────────────
@app.route("/api/categories")
@login_required
def api_categories():
    df = get_df()
    if df.empty: return jsonify({"labels":[],"values":[]})
    exp = df[df["type"]=="expense"].groupby("category")["amount"].sum()
    return jsonify({"labels": exp.index.tolist(), "values": [float(v) for v in exp.values]})

@app.route("/api/trends")
@login_required
def api_trends():
    df = get_df()
    if df.empty: return jsonify({"months":[],"income":[],"expense":[],"savings":[]})
    exp_df = add_month_col(df[df["type"]=="expense"].copy())
    inc_df = add_month_col(df[df["type"]=="income"].copy())
    me = exp_df.groupby("month")["amount"].sum()
    mi = inc_df.groupby("month")["amount"].sum()
    all_m = sorted(set(me.index)|set(mi.index))
    return jsonify({
        "months":  [str(m) for m in all_m],
        "income":  [float(mi.get(m,0)) for m in all_m],
        "expense": [float(me.get(m,0)) for m in all_m],
        "savings": [float(mi.get(m,0)-me.get(m,0)) for m in all_m],
    })

@app.route("/api/budget")
@login_required
def api_budget():
    df = get_df()
    budgets_path = os.path.join("Data","budgets.json")
    if not os.path.exists(budgets_path):
        return jsonify({"error":"No budget set yet. Add a Data/budgets.json file."})
    with open(budgets_path) as f:
        budgets = json.load(f)
    if df.empty:
        return jsonify({"categories":list(budgets.keys()),
                        "spent":[0]*len(budgets),
                        "budget":list(budgets.values())})
    exp = df[df["type"]=="expense"].groupby("category")["amount"].sum()
    cats = list(budgets.keys())
    return jsonify({
        "categories": cats,
        "spent":  [float(exp.get(c,0)) for c in cats],
        "budget": [float(budgets[c]) for c in cats],
    })

@app.route("/api/forecast")
@login_required
def api_forecast():
    df = get_df()
    if df.empty: return jsonify({"months":[],"forecast":[],"actual":[]})
    exp_df = add_month_col(df[df["type"]=="expense"].copy())
    monthly = exp_df.groupby("month")["amount"].sum().reset_index()
    monthly.columns = ["month","amount"]
    monthly = monthly.sort_values("month")
    actuals = monthly["amount"].tolist()
    avg = float(sum(actuals[-3:]) / min(3,len(actuals))) if actuals else 0
    future_months = []
    if len(monthly):
        last = monthly["month"].iloc[-1]
        for i in range(1,4):
            future_months.append(str(last + i))
    return jsonify({
        "months":   [str(m) for m in monthly["month"]] + future_months,
        "actual":   actuals + [None]*3,
        "forecast": [None]*len(actuals) + [round(avg*(1+0.02*i),2) for i in range(1,4)],
    })

@app.route("/api/goals")
@login_required
def api_goals():
    goals_path = os.path.join("Data","goals.json")
    if not os.path.exists(goals_path):
        return jsonify({"error":"No goals found. Create a Data/goals.json file."})
    with open(goals_path) as f:
        return jsonify(json.load(f))

@app.route("/api/recommendations")
@login_required
def api_recommendations():
    df = get_df()
    if df.empty:
        return jsonify({"tips":["Pehle kuch expenses add karo!"],"score":0})
    total_inc = float(df[df["type"]=="income"]["amount"].sum())
    total_exp = float(df[df["type"]=="expense"]["amount"].sum())
    savings_rate = ((total_inc-total_exp)/total_inc*100) if total_inc else 0
    exp_df = df[df["type"]=="expense"]
    top_cat = exp_df.groupby("category")["amount"].sum().idxmax() if not exp_df.empty else "N/A"
    tips = []
    if savings_rate < 20:
        tips.append(f"Savings rate {savings_rate:.1f}% hai — 20% target karo!")
    else:
        tips.append(f"Badiya! Savings rate {savings_rate:.1f}% hai.")
    tips.append(f"Sabse zyada spending '{top_cat}' mein hai — check karo.")
    if savings_rate >= 30: tips.append("Excellent savings! Investment ke baare mein socho.")
    score = min(100, int(savings_rate * 2))
    return jsonify({"tips": tips, "score": score})

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)