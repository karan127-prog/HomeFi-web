"""
expense_adder.py
----------------
HomeFi — Add new expense or income entry directly via CLI.
Appends to Data/expenses.csv without manual file editing.
"""

import os
import csv
from datetime import datetime


DATA_FILE = os.path.join("Data", "expenses.csv")

VALID_CATEGORIES = [
    "Food", "Rent", "EMI", "Entertainment", "Shopping",
    "Travel", "Utilities", "Healthcare", "Education",
    "Salary", "Freelance", "Other"
]

VALID_TYPES = ["expense", "income"]


def _print_categories():
    print("\n  Available Categories:")
    for i, cat in enumerate(VALID_CATEGORIES, 1):
        print(f"    {i:>2}. {cat}")


def _get_input(prompt, validator=None, error_msg="Invalid input."):
    """Keep asking until valid input."""
    while True:
        val = input(prompt).strip()
        if validator is None or validator(val):
            return val
        print(f"  [!] {error_msg}")


def add_entry_interactive():
    """Interactive CLI to add one expense/income entry."""
    print("\n" + "─" * 50)
    print("  ADD NEW ENTRY")
    print("─" * 50)

    # ── Date ──────────────────────────────────────────
    today = datetime.now().strftime("%Y-%m-%d")
    date_input = input(f"  Date (YYYY-MM-DD) [press Enter for today: {today}]: ").strip()
    if not date_input:
        date_input = today
    else:
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            print("  [!] Invalid date format. Using today's date.")
            date_input = today

    # ── Type ──────────────────────────────────────────
    print("\n  Type:")
    print("    1. expense")
    print("    2. income")
    type_choice = _get_input(
        "  Enter choice (1/2): ",
        lambda x: x in ["1", "2"],
        "Enter 1 for expense or 2 for income."
    )
    entry_type = "expense" if type_choice == "1" else "income"

    # ── Category ──────────────────────────────────────
    _print_categories()
    cat_choice = _get_input(
        f"\n  Enter category number (1-{len(VALID_CATEGORIES)}): ",
        lambda x: x.isdigit() and 1 <= int(x) <= len(VALID_CATEGORIES),
        f"Enter a number between 1 and {len(VALID_CATEGORIES)}."
    )
    category = VALID_CATEGORIES[int(cat_choice) - 1]

    # ── Amount ────────────────────────────────────────
    amount = _get_input(
        "  Amount (Rs.): ",
        lambda x: x.replace(".", "", 1).isdigit() and float(x) > 0,
        "Enter a valid positive number."
    )
    amount = float(amount)

    # ── Description ───────────────────────────────────
    description = input("  Description (optional): ").strip()
    if not description:
        description = category

    # ── Confirm ───────────────────────────────────────
    print("\n  ┌─────────────────────────────────────┐")
    print("  │         CONFIRM ENTRY               │")
    print("  ├─────────────────────────────────────┤")
    print(f"  │  Date        : {date_input:<21}│")
    print(f"  │  Type        : {entry_type:<21}│")
    print(f"  │  Category    : {category:<21}│")
    print(f"  │  Amount      : Rs. {amount:<18,.2f}│")
    print(f"  │  Description : {description[:21]:<21}│")
    print("  └─────────────────────────────────────┘")

    confirm = input("\n  Save this entry? (y/n): ").strip().lower()
    if confirm != "y":
        print("  [!] Entry cancelled.")
        return False

    # ── Write to CSV ──────────────────────────────────
    file_exists = os.path.exists(DATA_FILE)
    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "category", "type", "amount", "description"])
        writer.writerow([date_input, category, entry_type, amount, description])

    print(f"\n  [OK] Entry saved to {DATA_FILE}")
    print("  [!] Restart the app or reload data to see updated analysis.\n")
    return True


def add_multiple_entries():
    """Keep adding entries until user says stop."""
    count = 0
    while True:
        success = add_entry_interactive()
        if success:
            count += 1
        again = input("  Add another entry? (y/n): ").strip().lower()
        if again != "y":
            break
    print(f"\n  Done! {count} entr{'y' if count == 1 else 'ies'} added.")


if __name__ == "__main__":
    add_multiple_entries()