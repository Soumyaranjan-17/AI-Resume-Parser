import pytest
from app.services.text_analyzer import TextAnalyzer
from app.services.skill_extractor import SkillExtractor

@pytest.fixture
def text_analyzer():
    return TextAnalyzer()

@pytest.fixture
def skill_extractor():
    return SkillExtractor()

def test_extract_personal_info(text_analyzer):
    text = """
    John Doe
    john.doe@email.com
    +1-234-567-8901
    New York, USA
    """
    personal_info, confidence = text_analyzer.extract_personal_info(text)
    assert personal_info["email"] == "john.doe@email.com"
    assert confidence > 0

def test_extract_skills(skill_extractor):
    text = "Experienced in Python, JavaScript, and React. Strong leadership skills."
    skills, confidence = skill_extractor.extract_skills(text)
    assert "Python" in skills["technical"]
    assert "JavaScript" in skills["technical"]
    assert "leadership" in skills["soft"]
    assert confidence > 0

def test_skill_normalization(skill_extractor):
    text = "Proficient in JS, ReactJS, and node."
    skills, _ = skill_extractor.extract_skills(text)
    technical_skills = [s.lower() for s in skills["technical"]]
    assert "javascript" in technical_skills
    assert "react" in technical_skills
    assert "node.js" in technical_skills