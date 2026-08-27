from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, index=True)
    industry = Column(String)
    business_problem = Column(Text)
    target_users = Column(Text)
    budget_range = Column(String)
    timeline = Column(String)
    constraints = Column(Text)
    status = Column(String, default="CREATED")  # CREATED, ANALYZING, AWAITING_APPROVAL, APPROVED, REVISING, REJECTED, COMPLETED
    comparison_matrix = Column(Text, nullable=True)  # JSON string
    recommendation_reasoning = Column(Text, nullable=True)  # JSON string
    blueprint_json = Column(Text, nullable=True)  # Full implementation blueprint JSON
    extracted_requirements = Column(Text, nullable=True)  # Structured requirements JSON (from upload extraction or manual input)
    human_verified = Column(Boolean, default=False)  # True after user confirms/edits extracted requirements
    approved_solution_id = Column(Integer, nullable=True)  # Specific solution option approved by user
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    agent_runs = relationship("AgentRun", back_populates="project", cascade="all, delete-orphan")
    solutions = relationship("SolutionOption", back_populates="project", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="project", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    evidences = relationship("RequirementEvidence", back_populates="project", cascade="all, delete-orphan")
    summaries = relationship("StageSummary", back_populates="project", cascade="all, delete-orphan")
    evaluations = relationship("EvaluationRecord", back_populates="project", cascade="all, delete-orphan")

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    plan = Column(Text)  # JSON string
    selected_tools = Column(Text)  # JSON string representing list of executed tools
    current_step = Column(String)  # Current node execution
    status = Column(String)  # RUNNING, PAUSED, COMPLETED, FAILED

    project = relationship("Project", back_populates="agent_runs")

class SolutionOption(Base):
    __tablename__ = "solution_options"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String)
    description = Column(Text)
    ai_approach = Column(String)
    estimated_cost = Column(String)
    estimated_timeline = Column(String)
    complexity = Column(String)
    advantages = Column(Text)  # JSON string list
    limitations = Column(Text)  # JSON string list
    is_recommended = Column(Boolean, default=False)
    details_json = Column(Text, nullable=True)  # Complete rich JSON data

    project = relationship("Project", back_populates="solutions")

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    action = Column(String)  # approve, revise, reject
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="approvals")

class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    content = Column(Text)  # Markdown content
    status = Column(String)  # DRAFT, FINAL
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="proposals")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    filename = Column(String)
    file_type = Column(String)
    status = Column(String, default="PROCESSED")  # PROCESSED, ERROR
    page_count = Column(Integer, default=1)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    text = Column(Text)
    page_number = Column(Integer, default=1)
    section = Column(String, nullable=True)
    source = Column(String)

    document = relationship("Document", back_populates="chunks")

class RequirementEvidence(Base):
    __tablename__ = "requirement_evidences"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    requirement = Column(Text)
    source_document = Column(String)
    page_number = Column(Integer, default=1)
    evidence_text = Column(Text)
    trust_tag = Column(String, default="SOURCE-BACKED")  # SOURCE-BACKED, INFERRED, NOT SPECIFIED, ASSUMPTION

    project = relationship("Project", back_populates="evidences")

class StageSummary(Base):
    __tablename__ = "stage_summaries"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    stage = Column(String, index=True)  # e.g., document_processing, requirement_analysis, etc.
    status = Column(String, default="COMPLETED")
    title = Column(String)
    summary = Column(Text)
    key_findings = Column(Text, nullable=True)  # JSON list
    evidence = Column(Text, nullable=True)      # JSON list
    assumptions = Column(Text, nullable=True)   # JSON list
    next_step = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="summaries")

class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    overall_score = Column(Text)
    faithfulness = Column(Text)
    groundedness = Column(Text)
    relevancy = Column(Text)
    context_precision = Column(Text)
    hallucination_risk = Column(Text)
    latency_ms = Column(Text)
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Text)
    total_cost_inr = Column(Text)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="evaluations")


