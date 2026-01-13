#!/usr/bin/env python3
"""
Example Usage of MemoQ AIQE Connector

This script demonstrates how to use the connector programmatically.
"""

from src.config_loader import ConfigLoader
from src.memoq_client import MemoQClient
from src.aiqe_engine import AIQEEngine
from src.termbase_manager import TermBaseManager
from src.workflow_handler import WorkflowHandler
from loguru import logger


def example_document_check():
    """Example: Check quality of a single document."""

    print("=" * 80)
    print("Example: Document Quality Check")
    print("=" * 80)

    # Load configuration
    config = ConfigLoader("config.yaml")

    # Initialize MemoQ client
    memoq_config = config.get_memoq_config()
    client = MemoQClient(
        server_url=memoq_config["server_url"],
        username=memoq_config["username"],
        password=memoq_config["password"],
    )

    # Authenticate
    if not client.authenticate():
        print("Authentication failed!")
        return

    print("✓ Authenticated with MemoQ server")

    # Initialize other components
    termbase_manager = TermBaseManager(
        memoq_client=client,
        **config.get_termbase_config(),
    )

    aiqe_engine = AIQEEngine(
        ai_config=config.get_ai_provider_config(),
        mqm_config=config.get_mqm_config(),
    )

    workflow_handler = WorkflowHandler(
        memoq_client=client,
        aiqe_engine=aiqe_engine,
        termbase_manager=termbase_manager,
        thresholds=config.get_quality_thresholds(),
    )

    # Process a document
    project_guid = "your-project-guid-here"
    document_guid = "your-document-guid-here"

    print(f"\nProcessing document {document_guid}...")

    result = workflow_handler.process_document(
        project_guid=project_guid,
        document_guid=document_guid,
        workflow_stage="pre_proofreading",
    )

    # Display results
    print(f"\nDocument: {result.document_name}")
    print(f"Overall Score: {result.overall_score:.2f}/100")
    print(f"Total Segments: {result.total_segments}")
    print(f"Segments with Issues: {result.segments_with_issues}")
    print(f"\nRecommendation: {result.recommendation}")

    # Show top issues
    if result.error_breakdown:
        print("\nError Breakdown:")
        for category, count in result.error_breakdown.items():
            print(f"  {category.value}: {count}")

    # Show sample segment issues
    print("\nSample Segment Issues:")
    for seg_result in result.segment_results[:3]:  # First 3 segments
        if seg_result.issues:
            print(f"\nSegment {seg_result.segment_number} (score: {seg_result.quality_score:.1f}):")
            for issue in seg_result.issues:
                print(f"  - [{issue.severity.value}] {issue.description}")


def example_terminology_check():
    """Example: Check terminology in a segment."""

    print("\n" + "=" * 80)
    print("Example: Terminology Check")
    print("=" * 80)

    config = ConfigLoader("config.yaml")

    memoq_config = config.get_memoq_config()
    client = MemoQClient(
        server_url=memoq_config["server_url"],
        username=memoq_config["username"],
        password=memoq_config["password"],
    )

    if not client.authenticate():
        print("Authentication failed!")
        return

    termbase_manager = TermBaseManager(memoq_client=client)

    # Get project terms
    project_guid = "your-project-guid-here"
    source_lang = "en"
    target_lang = "es"

    print(f"\nRetrieving terminology for {source_lang} → {target_lang}...")

    terms = termbase_manager.get_project_terms(
        project_guid, source_lang, target_lang
    )

    print(f"Found {len(terms)} terms")

    # Check terminology in a segment
    source_text = "Please submit your application form."
    target_text = "Por favor envíe su formulario de solicitud."

    print(f"\nSource: {source_text}")
    print(f"Target: {target_text}")

    correctly_used, issues = termbase_manager.check_term_consistency(
        source_text, target_text, terms
    )

    print(f"\nCorrectly used terms: {len(correctly_used)}")
    for term in correctly_used:
        print(f"  ✓ {term.source_term} → {term.target_term}")

    if issues:
        print(f"\nTerminology issues: {len(issues)}")
        for issue in issues:
            print(f"  ✗ {issue}")
    else:
        print("\n✓ No terminology issues found")


def example_batch_processing():
    """Example: Process multiple documents in a project."""

    print("\n" + "=" * 80)
    print("Example: Batch Processing")
    print("=" * 80)

    config = ConfigLoader("config.yaml")

    memoq_config = config.get_memoq_config()
    client = MemoQClient(
        server_url=memoq_config["server_url"],
        username=memoq_config["username"],
        password=memoq_config["password"],
    )

    if not client.authenticate():
        print("Authentication failed!")
        return

    # Initialize workflow handler
    termbase_manager = TermBaseManager(memoq_client=client)
    aiqe_engine = AIQEEngine(
        ai_config=config.get_ai_provider_config(),
        mqm_config=config.get_mqm_config(),
    )

    workflow_handler = WorkflowHandler(
        memoq_client=client,
        aiqe_engine=aiqe_engine,
        termbase_manager=termbase_manager,
        thresholds=config.get_quality_thresholds(),
    )

    # Process entire project
    project_guid = "your-project-guid-here"

    print(f"\nProcessing entire project {project_guid}...")

    result = workflow_handler.process_project(
        project_guid=project_guid,
        workflow_stage="pre_proofreading",
    )

    # Display results
    print(f"\nProject: {result.project_name}")
    print(f"Overall Score: {result.overall_score:.2f}/100")
    print(f"Total Documents: {result.total_documents}")
    print(f"Total Segments: {result.total_segments}")
    print(f"\nRecommendation: {result.recommendation}")

    # Document breakdown
    print("\nDocument Scores:")
    for doc in result.document_results:
        status = "✓" if doc.overall_score >= 85 else "⚠" if doc.overall_score >= 70 else "✗"
        print(f"  {status} {doc.document_name}: {doc.overall_score:.1f}/100")


if __name__ == "__main__":
    print("\nMemoQ AIQE Connector - Usage Examples\n")

    print("Note: Update the project_guid and document_guid with your actual values\n")

    try:
        # Run examples (comment out the ones you don't want to run)

        # example_document_check()

        # example_terminology_check()

        # example_batch_processing()

        print("\nExamples completed!")

    except Exception as e:
        logger.exception(f"Error running examples: {e}")
