"""Persisted-row models and status vocabularies for the knowledge tables.

These mirror the columns created in migrations/versions/0001_knowledge_p1*.py.
The DDL lives only in the migration (Alembic-only, no ensure_*); this module is
the shared vocabulary the DAL and routes use to read and write those rows, kept
free of any database handle so it stays trivially importable and testable.

Type alignment with the main project (docs/Pearnly_KB_主项目契约事实):
tenant_id / created_by / uploaded_by are UUID strings, workspace_client_id is a
bigint, and the table primary keys and internal foreign keys are bigint.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

TABLE_BASES = "knowledge_bases"
TABLE_DOCUMENTS = "knowledge_documents"
TABLE_INGEST_JOBS = "knowledge_ingest_jobs"
TABLE_CHUNKS = "knowledge_chunks"
TABLE_EMBEDDINGS = "knowledge_embeddings"
TABLE_CLIENT_RULES = "client_rules"
TABLE_RISK_CHECKS = "invoice_risk_checks"

# invoice_risk_checks.status — the check run's own state (not the risk level).
CHECK_PENDING = "pending"
CHECK_SUCCESS = "success"
CHECK_FAILED = "failed"
CHECK_SKIPPED = "skipped"
HUMAN_UNREVIEWED = "unreviewed"

# Finding / client-rule severity. risk_level of a check is the max across findings.
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"
SEVERITIES = frozenset({SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW})

# client_rules.rule_type — the first batch of seven customer-tunable rule kinds.
RULE_SUPPLIER_ALLOWLIST = "supplier_allowlist"
RULE_SUPPLIER_FORCE_REVIEW = "supplier_force_review"
RULE_AMOUNT_LIMIT = "amount_limit"
RULE_NO_AUTO_PUSH_CATEGORY = "no_auto_push_category"
RULE_WHT_RATE = "wht_rate"
RULE_ACCOUNTING_PERIOD = "accounting_period"
RULE_FEATURE_TOGGLE = "feature_toggle"
RULE_TYPES = frozenset(
    {
        RULE_SUPPLIER_ALLOWLIST,
        RULE_SUPPLIER_FORCE_REVIEW,
        RULE_AMOUNT_LIMIT,
        RULE_NO_AUTO_PUSH_CATEGORY,
        RULE_WHT_RATE,
        RULE_ACCOUNTING_PERIOD,
        RULE_FEATURE_TOGGLE,
    }
)

SUBJECT_SUPPLIER = "supplier"
SUBJECT_CATEGORY = "category"
SUBJECT_CONTRACT = "contract"
SUBJECT_GLOBAL = "global"
SUBJECT_TYPES = frozenset({SUBJECT_SUPPLIER, SUBJECT_CATEGORY, SUBJECT_CONTRACT, SUBJECT_GLOBAL})

ORIGIN_MANUAL = "manual"
ORIGINS = frozenset({ORIGIN_MANUAL, "learned", "imported", "extracted"})

# knowledge_bases.scope — firm-wide vs scoped to one workspace client (account set).
SCOPE_FIRM = "firm"
SCOPE_WORKSPACE_CLIENT = "workspace_client"
BASE_SCOPES = frozenset({SCOPE_FIRM, SCOPE_WORKSPACE_CLIENT})

# knowledge_documents.status — the ingest lifecycle. DELETED is a soft-delete
# tombstone; rows are never hard-deleted so audit and isolation stay intact.
DOC_UPLOADED = "uploaded"
DOC_EXTRACTING = "extracting"
DOC_CHUNKING = "chunking"
DOC_EMBEDDING = "embedding"
DOC_READY = "ready"
DOC_FAILED = "failed"
DOC_DELETED = "deleted"
DOCUMENT_STATUSES = frozenset(
    {
        DOC_UPLOADED,
        DOC_EXTRACTING,
        DOC_CHUNKING,
        DOC_EMBEDDING,
        DOC_READY,
        DOC_FAILED,
        DOC_DELETED,
    }
)

# knowledge_ingest_jobs.status — the worker's view of one document's processing.
JOB_QUEUED = "queued"
JOB_RUNNING = "running"
JOB_SUCCESS = "success"
JOB_FAILED = "failed"
JOB_RETRYING = "retrying"
JOB_STATUSES = frozenset({JOB_QUEUED, JOB_RUNNING, JOB_SUCCESS, JOB_FAILED, JOB_RETRYING})

# A finished job's progress is full; a failed one made no usable progress.
PROGRESS_COMPLETE = 100

# Stable error codes recorded on a failed document (knowledge_documents.error_code).
ERROR_UNSUPPORTED = "unsupported_document"
ERROR_EMBEDDING = "embedding_failed"


@dataclass(frozen=True)
class KnowledgeBase:
    id: int
    tenant_id: str
    workspace_client_id: Optional[int]
    scope: str
    name: str
    status: str
    created_by: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class KnowledgeDocument:
    id: int
    tenant_id: str
    workspace_client_id: Optional[int]
    knowledge_base_id: int
    source_type: str
    filename: str
    mime_type: Optional[str]
    storage_path: Optional[str]
    checksum: str
    status: str
    uploaded_by: Optional[str]
    error_code: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class KnowledgeAnswer:
    id: int
    tenant_id: str
    workspace_client_id: Optional[int]
    question: str
    answer: str
    citations: list
    model: Optional[str]
    no_answer: bool
    created_at: datetime


@dataclass(frozen=True)
class InvoiceRiskCheck:
    id: int
    tenant_id: str
    workspace_client_id: Optional[int]
    history_id: str
    risk_level: str
    needs_human_review: bool
    findings: list
    status: str
    human_status: str
    created_at: datetime


@dataclass(frozen=True)
class SearchHit:
    chunk_id: int
    document_id: int
    filename: str
    text: str
    score: float  # cosine similarity in [0, 1]; higher is closer


@dataclass(frozen=True)
class ClientRule:
    id: int
    tenant_id: str
    workspace_client_id: Optional[int]
    rule_type: str
    subject_type: str
    subject_key: Optional[str]
    rule_body: dict
    severity: Optional[str]
    is_active: bool
    effective_from: Optional[date]
    effective_to: Optional[date]
    origin: str
    created_at: datetime


@dataclass(frozen=True)
class IngestJob:
    id: int
    tenant_id: str
    workspace_client_id: Optional[int]
    document_id: int
    status: str
    progress: int
    error_code: Optional[str]
    retry_count: int
    max_retries: int
    created_at: datetime
    finished_at: Optional[datetime]
