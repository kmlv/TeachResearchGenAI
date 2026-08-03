"""Esquemas Pydantic para el rastro auditable."""

from typing import Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    id: str
    title: str
    authors: str
    year: int
    country: str
    url: str
    verified_on: str


class Passage(BaseModel):
    id: str
    source_id: str
    summary: str
    locator: str
    study_design: str
    causal_strength: Literal["none", "descriptive", "suggestive", "causal"]
    verified_on: str
    source_url: str
    keywords: tuple[str, ...]
    content_kind: Literal["pedagogical_paraphrase"] = "pedagogical_paraphrase"


class EvidenceRef(BaseModel):
    passage_id: str
    relation: Literal["supports", "contradicts", "context"]
    use: str


class AuditDraft(BaseModel):
    verdict: Literal["supported", "contradicted", "partially_supported", "insufficient"]
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    uncertainty: str
    limitations: list[str] = Field(default_factory=list)
    next_step: str


class CanonicalCitation(BaseModel):
    passage_id: str
    source: str
    title: str
    url: str
    locator: str
    summary: str
    content_kind: Literal["pedagogical_paraphrase"] = "pedagogical_paraphrase"


class HumanReview(BaseModel):
    status: Literal["pending"] = "pending"


class RunSummary(BaseModel):
    operations: int
    searches: int
    opened_passages: list[str] = Field(default_factory=list)


class AuditResult(BaseModel):
    mode: Literal["live", "recorded_replay"]
    claim: str
    draft: AuditDraft
    citations: list[CanonicalCitation] = Field(default_factory=list)
    human_review: HumanReview = Field(default_factory=HumanReview)
    validation_errors: list[str] = Field(default_factory=list)
    run_summary: RunSummary
