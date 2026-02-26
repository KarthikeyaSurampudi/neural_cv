# Scoring tests

from domain.resume_models import ResumeData


def test_resume_model_defaults():

    resume = ResumeData(name="John Doe")

    assert resume.skill_match == 0.0
    assert resume.exp_match == 0.0
    assert resume.overall_score == 0.0
