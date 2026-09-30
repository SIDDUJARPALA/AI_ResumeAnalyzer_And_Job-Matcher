import re


def calculate_match(resume, job):
    required_skills = _unique_strings(job.get("required_skills", []))
    candidate_skills = _unique_strings(resume.get("skills", []))
    matched_skills = [
        skill
        for skill in required_skills
        if _normalize(skill) in {_normalize(item) for item in candidate_skills}
    ]
    missing_skills = [skill for skill in required_skills if skill not in matched_skills]

    components = {}
    if required_skills:
        components["skills"] = {
            "score": round(len(matched_skills) / len(required_skills) * 100),
            "base_weight": 60,
            "weight": 0,
            "matched": matched_skills,
            "missing": missing_skills,
            "criteria_count": len(required_skills),
        }

    required_years = job.get("minimum_experience_years")
    if required_years is not None:
        candidate_years = resume.get("experience_years")
        experience_score = (
            0
            if candidate_years is None
            else round(min(candidate_years / required_years, 1) * 100)
            if required_years > 0
            else 100
        )
        components["experience"] = {
            "score": experience_score,
            "base_weight": 25,
            "weight": 0,
            "candidate_years": candidate_years,
            "required_years": required_years,
        }

    required_education = job.get("required_education")
    if required_education:
        education_details = " ".join(resume.get("education", []))
        education_score = 100 if _education_matches(education_details, required_education) else 0
        components["education"] = {
            "score": education_score,
            "base_weight": 15,
            "weight": 0,
            "candidate_education": resume.get("education", []),
            "required_education": required_education,
        }

    total_weight = sum(component["base_weight"] for component in components.values())
    for component in components.values():
        component["weight"] = round(component["base_weight"] / total_weight * 100, 1) if total_weight else 0
    score = (
        round(
            sum(
                component["score"] * component["base_weight"]
                for component in components.values()
            )
            / total_weight
        )
        if total_weight
        else None
    )
    if score is None:
        explanation = (
            "No explicit skills, experience, or education requirements were identified, "
            "so a numeric score cannot be calculated."
        )
    else:
        explanation = (
            f"The score is a weighted average of explicit requirements only: "
            f"{', '.join(_component_explanation(key, value) for key, value in components.items())}. "
            f"Effective weights are normalized to 100%."
        )

    return {
        "score": score,
        "score_method": (
            "Required skills: 60%; minimum experience: 25%; required education: 15%. "
            "Only criteria explicitly found in the job description are included, and "
            "their weights are normalized to total 100%."
        ),
        "component_scores": components,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "explanation": explanation,
    }


def _component_explanation(name, component):
    if name == "skills":
        return (
            f"skills {len(component['matched'])}/{component['criteria_count']} "
            f"({component['score']}%, effective weight {component['weight']}%; "
            f"base weight {component['base_weight']}%)"
        )
    if name == "experience":
        return (
            f"experience {component['candidate_years'] if component['candidate_years'] is not None else 'not stated'} "
            f"/ {component['required_years']} years "
            f"({component['score']}%, effective weight {component['weight']}%; "
            f"base weight {component['base_weight']}%)"
        )
    return (
        f"education {component['score']}% "
        f"(effective weight {component['weight']}%; base weight {component['base_weight']}%; "
        f"required: {component['required_education']})"
    )


def _education_matches(candidate_education, required_education):
    candidate = _normalize(candidate_education)
    required = _normalize(required_education)
    if required in candidate:
        return True

    levels = (
        ("doctorate", ("phd", "doctorate", "doctoral")),
        ("masters", ("master", "msc", "mba", "m a ", "m.s.")),
        ("bachelors", ("bachelor", "bsc", "b a ", "b.s.")),
        ("associate", ("associate",)),
        ("high_school", ("high school", "secondary school")),
    )
    candidate_level = _education_level(candidate, levels)
    required_level = _education_level(required, levels)
    ranks = {"high_school": 1, "associate": 2, "bachelors": 3, "masters": 4, "doctorate": 5}
    return bool(
        candidate_level
        and required_level
        and ranks[candidate_level] >= ranks[required_level]
    )


def _education_level(value, levels):
    for level, indicators in levels:
        if any(indicator in value for indicator in indicators):
            return level
    return None


def _normalize(value):
    return re.sub(r"[^a-z0-9+#.]+", " ", value.casefold()).strip()


def _unique_strings(values):
    output = []
    seen = set()
    for value in values:
        normalized = _normalize(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            output.append(value.strip())
    return output
