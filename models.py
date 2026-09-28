"""
models.py
---------
Data-access layer — all SQL queries live here.
Routes call these functions; they never touch SQL directly.
This separation keeps the code clean and easy to test/swap later.
"""

from database import get_db


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def row_to_dict(row):
    """Convert a sqlite3.Row object into a plain Python dict for JSON serialisation."""
    return dict(row)


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

def get_all_transactions():
    """
    Return every transaction, ordered by date descending (newest first).
    The frontend applies further client-side sorting/filtering on top of this.
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions ORDER BY date DESC, created_at DESC"
    ).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def get_transaction_by_id(transaction_id):
    """
    Return a single transaction dict, or None if it doesn't exist.
    Using a parameterised query (?) to prevent SQL injection.
    """
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
    ).fetchone()
    conn.close()
    return row_to_dict(row) if row else None


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

def create_transaction(title, amount, type_, category, date, currency="USD"):
    """
    Insert a new transaction row and return the newly created record as a dict.

    Parameters
    ----------
    title    : str   – short description
    amount   : float – monetary value (must be > 0)
    type_    : str   – 'income' or 'expense'
    category : str   – free-text category label
    date     : str   – ISO date string 'YYYY-MM-DD'
    currency : str   – ISO 4217 currency code (e.g. 'USD', 'INR'). Defaults to 'USD'.
    """
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO transactions (title, amount, type, category, date, currency)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, amount, type_, category, date, currency),
    )
    conn.commit()

    # Fetch and return the record we just inserted
    new_id = cursor.lastrowid
    new_row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?", (new_id,)
    ).fetchone()
    conn.close()
    return row_to_dict(new_row)


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

def update_transaction(transaction_id, title, amount, type_, category, date, currency="USD"):
    """
    Update an existing transaction. Returns the updated dict, or None if not found.
    """
    conn = get_db()

    # Check the record exists before attempting the update
    existing = conn.execute(
        "SELECT id FROM transactions WHERE id = ?", (transaction_id,)
    ).fetchone()

    if not existing:
        conn.close()
        return None  # caller should return 404

    conn.execute(
        """
        UPDATE transactions
        SET title = ?, amount = ?, type = ?, category = ?, date = ?, currency = ?
        WHERE id = ?
        """,
        (title, amount, type_, category, date, currency, transaction_id),
    )
    conn.commit()

    updated_row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
    ).fetchone()
    conn.close()
    return row_to_dict(updated_row)


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

def delete_transaction(transaction_id):
    """
    Delete a transaction by ID.
    Returns True if a row was deleted, False if the ID was not found.
    """
    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM transactions WHERE id = ?", (transaction_id,)
    )
    conn.commit()
    conn.close()

    # rowcount tells us how many rows were affected
    return cursor.rowcount > 0
