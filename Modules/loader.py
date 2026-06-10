"""
loader.py
---------
Reads expenses.csv and validates the data.
Returns a clean pandas DataFrame for other modules to use.
"""

import pandas as pd
import os

# Valid categories allowed in the CSV
VALID_CATEGORIES = [
    "Food", "Rent", "Utilities", "Transport", "Entertainment",
    "Healthcare", "Education", "Clothing", "EMI", "Savings",
    "Salary", "Freelance", "Other"
]

VALID_TYPES = ["income", "expense"]


def load_data(filepath="Data/expenses.csv"):
    """
    Load and validate the CSV file.
    Returns a clean DataFrame or raises an error with a helpful message.
    """

    # --- 1. Check if file exists ---
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"\n❌ File not found: '{filepath}'"
            f"\n   Please make sure 'expenses.csv' is inside the 'Data/' folder."
        )

    # --- 2. Load CSV ---
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        raise ValueError(f"\n❌ Could not read the CSV file.\n   Error: {e}")

    # --- 3. Check required columns ---
    required_columns = {"date", "category", "type", "amount", "description"}
    missing = required_columns - set(df.columns.str.lower())
    if missing:
        raise ValueError(
            f"\n❌ Missing columns in CSV: {missing}"
            f"\n   Required columns: date, category, type, amount, description"
        )

    # Normalize column names to lowercase
    df.columns = df.columns.str.lower().str.strip()

    # --- 4. Drop empty rows ---
    df.dropna(subset=["date", "category", "type", "amount"], inplace=True)

    # --- 5. Clean & convert date column ---
    try:
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    except Exception:
        raise ValueError(
            "\n❌ Date format is wrong. Use YYYY-MM-DD format."
            "\n   Example: 2024-01-15"
        )

    # --- 6. Add helper columns ---
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")   # Jan, Feb, Mar...
    df["year"] = df["date"].dt.year
    df["month_year"] = df["date"].dt.strftime("%b %Y")  # Jan 2024

    # --- 7. Clean text columns ---
    df["category"] = df["category"].str.strip().str.title()   # "food" → "Food"
    df["type"] = df["type"].str.strip().str.lower()           # "Income" → "income"
    df["description"] = df["description"].str.strip()

    # --- 8. Validate 'type' column ---
    invalid_types = df[~df["type"].isin(VALID_TYPES)]
    if not invalid_types.empty:
        print(f"\n⚠️  Warning: {len(invalid_types)} rows have invalid type (not 'income'/'expense'). They will be skipped.")
        df = df[df["type"].isin(VALID_TYPES)]

    # --- 9. Validate 'amount' column ---
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    invalid_amounts = df[df["amount"].isna()]
    if not invalid_amounts.empty:
        print(f"\n⚠️  Warning: {len(invalid_amounts)} rows have invalid amount values. They will be skipped.")
        df = df[df["amount"].notna()]

    df["amount"] = df["amount"].astype(float)

    # --- 10. Warn about unknown categories ---
    unknown_cats = df[~df["category"].isin(VALID_CATEGORIES)]["category"].unique()
    if len(unknown_cats) > 0:
        print(f"\n⚠️  Unknown categories found: {list(unknown_cats)}")
        print("   These will be treated as 'Other'. You can add them to VALID_CATEGORIES in loader.py")
        df["category"] = df["category"].apply(
            lambda x: x if x in VALID_CATEGORIES else "Other"
        )

    # --- Final check ---
    if df.empty:
        raise ValueError("\n❌ No valid data found in the CSV after validation.")

    print(f"✅ Data loaded successfully! {len(df)} valid records found.")
    print(f"   Date range: {df['date'].min().strftime('%d %b %Y')} → {df['date'].max().strftime('%d %b %Y')}")
    print(f"   Months covered: {df['month_year'].nunique()}")

    return df


def get_summary(df):
    """
    Quick summary of what's in the dataset.
    Useful for debugging or first-run overview.
    """
    print("\n📋 Dataset Summary:")
    print(f"   Total records   : {len(df)}")
    print(f"   Income records  : {len(df[df['type'] == 'income'])}")
    print(f"   Expense records : {len(df[df['type'] == 'expense'])}")
    print(f"   Categories      : {', '.join(sorted(df['category'].unique()))}")
    print(f"   Months          : {', '.join(df['month_year'].unique())}")


# -------------------------------------------------------
# Quick test — run this file directly to check if it works
# -------------------------------------------------------
if __name__ == "__main__":
    df = load_data("Data/expenses.csv")
    get_summary(df)
