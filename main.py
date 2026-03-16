#!/usr/bin/env python3
"""
MemoQ AIQE Connector - Main Entry Point

Provides standalone, service, and API modes for quality checking.
"""

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

from src.config_loader import ConfigLoader
from src.memoq_client import MemoQClient
from src.aiqe_engine import AIQEEngine
from src.termbase_manager import TermBaseManager
from src.workflow_handler import WorkflowHandler
from src.models import ProjectQualityResult, DocumentQualityResult


def setup_logging(config_loader: ConfigLoader):
    """Configure logging based on settings."""
    log_config = config_loader.get_logging_config()

    log_level = log_config.get("level", "INFO")
    log_file = log_config.get("log_file", "./logs/aiqe-connector.log")

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    )

    # Add file handler
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_file,
        level=log_level,
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    )

    logger.info(f"Logging configured: level={log_level}, file={log_file}")


def initialize_components(config_loader: ConfigLoader):
    """Initialize all components."""

    # MemoQ Client
    memoq_config = config_loader.get_memoq_config()
    memoq_client = MemoQClient(
        server_url=memoq_config.get("server_url"),
        username=memoq_config.get("username"),
        password=memoq_config.get("password"),
        api_key=memoq_config.get("api_key"),
        verify_ssl=memoq_config.get("verify_ssl", True),
        timeout=memoq_config.get("timeout", 30),
        max_retries=memoq_config.get("max_retries", 3),
    )

    # Authenticate
    if not memoq_client.authenticate():
        logger.error("Failed to authenticate with MemoQ server")
        sys.exit(1)

    # Term Base Manager
    termbase_config = config_loader.get_termbase_config()
    termbase_manager = TermBaseManager(
        memoq_client=memoq_client,
        cache_enabled=termbase_config.get("enable_cache", True),
        cache_ttl=termbase_config.get("cache_ttl", 3600),
        case_sensitive=termbase_config.get("case_sensitive", False),
        fuzzy_matching=termbase_config.get("fuzzy_matching", True),
        fuzzy_threshold=termbase_config.get("fuzzy_threshold", 0.9),
    )

    # AIQE Engine
    ai_config = config_loader.get_ai_provider_config()
    mqm_config = config_loader.get_mqm_config()
    aiqe_engine = AIQEEngine(ai_config=ai_config, mqm_config=mqm_config)

    # Workflow Handler
    workflow_config = config_loader.get_workflow_config()
    thresholds = config_loader.get_quality_thresholds()
    workflow_handler = WorkflowHandler(
        memoq_client=memoq_client,
        aiqe_engine=aiqe_engine,
        termbase_manager=termbase_manager,
        thresholds=thresholds,
        notify_project_manager=workflow_config.get("notify_project_manager", True),
        notify_translator=workflow_config.get("notify_translator", True),
    )

    return {
        "memoq_client": memoq_client,
        "termbase_manager": termbase_manager,
        "aiqe_engine": aiqe_engine,
        "workflow_handler": workflow_handler,
    }


