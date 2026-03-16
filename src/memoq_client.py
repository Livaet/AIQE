"""
MemoQ API Client

Handles communication with MemoQ Server via REST Resources API and SOAP Web Service API.
"""

import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from zeep import Client as SOAPClient
from zeep.transports import Transport
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.models import (
    MemoQProject,
    MemoQDocument,
    Segment,
    TermEntry,
    WorkflowStage,
)


class MemoQClient:
    """
    Client for interacting with MemoQ Server APIs.

    Supports both REST Resources API (for TM/TB) and SOAP Web Service API (for projects).
    """

    def __init__(
        self,
        server_url: str,
        username: str,
        password: str,
        api_key: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize MemoQ API client.

        Args:
            server_url: MemoQ server URL (e.g., https://server.com:8081)
            username: MemoQ username
            password: MemoQ password
            api_key: Optional API key for authentication
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.server_url = server_url.rstrip("/")
        self.username = username
        self.password = password
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries

        self.auth_token: Optional[str] = None
        self.session = self._create_session()

        # API paths
        self.resources_api_url = f"{self.server_url}/memoqserverhttpapi/v1"
        self.ws_api_url = f"{self.server_url}/memoqservices"

        logger.info(f"Initialized MemoQ client for server: {self.server_url}")

    def _create_session(self) -> Session:
        """Create a requests session with retry logic."""
        session = Session()

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def authenticate(self) -> bool:
        """
        Authenticate with MemoQ server and obtain auth token.

        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # Use API key if provided, otherwise use username/password
            if self.api_key:
                self.auth_token = self.api_key
                logger.info("Using API key authentication")
            else:
                # Authenticate via REST API
                auth_url = f"{self.server_url}/memoqserverhttpapi/security/login"

                response = self.session.post(
                    auth_url,
                    json={"UserName": self.username, "Password": self.password},
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                )

                response.raise_for_status()
                data = response.json()

                self.auth_token = data.get("AuthToken")
                logger.info(f"Successfully authenticated as {self.username}")

            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        return headers

    def get_project(self, project_guid: str) -> Optional[MemoQProject]:
        """
        Get project information.

        Args:
            project_guid: Project GUID

        Returns:
            MemoQProject or None if not found
        """
        try:
            # Use SOAP API for project details
            wsdl_url = f"{self.ws_api_url}/ServerProjectService?wsdl"

            transport = Transport(session=self.session, timeout=self.timeout)
            client = SOAPClient(wsdl_url, transport=transport)

            # Get project info
            result = client.service.GetProject(
                authToken=self.auth_token,
                projectGuid=project_guid,
            )

            if result:
                return MemoQProject(
                    project_guid=result.ProjectGuid,
                    name=result.Name,
                    source_lang=result.SourceLanguageCode,
                    target_langs=result.TargetLanguageCodes,
                    created_date=result.CreatedTime if hasattr(result, 'CreatedTime') else None,
                    deadline=result.Deadline if hasattr(result, 'Deadline') else None,
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get project {project_guid}: {e}")
            return None

    def get_documents(self, project_guid: str) -> List[MemoQDocument]:
        """
        Get list of documents in a project.

        Args:
            project_guid: Project GUID

        Returns:
            List of MemoQDocument objects
        """
        try:
            wsdl_url = f"{self.ws_api_url}/ServerProjectService?wsdl"

            transport = Transport(session=self.session, timeout=self.timeout)
            client = SOAPClient(wsdl_url, transport=transport)

            # List documents
            result = client.service.ListProjectDocuments(
                authToken=self.auth_token,
                projectGuid=project_guid,
            )

            documents = []
            if result:
                for doc in result:
                    documents.append(
                        MemoQDocument(
                            document_guid=doc.DocumentGuid,
                            name=doc.DocumentName,
                            project_guid=project_guid,
                            source_lang=doc.SourceLanguageCode,
                            target_lang=doc.TargetLanguageCode,
                            segment_count=doc.SegmentCount if hasattr(doc, 'SegmentCount') else 0,
                        )
                    )

            logger.info(f"Found {len(documents)} documents in project {project_guid}")
            return documents

        except Exception as e:
            logger.error(f"Failed to get documents for project {project_guid}: {e}")
            return []

    def get_segments(
        self,
        project_guid: str,
        document_guid: str,
        workflow_stage: Optional[str] = None,
    ) -> List[Segment]:
        """
        Get translation segments from a document.

        Args:
            project_guid: Project GUID
            document_guid: Document GUID
            workflow_stage: Optional filter by workflow stage

        Returns:
            List of Segment objects
        """
        try:
            wsdl_url = f"{self.ws_api_url}/ServerProjectService?wsdl"

            transport = Transport(session=self.session, timeout=self.timeout)
            client = SOAPClient(wsdl_url, transport=transport)

            # Get document segments
            result = client.service.GetSegments(
                authToken=self.auth_token,
                projectGuid=project_guid,
                documentGuid=document_guid,
            )

            segments = []
            if result:
                for idx, seg in enumerate(result):
                    # Filter by workflow stage if specified
                    if workflow_stage and hasattr(seg, 'WorkflowStatus'):
                        if seg.WorkflowStatus.lower() != workflow_stage.lower():
                            continue

                    segments.append(
                        Segment(
                            segment_id=seg.SegmentId if hasattr(seg, 'SegmentId') else f"{document_guid}_{idx}",
                            source_text=seg.SourceText,
                            target_text=seg.TargetText if hasattr(seg, 'TargetText') else "",
                            source_lang=seg.SourceLanguage if hasattr(seg, 'SourceLanguage') else "",
                            target_lang=seg.TargetLanguage if hasattr(seg, 'TargetLanguage') else "",
                            segment_number=idx + 1,
                            status=seg.Status if hasattr(seg, 'Status') else None,
                        )
                    )

            logger.info(f"Retrieved {len(segments)} segments from document {document_guid}")
            return segments

        except Exception as e:
            logger.error(f"Failed to get segments: {e}")
            return []

    def list_projects(
        self,
        workflow_stage: Optional[str] = None,
    ) -> List[MemoQProject]:
        """
        List all accessible projects, optionally filtered by workflow stage.

        Args:
            workflow_stage: Optional workflow stage filter

        Returns:
            List of MemoQProject objects
        """
        try:
            wsdl_url = f"{self.ws_api_url}/ServerProjectService?wsdl"

            transport = Transport(session=self.session, timeout=self.timeout)
            client = SOAPClient(wsdl_url, transport=transport)

            result = client.service.ListProjects(
                authToken=self.auth_token,
            )

            projects = []
            if result:
                for proj in result:
                    stage = None
                    if hasattr(proj, "WorkflowStatus") and proj.WorkflowStatus:
                        try:
                            stage = WorkflowStage(proj.WorkflowStatus.lower())
                        except ValueError:
                            pass

                    if workflow_stage and stage and stage.value != workflow_stage.lower():
                        continue

                    projects.append(
                        MemoQProject(
                            project_guid=proj.ProjectGuid,
                            name=proj.Name,
                            source_lang=proj.SourceLanguageCode,
                            target_langs=list(proj.TargetLanguageCodes)
                            if hasattr(proj, "TargetLanguageCodes")
                            else [],
                            workflow_stage=stage,
                            created_date=proj.CreatedTime
                            if hasattr(proj, "CreatedTime")
                            else None,
                            deadline=proj.Deadline
                            if hasattr(proj, "Deadline")
                            else None,
                        )
                    )

            logger.info(f"Listed {len(projects)} projects")
            return projects

        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    def get_termbases(self, project_guid: str) -> List[str]:
        """
        Get list of termbase GUIDs attached to a project.

        Args:
            project_guid: Project GUID

        Returns:
            List of termbase GUIDs
        """
        try:
            url = f"{self.resources_api_url}/projects/{project_guid}/termbases"

            response = self.session.get(
                url,
                headers=self._get_headers(),
                params={"authToken": self.auth_token},
                verify=self.verify_ssl,
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

            termbase_guids = [tb["TermBaseGuid"] for tb in data if "TermBaseGuid" in tb]
            logger.info(f"Found {len(termbase_guids)} termbases for project {project_guid}")

            return termbase_guids

        except Exception as e:
            logger.error(f"Failed to get termbases: {e}")
            return []

    def get_termbase_entries(
        self,
        termbase_guid: str,
        source_lang: str,
        target_lang: str,
        search_term: Optional[str] = None,
    ) -> List[TermEntry]:
        """
        Get termbase entries.

        Args:
            termbase_guid: Termbase GUID
            source_lang: Source language code
            target_lang: Target language code
            search_term: Optional search term to filter entries

        Returns:
            List of TermEntry objects
        """
        try:
            url = f"{self.resources_api_url}/tbs/{termbase_guid}/entries"

            params = {
                "authToken": self.auth_token,
                "sourceLang": source_lang,
                "targetLang": target_lang,
            }

            if search_term:
                params["search"] = search_term

            response = self.session.get(
                url,
                headers=self._get_headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

            entries = []
            for entry in data:
                entries.append(
                    TermEntry(
                        source_term=entry.get("SourceTerm", ""),
                        target_term=entry.get("TargetTerm", ""),
                        source_lang=source_lang,
                        target_lang=target_lang,
                        definition=entry.get("Definition"),
                        context=entry.get("Context"),
                        domain=entry.get("Domain"),
                        forbidden=entry.get("Forbidden", False),
                    )
                )

            logger.debug(f"Retrieved {len(entries)} terms from termbase {termbase_guid}")
            return entries

        except Exception as e:
            logger.error(f"Failed to get termbase entries: {e}")
            return []

    def update_segment_status(
        self,
        project_guid: str,
        document_guid: str,
        segment_id: str,
        status: str,
        comment: Optional[str] = None,
    ) -> bool:
        """
        Update segment status (e.g., flag for review).

        Args:
            project_guid: Project GUID
            document_guid: Document GUID
            segment_id: Segment ID
            status: New status
            comment: Optional comment

        Returns:
            bool: True if successful
        """
        try:
            wsdl_url = f"{self.ws_api_url}/ServerProjectService?wsdl"

            transport = Transport(session=self.session, timeout=self.timeout)
            client = SOAPClient(wsdl_url, transport=transport)

            client.service.UpdateSegmentStatus(
                authToken=self.auth_token,
                projectGuid=project_guid,
                documentGuid=document_guid,
                segmentId=segment_id,
                status=status,
                comment=comment,
            )

            logger.info(f"Updated segment {segment_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update segment status: {e}")
            return False

    def add_segment_comment(
        self,
        project_guid: str,
        document_guid: str,
        segment_id: str,
        comment: str,
    ) -> bool:
        """
        Add a comment to a segment.

        Args:
            project_guid: Project GUID
            document_guid: Document GUID
            segment_id: Segment ID
            comment: Comment text

        Returns:
            bool: True if successful
        """
        try:
            wsdl_url = f"{self.ws_api_url}/ServerProjectService?wsdl"

            transport = Transport(session=self.session, timeout=self.timeout)
            client = SOAPClient(wsdl_url, transport=transport)

            client.service.AddSegmentComment(
                authToken=self.auth_token,
                projectGuid=project_guid,
                documentGuid=document_guid,
                segmentId=segment_id,
                comment=comment,
            )

            logger.debug(f"Added comment to segment {segment_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add segment comment: {e}")
            return False
