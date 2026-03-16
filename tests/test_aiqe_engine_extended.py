"""
Extended tests for AIQE Engine - parsing, edge cases, batch processing
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from src.aiqe_engine import AIQEEngine
from src.models import (
    Segment,
    TermEntry,
    QualityIssue,
    AIProviderConfig,
    MQMConfig,
    ErrorCategory,
    ErrorSeverity,
)


@pytest.fixture
def mock_ai_config():
    return AIProviderConfig(
        provider="anthropic",
        api_key="test-key",
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        temperature=0.1,
    )


@pytest.fixture
def mock_mqm_config():
    return MQMConfig(
        enabled_categories=[
            ErrorCategory.ACCURACY,
            ErrorCategory.FLUENCY,
            ErrorCategory.TERMINOLOGY,
            ErrorCategory.STYLE,
        ],
        severity_weights={
            ErrorSeverity.CRITICAL: -25,
            ErrorSeverity.MAJOR: -10,
            ErrorSeverity.MINOR: -3,
            ErrorSeverity.NEUTRAL: 0,
        },
        base_score=100,
    )


@pytest.fixture
def engine(mock_ai_config, mock_mqm_config):
    with patch("anthropic.Anthropic"):
        return AIQEEngine(mock_ai_config, mock_mqm_config)


def test_parse_ai_response_plain_json(engine):
    """Test parsing a plain JSON response."""
    response = json.dumps({
        "issues": [
            {
                "category": "accuracy",
                "severity": "major",
                "description": "Mistranslation",
                "source_excerpt": "Hello",
                "target_excerpt": "Hola",
                "suggestion": "Use correct word",
                "explanation": "Wrong word used",
            }
        ],
        "overall_quality": "Needs improvement",
    })

    issues = engine._parse_ai_response(response)
    assert len(issues) == 1
    assert issues[0].category == ErrorCategory.ACCURACY
    assert issues[0].severity == ErrorSeverity.MAJOR
    assert issues[0].description == "Mistranslation"


def test_parse_ai_response_markdown_json(engine):
    """Test parsing a JSON response wrapped in markdown code block."""
    response = """Here is my analysis:

```json
{
  "issues": [
    {
      "category": "fluency",
      "severity": "minor",
      "description": "Awkward phrasing",
      "explanation": "The sentence sounds unnatural"
    }
  ],
  "overall_quality": "Good"
}
```
"""

    issues = engine._parse_ai_response(response)
    assert len(issues) == 1
    assert issues[0].category == ErrorCategory.FLUENCY
    assert issues[0].severity == ErrorSeverity.MINOR


def test_parse_ai_response_no_issues(engine):
    """Test parsing a response with no issues."""
    response = json.dumps({
        "issues": [],
        "overall_quality": "Perfect translation",
    })

    issues = engine._parse_ai_response(response)
    assert len(issues) == 0


def test_parse_ai_response_invalid_json(engine):
    """Test parsing an invalid JSON response returns empty list."""
    response = "This is not valid JSON at all"
    issues = engine._parse_ai_response(response)
    assert issues == []


def test_parse_ai_response_unknown_category(engine):
    """Test that unknown category defaults to FLUENCY."""
    response = json.dumps({
        "issues": [
            {
                "category": "unknown_category",
                "severity": "minor",
                "description": "Test",
                "explanation": "Test",
            }
        ]
    })

    issues = engine._parse_ai_response(response)
    assert len(issues) == 1
    assert issues[0].category == ErrorCategory.FLUENCY


def test_parse_ai_response_unknown_severity(engine):
    """Test that unknown severity defaults to MINOR."""
    response = json.dumps({
        "issues": [
            {
                "category": "accuracy",
                "severity": "unknown_severity",
                "description": "Test",
                "explanation": "Test",
            }
        ]
    })

    issues = engine._parse_ai_response(response)
    assert len(issues) == 1
    assert issues[0].severity == ErrorSeverity.MINOR


def test_calculate_quality_score_critical_issue(engine):
    """Test that critical issues significantly reduce score."""
    issues = [
        QualityIssue(
            category=ErrorCategory.ACCURACY,
            severity=ErrorSeverity.CRITICAL,
            description="Critical error",
            explanation="Very bad",
        )
    ]
    score = engine._calculate_quality_score(issues)
    assert score == 75.0  # 100 - 25


def test_calculate_quality_score_multiple_criticals(engine):
    """Test score floor at 0 with multiple critical issues."""
    issues = [
        QualityIssue(
            category=ErrorCategory.ACCURACY,
            severity=ErrorSeverity.CRITICAL,
            description=f"Critical error {i}",
            explanation="Very bad",
        )
        for i in range(10)  # 10 * 25 = 250 deduction
    ]
    score = engine._calculate_quality_score(issues)
    assert score == 0.0  # Should not go below 0


def test_calculate_quality_score_neutral_issue(engine):
    """Test that neutral issues don't affect score."""
    issues = [
        QualityIssue(
            category=ErrorCategory.STYLE,
            severity=ErrorSeverity.NEUTRAL,
            description="Style preference",
            explanation="Minor style note",
        )
    ]
    score = engine._calculate_quality_score(issues)
    assert score == 100.0  # No deduction for neutral


def test_generate_assessment_poor_quality(engine):
    """Test assessment for poor quality score."""
    assessment = engine._generate_assessment(55.0, [])
    assert "Poor" in assessment or "significant" in assessment.lower()


