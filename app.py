import os

from flask import Flask, jsonify, render_template

from config import Config
from database.models import get_recent_analyses, init_db
from routes.job_routes import job_routes
from routes.resume_routes import resume_routes


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    database_directory = os.path.dirname(os.path.abspath(app.config["DATABASE_PATH"]))
    os.makedirs(database_directory, exist_ok=True)
    init_db(app.config["DATABASE_PATH"])
    app.register_blueprint(resume_routes)
    app.register_blueprint(job_routes)

    @app.context_processor
    def inject_recent_analyses():
        return {
            "recent_analyses": get_recent_analyses(app.config["DATABASE_PATH"]),
            "llm_provider_name": app.config["LLM_PROVIDER"].title(),
        }

    @app.errorhandler(413)
    def request_too_large(_error):
        message = "The uploaded file is too large. The maximum upload size is 8 MB."
        if not _is_api_request():
            return render_template("upload.html", error=message), 413
        return jsonify({"error": message}), 413

    @app.errorhandler(404)
    def not_found(_error):
        if _is_api_request():
            return jsonify({"error": "The requested resource was not found."}), 404
        return render_template("404.html"), 404

    return app


def _is_api_request():
    from flask import request

    return request.path.startswith("/api/")


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "").lower() == "true",
    )
