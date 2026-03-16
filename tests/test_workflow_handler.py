"""
Tests for WorkflowHandler decision making and report generation
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.workflow_handler import WorkflowHandler
from src.models import (
    DocumentQualityResult,
    SegmentQualityResult,
    QualityIssue,
    WorkflowAction,
    WorkflowDecision,
    QualityThresholds,
    ErrorCategory,
    ErrorSeverity,
)


@pytest.fixture
def thresholds():
    return QualityThresholds(
        auto_approve_threshold=95.0,
        flag_for_review_threshold=70.0,
        block_threshold=50.0,
    )


@pytest.fixture
def handler(thresholds):
    memoq_client = MagicMock()
    aiqe_engine = MagicMock()
    termbase_manager = MagicMock()

    return WorkflowHandler(
        memoq_client=memoq_client,
        aiqe_engine=aiqe_engine,
        termbase_manager=termbase_manager,
        thresholds=thresholds,
    )


def make_doc_result(score: float, issues=None) -> DocumentQualityResult:
    if issues is None:
        issues = []

    seg_result = SegmentQualityResult(
        segment_id="seg-001",
        segment_number=1,
        quality_score=score,
        issues=issues,
        terminology_matches=[],
        terminology_issues=[],
        overall_assessment="Test",
        requires_review=score < 90,
        processing_time=0.5,
    )

    return DocumentQualityResult(
        document_guid="doc-001",
        document_name="test.docx",
        overall_score=score,
        segment_results=[seg_result],
        total_segments=1,
        segments_with_issues=len(issues),
        error_breakdown={},
        severity_breakdown={},
        recommendation="",
        processing_time=1.0,
    )


def test_make_workflow_decision_approve(handler):
    """Score above auto-approve threshold -> APPROVE."""
    doc_result = make_doc_result(96.0)
    decision = handler._make_workflow_decision(doc_result)

    assert decision.action == WorkflowAction.APPROVE
    assert not decision.requires_notification


def test_make_workflow_decision_flag_for_review(handler):
    """Score between thresholds -> FLAG_FOR_REVIEW."""
    doc_result = make_doc_result(80.0)
    decision = handler._make_workflow_decision(doc_result)

    assert decision.action == WorkflowAction.FLAG_FOR_REVIEW
    assert decision.quality_score == 80.0


def test_make_workflow_decision_block(handler):
    """Score below block threshold -> BLOCK."""
    doc_result = make_doc_result(45.0)
    decision = handler._make_workflow_decision(doc_result)

    assert decision.action == WorkflowAction.BLOCK
    assert decision.requires_notification


def test_make_workflow_decision_at_approve_boundary(handler):
    """Score exactly at auto-approve threshold -> APPROVE."""
    doc_result = make_doc_result(95.0)
    decision = handler._make_workflow_decision(doc_result)

    assert decision.action == WorkflowAction.APPROVE


def test_make_workflow_decision_just_below_approve(handler):
    """Score just below auto-approve threshold -> FLAG_FOR_REVIEW."""
    doc_result = make_doc_result(94.9)
    decision = handler._make_workflow_decision(doc_result)

    assert decision.action == WorkflowAction.FLAG_FOR_REVIEW


def test_generate_recommendation_approved(handler):
    """High score -> approved recommendation."""
    seg_result = SegmentQualityResult(
        segment_id="seg-001",
        segment_number=1,
        quality_score=96.0,
        issues=[],
        terminology_matches=[],
        terminology_issues=[],
        overall_assessment="Excellent",
        requires_review=False,
        processing_time=0.5,
    )

    recommendation = handler._generate_recommendation(96.0, [seg_result])
    assert "APPROVED" in recommendation


def test_generate_recommendation_blocked(handler):
    """Low score -> blocked recommendation."""
    seg_result = SegmentQualityResult(
        segment_id="seg-001",
        segment_number=1,
        quality_score=40.0,
        issues=[],
        terminology_matches=[],
        terminology_issues=[],
        overall_assessment="Poor",
        requires_review=True,
        processing_time=0.5,
    )

    recommendation = handler._generate_recommendation(40.0, [seg_result])
    assert "BLOCKED" in recommendation


def test_generate_recommendation_review_with_critical(handler):
    """Mid score with critical issues -> review required."""
    critical_issue = QualityIssue(
        category=ErrorCategory.ACCURACY,
        severity=ErrorSeverity.CRITICAL,
        description="Critical error",
        explanation="Test",
    )

    seg_result = SegmentQualityResult(
        segment_id="seg-001",
        segment_number=1,
        quality_score=75.0,
        issues=[critical_issue],
        terminology_matches=[],
        terminology_issues=[],
        overall_assessment="Needs review",
        requires_review=True,
        processing_time=0.5,
    )

    recommendation = handler._generate_recommendation(75.0, [seg_result])
    assert "REVIEW" in recommendation
    assert "critical" in recommendation.lower()


def test_format_segment_comment_with_issues(handler):
    """Test comment formatting includes issue details."""
    issues = [
        QualityIssue(
            category=ErrorCategory.ACCURACY,
            severity=ErrorSeverity.MAJOR,
            description="Wrong translation",
            explanation="The meaning is lost",
            suggestion="Use correct term",
        )
    ]

    seg_result = SegmentQualityResult(
        segment_id="seg-001",
        segment_number=1,
        quality_score=88.0,
        issues=issues,
        terminology_matches=[],
        terminology_issues=["Expected term 'automobile' for 'car'"],
        overall_assessment="Good",
        requires_review=False,
        processing_time=0.5,
    )

    comment = handler._format_segment_comment(seg_result)

    assert "88" in comment
    assert "MAJOR" in comment
    assert "Wrong translation" in comment
    assert "Use correct term" in comment
    assert "automobile" in comment


def test_format_segment_comment_no_issues(handler):
    """Test comment formatting with no issues."""
    seg_result = SegmentQualityResult(
        segment_id="seg-001",
        segment_number=1,
        quality_score=100.0,
        issues=[],
        terminology_matches=[],
        terminology_issues=[],
        overall_assessment="Excellent",
        requires_review=False,
        processing_time=0.5,
    )

    comment = handler._format_segment_comment(seg_result)
    assert "100" in comment


def test_generate_project_recommendation_blocked(handler):
    """Project with blocked documents -> project blocked."""
    doc_results = [
        DocumentQualityResult(
            document_guid=f"doc-{i}",
            document_name=f"doc{i}.docx",
            overall_score=40.0,  # Below block threshold
            segment_results=[],
            total_segments=10,
            segments_with_issues=5,
            error_breakdown={},
            severity_breakdown={},
            recommendation="BLOCKED",
            processing_time=1.0,
        )
        for i in range(2)
    ]

    recommendation = handler._generate_project_recommendation(40.0, doc_results)
    assert "BLOCKED" in recommendation
    assert "2" in recommendation


def test_generate_project_recommendation_approved(handler):
    """Project with all high-quality docs -> project approved."""
    doc_results = [
        DocumentQualityResult(
            document_guid=f"doc-{i}",
            document_name=f"doc{i}.docx",
            overall_score=97.0,
            segment_results=[],
            total_segments=10,
            segments_with_issues=0,
            error_breakdown={},
            severity_breakdown={},
            recommendation="APPROVED",
            processing_time=1.0,
        )
        for i in range(3)
    ]

    recommendation = handler._generate_project_recommendation(97.0, doc_results)
    assert "APPROVED" in recommendation
