from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import datetime
import json

# Solution Option schemas
class SolutionOptionBase(BaseModel):
    name: str
    description: str
    ai_approach: str
    estimated_cost: str
    estimated_timeline: str
    complexity: str
    advantages: List[str]
    limitations: List[str]
    is_recommended: bool
    details_json: Optional[str] = None

    @field_validator('advantages', 'limitations', mode='before')
    def parse_json_list(cls, v):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [str(parsed)]
            except Exception:
                return [v]
        return v or []

class SolutionOptionCreate(SolutionOptionBase):
    pass

class SolutionOptionResponse(SolutionOptionBase):
    id: int

    class Config:
        from_attributes = True

# Agent Run schemas
class AgentRunBase(BaseModel):
    plan: Optional[str] = None
    selected_tools: Optional[str] = None
    current_step: Optional[str] = None
    status: Optional[str] = None

class AgentRunResponse(BaseModel):
    id: int
    plan: Optional[str] = None
    selected_tools: Optional[str] = None
    current_step: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

# Extracted Requirements schema (used by both upload and manual paths)
class ExtractedRequirements(BaseModel):
    business_problem: Optional[str] = ""
    business_objective: Optional[str] = ""
    industry: Optional[str] = ""
    target_users: Optional[List[str]] = []
    current_process: Optional[str] = ""
    pain_points: Optional[List[str]] = []
    functional_requirements: Optional[List[str]] = []
    non_functional_requirements: Optional[List[str]] = []
    budget: Optional[str] = ""
    timeline: Optional[str] = ""
    expected_scale: Optional[str] = ""
    security_requirements: Optional[List[str]] = []
    integration_requirements: Optional[List[str]] = []
    success_metrics: Optional[List[str]] = []
    constraints: Optional[List[str]] = []
    risks: Optional[List[str]] = []
    open_questions: Optional[List[str]] = []
    source_document: Optional[str] = ""
    human_verified: bool = False

    @field_validator(
        'target_users', 'pain_points', 'functional_requirements', 
        'non_functional_requirements', 'security_requirements', 
        'integration_requirements', 'success_metrics', 'constraints', 
        'risks', 'open_questions', mode='before'
    )
    def parse_str_or_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            if v.startswith('[') and v.endswith(']'):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(x) for x in parsed]
                except Exception:
                    pass
            return [s.strip() for s in v.split(',') if s.strip()]
        if isinstance(v, list):
            return [str(x) for x in v]
        return [str(v)]

class RequirementsUpdate(BaseModel):
    """For PUT /requirements — user edits extracted requirements."""
    requirements: ExtractedRequirements
    human_verified: bool = True

# Project schemas
class ProjectCreate(BaseModel):
    client_name: str
    industry: str
    business_problem: str
    target_users: str
    budget_range: str
    timeline: str
    constraints: Optional[str] = ""

class ProjectResponse(BaseModel):
    id: int
    client_name: str
    industry: str
    business_problem: str
    target_users: str
    budget_range: str
    timeline: str
    constraints: Optional[str] = ""
    status: str
    comparison_matrix: Optional[str] = None
    recommendation_reasoning: Optional[str] = None
    blueprint_json: Optional[str] = None
    extracted_requirements: Optional[str] = None
    human_verified: bool = False
    created_at: datetime.datetime
    solutions: List[SolutionOptionResponse] = []
    agent_runs: List[AgentRunResponse] = []

    class Config:
        from_attributes = True

# Stage Summary Schemas
class StageSummaryResponse(BaseModel):
    id: int
    project_id: int
    stage: str
    status: str
    title: str
    summary: str
    key_findings: Optional[List[str]] = []
    evidence: Optional[List[dict]] = []
    assumptions: Optional[List[str]] = []
    next_step: Optional[str] = None
    created_at: datetime.datetime

    @field_validator('key_findings', 'evidence', 'assumptions', mode='before')
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [parsed]
            except Exception:
                return [v]
        return v or []

    class Config:
        from_attributes = True

# Requirement Evidence Schemas
class RequirementEvidenceResponse(BaseModel):
    id: int
    project_id: int
    requirement: str
    source_document: str
    page_number: int
    evidence_text: str
    trust_tag: str

    class Config:
        from_attributes = True

# Document Schemas
class DocumentResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    file_type: str
    status: str
    page_count: int
    chunk_count: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Approval schemas
class ApprovalCreate(BaseModel):
    action: str  # approve, revise, reject
    feedback: Optional[str] = None
    solution_id: Optional[int] = None

class ApprovalResponse(BaseModel):
    id: int
    action: str
    feedback: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Proposal schemas
class ProposalResponse(BaseModel):
    id: int
    project_id: int
    content: str
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Evaluation Schemas
class EvaluationResponse(BaseModel):
    overall_score: float
    faithfulness_score: float
    groundedness_score: float
    answer_relevancy: float
    context_precision: float
    hallucination_risk_pct: float
    constraint_alignment_score: float
    evaluation_duration_ms: float
    status: str
    eval_summary: str
    cache_stats: Optional[dict] = None

# Accuracy-First Problem Classification Schemas
class ProblemClassificationResponse(BaseModel):
    primary_category: str
    supporting_categories: List[str] = []
    computational_type: str
    rationale: str
    rag_required: bool
    llm_required: bool
    agentic_required: bool
    selected_capabilities: List[dict] = []  # [{"name": "...", "required": True, "reason": "..."}]
    not_required_capabilities: List[dict] = []  # [{"name": "...", "reason": "..."}]

class RequirementTraceabilityItem(BaseModel):
    requirement_id: str
    requirement_text: str
    solution_component: str
    technology: str
    reasoning: str

class SolutionConfidenceScore(BaseModel):
    requirement_coverage: float  # out of 100
    architecture_alignment: float
    technology_appropriateness: float
    business_fit: float
    feasibility: float
    overall_confidence: float
    confidence_label: str


