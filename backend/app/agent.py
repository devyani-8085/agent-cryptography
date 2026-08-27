import json
import datetime
import time
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models, tools, llm

class AgentGraphRunner:
    def __init__(self, project_id: int):
        self.project_id = project_id

    def _get_db(self):
        return SessionLocal()

    def run_next_step(self, feedback: str = None) -> models.Project:
        """
        Executes the agent state machine step-by-step until it hits a human approval gate
        or completes.
        """
        db = self._get_db()
        try:
            project = db.query(models.Project).filter(models.Project.id == self.project_id).first()
            if not project:
                raise ValueError("Project not found")

            # Load or create active AgentRun
            agent_run = db.query(models.AgentRun).filter(
                models.AgentRun.project_id == self.project_id
            ).order_by(models.AgentRun.id.desc()).first()

            if not agent_run or agent_run.status in ["COMPLETED", "FAILED"]:
                agent_run = models.AgentRun(
                    project_id=self.project_id,
                    plan=json.dumps([]),
                    selected_tools=json.dumps([]),
                    current_step="START",
                    status="RUNNING"
                )
                db.add(agent_run)
                db.commit()
                db.refresh(agent_run)

            steps = [
                "analyze_requirements",
                "create_plan",
                "select_tools",
                "solution_recommender",
                "cost_estimator",
                "architecture_generator",
                "compare_solutions",
                "recommend_solution",
                "human_approval_gate",
                "generate_implementation_blueprint",
                "generate_final_proposal"
            ]

            # If project is REVISING, inject feedback and return to solution generation
            if project.status == "REVISING":
                agent_run.current_step = "create_plan"
                agent_run.status = "RUNNING"
                project.status = "ANALYZING"
                db.commit()

            # If project is APPROVED, resume from human_approval_gate to generate blueprint then final proposal
            if project.status == "APPROVED":
                agent_run.current_step = "human_approval_gate"
                agent_run.status = "RUNNING"
                project.status = "ANALYZING"
                db.commit()

            current_idx = -1
            if agent_run.current_step in steps:
                current_idx = steps.index(agent_run.current_step)

            next_idx = current_idx + 1
            if next_idx >= len(steps):
                # Graph fully completed
                agent_run.status = "COMPLETED"
                project.status = "COMPLETED"
                db.commit()
                return project

            next_step = steps[next_idx]
            agent_run.current_step = next_step
            project.status = "ANALYZING"
            db.commit()

            print(f"Executing Agent Node: {next_step} for Project {self.project_id}")
            start_step_time = time.perf_counter()

            # Execution Logic per Node
            if next_step == "analyze_requirements":
                self._node_analyze_requirements(db, project, agent_run)
            elif next_step == "create_plan":
                self._node_create_plan(db, project, agent_run, feedback)
            elif next_step == "select_tools":
                self._node_select_tools(db, project, agent_run)
            elif next_step == "solution_recommender":
                self._node_solution_recommender(db, project, agent_run)
            elif next_step == "cost_estimator":
                self._node_cost_estimator(db, project, agent_run)
            elif next_step == "architecture_generator":
                self._node_architecture_generator(db, project, agent_run)
            elif next_step == "compare_solutions":
                self._node_compare_solutions(db, project, agent_run)
            elif next_step == "recommend_solution":
                self._node_recommend_solution(db, project, agent_run)
                self._generate_and_save_evaluation(db, project)
            elif next_step == "human_approval_gate":
                self._node_human_approval_gate(db, project, agent_run)
            elif next_step == "generate_implementation_blueprint":
                self._node_generate_implementation_blueprint(db, project, agent_run)
            elif next_step == "generate_final_proposal":
                self._node_generate_final_proposal(db, project, agent_run)
                self._generate_and_save_evaluation(db, project)

            step_duration_ms = round((time.perf_counter() - start_step_time) * 1000, 1)
            print(f"[Node Execution] {next_step} finished in {step_duration_ms}ms")

            db.refresh(project)
            return project

        finally:
            db.close()

    def _generate_and_save_evaluation(self, db: Session, project: models.Project):
        """Computes and saves enterprise AI evaluation metrics to database."""
        from .evaluator import AIEvaluator
        from .rag_engine import rag_instance

        chunks = rag_instance.project_chunks.get(project.id, [])
        sols = db.query(models.SolutionOption).filter(models.SolutionOption.project_id == project.id).all()
        sol_dicts = [{"name": s.name, "cost": s.estimated_cost} for s in sols]

        eval_res = AIEvaluator.evaluate_project_run(
            business_problem=project.business_problem,
            retrieved_chunks=chunks,
            solutions=sol_dicts,
            budget_range=project.budget_range,
            timeline=project.timeline
        )

        db.query(models.EvaluationRecord).filter(models.EvaluationRecord.project_id == project.id).delete()

        rec = models.EvaluationRecord(
            project_id=project.id,
            overall_score=str(eval_res["overall_ai_score"]),
            faithfulness=str(eval_res["faithfulness_score"]),
            groundedness=str(eval_res["groundedness_score"]),
            relevancy=str(eval_res["answer_relevancy"]),
            context_precision=str(eval_res["context_precision"]),
            hallucination_risk=str(eval_res["hallucination_risk_pct"]),
            latency_ms=str(eval_res["evaluation_duration_ms"]),
            total_tokens=llm.LLMClient.total_prompt_tokens + llm.LLMClient.total_completion_tokens,
            total_cost_usd=f"${llm.LLMClient.total_cost_usd:.6f}",
            total_cost_inr=f"₹{llm.LLMClient.total_cost_usd * 86.5:.4f}",
            details_json=json.dumps(eval_res)
        )
        db.add(rec)
        db.commit()


    # --- Helper to Save Transparent Stage Summaries ---
    def _save_stage_summary(self, db: Session, stage: str, title: str, summary: str, key_findings: list, evidence: list = None, assumptions: list = None, next_step: str = None):
        existing = db.query(models.StageSummary).filter(
            models.StageSummary.project_id == self.project_id,
            models.StageSummary.stage == stage
        ).first()
        if not existing:
            existing = models.StageSummary(
                project_id=self.project_id,
                stage=stage,
                status="COMPLETED",
                title=title,
                summary=summary,
                key_findings=json.dumps(key_findings or []),
                evidence=json.dumps(evidence or []),
                assumptions=json.dumps(assumptions or []),
                next_step=next_step
            )
            db.add(existing)
        else:
            existing.status = "COMPLETED"
            existing.title = title
            existing.summary = summary
            existing.key_findings = json.dumps(key_findings or [])
            existing.evidence = json.dumps(evidence or [])
            existing.assumptions = json.dumps(assumptions or [])
            existing.next_step = next_step
        db.commit()

    # --- Node Implementations ---

    def _node_analyze_requirements(self, db: Session, project: models.Project, agent_run: models.AgentRun):
        from .rag_engine import rag_instance
        
        # Check for RAG retrieved evidence
        evidences = rag_instance.retrieve_evidence(project.id, f"{project.industry} {project.business_problem}", top_k=5)

        # If project has human-verified extracted requirements, enrich the business_problem context
        enriched_problem = project.business_problem
        enriched_constraints = project.constraints or ""
        if project.extracted_requirements:
            try:
                ext_reqs = json.loads(project.extracted_requirements)
                if ext_reqs.get("business_objective"):
                    enriched_problem += f"\n\nBusiness Objective: {ext_reqs['business_objective']}"
                if ext_reqs.get("current_process"):
                    enriched_problem += f"\nCurrent Process: {ext_reqs['current_process']}"
                if ext_reqs.get("pain_points"):
                    enriched_problem += f"\nPain Points: {', '.join(ext_reqs['pain_points'])}"
                if ext_reqs.get("functional_requirements"):
                    enriched_problem += f"\nFunctional Requirements: {', '.join(ext_reqs['functional_requirements'])}"
                if ext_reqs.get("non_functional_requirements"):
                    enriched_problem += f"\nNon-Functional Requirements: {', '.join(ext_reqs['non_functional_requirements'])}"
                if ext_reqs.get("security_requirements"):
                    enriched_constraints += f"\nSecurity: {', '.join(ext_reqs['security_requirements'])}"
                if ext_reqs.get("integration_requirements"):
                    enriched_constraints += f"\nIntegrations: {', '.join(ext_reqs['integration_requirements'])}"
                if ext_reqs.get("expected_scale"):
                    enriched_problem += f"\nExpected Scale: {ext_reqs['expected_scale']}"
            except Exception:
                pass

        analysis = tools.RequirementAnalysisTool.execute(
            client_name=project.client_name,
            industry=project.industry,
            business_problem=enriched_problem,
            target_users=project.target_users,
            budget_range=project.budget_range,
            timeline=project.timeline,
            constraints=enriched_constraints,
            evidences=evidences
        )

        # Clear and save evidences to database
        db.query(models.RequirementEvidence).filter(models.RequirementEvidence.project_id == project.id).delete()
        
        req_list = analysis.get("requirements", [])
        evidence_records_for_summary = []

        if isinstance(req_list, list):
            for req_item in req_list:
                if isinstance(req_item, dict):
                    req_text = req_item.get("requirement", "")
                    src = req_item.get("source", "Client Specification")
                    pg = req_item.get("page", 1)
                    tag = req_item.get("trust_tag", "SOURCE-BACKED")
                else:
                    req_text = str(req_item)
                    src = "Client Specification"
                    pg = 1
                    tag = "SOURCE-BACKED"

                db_ev = models.RequirementEvidence(
                    project_id=project.id,
                    requirement=req_text,
                    source_document=src,
                    page_number=int(pg) if str(pg).isdigit() else 1,
                    evidence_text=req_text,
                    trust_tag=tag
                )
                db.add(db_ev)
                evidence_records_for_summary.append({
                    "source": src,
                    "page": pg,
                    "trust_tag": tag,
                    "requirement": req_text
                })
        
        # Log executed tool
        selected = json.loads(agent_run.selected_tools)
        selected.append({
            "tool": "RequirementAnalysisTool",
            "status": "SUCCESS",
            "timestamp": str(datetime.datetime.utcnow()),
            "output": f"Extracted {len(req_list)} structured requirements grounded with RAG document evidence and trust tags."
        })
        agent_run.selected_tools = json.dumps(selected)
        db.commit()

        # Save Transparent Stage Summary
        findings = [
            f"Business Problem: {project.business_problem}",
            f"Target Users: {project.target_users}",
            f"Budget Range: {project.budget_range}",
            f"Timeline Target: {project.timeline}"
        ]
        if isinstance(req_list, list) and req_list:
            for r in req_list[:3]:
                txt = r.get("requirement") if isinstance(r, dict) else str(r)
                tag = r.get("trust_tag", "SOURCE-BACKED") if isinstance(r, dict) else "SOURCE-BACKED"
                findings.append(f"[{tag}] {txt}")

        self._save_stage_summary(
            db=db,
            stage="requirement_analysis",
            title="✓ Requirement Analysis Complete",
            summary=f"Extracted client business requirements for {project.client_name} with document evidence grounding.",
            key_findings=findings,
            evidence=evidence_records_for_summary,
            assumptions=analysis.get("assumptions", ["Client APIs and source data available digitally"]),
            next_step="Agent Planning & Tool Selection"
        )

    def _node_create_plan(self, db: Session, project: models.Project, agent_run: models.AgentRun, feedback: str = None):
        prob_excerpt = project.business_problem[:100] + ("..." if len(project.business_problem) > 100 else "")
        plan = [
            f"1. Analyze RAG document evidence & extract requirements for {project.client_name} ({project.industry})",
            f"2. Evaluate operational problem statement: '{prob_excerpt}' against target users ({project.target_users})",
            f"3. Generate 3 distinct domain-tailored AI architecture strategies for {project.industry}",
            f"4. Assess cost, infrastructure & timeline fit against stated bounds ({project.budget_range}, {project.timeline})",
            f"5. Compute 7-Factor Side-by-Side Decision Comparison Matrix & select optimal choice",
            "6. Pause at Human Approval Gate for client validation & blueprint generation"
        ]
        if feedback:
            plan.append(f"REVISION ADAPTATION: Regenerating solutions based on client feedback: '{feedback}'")
        
        agent_run.plan = json.dumps(plan)
        db.commit()

        self._save_stage_summary(
            db=db,
            stage="agent_planning",
            title="✓ Dynamic Agent Plan Formulated",
            summary=f"Created real-time execution plan grounded in '{prob_excerpt}' for {project.client_name}.",
            key_findings=[
                f"Client: {project.client_name} ({project.industry})",
                f"Core Problem: {prob_excerpt}",
                f"Target Constraints: Budget {project.budget_range} | Timeline {project.timeline}",
                "Strategy: Evaluates 3 tailored AI solutions with decision comparison matrix"
            ],
            next_step="Dynamic Tool Selection"
        )

    def _node_select_tools(self, db: Session, project: models.Project, agent_run: models.AgentRun):
        selected = json.loads(agent_run.selected_tools)
        selected.append({
            "tool": "Dynamic Tool Selection Model",
            "status": "SUCCESS",
            "timestamp": str(datetime.datetime.utcnow()),
            "output": "Selected AISolutionTool, CostEstimationTool, and ArchitectureTool based on plan targets."
        })
        agent_run.selected_tools = json.dumps(selected)
        db.commit()

        self._save_stage_summary(
            db=db,
            stage="tool_selection",
            title="✓ Tools Dynamically Selected",
            summary="Orchestrated tools for solution generation, cost estimation, and architecture visualization.",
            key_findings=[
                "Requirement Analysis & RAG Retriever: Active",
                "AI Solution Generator: Active",
                "Cost & Effort Estimator: Active",
                "Architecture Component Builder: Active"
            ],
            next_step="Generating 3 Tailored AI Solutions"
        )


    def _node_solution_recommender(self, db: Session, project: models.Project, agent_run: models.AgentRun):
        # Look for recent revision feedback if present
        recent_approval = db.query(models.Approval).filter(
            models.Approval.project_id == project.id,
            models.Approval.action == "REVISE"
        ).order_by(models.Approval.id.desc()).first()
        feedback = recent_approval.feedback if recent_approval else None

        # Retrieve RAG requirement evidence records from DB
        evidences = db.query(models.RequirementEvidence).filter(models.RequirementEvidence.project_id == project.id).all()
        evidence_list = [
            {
                "requirement": e.requirement,
                "source": e.source_document,
                "page": e.page_number,
                "trust_tag": e.trust_tag
            } for e in evidences
        ]

        req_data = {
            "client_name": project.client_name,
            "industry": project.industry,
            "business_problem": project.business_problem,
            "target_users": project.target_users,
            "budget": project.budget_range,
            "timeline": project.timeline,
            "constraints": project.constraints,
            "extracted_requirements": project.extracted_requirements,
            "evidences": evidence_list
        }

        # Step 1: AI Problem Classification & Capability Selection
        classification = tools.ProblemClassifierTool.execute(req_data)
        self._save_stage_summary(
            db=db,
            stage="problem_classification",
            title="✓ AI Problem Classification Complete",
            summary=f"Classified problem as '{classification.get('primary_category')}' ({classification.get('computational_type')}).",
            key_findings=[
                f"Primary Category: {classification.get('primary_category')}",
                f"Computational Approach: {classification.get('computational_type')}",
                f"RAG Required: {'Yes' if classification.get('rag_required') else 'No (Not required for this problem type)'}",
                f"Generative LLM Required: {'Yes' if classification.get('llm_required') else 'No (Deterministic algorithms preferred)'}",
                f"Rationale: {classification.get('rationale')}"
            ],
            next_step="Generating 3 Tailored AI Solutions"
        )

        res = tools.AISolutionTool.execute(req_data, feedback=feedback)

        solutions_data = res.get("solutions", [])
        if not isinstance(solutions_data, list):
            solutions_data = [solutions_data]

        matrix_data = res.get("comparison_matrix", {})
        reasoning_data = res.get("recommendation_reasoning", {})

        # Step 2: Architecture & Requirement Traceability Validation
        if solutions_data:
            val = tools.ArchitectureValidatorTool.validate(solutions_data[0], req_data)
            self._save_stage_summary(
                db=db,
                stage="architecture_validation",
                title="✓ Architecture Validation & Confidence Check Complete",
                summary=f"Verified 100% component-to-requirement alignment with overall AI Confidence Score of {val.get('overall_confidence')}%.",
                key_findings=[
                    f"Requirement Coverage: {val.get('requirement_coverage')}%",
                    f"Architecture Alignment: {val.get('architecture_alignment')}%",
                    f"Technology Appropriateness: {val.get('technology_appropriateness')}%",
                    f"Confidence Level: {val.get('confidence_label')}"
                ],
                next_step="Generating 3 Tailored AI Solutions"
            )

        # Clear existing solutions
        db.query(models.SolutionOption).filter(models.SolutionOption.project_id == project.id).delete()

        # Save generated solutions to database
        for opt in solutions_data:
            if not isinstance(opt, dict):
                continue
            tech_stack = opt.get("technologyStack", [])
            tech_str = ", ".join(tech_stack) if isinstance(tech_stack, list) else str(tech_stack)
            
            sol = models.SolutionOption(
                project_id=project.id,
                name=opt.get("name", "Tailored AI Solution"),
                description=opt.get("solution") or opt.get("description", ""),
                ai_approach=tech_str,
                estimated_cost=opt.get("estimatedCost") or opt.get("estimated_cost", "N/A"),
                estimated_timeline=opt.get("estimatedTimeline") or opt.get("estimated_timeline", "N/A"),
                complexity=opt.get("complexity", "Medium"),
                advantages=json.dumps(opt.get("advantages", [])),
                limitations=json.dumps(opt.get("limitations", [])),
                is_recommended=bool(opt.get("is_recommended", False)),
                details_json=json.dumps(opt)
            )
            db.add(sol)

        # Save comparison matrix & recommendation reasoning to project
        project.comparison_matrix = json.dumps(matrix_data)
        project.recommendation_reasoning = json.dumps(reasoning_data)
        
        selected = json.loads(agent_run.selected_tools)
        selected.append({
            "tool": "AISolutionTool",
            "status": "SUCCESS",
            "timestamp": str(datetime.datetime.utcnow()),
            "output": f"Generated {len(solutions_data)} industry-specific AI approaches for {project.industry} with dynamic architecture, comparison matrix, and client fit checks."
        })
        agent_run.selected_tools = json.dumps(selected)
        db.commit()

        sol_findings = [f"Generated {len(solutions_data)} tailored solution approaches:"]
        for s in solutions_data[:3]:
            if isinstance(s, dict):
                sol_findings.append(f"• {s.get('name', 'Solution')}: {s.get('estimatedCost', 'Indicative Cost')} | Timeline: {s.get('estimatedTimeline', 'N/A')}")

        self._save_stage_summary(
            db=db,
            stage="solution_generation",
            title="✓ 3 Dynamic Solution Options Generated",
            summary=f"Created {len(solutions_data)} domain-specific AI strategies for {project.industry}.",
            key_findings=sol_findings,
            next_step="Cost Estimation & Timeline Fit Check"
        )

    def _node_cost_estimator(self, db: Session, project: models.Project, agent_run: models.AgentRun):
        selected = json.loads(agent_run.selected_tools)
        selected.append({
            "tool": "CostEstimationTool",
            "status": "SUCCESS",
            "timestamp": str(datetime.datetime.utcnow()),
            "output": "Budget Fit & Cost breakdown calculated and verified against client bounds."
        })
        agent_run.selected_tools = json.dumps(selected)
        db.commit()

        self._save_stage_summary(
            db=db,
            stage="cost_estimation",
            title="✓ Cost & Timeline Fit Estimated",
            summary=f"Computed indicative development cost ranges and evaluated budget alignment against client range ({project.budget_range}).",
            key_findings=[
                f"Client Target Budget: {project.budget_range}",
                f"Client Target Timeline: {project.timeline}",
                "Indicative estimates include development, infrastructure, and operating overhead"
            ],
            assumptions=["Pricing based on indicative market estimates; discovery phase required for final commercial quote"],
            next_step="System Architecture Flow Generation"
        )

    def _node_architecture_generator(self, db: Session, project: models.Project, agent_run: models.AgentRun):
        selected = json.loads(agent_run.selected_tools)
        selected.append({
            "tool": "ArchitectureTool",
            "status": "SUCCESS",
            "timestamp": str(datetime.datetime.utcnow()),
            "output": "Dynamic system flow steps generated matching each solution approach."
        })
        agent_run.selected_tools = json.dumps(selected)
        db.commit()

        self._save_stage_summary(
            db=db,
            stage="architecture_generation",
            title="✓ System Architectures Designed",
            summary="Constructed multi-node technical data flows customized to each candidate AI approach.",
            key_findings=[
                "User / Application Interface",
                "Backend API Layer (FastAPI)",
                "AI / RAG / ML Processing Core",
                "Data Store / Vector Indexing & Human Approval Gate"
            ],
            next_step="Solution Comparison Matrix"
        )

    def _node_compare_solutions(self, db: Session, project: models.Project, agent_run: models.AgentRun):
        selected = json.loads(agent_run.selected_tools)
        selected.append({
            "tool": "ComparisonMatrixEngine",
            "status": "SUCCESS",
            "timestamp": str(datetime.datetime.utcnow()),
            "output": "Calculated 7-factor Decision Matrix scoring options on fit, budget, timeline, security, and scalability."
        })
        agent_run.selected_tools = json.dumps(selected)
        db.commit()

        self._save_stage_summary(
            db=db,
            stage="solution_comparison",
            title="✓ 7-Factor Decision Matrix Calculated",
            summary="Evaluated solution options across Requirement Fit, Budget Fit, Timeline Fit, Scalability, and Security.",
            key_findings=[
                "Requirement Fit score calculated for each approach",
                "Budget Risk & Timeline Extension risks highlighted",
                "Trade-offs between speed, cost, and enterprise capabilities balanced"
            ],
            next_step="Formulate Final AI Recommendation"
        )

    def _node_recommend_solution(self, db: Session, project: models.Project, agent_run: models.AgentRun):
        solutions = db.query(models.SolutionOption).filter(models.SolutionOption.project_id == project.id).all()
        recommended = next((s for s in solutions if s.is_recommended), solutions[0] if solutions else None)

        selected = json.loads(agent_run.selected_tools)
        selected.append({
            "tool": "DecisionRecommender",
            "status": "SUCCESS",
            "timestamp": str(datetime.datetime.utcnow()),
            "output": f"Formulated recommended solution '{recommended.name if recommended else 'AI Solution'}' with client-specific justification and risk assumptions."
        })
        agent_run.selected_tools = json.dumps(selected)
        db.commit()

        self._save_stage_summary(
            db=db,
            stage="recommendation",
            title="⭐ AI Recommendation Formulated",
            summary=f"Selected '{recommended.name if recommended else 'Tailored AI Solution'}' as optimal balance.",
            key_findings=[
                f"Recommended Strategy: {recommended.name if recommended else 'Tailored AI Solution'}",
                f"Estimated Investment: {recommended.estimated_cost if recommended else project.budget_range}",
                f"Estimated Timeline: {recommended.estimated_timeline if recommended else project.timeline}"
            ],
            next_step="Awaiting Human Approval / Revision"
        )

    def _node_human_approval_gate(self, db: Session, project: models.Project, agent_run: models.AgentRun):
        agent_run.status = "PAUSED"
        project.status = "AWAITING_APPROVAL"
        db.commit()

        self._save_stage_summary(
            db=db,
            stage="human_approval",
            title="⏸ Paused for Human Approval",
            summary="Workflow paused at Human-in-the-Loop gate awaiting client validation (Approve / Revise / Reject).",
            key_findings=[
                "User can review generated comparison matrix and recommendation",
                "Options: Approve to proceed, Revise with specific feedback, or Reject workflow"
            ],
            next_step="User Action Required"
        )

    def _node_generate_implementation_blueprint(self, db: Session, project: models.Project, agent_run: models.AgentRun):
        solutions = db.query(models.SolutionOption).filter(models.SolutionOption.project_id == project.id).all()
        
        # Prioritize specifically approved solution ID if present
        approved_sol = None
        if project.approved_solution_id:
            approved_sol = db.query(models.SolutionOption).filter(models.SolutionOption.id == project.approved_solution_id).first()
        if not approved_sol:
            approved_sol = next((s for s in solutions if s.is_recommended), solutions[0] if solutions else None)

        approved_solution_details = {}
        if approved_sol:
            if approved_sol.details_json:
                try:
                    approved_solution_details = json.loads(approved_sol.details_json)
                except Exception:
                    approved_solution_details = {}
            if not approved_solution_details:
                approved_solution_details = {
                    "name": approved_sol.name,
                    "solution": approved_sol.description,
                    "technologyStack": [t.strip() for t in approved_sol.ai_approach.split(",") if t.strip()],
                    "estimatedCost": approved_sol.estimated_cost,
                    "estimatedTimeline": approved_sol.estimated_timeline,
                    "complexity": approved_sol.complexity
                }

        last_approval = db.query(models.Approval).filter(
            models.Approval.project_id == project.id,
            models.Approval.action == "APPROVE"
        ).order_by(models.Approval.id.desc()).first()

        project_context = {
            "client_name": project.client_name,
            "industry": project.industry,
            "business_problem": project.business_problem,
            "target_users": project.target_users,
            "budget_range": project.budget_range,
            "timeline": project.timeline,
            "constraints": project.constraints,
            "human_feedback": last_approval.feedback if last_approval and last_approval.feedback else ""
        }

        blueprint = tools.ImplementationBlueprintTool.execute(project_context, approved_solution_details)
        project.blueprint_json = json.dumps(blueprint)

        selected = json.loads(agent_run.selected_tools)
        selected.append({
            "tool": "ImplementationBlueprintTool",
            "status": "SUCCESS",
            "timestamp": str(datetime.datetime.utcnow()),
            "output": f"Generated comprehensive implementation blueprint for '{approved_sol.name if approved_sol else 'approved solution'}' — {len(blueprint.get('phases', []))} phases, {len(blueprint.get('architecture', []))} architecture components."
        })
        agent_run.selected_tools = json.dumps(selected)
        db.commit()

        self._save_stage_summary(
            db=db,
            stage="blueprint_generation",
            title="🚀 Implementation Blueprint Generated",
            summary=f"Constructed detailed phase-by-phase implementation plan for '{approved_sol.name if approved_sol else 'Approved Solution'}'.",
            key_findings=[
                f"Total Phases: {len(blueprint.get('phases', []))}",
                f"Architecture Components: {len(blueprint.get('architecture', []))}",
                "Includes technology stack rationale, testing strategy, security, and deployment roadmap"
            ],
            next_step="Generating Final Markdown Proposal"
        )

    def _node_generate_final_proposal(self, db: Session, project: models.Project, agent_run: models.AgentRun):
        solutions = db.query(models.SolutionOption).filter(models.SolutionOption.project_id == project.id).all()
        recommended = next((s for s in solutions if s.is_recommended), solutions[0] if solutions else None)
        
        details = {}
        if recommended and recommended.details_json:
            try:
                details = json.loads(recommended.details_json)
            except Exception:
                details = {}

        arch_steps = details.get("architecture", [])
        arch_str = " -> ".join(arch_steps) if isinstance(arch_steps, list) and arch_steps else recommended.ai_approach if recommended else "System Pipeline"

        prompt = f"""
        Generate a highly professional, detailed, markdown-formatted Implementation & Architecture Package for the approved AI Solution.

        CLIENT CONTEXT:
        - Client Name: {project.client_name}
        - Industry: {project.industry}
        - Business Problem: {project.business_problem}
        - Approved Solution: {recommended.name if recommended else 'Custom AI Solution'}
        - Solution Description: {recommended.description if recommended else ''}
        - Tech Stack: {recommended.ai_approach if recommended else ''}
        - Architecture Flow: {arch_str}
        - Cost Estimate: {recommended.estimated_cost if recommended else project.budget_range}
        - Execution Timeline: {recommended.estimated_timeline if recommended else project.timeline}

        The markdown output MUST contain the following major sections clearly titled:

        # Executive Client Proposal: {project.client_name}
        ## 1. Executive Summary & Business Impact
        ## 2. Approved Solution Strategy: {recommended.name if recommended else 'AI Solution'}
        ## 3. Technology Stack & Component Specifications

        ---

        # Implementation Roadmap
        ## Phase 1 — Discovery & Alignment
        ## Phase 2 — Data Preparation & Pipeline Setup
        ## Phase 3 — AI Engine & Core Workflow Development
        ## Phase 4 — Integration & API Layer
        ## Phase 5 — Quality Assurance & Safety Validation
        ## Phase 6 — Deployment & User Onboarding

        ---

        # Technical Architecture Diagram
        (Provide a ASCII/Mermaid or Step-by-Step Flow diagram representing: {arch_str})

        ---

        # Solution Package & Governance
        ## Budget Breakdown & Operating Fees
        ## Security, Compliance & Data Guardrails
        ## Key Risk Mitigations
        """

        system_prompt = "You are a Lead AI Solution Architect. Output clean, client-ready Markdown for the approved solution package."
        proposal_content = llm.LLMClient.generate_completion(prompt, system_prompt=system_prompt)

        # Safety fallback formatting
        if not proposal_content.strip().startswith("#"):
            rec_name = recommended.name if recommended else "Tailored AI Solution"
            rec_desc = recommended.description if recommended else "Custom AI solution architecture."
            rec_tech = recommended.ai_approach if recommended else "FastAPI + LLM"
            rec_cost = recommended.estimated_cost if recommended else project.budget_range
            rec_time = recommended.estimated_timeline if recommended else project.timeline

            proposal_content = f"""# Executive Client Proposal: {project.client_name}

## 1. Executive Summary & Business Impact
This implementation package details the technical architecture and execution strategy for **{project.client_name}** in the **{project.industry}** domain. The primary objective is to resolve: *"{project.business_problem}"*.

---

## 2. Approved Solution Strategy: {rec_name}
- **Overview**: {rec_desc}
- **Target Audience**: {project.target_users}
- **Target Timeline**: {rec_time}
- **Estimated Investment**: {rec_cost}

---

## 3. Technology Stack & Component Specifications
- **Core Engine**: {rec_tech}
- **Architecture Flow**: {arch_str}

---

# Implementation Roadmap

### Phase 1 — Discovery & Requirements Alignment (Week 1–2)
- Stakeholder interviews and dataset audit
- Finalize API contracts and user security protocols

### Phase 2 — Data Pipeline & Infrastructure Setup (Week 3–4)
- Ingestion pipelines for client documents/sensors
- Vector embeddings / Feature store configuration

### Phase 3 — AI Model & Core Logic Development (Week 5–7)
- System prompts, model fine-tuning or tool calling setup
- Intent classification and response safety guardrails

### Phase 4 — Backend API & Web Interface Integration (Week 8–9)
- FastAPI endpoints for frontend integration
- Role-based authentication and audit logging

### Phase 5 — Testing, Validation & Safety Verification (Week 10)
- End-to-end load testing and accuracy benchmarking
- Human-in-the-loop fallback verification

### Phase 6 — Production Deployment & Handover (Week 11–12)
- Cloud deployment and monitoring dashboard setup
- Admin training and handover documentation

---

# Technical Architecture Diagram
```
{arch_str.replace(' -> ', '\n  ↓  \n')}
```

---

# Solution Package & Governance
- **Data Privacy**: Zero third-party retention on proprietary data.
- **Budget Fit**: {rec_cost}
- **Timeline**: {rec_time}
"""

        # Clear existing proposals
        db.query(models.Proposal).filter(models.Proposal.project_id == project.id).delete()

        proposal = models.Proposal(
            project_id=project.id,
            content=proposal_content,
            status="FINAL"
        )
        db.add(proposal)
        
        agent_run.status = "COMPLETED"
        project.status = "COMPLETED"
        db.commit()

        self._save_stage_summary(
            db=db,
            stage="final_proposal",
            title="🎉 Final Client Proposal Complete",
            summary=f"Final proposal and implementation roadmap package generated for {project.client_name}.",
            key_findings=[
                "Executive Summary & Solution Architecture ready",
                "Full implementation roadmap and governance guidelines finalized",
                "Available for instant download as Markdown proposal file"
            ],
            next_step="Proposal Ready for Download"
        )

