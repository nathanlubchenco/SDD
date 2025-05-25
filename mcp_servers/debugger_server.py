from typing import Dict
from mcp.server import MCPServer, Tool


class DebuggerMCPServer(MCPServer):
    """MCP Server for behavior-centric debugging"""

    @Tool(
        name="analyze_incident",
        description="Analyze an incident and provide human-readable explanation"
    )
    async def analyze_incident(self, incident_id: str) -> Dict:
        """AI analyzes an incident and provides a human-readable explanation"""
        # Gather relevant diagnostic data
        logs = self.fetch_logs(incident_id)
        metrics = self.fetch_metrics(incident_id)
        traces = self.fetch_traces(incident_id)

        prompt = f"""
Incident: {incident_id}
Logs: {logs}
Metrics: {metrics}
Traces: {traces}

Analyze and explain:
1. Which scenario/constraint was violated?
2. What was the expected behavior?
3. What actually happened?
4. Root cause hypothesis (top 3 most likely)
5. What data would confirm/refute each hypothesis?
6. Suggested remediation steps

Explain in terms of business behavior, not implementation.
"""
        return self.ai_analyze(prompt)