"""
database.py
-----------
Handles SQLite database connection and initialization.
This module provides a single get_db() function that returns a database
connection, and an init_db() function that creates the tables on first run.
"""

import sqlite3
import os

# Path to the SQLite database file (same directory as this script)
DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")


def get_db():
    """
    Open and return a new SQLite database connection.
    
    - row_factory = sqlite3.Row lets us access columns by name (like a dict)
      e.g. row["title"] instead of row[1]
    - detect_types parses stored ISO-date strings back into Python date objects
    """
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row  # enables dict-style column access
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrency for SQLite
    return conn


def init_db():
    """
    Create the 'transactions' table if it does not already exist,
    and migrate any existing database to add the 'currency' column.
    Called once at application startup from app.py.
    """
    conn = get_db()
    cursor = conn.cursor()

    # CREATE TABLE IF NOT EXISTS means this is safe to call multiple times.
    # 'currency' defaults to 'USD' so any rows inserted before this feature
    # existed will still display correctly.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,  -- auto-incrementing unique ID
            title       TEXT    NOT NULL,                   -- short description of transaction
            amount      REAL    NOT NULL,                   -- monetary value (always positive)
            type        TEXT    NOT NULL                    -- 'income' or 'expense'
                        CHECK(type IN ('income', 'expense')),
            category    TEXT    NOT NULL,                   -- e.g. Food, Salary, Rent ...
            date        TEXT    NOT NULL,                   -- ISO format: YYYY-MM-DD
            currency    TEXT    NOT NULL DEFAULT 'USD',     -- ISO 4217 currency code
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))  -- auto timestamp
        )
    """)

    # -------------------------------------------------------------------
    # Migration: add the 'currency' column to an existing database that
    # was created before multi-currency support was added.
    # SQLite does not support IF NOT EXISTS on ALTER TABLE, so we check
    # the column list first and only run the ALTER if it is missing.
    # -------------------------------------------------------------------
    existing_columns = {row[1] for row in cursor.execute("PRAGMA table_info(transactions)")}
    if "currency" not in existing_columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN currency TEXT NOT NULL DEFAULT 'USD'")
        print("[DB] Migration applied — 'currency' column added (existing rows default to USD).")

    conn.commit()
    conn.close()
    print("[DB] Database initialised — table 'transactions' is ready.")
