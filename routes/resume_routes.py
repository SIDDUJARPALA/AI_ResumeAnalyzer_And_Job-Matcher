from uuid import UUID

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.utils import secure_filename

from database.models import delete_analysis, get_analysis, save_analysis, update_analysis
from services.analysis_service import AnalysisFormatError, analyze, refine_suggestions
from services.llm_service import LLMServiceError
from services.report_service import create_report
from services.resume_parser import ResumeFileError, extract_resume_text


resume_routes = Blueprint("resume", __name__)
MAX_JOB_DESCRIPTION_CHARS = 20_000


@resume_routes.get("/")
def index():
    return render_template("upload.html")


@resume_routes.post("/analyze")
def analyze_form():
    try:
        result = _run_analysis()
    except (ResumeFileError, ValueError, LLMServiceError) as error:
        flash(str(error), "error")
        return render_template("upload.html", job_description=request.form.get("job_description", "")), 400
    return redirect(url_for("resume.results", analysis_id=result["id"]))


@resume_routes.get("/analysis/<analysis_id>")
def results(analysis_id):
    analysis = _load_analysis(analysis_id)
    return render_template("results.html", analysis=analysis)


@resume_routes.post("/analysis/<analysis_id>/refine")
def refine(analysis_id):
    analysis = _load_analysis(analysis_id)
    feedback = request.form.get("feedback", "").strip()
    if not feedback or len(feedback) > 2_000:
        flash("Enter feedback between 1 and 2,000 characters.", "error")
        return redirect(url_for("resume.results", analysis_id=analysis_id))
    try:
        updated = refine_suggestions(analysis, feedback)
    except (AnalysisFormatError, LLMServiceError) as error:
        flash(str(error), "error")
        return redirect(url_for("resume.results", analysis_id=analysis_id))
    update_analysis(current_app.config["DATABASE_PATH"], analysis_id, updated)
    flash("Your improvement suggestions have been refined.", "success")
    return redirect(url_for("resume.results", analysis_id=analysis_id))


@resume_routes.get("/analysis/<analysis_id>/report.pdf")
def download_report(analysis_id):
    analysis = _load_analysis(analysis_id)
    report = create_report(analysis)
    return send_file(
        report,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="resume-job-match-report.pdf",
    )


@resume_routes.post("/analysis/<analysis_id>/delete")
def remove_analysis(analysis_id):
    _load_analysis(analysis_id)
    delete_analysis(current_app.config["DATABASE_PATH"], analysis_id)
    flash("The saved analysis has been deleted.", "success")
    return redirect(url_for("resume.index"))


def _run_analysis():
    resume_file = request.files.get("resume")
    job_description = request.form.get("job_description", "").strip()
    if not resume_file or not resume_file.filename:
        raise ResumeFileError("Choose a PDF or DOCX resume to upload.")
    if not job_description:
        raise ResumeFileError("Enter the job description you want to match against.")
    if len(job_description) > MAX_JOB_DESCRIPTION_CHARS:
        raise ResumeFileError(
            f"The job description must be {MAX_JOB_DESCRIPTION_CHARS:,} characters or fewer."
        )

    file_name = secure_filename(resume_file.filename) or "resume"
    resume_text = extract_resume_text(
        file_name, resume_file.read(), current_app.config
    )
    result = analyze(resume_text, job_description, file_name)
    save_analysis(
        current_app.config["DATABASE_PATH"], result["id"], file_name, result
    )
    return result


def _load_analysis(analysis_id):
    try:
        normalized_id = str(UUID(analysis_id))
    except (ValueError, AttributeError):
        abort(404)
    analysis = get_analysis(current_app.config["DATABASE_PATH"], normalized_id)
    if not analysis:
        abort(404)
    return analysis
