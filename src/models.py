"""
Data models for MemoQ AIQE Connector
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ErrorSeverity(str, Enum):
    """MQM Error severity levels"""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    NEUTRAL = "neutral"


class ErrorCategory(str, Enum):
    """MQM Error categories"""
    ACCURACY = "accuracy"
    FLUENCY = "fluency"
    TERMINOLOGY = "terminology"
    STYLE = "style"
    LOCALE_CONVENTION = "locale_convention"
    VERITY = "verity"
    DESIGN = "design"


class WorkflowStage(str, Enum):
    """MemoQ workflow stages"""
    TRANSLATION = "translation"
    EDITING = "editing"
    PROOFREADING = "proofreading"
    REVIEW = "review"
    FINALIZED = "finalized"


class TermEntry(BaseModel):
    """Term base entry"""
    source_term: str
    target_term: str
    source_lang: str
    target_lang: str
    definition: Optional[str] = None
    context: Optional[str] = None
    domain: Optional[str] = None
    forbidden: bool = False


class Segment(BaseModel):
    """Translation segment"""
    segment_id: str
    source_text: str
    target_text: str
    source_lang: str
    target_lang: str
    segment_number: int
    status: Optional[str] = None
    translator: Optional[str] = None
    timestamp: Optional[datetime] = None
    context: Optional[str] = None


class QualityIssue(BaseModel):
    """Detected quality issue"""
    category: ErrorCategory
    severity: ErrorSeverity
    description: str
    source_excerpt: Optional[str] = None
    target_excerpt: Optional[str] = None
    suggestion: Optional[str] = None
    position: Optional[int] = None
    explanation: str


class SegmentQualityResult(BaseModel):
    """Quality assessment result for a single segment"""
    segment_id: str
    segment_number: int
    quality_score: float = Field(ge=0, le=100)
    issues: List[QualityIssue] = Field(default_factory=list)
    terminology_matches: List[TermEntry] = Field(default_factory=list)
    terminology_issues: List[str] = Field(default_factory=list)
    overall_assessment: str
    requires_review: bool
    processing_time: float


class DocumentQualityResult(BaseModel):
    """Quality assessment result for entire document"""
    document_guid: str
    document_name: str
    overall_score: float = Field(ge=0, le=100)
    segment_results: List[SegmentQualityResult]
    total_segments: int
    segments_with_issues: int
    error_breakdown: Dict[ErrorCategory, int]
    severity_breakdown: Dict[ErrorSeverity, int]
    recommendation: str
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProjectQualityResult(BaseModel):
    """Quality assessment result for entire project"""
    project_guid: str
    project_name: str
    overall_score: float = Field(ge=0, le=100)
    document_results: List[DocumentQualityResult]
    total_documents: int
    total_segments: int
    segments_with_issues: int
    error_breakdown: Dict[ErrorCategory, int]
    severity_breakdown: Dict[ErrorSeverity, int]
    recommendation: str
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MemoQProject(BaseModel):
    """MemoQ project information"""
    project_guid: str
    name: str
    source_lang: str
    target_langs: List[str]
    workflow_stage: Optional[WorkflowStage] = None
    created_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    project_manager: Optional[str] = None


class MemoQDocument(BaseModel):
    """MemoQ document information"""
    document_guid: str
    name: str
    project_guid: str
    source_lang: str
    target_lang: str
    segment_count: int
    status: Optional[str] = None


class WorkflowAction(str, Enum):
    """Actions to take based on quality assessment"""
    APPROVE = "approve"
    FLAG_FOR_REVIEW = "flag_for_review"
    BLOCK = "block"
    NOTIFY = "notify"


class WorkflowDecision(BaseModel):
    """Workflow decision based on quality assessment"""
    action: WorkflowAction
    reason: str
    quality_score: float
    requires_notification: bool
    notification_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AIProviderConfig(BaseModel):
    """AI provider configuration"""
    provider: str  # "anthropic" or "openai"
    api_key: str
    model: str
    max_tokens: int = 4096
    temperature: float = 0.1


class MQMConfig(BaseModel):
    """MQM framework configuration"""
    enabled_categories: List[ErrorCategory]
    severity_weights: Dict[ErrorSeverity, int]
    base_score: int = 100


class QualityThresholds(BaseModel):
    """Quality score thresholds"""
    auto_approve_threshold: float = 95.0
    flag_for_review_threshold: float = 70.0
    block_threshold: float = 50.0
