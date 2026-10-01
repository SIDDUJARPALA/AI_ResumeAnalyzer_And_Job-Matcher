# CareerLens: AI Resume Analyzer & Job Matcher
<img width="1920" height="1020" alt="Image" src="https://github.com/user-attachments/assets/e307d8b4-0178-44dd-88ed-ea02ae2d7ec6" />

CareerLens is a Flask web application for analyzing PDF/DOCX resumes against a job description. It uses Groq for evidence-grounded resume and job-description analysis, then calculates a transparent match score in Python. The results include skill gaps, improvement suggestions, interview questions, a customized cover letter, structured JSON, iterative suggestion refinement, and a downloadable PDF report.

## Technology

- Python, Flask, HTML, CSS, Bootstrap 5 and JavaScript
- Groq Chat Completions API for structured analysis and recommendations
- PyMuPDF for PDF extraction and python-docx for DOCX extraction
- SQLite for saved structured analysis and iterative refinements
- ReportLab for downloadable PDF reports
- JSON validation and rendering on the server

## Requirements

- Python 3.10 or later
- A Groq API key with API access

## Run locally on Windows

From the project folder, run these PowerShell commands:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Create a Groq API key in the [Groq Console](https://console.groq.com/keys). Edit `.env`, keep `LLM_PROVIDER=groq`, and set `GROQ_API_KEY` to that key. The default Groq model is `openai/gpt-oss-120b`. Do not commit `.env` or share the API key. Then run:

```powershell
python app.py
```

Open <http://127.0.0.1:5000>. The API key is required to submit an analysis; the app can start without it.

## Use the application

1. Upload a text-based PDF or DOCX resume (maximum 8 MB).
2. Paste the job description (maximum 20,000 characters).
3. Review the profile extracted from the resume, job criteria, match breakdown, skill gaps, suggestions, interview questions, and cover letter.
4. Use the feedback form to iteratively refine suggestions.
5. Download a PDF report or open the JSON response.
6. Delete the saved structured analysis when finished.

Scanned image-only PDFs are not OCR-processed. Password-protected PDFs are not supported.

## Matching score

Python calculates the score from explicit criteria returned from the job description: required skills have a base weight of 60%, minimum experience 25%, and required education 15%. Criteria not stated in the job description are excluded, and applicable weights are normalized to 100%. Skills are matched by normalized exact name; experience is proportional up to the stated minimum; education matches an explicit requirement or an equal/higher recognized degree level. The report shows the criteria, component scores, effective weights, and explanation. If no criteria can be identified, no numeric score is shown.

The score is an explainable comparison aid, not a hiring decision or a measure of a person's overall ability. A missing item means it was not found in the resume text—not that the candidate lacks it.

## Prompt chain and grounding

The analysis runs as dependent stages: extract resume facts, extract explicit job criteria, calculate the match deterministically, and generate recommendations using those prior outputs. Prompts use a professional resume-review role, few-shot format examples, reusable Python prompt functions, JSON-only responses, and explicit instructions not to fabricate candidate facts. Refined suggestions are generated from the stored structured analysis and user feedback; original resume text is not stored in SQLite.

The selected AI provider receives the extracted resume text and job description for processing. The application stores the structured result locally in SQLite until the user deletes it. The app has no login or multi-user access controls, so run it locally or put appropriate authentication and access controls in front of it before exposing it to other users. Check your chosen provider's current data-handling terms before sending real candidate data.

## JSON API

`POST /api/analyze` accepts `multipart/form-data` with `resume` (PDF/DOCX file) and `job_description` fields, and returns a JSON analysis object. `GET /api/analysis/<id>` returns a saved object. `POST /api/analysis/<id>/refine` accepts JSON such as `{"feedback":"Focus on concise, evidence-based suggestions."}` and returns the updated object. API errors use a JSON `error` field and appropriate HTTP status codes.

## Configuration

See `.env.example` for environment variables. The app uses Groq with `GROQ_API_KEY` and defaults to `openai/gpt-oss-120b`. `DATABASE_PATH` defaults to `instance/resume_analyzer.sqlite3`; keep the instance directory private and persistent when deploying.

## Deploy to Render

The included `render.yaml` configures a Gunicorn Starter web service, generated Flask secret, Groq provider, and persistent SQLite disk. Review Render's current service and disk pricing before deployment. Set `GROQ_API_KEY` in the deployment environment; never put the key in source control.

## Tests

Run the application and matching tests:

```powershell
python -m unittest discover -v
```

## Assignment demo and submission

- Use `samples/sample_resume.txt` and `samples/sample_job_description.txt` as fictional source content; place the resume text in a DOCX/PDF file before uploading.
- Capture screenshots of the upload form, match results, refinement, and downloaded report from a local run.
- Record the requested 5–7 minute demo showing the analysis flow and score explanation.
- Include architecture/prompt walkthrough and the screenshots/video in the final submission package.

No real personal information or API credentials are included in the sample files.
