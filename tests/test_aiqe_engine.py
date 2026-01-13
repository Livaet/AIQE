"""
Tests for AIQE Engine
"""

import pytest
from src.aiqe_engine import AIQEEngine
from src.models import (
    Segment,
    TermEntry,
    AIProviderConfig,
    MQMConfig,
    ErrorCategory,
    ErrorSeverity,
)


@pytest.fixture
def mock_ai_config():
    """Mock AI configuration for testing."""
    return AIProviderConfig(
        provider="anthropic",
        api_key="test-key",
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        temperature=0.1,
    )


@pytest.fixture
def mock_mqm_config():
    """Mock MQM configuration for testing."""
    return MQMConfig(
        enabled_categories=[
            ErrorCategory.ACCURACY,
            ErrorCategory.FLUENCY,
            ErrorCategory.TERMINOLOGY,
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
def sample_segment():
    """Sample segment for testing."""
    return Segment(
        segment_id="seg-001",
        source_text="Hello world",
        target_text="Hola mundo",
        source_lang="en",
        target_lang="es",
        segment_number=1,
    )


@pytest.fixture
def sample_terminology():
    """Sample terminology for testing."""
    return [
        TermEntry(
            source_term="world",
            target_term="mundo",
            source_lang="en",
            target_lang="es",
            definition="The earth and all its inhabitants",
        )
    ]


def test_calculate_quality_score(mock_ai_config, mock_mqm_config):
    """Test quality score calculation."""
    from src.models import QualityIssue

    engine = AIQEEngine(mock_ai_config, mock_mqm_config)

    # Test with no issues
    score = engine._calculate_quality_score([])
    assert score == 100.0

    # Test with minor issue
    issues = [
        QualityIssue(
            category=ErrorCategory.FLUENCY,
            severity=ErrorSeverity.MINOR,
            description="Test issue",
            explanation="Test",
        )
    ]
    score = engine._calculate_quality_score(issues)
    assert score == 97.0  # 100 - 3

    # Test with multiple issues
    issues = [
        QualityIssue(
            category=ErrorCategory.ACCURACY,
            severity=ErrorSeverity.MAJOR,
            description="Major issue",
            explanation="Test",
        ),
        QualityIssue(
            category=ErrorCategory.FLUENCY,
            severity=ErrorSeverity.MINOR,
            description="Minor issue",
            explanation="Test",
        ),
    ]
    score = engine._calculate_quality_score(issues)
    assert score == 87.0  # 100 - 10 - 3


def test_generate_assessment(mock_ai_config, mock_mqm_config):
    """Test assessment generation."""
    from src.models import QualityIssue

    engine = AIQEEngine(mock_ai_config, mock_mqm_config)

    # Excellent quality
    assessment = engine._generate_assessment(95.0, [])
    assert "Excellent" in assessment

    # Good quality
    issues = [
        QualityIssue(
            category=ErrorCategory.FLUENCY,
            severity=ErrorSeverity.MINOR,
            description="Minor issue",
            explanation="Test",
        )
    ]
    assessment = engine._generate_assessment(87.0, issues)
    assert "Good" in assessment
    assert "1 minor" in assessment


def test_build_quality_check_prompt(
    mock_ai_config, mock_mqm_config, sample_segment, sample_terminology
):
    """Test prompt building."""
    engine = AIQEEngine(mock_ai_config, mock_mqm_config)

    prompt = engine._build_quality_check_prompt(
        source_text=sample_segment.source_text,
        target_text=sample_segment.target_text,
        source_lang=sample_segment.source_lang,
        target_lang=sample_segment.target_lang,
        terminology=sample_terminology,
        context=None,
    )

    # Check that prompt contains required elements
    assert "Hello world" in prompt
    assert "Hola mundo" in prompt
    assert "world" in prompt
    assert "mundo" in prompt
    assert "MQM" in prompt
    assert "accuracy" in prompt.lower()


# Note: Full integration tests would require actual API keys
# and should be run separately with --integration flag
