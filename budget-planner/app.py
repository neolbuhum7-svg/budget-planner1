import sqlite3
from datetime import date, datetime
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "budget.db"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY","dev-only-key")  # change before deploying anywhere public

EXPENSE_CATEGORIES = [
    "Food", "Rent", "Transport", "Utilities", "Shopping",
    "Health", "Education", "Entertainment", "Savings", "Other",
]
INCOME_CATEGORIES = ["Salary", "Business", "Gift", "Interest", "Other"]


# ---------- Database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            category TEXT NOT NULL,
            amount REAL NOT NULL CHECK (amount > 0),
            description TEXT,
            date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS budgets (
            month TEXT PRIMARY KEY,
            amount REAL NOT NULL CHECK (amount >= 0)
        );
        """
    )
    db.commit()
    db.close()


# ---------- Utilities ----------
def valid_month(value):
    try:
        datetime.strptime(value, "%Y-%m")
        return value
    except (ValueError, TypeError):
        return date.today().strftime("%Y-%m")


def shift_month(month, delta):
    year, mon = map(int, month.split("-"))
    idx = year * 12 + (mon - 1) + delta
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


# ---------- Routes ----------
@app.route("/")
def index():
    month = valid_month(request.args.get("month"))
    db = get_db()

    transactions = db.execute(
        "SELECT * FROM transactions WHERE substr(date, 1, 7) = ? "
        "ORDER BY date DESC, id DESC",
        (month,),
    ).fetchall()

    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expense = sum(t["amount"] for t in transactions if t["type"] == "expense")

    row = db.execute("SELECT amount FROM budgets WHERE month = ?", (month,)).fetchone()
    budget = row["amount"] if row else 0
    remaining = budget - expense
    percent_used = min(round(expense / budget * 100), 100) if budget else 0

    by_category = {}
    for t in transactions:
        if t["type"] == "expense":
            by_category[t["category"]] = by_category.get(t["category"], 0) + t["amount"]

    return render_template(
        "index.html",
        month=month,
        month_label=datetime.strptime(month, "%Y-%m").strftime("%B %Y"),
        prev_month=shift_month(month, -1),
        next_month=shift_month(month, 1),
        transactions=transactions,
        income=income,
        expense=expense,
        balance=income - expense,
        budget=budget,
        remaining=remaining,
        percent_used=percent_used,
        over_budget=budget > 0 and expense > budget,
        chart_labels=list(by_category.keys()),
        chart_values=[round(v, 2) for v in by_category.values()],
        expense_categories=EXPENSE_CATEGORIES,
        income_categories=INCOME_CATEGORIES,
        today=date.today().isoformat(),
    )


@app.route("/add", methods=["POST"])
def add_transaction():
    t_type = request.form.get("type")
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    tx_date = request.form.get("date", "")
    try:
        amount = float(request.form.get("amount", ""))
        datetime.strptime(tx_date, "%Y-%m-%d")
    except ValueError:
        flash("Please enter a valid amount and date.", "error")
        return redirect(url_for("index"))

    if t_type not in ("income", "expense") or not category or amount <= 0:
        flash("Invalid transaction details.", "error")
        return redirect(url_for("index"))

    db = get_db()
    db.execute(
        "INSERT INTO transactions (type, category, amount, description, date) "
        "VALUES (?, ?, ?, ?, ?)",
        (t_type, category, amount, description, tx_date),
    )
    db.commit()
    flash("Transaction added.", "success")
    return redirect(url_for("index", month=tx_date[:7]))


@app.route("/delete/<int:tx_id>", methods=["POST"])
def delete_transaction(tx_id):
    month = valid_month(request.form.get("month"))
    db = get_db()
    db.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    db.commit()
    flash("Transaction deleted.", "success")
    return redirect(url_for("index", month=month))


@app.route("/budget", methods=["POST"])
def set_budget():
    month = valid_month(request.form.get("month"))
    try:
        amount = float(request.form.get("amount", ""))
        if amount < 0:
            raise ValueError
    except ValueError:
        flash("Please enter a valid budget amount.", "error")
        return redirect(url_for("index", month=month))

    db = get_db()
    db.execute(
        "INSERT INTO budgets (month, amount) VALUES (?, ?) "
        "ON CONFLICT(month) DO UPDATE SET amount = excluded.amount",
        (month, amount),
    )
    db.commit()
    flash("Monthly budget saved.", "success")
    return redirect(url_for("index", month=month))

init_db()
if __name__ == "__main__":
  app.run(debug=True)
