"""
routes.py
---------
Defines all REST API endpoints as a Flask Blueprint.
A Blueprint is like a mini-application — it keeps routes separate from the
app factory in app.py, making the code modular and easy to extend.

Endpoints
---------
GET    /transactions          – list all transactions
GET    /transactions/<id>     – get a single transaction
POST   /transactions          – create a new transaction
PUT    /transactions/<id>     – update an existing transaction
DELETE /transactions/<id>     – delete a transaction
"""

from flask import Blueprint, request, jsonify
import models

# Create a Blueprint named 'transactions'
# All routes registered here will be accessible from the main app
transactions_bp = Blueprint("transactions", __name__)


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------

def validate_transaction_data(data):
    """
    Validate incoming JSON payload for create / update operations.
    Returns (cleaned_data, None) on success, or (None, error_message) on failure.
    """
    errors = []

    # --- title ---
    title = data.get("title", "").strip()
    if not title:
        errors.append("'title' is required and cannot be empty.")
    elif len(title) > 200:
        errors.append("'title' must be 200 characters or fewer.")

    # --- amount ---
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            errors.append("'amount' must be a positive number.")
    except (TypeError, ValueError):
        amount = None
        errors.append("'amount' must be a valid number.")

    # --- type ---
    type_ = data.get("type", "").strip().lower()
    if type_ not in ("income", "expense"):
        errors.append("'type' must be either 'income' or 'expense'.")

    # --- category ---
    category = data.get("category", "").strip()
    if not category:
        errors.append("'category' is required and cannot be empty.")

    # --- date ---
    import re
    date = data.get("date", "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        errors.append("'date' must be in YYYY-MM-DD format.")

    # --- currency ---
    # Full list of supported ISO 4217 codes. Must stay in sync with the
    # CURRENCIES map in script.js on the frontend.
    VALID_CURRENCIES = {
        "USD", "INR", "EUR", "GBP", "JPY", "CAD", "AUD", "AED", "SGD"
    }
    currency = data.get("currency", "USD").strip().upper()
    if currency not in VALID_CURRENCIES:
        errors.append(
            f"'currency' must be one of: {', '.join(sorted(VALID_CURRENCIES))}."
        )

    if errors:
        return None, errors

    return {"title": title, "amount": amount, "type": type_,
            "category": category, "date": date, "currency": currency}, None


# ---------------------------------------------------------------------------
# GET /transactions  — list all
# ---------------------------------------------------------------------------

@transactions_bp.route("/transactions", methods=["GET"])
def get_transactions():
    """
    Return all transactions as a JSON array.
    The frontend handles filtering, searching, and sorting on the client side,
    so we simply return everything here in one shot.
    """
    transactions = models.get_all_transactions()
    return jsonify({
        "success": True,
        "count": len(transactions),
        "data": transactions
    }), 200


# ---------------------------------------------------------------------------
# GET /transactions/<id>  — single record
# ---------------------------------------------------------------------------

@transactions_bp.route("/transactions/<int:transaction_id>", methods=["GET"])
def get_transaction(transaction_id):
    """Return a single transaction by its numeric ID."""
    transaction = models.get_transaction_by_id(transaction_id)

    if not transaction:
        return jsonify({"success": False, "error": "Transaction not found."}), 404

    return jsonify({"success": True, "data": transaction}), 200


# ---------------------------------------------------------------------------
# POST /transactions  — create
# ---------------------------------------------------------------------------

@transactions_bp.route("/transactions", methods=["POST"])
def create_transaction():
    """
    Create a new transaction.

    Expected JSON body:
    {
        "title":    "Groceries",
        "amount":   45.50,
        "type":     "expense",
        "category": "Food",
        "date":     "2025-07-26"
    }
    """
    data = request.get_json(silent=True)  # silent=True returns None on bad JSON

    if not data:
        return jsonify({"success": False, "error": "Request body must be valid JSON."}), 400

    cleaned, errors = validate_transaction_data(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 422  # Unprocessable Entity

    new_transaction = models.create_transaction(
        title=cleaned["title"],
        amount=cleaned["amount"],
        type_=cleaned["type"],
        category=cleaned["category"],
        date=cleaned["date"],
        currency=cleaned["currency"],
    )

    return jsonify({"success": True, "data": new_transaction}), 201  # 201 Created


# ---------------------------------------------------------------------------
# PUT /transactions/<id>  — update
# ---------------------------------------------------------------------------

@transactions_bp.route("/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    """
    Update all fields of an existing transaction.
    Requires the same fields as POST — full replacement, not partial patch.
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"success": False, "error": "Request body must be valid JSON."}), 400

    cleaned, errors = validate_transaction_data(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 422

    updated = models.update_transaction(
        transaction_id=transaction_id,
        title=cleaned["title"],
        amount=cleaned["amount"],
        type_=cleaned["type"],
        category=cleaned["category"],
        date=cleaned["date"],
        currency=cleaned["currency"],
    )

    if updated is None:
        return jsonify({"success": False, "error": "Transaction not found."}), 404

    return jsonify({"success": True, "data": updated}), 200


# ---------------------------------------------------------------------------
# DELETE /transactions/<id>  — delete
# ---------------------------------------------------------------------------

@transactions_bp.route("/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    """Delete a transaction by ID. Returns 204 No Content on success."""
    deleted = models.delete_transaction(transaction_id)

    if not deleted:
        return jsonify({"success": False, "error": "Transaction not found."}), 404

    # 204 No Content is the conventional response for a successful DELETE
    return "", 204