def test_generate_assessment_unacceptable(engine):
    """Test assessment for unacceptable quality score."""
    assessment = engine._generate_assessment(30.0, [])
    assert "Unacceptable" in assessment or "revision" in assessment.lower()


def test_generate_assessment_acceptable(engine):
    """Test assessment for acceptable quality score."""
    assessment = engine._generate_assessment(75.0, [])
    assert "Acceptable" in assessment or "attention" in assessment.lower()


def test_generate_assessment_counts_severities(engine):
    """Test that assessment correctly counts issue severities."""
    issues = [
        QualityIssue(
            category=ErrorCategory.ACCURACY,
            severity=ErrorSeverity.CRITICAL,
            description="Critical issue",
            explanation="Test",
        ),
        QualityIssue(
            category=ErrorCategory.FLUENCY,
            severity=ErrorSeverity.MAJOR,
            description="Major issue",
            explanation="Test",
        ),
        QualityIssue(
            category=ErrorCategory.STYLE,
            severity=ErrorSeverity.MINOR,
            description="Minor issue",
            explanation="Test",
        ),
    ]
    assessment = engine._generate_assessment(62.0, issues)
    assert "1 critical" in assessment
    assert "1 major" in assessment
    assert "1 minor" in assessment


def test_build_prompt_includes_terminology(engine):
    """Test that prompt includes provided terminology."""
    terminology = [
        TermEntry(
            source_term="software",
            target_term="logiciel",
            source_lang="en",
            target_lang="fr",
        ),
        TermEntry(
            source_term="hardware",
            target_term="matériel",
            source_lang="en",
            target_lang="fr",
            forbidden=False,
        ),
    ]

    prompt = engine._build_quality_check_prompt(
        source_text="The software runs on the hardware.",
        target_text="Le logiciel tourne sur le matériel.",
        source_lang="en",
        target_lang="fr",
        terminology=terminology,
        context=None,
    )

    assert "software" in prompt
    assert "logiciel" in prompt
    assert "hardware" in prompt
    assert "matériel" in prompt


def test_build_prompt_forbidden_term(engine):
    """Test that forbidden terms are marked in the prompt."""
    terminology = [
        TermEntry(
            source_term="car",
            target_term="auto",
            source_lang="en",
            target_lang="fr",
            forbidden=True,
        )
    ]

    prompt = engine._build_quality_check_prompt(
        source_text="I drive a car.",
        target_text="Je conduis une auto.",
        source_lang="en",
        target_lang="fr",
        terminology=terminology,
        context=None,
    )

    assert "FORBIDDEN" in prompt


def test_build_prompt_limits_terminology(engine):
    """Test that prompt limits terminology to 20 entries."""
    terminology = [
        TermEntry(
            source_term=f"term{i}",
            target_term=f"terme{i}",
            source_lang="en",
            target_lang="fr",
        )
        for i in range(30)
    ]

    prompt = engine._build_quality_check_prompt(
        source_text="Test text",
        target_text="Texte test",
        source_lang="en",
        target_lang="fr",
        terminology=terminology,
        context=None,
    )

    # Should only include first 20 terms
    assert "term19" in prompt
    assert "term20" not in prompt


def test_build_prompt_with_context(engine):
    """Test that prompt includes provided context."""
    prompt = engine._build_quality_check_prompt(
        source_text="Click here",
        target_text="Cliquez ici",
        source_lang="en",
        target_lang="fr",
        terminology=[],
        context="This is a UI button label",
    )

    assert "UI button label" in prompt


def test_check_segment_terminology_match(engine):
    """Test that terminology mismatches are detected."""
    segment = Segment(
        segment_id="seg-001",
        source_text="The car is fast.",
        target_text="La voiture est rapide.",
        source_lang="en",
        target_lang="fr",
        segment_number=1,
    )

    terminology = [
        TermEntry(
            source_term="car",
            target_term="automobile",  # Expected term not used
            source_lang="en",
            target_lang="fr",
        )
    ]

    # Mock AI response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({"issues": []}))]
    engine.client.messages.create = MagicMock(return_value=mock_response)

    result = engine.check_segment(segment, terminology)

    # Should detect that "automobile" was expected but "voiture" was used
    assert len(result.terminology_issues) > 0
    assert any("automobile" in issue for issue in result.terminology_issues)


def test_check_segments_batch(engine):
    """Test batch segment processing."""
    segments = [
        Segment(
            segment_id=f"seg-{i:03d}",
            source_text=f"Source text {i}",
            target_text=f"Target text {i}",
            source_lang="en",
            target_lang="fr",
            segment_number=i,
        )
        for i in range(3)
    ]

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({"issues": []}))]
    engine.client.messages.create = MagicMock(return_value=mock_response)

    results = engine.check_segments_batch(segments, [])

    assert len(results) == 3
    for result in results:
        assert result.quality_score == 100.0


def test_check_segment_api_error_returns_result(engine):
    """Test that API errors return a result with requires_review=True."""
    segment = Segment(
        segment_id="seg-001",
        source_text="Hello",
        target_text="Bonjour",
        source_lang="en",
        target_lang="fr",
        segment_number=1,
    )

    engine.client.messages.create = MagicMock(side_effect=Exception("API Error"))

    result = engine.check_segment(segment, [])

    assert result.segment_id == "seg-001"
    assert result.requires_review is True
    assert result.quality_score == 0.0
    assert "Error" in result.overall_assessment
