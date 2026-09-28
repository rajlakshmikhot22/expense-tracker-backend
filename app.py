"""
app.py
------
Application entry point and factory.

Run the development server:
    python app.py

The server starts on http://127.0.0.1:5000 by default.
CORS is enabled so the frontend (served from a different origin / file://)
can make API requests without being blocked by the browser.
"""

from flask import Flask
from flask_cors import CORS

# Import our database initialiser and route blueprint
from database import init_db
from routes import transactions_bp


def create_app():
    """
    Application factory function.
    Creating the app inside a function (rather than at module level) is a
    Flask best practice — it makes testing and configuration easier.
    """
    app = Flask(__name__)

    # -----------------------------------------------------------------------
    # CORS (Cross-Origin Resource Sharing)
    # -----------------------------------------------------------------------
    # The frontend HTML is opened directly from the filesystem (file://) or
    # served from a different port, so we need to allow cross-origin requests.
    # In production you would restrict this to your actual domain.
    CORS(app, resources={r"/*": {"origins": "*"}})

    # -----------------------------------------------------------------------
    # Register Blueprints
    # -----------------------------------------------------------------------
    # All /transactions routes are defined in routes.py and registered here
    # under the /api prefix, e.g. GET /api/transactions
    app.register_blueprint(transactions_bp, url_prefix="/api")

    # -----------------------------------------------------------------------
    # Root health-check endpoint
    # -----------------------------------------------------------------------
    @app.route("/")
    def index():
        return {
            "message": "Expense Tracker API is running.",
            "version": "1.0.0",
            "endpoints": {
                "list_all":   "GET  /api/transactions",
                "get_one":    "GET  /api/transactions/<id>",
                "create":     "POST /api/transactions",
                "update":     "PUT  /api/transactions/<id>",
                "delete":     "DELETE /api/transactions/<id>",
            }
        }, 200

    # -----------------------------------------------------------------------
    # Global error handlers
    # -----------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(e):
        """Return JSON instead of Flask's default HTML 404 page."""
        return {"success": False, "error": "Route not found."}, 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return {"success": False, "error": "Method not allowed."}, 405

    @app.errorhandler(500)
    def internal_error(e):
        return {"success": False, "error": "An internal server error occurred."}, 500

    return app


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Initialise the database (creates tables if they don't exist)
    init_db()

    # Build the Flask app
    app = create_app()

    # debug=True enables:
    #   • Auto-reload when you save a Python file
    #   • Detailed error pages in the browser
    # Never use debug=True in production!
    app.run(host="0.0.0.0", port=5000, debug=True)