def save_report(result, config_loader: ConfigLoader, output_file: str = None):
    """Save quality report to file."""
    reporting_config = config_loader.get_reporting_config()

    if not reporting_config.get("save_reports", True):
        return

    reports_dir = Path(reporting_config.get("reports_directory", "./reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    if output_file:
        report_path = Path(output_file)
    else:
        timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
        if isinstance(result, ProjectQualityResult):
            filename = f"project_{result.project_guid}_{timestamp}.json"
        else:
            filename = f"document_{result.document_guid}_{timestamp}.json"

        report_path = reports_dir / filename

    # Save as JSON
    with open(report_path, 'w') as f:
        json.dump(result.model_dump(), f, indent=2, default=str)

    logger.info(f"Report saved to {report_path}")
    return report_path


def run_standalone(args, config_loader: ConfigLoader, components: dict):
    """Run in standalone mode - check a specific project or document."""

    workflow_handler = components["workflow_handler"]

    if args.project_guid:
        logger.info(f"Running quality check on project {args.project_guid}")

        result = workflow_handler.process_project(
            project_guid=args.project_guid,
            workflow_stage=args.workflow_stage or "pre_proofreading",
        )

        # Print summary
        print("\n" + "=" * 80)
        print(f"Project: {result.project_name}")
        print(f"Overall Score: {result.overall_score:.2f}/100")
        print(f"Documents: {result.total_documents}")
        print(f"Total Segments: {result.total_segments}")
        print(f"Segments with Issues: {result.segments_with_issues}")
        print(f"Recommendation: {result.recommendation}")
        print("=" * 80 + "\n")

        # Save report
        report_path = save_report(result, config_loader, args.output)
        print(f"Full report saved to: {report_path}")

    elif args.document_guid:
        if not args.project_guid:
            logger.error("--project-guid is required when using --document-guid")
            sys.exit(1)

        logger.info(
            f"Running quality check on document {args.document_guid} "
            f"in project {args.project_guid}"
        )

        result = workflow_handler.process_document(
            project_guid=args.project_guid,
            document_guid=args.document_guid,
            workflow_stage=args.workflow_stage or "pre_proofreading",
        )

        # Print summary
        print("\n" + "=" * 80)
        print(f"Document: {result.document_name}")
        print(f"Overall Score: {result.overall_score:.2f}/100")
        print(f"Total Segments: {result.total_segments}")
        print(f"Segments with Issues: {result.segments_with_issues}")
        print(f"Recommendation: {result.recommendation}")
        print("=" * 80 + "\n")

        # Print top issues
        if result.error_breakdown:
            print("Error Breakdown:")
            for category, count in result.error_breakdown.items():
                print(f"  {category.value}: {count}")
            print()

        # Save report
        report_path = save_report(result, config_loader, args.output)
        print(f"Full report saved to: {report_path}")

    else:
        logger.error("Either --project-guid or --document-guid must be provided")
        sys.exit(1)


def run_service(args, config_loader: ConfigLoader, components: dict):
    """Run in service mode - monitor workflow and process automatically."""
    import time

    memoq_client = components["memoq_client"]
    workflow_handler = components["workflow_handler"]
    workflow_config = config_loader.get_workflow_config()

    polling_interval = workflow_config.get("polling_interval", 60)
    trigger_stage = workflow_config.get("trigger", "pre_proofreading")
    state_file = Path(workflow_config.get("state_file", "./data/service_state.json"))

    logger.info(f"Starting service mode (polling every {polling_interval}s)")
    logger.info(f"Monitoring stage: {trigger_stage}")
    logger.info("Press Ctrl+C to stop")

    # Load processed items state
    state_file.parent.mkdir(parents=True, exist_ok=True)

    def load_state() -> dict:
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        return {"processed_documents": {}}

    def save_state(state: dict):
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)

    state = load_state()
    processed_documents: dict = state.get("processed_documents", {})

    logger.info(
        f"Loaded state: {len(processed_documents)} previously processed documents"
    )

    while True:
        try:
            logger.info("Polling MemoQ for projects...")

            projects = memoq_client.list_projects(workflow_stage=trigger_stage)
            logger.info(f"Found {len(projects)} project(s) at stage '{trigger_stage}'")

            for project in projects:
                try:
                    documents = memoq_client.get_documents(project.project_guid)

                    for doc in documents:
                        doc_key = f"{project.project_guid}:{doc.document_guid}"

                        if doc_key in processed_documents:
                            logger.debug(
                                f"Skipping already-processed document {doc.name}"
                            )
                            continue

                        logger.info(
                            f"Processing document '{doc.name}' "
                            f"in project '{project.name}'"
                        )

                        result = workflow_handler.process_document(
                            project_guid=project.project_guid,
                            document_guid=doc.document_guid,
                            workflow_stage=trigger_stage,
                        )

                        # Record as processed
                        processed_documents[doc_key] = {
                            "project_name": project.name,
                            "document_name": doc.name,
                            "processed_at": datetime.utcnow().isoformat(),
                            "quality_score": result.overall_score,
                            "recommendation": result.recommendation,
                        }

                        # Persist state after each document
                        save_state({"processed_documents": processed_documents})

                        # Save report
                        save_report(result, config_loader)

                        logger.info(
                            f"Document '{doc.name}' processed: "
                            f"score={result.overall_score:.1f}, "
                            f"{result.recommendation}"
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to process project {project.project_guid}: {e}"
                    )
                    continue

        except Exception as e:
            logger.error(f"Polling error: {e}")

        logger.debug(f"Sleeping {polling_interval}s until next poll...")
        time.sleep(polling_interval)


def run_api(args, config_loader: ConfigLoader, components: dict):
    """Run in API mode - provide REST API for quality checking."""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        import uvicorn
    except ImportError:
        logger.error("FastAPI and uvicorn are required for API mode")
        logger.error("Install with: pip install fastapi uvicorn")
        sys.exit(1)

    app = FastAPI(
        title="MemoQ AIQE Connector API",
        description="AI-powered Quality Estimation API for MemoQ",
        version="1.0.0",
    )

    # CORS
    api_config = config_loader.get_api_config()
    if api_config.get("enable_cors", True):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=api_config.get("allowed_origins", ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    workflow_handler = components["workflow_handler"]

    # Request models
    class CheckProjectRequest(BaseModel):
        project_guid: str
        workflow_stage: str = "pre_proofreading"

    class CheckDocumentRequest(BaseModel):
        project_guid: str
        document_guid: str
        workflow_stage: str = "pre_proofreading"

    # Endpoints
    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.post("/check/project")
    async def check_project(request: CheckProjectRequest):
        try:
            result = workflow_handler.process_project(
                project_guid=request.project_guid,
                workflow_stage=request.workflow_stage,
            )
            return result.model_dump()
        except Exception as e:
            logger.error(f"API error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/check/document")
    async def check_document(request: CheckDocumentRequest):
        try:
            result = workflow_handler.process_document(
                project_guid=request.project_guid,
                document_guid=request.document_guid,
                workflow_stage=request.workflow_stage,
            )
            return result.model_dump()
        except Exception as e:
            logger.error(f"API error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Run server
    host = api_config.get("host", "0.0.0.0")
    port = args.port or api_config.get("port", 8080)

    logger.info(f"Starting API server on {host}:{port}")

    uvicorn.run(app, host=host, port=port)


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description="MemoQ AIQE Connector - AI-powered Quality Estimation"
    )

    parser.add_argument(
        "--mode",
        choices=["standalone", "service", "api"],
        default="standalone",
        help="Operation mode (default: standalone)",
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    # Standalone mode arguments
    parser.add_argument(
        "--project-guid",
        help="Project GUID to check",
    )

    parser.add_argument(
        "--document-guid",
        help="Document GUID to check",
    )

    parser.add_argument(
        "--workflow-stage",
        help="Workflow stage to check (default: pre_proofreading)",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output file for report",
    )

    # API mode arguments
    parser.add_argument(
        "--port",
        type=int,
        help="Port for API server (default: from config)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config_loader = ConfigLoader(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Setup logging
    setup_logging(config_loader)

    logger.info("=" * 80)
    logger.info("MemoQ AIQE Connector Starting")
    logger.info("=" * 80)

    # Initialize components
    try:
        components = initialize_components(config_loader)
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)

    # Run in selected mode
    try:
        if args.mode == "standalone":
            run_standalone(args, config_loader, components)
        elif args.mode == "service":
            run_service(args, config_loader, components)
        elif args.mode == "api":
            run_api(args, config_loader, components)

    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

    logger.info("MemoQ AIQE Connector stopped")


if __name__ == "__main__":
    main()
