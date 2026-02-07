"""
Sue (Compliance Specialist) Agent Implementation
Reviews for regulatory compliance and policy adherence
"""

from langgraph.graph import StateGraph, END

from backend.agents.base.agent_interface import (
    BaseAgent,
    AgentMetadata,
    AgentExecutionContext,
    AgentExecutionResult,
)
from backend.agents.specialized.agent_b.state import ComplianceAgentState


async def load_policies_node(state: ComplianceAgentState) -> dict:
    """
    Identify relevant policies based on query
    TODO: Load from policy database in production
    """
    query_lower = state["query"].lower()

    policies = []
    if "gdpr" in query_lower or "personal data" in query_lower or "privacy" in query_lower:
        policies.append("GDPR")

    if "hipaa" in query_lower or "health" in query_lower:
        policies.append("HIPAA")

    if "pci" in query_lower or "payment" in query_lower or "credit card" in query_lower:
        policies.append("PCI-DSS")

    if not policies:
        policies.append("General Data Protection")

    return {
        **state,
        "policies_to_check": policies,
        "current_step": "policies_loaded",
    }


async def analyze_compliance_node(state: ComplianceAgentState) -> dict:
    """
    Analyze for compliance issues
    TODO: Use LLM + policy rules in production
    """
    query = state["query"]
    issues = []

    # Placeholder compliance checks
    if "personal data" in query.lower():
        issues.append({
            "severity": "medium",
            "issue": "Personal data collection detected",
            "policy": "GDPR",
        })

    if "consent" not in query.lower() and "personal data" in query.lower():
        issues.append({
            "severity": "high",
            "issue": "No consent mechanism mentioned",
            "policy": "GDPR Article 7",
        })

    return {
        **state,
        "compliance_issues": issues,
        "current_step": "analyzed",
    }


async def assess_risk_node(state: ComplianceAgentState) -> dict:
    """
    Assess overall compliance risk level
    """
    issues = state["compliance_issues"]

    if not issues:
        risk_level = "low"
    elif any(issue["severity"] == "high" for issue in issues):
        risk_level = "high"
    elif any(issue["severity"] == "medium" for issue in issues):
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        **state,
        "risk_level": risk_level,
        "current_step": "risk_assessed",
    }


async def recommend_node(state: ComplianceAgentState) -> dict:
    """
    Generate compliance recommendations
    """
    recommendations = []

    for issue in state["compliance_issues"]:
        if issue["issue"] == "No consent mechanism mentioned":
            recommendations.append(
                "Implement explicit user consent mechanism before collecting personal data"
            )
        elif issue["issue"] == "Personal data collection detected":
            recommendations.append(
                "Ensure data minimization principle - only collect necessary data"
            )
            recommendations.append("Implement appropriate security measures for data storage")

    if state["risk_level"] == "high":
        recommendations.append("⚠️ Consult legal team before proceeding")

    return {
        **state,
        "recommendations": recommendations,
        "current_step": "recommendations_generated",
    }


async def finalize_review_node(state: ComplianceAgentState) -> dict:
    """
    Create final compliance review response
    """
    response_parts = []

    # Header
    response_parts.append(f"**Compliance Review** (Risk Level: {state['risk_level'].upper()})\n")

    # Policies checked
    response_parts.append(f"**Policies Reviewed:** {', '.join(state['policies_to_check'])}\n")

    # Issues
    if state["compliance_issues"]:
        response_parts.append("**Issues Found:**")
        for i, issue in enumerate(state["compliance_issues"], 1):
            response_parts.append(
                f"{i}. [{issue['severity'].upper()}] {issue['issue']} ({issue['policy']})"
            )
        response_parts.append("")
    else:
        response_parts.append("✅ No compliance issues detected\n")

    # Recommendations
    if state["recommendations"]:
        response_parts.append("**Recommendations:**")
        for i, rec in enumerate(state["recommendations"], 1):
            response_parts.append(f"{i}. {rec}")

    final_response = "\n".join(response_parts)

    return {
        **state,
        "final_response": final_response,
        "current_step": "completed",
    }


class ComplianceAgent(BaseAgent):
    """
    Sue - Compliance Specialist
    Reviews for regulatory compliance and policy adherence
    """

    def __init__(self):
        metadata = AgentMetadata(
            id="agent_b",
            nickname="sue",
            specialization="Compliance Specialist",
            description="Reviews for regulatory compliance and policy adherence",
        )
        super().__init__(metadata)

    def create_graph(self) -> StateGraph:
        """
        Create compliance review graph

        Flow:
        load_policies → analyze → assess_risk → recommend → finalize → END
        """
        graph = StateGraph(ComplianceAgentState)

        # Add nodes
        graph.add_node("load_policies", load_policies_node)
        graph.add_node("analyze", analyze_compliance_node)
        graph.add_node("assess_risk", assess_risk_node)
        graph.add_node("recommend", recommend_node)
        graph.add_node("finalize", finalize_review_node)

        # Define flow
        graph.set_entry_point("load_policies")
        graph.add_edge("load_policies", "analyze")
        graph.add_edge("analyze", "assess_risk")
        graph.add_edge("assess_risk", "recommend")
        graph.add_edge("recommend", "finalize")
        graph.add_edge("finalize", END)

        # TODO: Fix checkpointer implementation - disabled for MVP
        return graph.compile(checkpointer=None)

    async def _execute_graph(
        self,
        command: str,
        context: AgentExecutionContext,
    ) -> AgentExecutionResult:
        """Execute Sue's compliance review graph"""
        initial_state: ComplianceAgentState = {
            "query": command,
            "user_id": context.user_id,
            "thread_id": context.thread_id,
            "conversation_context": (
                context.conversation_context.model_dump()
                if context.conversation_context
                else {}
            ),
            "policies_to_check": [],
            "compliance_issues": [],
            "recommendations": [],
            "final_response": None,
            "error": None,
            "current_step": "starting",
            "risk_level": None,
            "model_config": self.model_config,
        }

        # Build config with execution tracker callbacks
        config = self._build_graph_config(context)

        try:
            final_state = await self.graph.ainvoke(initial_state, config)

            return AgentExecutionResult(
                success=True,
                response=final_state.get("final_response", "Compliance review completed"),
                final_state=final_state,
                metadata={
                    "risk_level": final_state.get("risk_level"),
                    "issues_count": len(final_state.get("compliance_issues", [])),
                    "policies_checked": final_state.get("policies_to_check", []),
                },
            )

        except Exception as e:
            return AgentExecutionResult(
                success=False,
                response="",
                error=f"Compliance review failed: {str(e)}",
            )
