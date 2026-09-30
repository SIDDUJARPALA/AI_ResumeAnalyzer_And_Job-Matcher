from flask import Blueprint, current_app, jsonify, request

from database.models import update_analysis
from routes.resume_routes import _load_analysis, _run_analysis
from services.analysis_service import AnalysisFormatError, refine_suggestions
from services.llm_service import LLMServiceError
from services.resume_parser import ResumeFileError


job_routes = Blueprint("jobs", __name__, url_prefix="/api")


@job_routes.post("/analyze")
def analyze_api():
    try:
        result = _run_analysis()
    except ResumeFileError as error:
        return jsonify({"error": str(error)}), 400
    except LLMServiceError as error:
        return jsonify({"error": str(error)}), 502
    except ValueError as error:
        return jsonify({"error": str(error)}), 502
    return jsonify(result), 201


@job_routes.get("/analysis/<analysis_id>")
def get_analysis_api(analysis_id):
    analysis = _load_analysis(analysis_id)
    return jsonify(analysis)


@job_routes.post("/analysis/<analysis_id>/refine")
def refine_api(analysis_id):
    analysis = _load_analysis(analysis_id)
    data = request.get_json(silent=True)
    feedback_value = data.get("feedback") if isinstance(data, dict) else None
    feedback = feedback_value.strip() if isinstance(feedback_value, str) else ""
    if not feedback or len(feedback) > 2_000:
        return jsonify({"error": "Feedback must be between 1 and 2,000 characters."}), 400
    try:
        updated = refine_suggestions(analysis, feedback)
    except (AnalysisFormatError, LLMServiceError) as error:
        return jsonify({"error": str(error)}), 502
    update_analysis(current_app.config["DATABASE_PATH"], analysis_id, updated)
    return jsonify(updated)
