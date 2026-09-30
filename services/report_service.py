from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def create_report(analysis):
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="Resume and Job Match Report",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#183153"),
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySafe",
            parent=styles["BodyText"],
            alignment=TA_LEFT,
            leading=14,
        )
    )

    content = [
        Paragraph("Resume and Job Match Report", styles["Title"]),
        Paragraph(f"Resume file: {_safe(analysis['file_name'])}", styles["BodySafe"]),
        Spacer(1, 8),
    ]
    score = analysis["match"]["score"]
    content.append(
        Paragraph(
            f"Overall match: {_safe(str(score) + '%' if score is not None else 'Not scored')}",
            styles["Heading2"],
        )
    )
    content.extend(
        [
            Paragraph("How the score is calculated", styles["SectionHeading"]),
            Paragraph(_safe(analysis["match"]["score_method"]), styles["BodySafe"]),
            Paragraph(_safe(analysis["match"]["explanation"]), styles["BodySafe"]),
        ]
    )
    components = analysis["match"]["component_scores"]
    if components:
        rows = [["Criterion", "Evidence", "Effective weight", "Score"]]
        for name, component in components.items():
            if name == "skills":
                evidence = (
                    f"{len(component['matched'])} of {component['criteria_count']} "
                    "required skills"
                )
            elif name == "experience":
                years = (
                    component["candidate_years"]
                    if component["candidate_years"] is not None
                    else "Not stated"
                )
                evidence = f"{years} / {component['required_years']} years"
            else:
                evidence = ", ".join(component["candidate_education"]) or "Not stated"
            rows.append(
                [
                    Paragraph(_safe(name.title()), styles["BodySafe"]),
                    Paragraph(_safe(evidence), styles["BodySafe"]),
                    f"{component['weight']}%",
                    f"{component['score']}%",
                ]
            )
        breakdown = Table(rows, colWidths=[1.15 * inch, 3.15 * inch, 1.05 * inch, 0.75 * inch])
        breakdown.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0f8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#183153")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dbe3ed")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        content.extend([Spacer(1, 8), breakdown])
    content.extend(
        [
            Paragraph("Resume analysis", styles["SectionHeading"]),
            Paragraph(
                f"Name: {_safe(analysis['resume']['name'] or 'Not stated')}<br/>"
                f"Headline: {_safe(analysis['resume']['headline'] or 'Not stated')}<br/>"
                f"Experience: {_safe(str(analysis['resume']['experience_years']) + ' years' if analysis['resume']['experience_years'] is not None else 'Not stated')}",
                styles["BodySafe"],
            ),
        ]
    )
    _add_list(content, "Skills", analysis["resume"]["skills"], styles)
    _add_list(content, "Education", analysis["resume"]["education"], styles)
    _add_list(content, "Experience summary", analysis["resume"]["experience_summary"], styles)
    _add_list(content, "Projects", analysis["resume"]["projects"], styles)
    _add_list(content, "Required skills found", analysis["match"]["matched_skills"], styles)
    _add_list(content, "Skill gaps", analysis["match"]["missing_skills"], styles)
    content.append(Paragraph("Job description requirements", styles["SectionHeading"]))
    content.append(
        Paragraph(
            f"Role: {_safe(analysis['job']['title'] or 'Not stated')}<br/>"
            f"Minimum experience: {_safe(str(analysis['job']['minimum_experience_years']) + ' years' if analysis['job']['minimum_experience_years'] is not None else 'Not stated')}<br/>"
            f"Required education: {_safe(analysis['job']['required_education'] or 'Not stated')}",
            styles["BodySafe"],
        )
    )
    _add_list(content, "Explicitly required skills", analysis["job"]["required_skills"], styles)
    _add_list(content, "Key responsibilities", analysis["job"]["key_responsibilities"], styles)
    _add_list(
        content,
        "Resume improvement suggestions",
        analysis["recommendations"]["resume_improvements"],
        styles,
    )
    _add_list(
        content,
        "Interview preparation questions",
        analysis["recommendations"]["interview_questions"],
        styles,
    )
    if analysis.get("refinement"):
        _add_list(
            content,
            "Refined suggestions",
            analysis["refinement"]["revised_suggestions"],
            styles,
        )
    content.extend(
        [
            Paragraph("Customized cover letter", styles["SectionHeading"]),
            Paragraph(
                _safe(analysis["recommendations"]["cover_letter"]).replace("\n", "<br/>"),
                styles["BodySafe"],
            ),
            Spacer(1, 10),
            Paragraph(
                "AI-generated analysis can be incomplete. Verify every statement before using it.",
                styles["Italic"],
            ),
        ]
    )
    document.build(content)
    output.seek(0)
    return output


def _add_list(content, title, values, styles):
    content.append(Paragraph(title, styles["SectionHeading"]))
    if values:
        content.extend(
            Paragraph(f"&bull; {_safe(value)}", styles["BodySafe"]) for value in values
        )
    else:
        content.append(Paragraph("None identified.", styles["BodySafe"]))


def _safe(value):
    return escape(str(value), quote=True)
