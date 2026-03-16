"""
Tests for data models
"""

import pytest
from datetime import datetime
from src.models import (
    ErrorSeverity,
    ErrorCategory,
    WorkflowStage,
    WorkflowAction,
    TermEntry,
    Segment,
    QualityIssue,
    SegmentQualityResult,
    DocumentQualityResult,
    ProjectQualityResult,
    MemoQProject,
    MemoQDocument,
    WorkflowDecision,
    AIProviderConfig,
    MQMConfig,
    QualityThresholds,
)


def test_error_severity_values():
    assert ErrorSeverity.CRITICAL == "critical"
    assert ErrorSeverity.MAJOR == "major"
    assert ErrorSeverity.MINOR == "minor"
    assert ErrorSeverity.NEUTRAL == "neutral"


def test_error_category_values():
    assert ErrorCategory.ACCURACY == "accuracy"
    assert ErrorCategory.FLUENCY == "fluency"
    assert ErrorCategory.TERMINOLOGY == "terminology"
    assert ErrorCategory.STYLE == "style"
    assert ErrorCategory.LOCALE_CONVENTION == "locale_convention"
    assert ErrorCategory.VERITY == "verity"


def test_term_entry_creation():
    entry = TermEntry(
        source_term="car",
        target_term="voiture",
        source_lang="en",
        target_lang="fr",
        definition="A road vehicle",
        forbidden=False,
    )
    assert entry.source_term == "car"
    assert entry.target_term == "voiture"
    assert not entry.forbidden


def test_term_entry_forbidden():
    entry = TermEntry(
        source_term="car",
        target_term="auto",
        source_lang="en",
        target_lang="fr",
        forbidden=True,
    )
    assert entry.forbidden


def test_segment_creation():
    seg = Segment(
        segment_id="seg-001",
        source_text="Hello",
        target_text="Bonjour",
        source_lang="en",
        target_lang="fr",
        segment_number=1,
    )
    assert seg.segment_id == "seg-001"
    assert seg.source_text == "Hello"
    assert seg.target_text == "Bonjour"
    assert seg.segment_number == 1


def test_quality_issue_creation():
    issue = QualityIssue(
        category=ErrorCategory.ACCURACY,
        severity=ErrorSeverity.MAJOR,
        description="Mistranslation",
        explanation="The word was incorrectly translated",
        suggestion="Use the correct translation",
        source_excerpt="Hello",
        target_excerpt="Hola",
    )
    assert issue.category == ErrorCategory.ACCURACY
    assert issue.severity == ErrorSeverity.MAJOR
    assert issue.suggestion == "Use the correct translation"


def test_segment_quality_result():
    result = SegmentQualityResult(
        segment_id="seg-001",
        segment_number=1,
        quality_score=87.0,
        issues=[],
        terminology_matches=[],
        terminology_issues=[],
        overall_assessment="Good quality",
        requires_review=False,
        processing_time=1.5,
    )
    assert result.quality_score == 87.0
    assert not result.requires_review


def test_segment_quality_result_score_bounds():
    with pytest.raises(Exception):
        SegmentQualityResult(
            segment_id="seg-001",
            segment_number=1,
            quality_score=101.0,  # Invalid: above 100
            issues=[],
            terminology_matches=[],
            terminology_issues=[],
            overall_assessment="Test",
            requires_review=False,
            processing_time=0.0,
        )

    with pytest.raises(Exception):
        SegmentQualityResult(
            segment_id="seg-001",
            segment_number=1,
            quality_score=-1.0,  # Invalid: below 0
            issues=[],
            terminology_matches=[],
            terminology_issues=[],
            overall_assessment="Test",
            requires_review=False,
            processing_time=0.0,
        )


def test_ai_provider_config_defaults():
    config = AIProviderConfig(
        provider="anthropic",
        api_key="test-key",
        model="claude-3-5-sonnet-20241022",
    )
    assert config.max_tokens == 4096
    assert config.temperature == 0.1


def test_mqm_config():
    config = MQMConfig(
        enabled_categories=[ErrorCategory.ACCURACY, ErrorCategory.FLUENCY],
        severity_weights={
            ErrorSeverity.CRITICAL: -25,
            ErrorSeverity.MAJOR: -10,
            ErrorSeverity.MINOR: -3,
            ErrorSeverity.NEUTRAL: 0,
        },
        base_score=100,
    )
    assert len(config.enabled_categories) == 2
    assert config.severity_weights[ErrorSeverity.CRITICAL] == -25


def test_quality_thresholds_defaults():
    thresholds = QualityThresholds()
    assert thresholds.auto_approve_threshold == 95.0
    assert thresholds.flag_for_review_threshold == 70.0
    assert thresholds.block_threshold == 50.0


def test_workflow_decision_creation():
    decision = WorkflowDecision(
        action=WorkflowAction.APPROVE,
        reason="Quality exceeds threshold",
        quality_score=96.0,
        requires_notification=False,
    )
    assert decision.action == WorkflowAction.APPROVE
    assert decision.quality_score == 96.0
    assert not decision.requires_notification


def test_memoq_project_creation():
    project = MemoQProject(
        project_guid="abc-123",
        name="Test Project",
        source_lang="en",
        target_langs=["fr", "de"],
    )
    assert project.project_guid == "abc-123"
    assert len(project.target_langs) == 2


def test_memoq_document_creation():
    doc = MemoQDocument(
        document_guid="doc-456",
        name="test.docx",
        project_guid="abc-123",
        source_lang="en",
        target_lang="fr",
        segment_count=50,
    )
    assert doc.segment_count == 50
