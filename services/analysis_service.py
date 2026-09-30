import math
import uuid

from services.matching_service import calculate_match
from services.llm_service import generate_json
from services.prompt_templates import (
    JOB_ANALYSIS_SYSTEM,
    RECOMMENDATIONS_SYSTEM,
    RESUME_ANALYSIS_SYSTEM,
    refinement_prompt,
    recommendations_prompt,
    job_analysis_prompt,
    resume_analysis_prompt,
    REFINEMENT_SYSTEM,
)


class AnalysisFormatError(ValueError):
    pass


def analyze(resume_text, job_description, file_name):
    resume = _validate_resume(
        generate_json(RESUME_ANALYSIS_SYSTEM, resume_analysis_prompt(resume_text))
    )
    job = _validate_job(generate_json(JOB_ANALYSIS_SYSTEM, job_analysis_prompt(job_description)))
    match = calculate_match(resume, job)
    recommendations = _validate_recommendations(
        generate_json(
            RECOMMENDATIONS_SYSTEM, recommendations_prompt(resume, job, match)
        )
    )
    return {
        "id": str(uuid.uuid4()),
        "file_name": file_name,
        "resume": resume,
        "job": job,
        "match": match,
        "recommendations": recommendations,
        "refinement": None,
    }


def refine_suggestions(analysis, feedback):
    current_suggestions = (
        analysis["refinement"]["revised_suggestions"]
        if analysis.get("refinement")
        else analysis["recommendations"]["resume_improvements"]
    )
    data = generate_json(
        REFINEMENT_SYSTEM,
        refinement_prompt(
            {
                "resume": analysis["resume"],
                "job": analysis["job"],
                "match": analysis["match"],
                "current_suggestions": current_suggestions,
            },
            feedback,
        ),
    )
    suggestions = _string_list(data, "revised_suggestions", required=True)
    refinement = {
        "feedback": feedback,
        "revised_suggestions": suggestions,
    }
    analysis.setdefault("refinement_history", []).append(refinement)
    analysis["refinement"] = refinement
    return analysis


def _validate_resume(data):
    return {
        "name": _optional_string(data, "name"),
        "headline": _optional_string(data, "headline"),
        "skills": _string_list(data, "skills"),
        "education": _string_list(data, "education"),
        "experience_years": _optional_number(data, "experience_years"),
        "experience_summary": _string_list(data, "experience_summary"),
        "projects": _string_list(data, "projects"),
        "strengths": _string_list(data, "strengths"),
    }


def _validate_job(data):
    return {
        "title": _optional_string(data, "title"),
        "required_skills": _string_list(data, "required_skills"),
        "minimum_experience_years": _optional_number(data, "minimum_experience_years"),
        "required_education": _optional_string(data, "required_education"),
        "key_responsibilities": _string_list(data, "key_responsibilities"),
    }


def _validate_recommendations(data):
    cover_letter = data.get("cover_letter")
    if not isinstance(cover_letter, str) or not cover_letter.strip():
        raise AnalysisFormatError("The model did not return a valid cover letter.")
    return {
        "resume_improvements": _string_list(data, "resume_improvements", required=True),
        "interview_questions": _string_list(data, "interview_questions", required=True),
        "cover_letter": cover_letter.strip(),
    }


def _optional_string(data, field):
    value = data.get(field)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise AnalysisFormatError(f"The model returned an invalid {field} value.")
    return value.strip() or None


def _optional_number(data, field):
    value = data.get(field)
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise AnalysisFormatError(f"The model returned an invalid {field} value.")
    if value < 0 or value > 80:
        raise AnalysisFormatError(f"The model returned an out-of-range {field} value.")
    return value


def _string_list(data, field, required=False):
    values = data.get(field)
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise AnalysisFormatError(f"The model returned an invalid {field} list.")
    cleaned = [value.strip() for value in values if value.strip()]
    if required and not cleaned:
        raise AnalysisFormatError(f"The model returned an empty {field} list.")
    return cleaned[:30]
