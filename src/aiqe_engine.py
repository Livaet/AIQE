"""
AIQE Engine

AI-powered Quality Estimation engine using Claude or GPT for translation quality assessment.
"""

import json
import time
from typing import List, Dict, Optional, Any
from loguru import logger

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

from src.models import (
    Segment,
    TermEntry,
    QualityIssue,
    SegmentQualityResult,
    ErrorCategory,
    ErrorSeverity,
    AIProviderConfig,
    MQMConfig,
)


class AIQEEngine:
    """
    AI-powered Quality Estimation engine.

    Uses LLMs (Claude or GPT) to analyze translation quality following the MQM framework.
    """

    def __init__(
        self,
        ai_config: AIProviderConfig,
        mqm_config: MQMConfig,
    ):
        """
        Initialize AIQE Engine.

        Args:
            ai_config: AI provider configuration
            mqm_config: MQM framework configuration
        """
        self.ai_config = ai_config
        self.mqm_config = mqm_config

        # Initialize AI client
        if ai_config.provider == "anthropic":
            if anthropic is None:
                raise ImportError("anthropic package is required for Anthropic provider")
            self.client = anthropic.Anthropic(api_key=ai_config.api_key)
        elif ai_config.provider == "openai":
            if openai is None:
                raise ImportError("openai package is required for OpenAI provider")
            self.client = openai.OpenAI(api_key=ai_config.api_key)
        else:
            raise ValueError(f"Unsupported AI provider: {ai_config.provider}")

        logger.info(
            f"Initialized AIQE Engine with {ai_config.provider} ({ai_config.model})"
        )

    def check_segment(
        self,
        segment: Segment,
        terminology: List[TermEntry],
        context: Optional[str] = None,
    ) -> SegmentQualityResult:
        """
        Check quality of a single segment.

        Args:
            segment: Segment to check
            terminology: Relevant term entries
            context: Optional additional context

        Returns:
            SegmentQualityResult with quality assessment
        """
        start_time = time.time()

        try:
            # Build the prompt
            prompt = self._build_quality_check_prompt(
                segment.source_text,
                segment.target_text,
                segment.source_lang,
                segment.target_lang,
                terminology,
                context,
            )

            # Call AI provider
            response = self._call_ai_provider(prompt)

            # Parse response
            issues = self._parse_ai_response(response)

            # Calculate quality score
            quality_score = self._calculate_quality_score(issues)

            # Determine if review is required
            requires_review = quality_score < self.mqm_config.base_score * 0.9

            processing_time = time.time() - start_time

            # Check terminology consistency
            terminology_issues = []
            for term in terminology:
                if term.source_term.lower() in segment.source_text.lower():
                    if term.target_term.lower() not in segment.target_text.lower():
                        terminology_issues.append(
                            f"Expected term '{term.target_term}' for '{term.source_term}'"
                        )

            result = SegmentQualityResult(
                segment_id=segment.segment_id,
                segment_number=segment.segment_number,
                quality_score=quality_score,
                issues=issues,
                terminology_matches=terminology,
                terminology_issues=terminology_issues,
                overall_assessment=self._generate_assessment(quality_score, issues),
                requires_review=requires_review,
                processing_time=processing_time,
            )

            logger.debug(
                f"Segment {segment.segment_id}: score={quality_score:.2f}, "
                f"issues={len(issues)}, time={processing_time:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to check segment {segment.segment_id}: {e}")

            # Return a result with error indication
            return SegmentQualityResult(
                segment_id=segment.segment_id,
                segment_number=segment.segment_number,
                quality_score=0.0,
                issues=[],
                terminology_matches=[],
                terminology_issues=[],
                overall_assessment=f"Error during quality check: {str(e)}",
                requires_review=True,
                processing_time=time.time() - start_time,
            )

    def _build_quality_check_prompt(
        self,
        source_text: str,
        target_text: str,
        source_lang: str,
        target_lang: str,
        terminology: List[TermEntry],
        context: Optional[str] = None,
    ) -> str:
        """Build the prompt for AI quality assessment."""

        # Format terminology
        term_list = []
        for term in terminology[:20]:  # Limit to top 20 most relevant
            term_list.append(
                f"- '{term.source_term}' → '{term.target_term}'"
                + (f" (FORBIDDEN)" if term.forbidden else "")
            )

        terms_str = "\n".join(term_list) if term_list else "None provided"

        # Build enabled categories list
        enabled_categories = [cat.value for cat in self.mqm_config.enabled_categories]

        prompt = f"""You are a professional translation quality assessor. Analyze the following translation using the MQM (Multidimensional Quality Metrics) framework.

**Source Text ({source_lang}):**
{source_text}

**Target Text ({target_lang}):**
{target_text}

**Approved Terminology:**
{terms_str}

**Context:**
{context if context else "No additional context provided"}

**Task:**
Evaluate the translation quality by identifying issues in these MQM categories:
{', '.join(enabled_categories)}

**For each issue found, provide:**
1. Category: {', '.join(enabled_categories)}
2. Severity: critical, major, minor, or neutral
3. Description: Brief explanation of the issue
4. Source excerpt: Relevant part of source text (if applicable)
5. Target excerpt: Relevant part of target text where issue occurs
6. Suggestion: How to fix the issue
7. Explanation: Detailed reasoning

**Severity Guidelines:**
- Critical: Makes content dangerous, misleading, or completely unusable
- Major: Significantly impacts meaning or readability
- Minor: Slight quality reduction but still understandable
- Neutral: Style preference without quality impact

**Output Format (JSON):**
```json
{{
  "issues": [
    {{
      "category": "accuracy",
      "severity": "major",
      "description": "Brief issue description",
      "source_excerpt": "relevant source text",
      "target_excerpt": "relevant target text",
      "suggestion": "how to fix",
      "explanation": "detailed reasoning"
    }}
  ],
  "overall_quality": "Brief overall assessment"
}}
```

If the translation is perfect, return an empty issues array. Be thorough but fair in your assessment."""

        return prompt

    def _call_ai_provider(self, prompt: str) -> str:
        """Call the AI provider API."""

        if self.ai_config.provider == "anthropic":
            response = self.client.messages.create(
                model=self.ai_config.model,
                max_tokens=self.ai_config.max_tokens,
                temperature=self.ai_config.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            return response.content[0].text

        elif self.ai_config.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.ai_config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translation quality assessor using the MQM framework.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                max_tokens=self.ai_config.max_tokens,
                temperature=self.ai_config.temperature,
            )

            return response.choices[0].message.content

        else:
            raise ValueError(f"Unsupported provider: {self.ai_config.provider}")

    def _parse_ai_response(self, response: str) -> List[QualityIssue]:
        """Parse AI response into QualityIssue objects."""

        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)

            issues = []
            for issue_data in data.get("issues", []):
                try:
                    # Map string values to enums
                    category_str = issue_data.get("category", "fluency")
                    severity_str = issue_data.get("severity", "minor")

                    # Find matching enum value (case-insensitive)
                    category = None
                    for cat in ErrorCategory:
                        if cat.value.lower() == category_str.lower():
                            category = cat
                            break
                    if not category:
                        category = ErrorCategory.FLUENCY

                    severity = None
                    for sev in ErrorSeverity:
                        if sev.value.lower() == severity_str.lower():
                            severity = sev
                            break
                    if not severity:
                        severity = ErrorSeverity.MINOR

                    issue = QualityIssue(
                        category=category,
                        severity=severity,
                        description=issue_data.get("description", ""),
                        source_excerpt=issue_data.get("source_excerpt"),
                        target_excerpt=issue_data.get("target_excerpt"),
                        suggestion=issue_data.get("suggestion"),
                        explanation=issue_data.get("explanation", ""),
                    )
                    issues.append(issue)

                except Exception as e:
                    logger.warning(f"Failed to parse issue: {e}")
                    continue

            return issues

        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"Response was: {response}")
            return []

    def _calculate_quality_score(self, issues: List[QualityIssue]) -> float:
        """
        Calculate quality score based on issues found.

        Uses MQM severity weights to deduct from base score.
        """
        score = float(self.mqm_config.base_score)

        for issue in issues:
            weight = self.mqm_config.severity_weights.get(issue.severity, 0)
            score += weight  # Weights are negative, so this subtracts

        # Ensure score is within bounds
        score = max(0.0, min(100.0, score))

        return score

    def _generate_assessment(
        self, quality_score: float, issues: List[QualityIssue]
    ) -> str:
        """Generate overall quality assessment text."""

        if quality_score >= 95:
            assessment = "Excellent quality translation."
        elif quality_score >= 85:
            assessment = "Good quality translation with minor issues."
        elif quality_score >= 70:
            assessment = "Acceptable quality but requires attention."
        elif quality_score >= 50:
            assessment = "Poor quality with significant issues."
        else:
            assessment = "Unacceptable quality requiring revision."

        if issues:
            critical_count = sum(1 for i in issues if i.severity == ErrorSeverity.CRITICAL)
            major_count = sum(1 for i in issues if i.severity == ErrorSeverity.MAJOR)
            minor_count = sum(1 for i in issues if i.severity == ErrorSeverity.MINOR)

            counts = []
            if critical_count:
                counts.append(f"{critical_count} critical")
            if major_count:
                counts.append(f"{major_count} major")
            if minor_count:
                counts.append(f"{minor_count} minor")

            if counts:
                assessment += f" Found {', '.join(counts)} issue(s)."

        return assessment

    def check_segments_batch(
        self,
        segments: List[Segment],
        terminology: List[TermEntry],
        batch_size: int = 10,
    ) -> List[SegmentQualityResult]:
        """
        Check quality of multiple segments.

        Args:
            segments: List of segments to check
            terminology: Relevant term entries
            batch_size: Number of segments to process at once (currently sequential)

        Returns:
            List of SegmentQualityResult objects
        """
        results = []

        for idx, segment in enumerate(segments):
            logger.info(f"Checking segment {idx + 1}/{len(segments)}")

            result = self.check_segment(segment, terminology)
            results.append(result)

            # Rate limiting (simple implementation)
            if (idx + 1) % batch_size == 0:
                time.sleep(1)  # Brief pause between batches

        return results
