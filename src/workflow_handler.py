"""
Workflow Handler

Manages integration with MemoQ workflow stages and handles quality-based decisions.
"""

from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from src.models import (
    Segment,
    SegmentQualityResult,
    DocumentQualityResult,
    ProjectQualityResult,
    WorkflowAction,
    WorkflowDecision,
    QualityThresholds,
    ErrorCategory,
    ErrorSeverity,
)
from src.memoq_client import MemoQClient
from src.aiqe_engine import AIQEEngine
from src.termbase_manager import TermBaseManager


class WorkflowHandler:
    """
    Handles workflow integration and quality-based decision making.
    """

    def __init__(
        self,
        memoq_client: MemoQClient,
        aiqe_engine: AIQEEngine,
        termbase_manager: TermBaseManager,
        thresholds: QualityThresholds,
        notify_project_manager: bool = True,
        notify_translator: bool = True,
    ):
        """
        Initialize Workflow Handler.

        Args:
            memoq_client: MemoQ API client
            aiqe_engine: AIQE engine for quality checks
            termbase_manager: Term base manager
            thresholds: Quality score thresholds
            notify_project_manager: Send notifications to PM
            notify_translator: Send notifications to translator
        """
        self.client = memoq_client
        self.engine = aiqe_engine
        self.termbase = termbase_manager
        self.thresholds = thresholds
        self.notify_pm = notify_project_manager
        self.notify_translator = notify_translator

        logger.info("Initialized Workflow Handler")

    def process_document(
        self,
        project_guid: str,
        document_guid: str,
        workflow_stage: str = "pre_proofreading",
    ) -> DocumentQualityResult:
        """
        Process a document for quality checking.

        Args:
            project_guid: Project GUID
            document_guid: Document GUID
            workflow_stage: Workflow stage to check

        Returns:
            DocumentQualityResult with complete quality assessment
        """
        start_time = datetime.utcnow()

        logger.info(f"Processing document {document_guid} in project {project_guid}")

        # Get project info
        project = self.client.get_project(project_guid)
        if not project:
            raise ValueError(f"Project {project_guid} not found")

        # Get document info
        documents = self.client.get_documents(project_guid)
        document = next((d for d in documents if d.document_guid == document_guid), None)

        if not document:
            raise ValueError(f"Document {document_guid} not found")

        # Get segments
        segments = self.client.get_segments(project_guid, document_guid, workflow_stage)

        if not segments:
            logger.warning(f"No segments found in document {document_guid}")
            return self._create_empty_document_result(document)

        # Get terminology
        terminology = self.termbase.get_project_terms(
            project_guid,
            document.source_lang,
            document.target_lang,
        )

        logger.info(f"Checking {len(segments)} segments with {len(terminology)} terms")

        # Check all segments
        segment_results = self.engine.check_segments_batch(segments, terminology)

        # Calculate document-level statistics
        overall_score = sum(r.quality_score for r in segment_results) / len(segment_results)
        segments_with_issues = sum(1 for r in segment_results if r.issues)

        # Count errors by category and severity
        error_breakdown: Dict[ErrorCategory, int] = {}
        severity_breakdown: Dict[ErrorSeverity, int] = {}

        for result in segment_results:
            for issue in result.issues:
                error_breakdown[issue.category] = error_breakdown.get(issue.category, 0) + 1
                severity_breakdown[issue.severity] = severity_breakdown.get(issue.severity, 0) + 1

        # Generate recommendation
        recommendation = self._generate_recommendation(overall_score, segment_results)

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        doc_result = DocumentQualityResult(
            document_guid=document_guid,
            document_name=document.name,
            overall_score=overall_score,
            segment_results=segment_results,
            total_segments=len(segments),
            segments_with_issues=segments_with_issues,
            error_breakdown=error_breakdown,
            severity_breakdown=severity_breakdown,
            recommendation=recommendation,
            processing_time=processing_time,
        )

        # Take workflow action
        self._execute_workflow_action(project_guid, document_guid, doc_result)

        logger.info(
            f"Document {document_guid} processed: score={overall_score:.2f}, "
            f"issues={segments_with_issues}/{len(segments)} segments"
        )

        return doc_result

    def process_project(
        self,
        project_guid: str,
        workflow_stage: str = "pre_proofreading",
    ) -> ProjectQualityResult:
        """
        Process all documents in a project.

        Args:
            project_guid: Project GUID
            workflow_stage: Workflow stage to check

        Returns:
            ProjectQualityResult with complete project assessment
        """
        start_time = datetime.utcnow()

        logger.info(f"Processing project {project_guid}")

        # Get project info
        project = self.client.get_project(project_guid)
        if not project:
            raise ValueError(f"Project {project_guid} not found")

        # Get all documents
        documents = self.client.get_documents(project_guid)

        if not documents:
            logger.warning(f"No documents found in project {project_guid}")
            raise ValueError(f"No documents in project {project_guid}")

        # Process each document
        document_results = []
        for doc in documents:
            try:
                doc_result = self.process_document(
                    project_guid, doc.document_guid, workflow_stage
                )
                document_results.append(doc_result)
            except Exception as e:
                logger.error(f"Failed to process document {doc.document_guid}: {e}")
                continue

        # Calculate project-level statistics
        overall_score = (
            sum(d.overall_score for d in document_results) / len(document_results)
            if document_results
            else 0.0
        )

        total_segments = sum(d.total_segments for d in document_results)
        segments_with_issues = sum(d.segments_with_issues for d in document_results)

        # Aggregate error breakdowns
        error_breakdown: Dict[ErrorCategory, int] = {}
        severity_breakdown: Dict[ErrorSeverity, int] = {}

        for doc_result in document_results:
            for category, count in doc_result.error_breakdown.items():
                error_breakdown[category] = error_breakdown.get(category, 0) + count

            for severity, count in doc_result.severity_breakdown.items():
                severity_breakdown[severity] = severity_breakdown.get(severity, 0) + count

        recommendation = self._generate_project_recommendation(
            overall_score, document_results
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        project_result = ProjectQualityResult(
            project_guid=project_guid,
            project_name=project.name,
            overall_score=overall_score,
            document_results=document_results,
            total_documents=len(documents),
            total_segments=total_segments,
            segments_with_issues=segments_with_issues,
            error_breakdown=error_breakdown,
            severity_breakdown=severity_breakdown,
            recommendation=recommendation,
            processing_time=processing_time,
        )

        logger.info(
            f"Project {project_guid} processed: {len(document_results)} documents, "
            f"score={overall_score:.2f}"
        )

        return project_result

    def _create_empty_document_result(self, document) -> DocumentQualityResult:
        """Create an empty result for documents with no segments."""
        return DocumentQualityResult(
            document_guid=document.document_guid,
            document_name=document.name,
            overall_score=100.0,
            segment_results=[],
            total_segments=0,
            segments_with_issues=0,
            error_breakdown={},
            severity_breakdown={},
            recommendation="No segments to check",
            processing_time=0.0,
        )

    def _generate_recommendation(
        self,
        overall_score: float,
        segment_results: List[SegmentQualityResult],
    ) -> str:
        """Generate recommendation based on document quality."""

        if overall_score >= self.thresholds.auto_approve_threshold:
            return "APPROVED: Excellent quality. Ready for proofreading."

        elif overall_score >= self.thresholds.flag_for_review_threshold:
            critical_count = sum(
                1
                for r in segment_results
                for i in r.issues
                if i.severity == ErrorSeverity.CRITICAL
            )

            if critical_count > 0:
                return (
                    f"REVIEW REQUIRED: {critical_count} critical issue(s) found. "
                    "Please address before proceeding."
                )
            else:
                return (
                    "FLAGGED FOR REVIEW: Good quality but some issues detected. "
                    "Review recommended before proofreading."
                )

        else:
            return (
                "BLOCKED: Quality below acceptable threshold. "
                "Revision required before proofreading."
            )

    def _generate_project_recommendation(
        self,
        overall_score: float,
        document_results: List[DocumentQualityResult],
    ) -> str:
        """Generate recommendation for entire project."""

        docs_blocked = sum(
            1
            for d in document_results
            if d.overall_score < self.thresholds.block_threshold
        )

        docs_flagged = sum(
            1
            for d in document_results
            if self.thresholds.block_threshold
            <= d.overall_score
            < self.thresholds.flag_for_review_threshold
        )

        if docs_blocked > 0:
            return (
                f"PROJECT BLOCKED: {docs_blocked} document(s) require revision. "
                f"Overall project score: {overall_score:.1f}"
            )
        elif docs_flagged > 0:
            return (
                f"PROJECT REVIEW: {docs_flagged} document(s) flagged for review. "
                f"Overall project score: {overall_score:.1f}"
            )
        else:
            return (
                f"PROJECT APPROVED: All documents meet quality standards. "
                f"Overall project score: {overall_score:.1f}"
            )

    def _execute_workflow_action(
        self,
        project_guid: str,
        document_guid: str,
        doc_result: DocumentQualityResult,
    ):
        """Execute workflow actions based on quality results."""

        decision = self._make_workflow_decision(doc_result)

        logger.info(
            f"Workflow decision for {document_guid}: {decision.action.value} "
            f"(score: {decision.quality_score:.2f})"
        )

        # Add comments to segments with issues
        for seg_result in doc_result.segment_results:
            if seg_result.issues:
                comment = self._format_segment_comment(seg_result)

                self.client.add_segment_comment(
                    project_guid,
                    document_guid,
                    seg_result.segment_id,
                    comment,
                )

                # Update segment status if needed
                if decision.action == WorkflowAction.BLOCK:
                    self.client.update_segment_status(
                        project_guid,
                        document_guid,
                        seg_result.segment_id,
                        "needs_revision",
                        "AIQE: Quality below threshold",
                    )

    def _make_workflow_decision(
        self, doc_result: DocumentQualityResult
    ) -> WorkflowDecision:
        """Make workflow decision based on quality score."""

        score = doc_result.overall_score

        if score >= self.thresholds.auto_approve_threshold:
            return WorkflowDecision(
                action=WorkflowAction.APPROVE,
                reason="Quality score exceeds auto-approve threshold",
                quality_score=score,
                requires_notification=False,
            )

        elif score >= self.thresholds.flag_for_review_threshold:
            return WorkflowDecision(
                action=WorkflowAction.FLAG_FOR_REVIEW,
                reason="Quality score requires review",
                quality_score=score,
                requires_notification=self.notify_pm,
                notification_message=f"Document {doc_result.document_name} flagged: score {score:.1f}",
            )

        else:
            return WorkflowDecision(
                action=WorkflowAction.BLOCK,
                reason="Quality score below acceptable threshold",
                quality_score=score,
                requires_notification=True,
                notification_message=f"Document {doc_result.document_name} blocked: score {score:.1f}",
            )

    def _format_segment_comment(self, seg_result: SegmentQualityResult) -> str:
        """Format quality issues as a segment comment."""

        lines = [
            f"AIQE Quality Check - Score: {seg_result.quality_score:.1f}/100",
            "",
        ]

        if seg_result.issues:
            lines.append("Issues Found:")
            for idx, issue in enumerate(seg_result.issues, 1):
                lines.append(
                    f"{idx}. [{issue.severity.value.upper()}] {issue.category.value}: "
                    f"{issue.description}"
                )
                if issue.suggestion:
                    lines.append(f"   Suggestion: {issue.suggestion}")

        if seg_result.terminology_issues:
            lines.append("")
            lines.append("Terminology Issues:")
            for issue in seg_result.terminology_issues:
                lines.append(f"- {issue}")

        return "\n".join(lines)
