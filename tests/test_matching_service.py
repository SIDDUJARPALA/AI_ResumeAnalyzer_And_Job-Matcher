import unittest

from services.matching_service import calculate_match


class MatchingServiceTests(unittest.TestCase):
    def test_score_uses_only_explicit_criteria_and_normalizes_weights(self):
        resume = {
            "skills": ["Python", "flask"],
            "education": ["Bachelor of Science in Computer Science"],
            "experience_years": 1,
        }
        job = {
            "required_skills": ["Python", "Flask", "SQL"],
            "minimum_experience_years": 2,
            "required_education": "Bachelor's degree",
        }

        result = calculate_match(resume, job)

        self.assertEqual(result["score"], 68)
        self.assertEqual(result["matched_skills"], ["Python", "Flask"])
        self.assertEqual(result["missing_skills"], ["SQL"])
        self.assertEqual(sum(item["weight"] for item in result["component_scores"].values()), 100)

    def test_no_explicit_requirements_returns_no_score(self):
        result = calculate_match(
            {"skills": [], "education": [], "experience_years": None},
            {
                "required_skills": [],
                "minimum_experience_years": None,
                "required_education": None,
            },
        )

        self.assertIsNone(result["score"])
        self.assertEqual(result["component_scores"], {})
        self.assertIn("cannot be calculated", result["explanation"])

    def test_missing_experience_counts_as_zero_when_job_requires_it(self):
        result = calculate_match(
            {"skills": [], "education": [], "experience_years": None},
            {
                "required_skills": [],
                "minimum_experience_years": 3,
                "required_education": None,
            },
        )

        self.assertEqual(result["score"], 0)
        self.assertEqual(result["component_scores"]["experience"]["score"], 0)


if __name__ == "__main__":
    unittest.main()
