from . import eden_tool, JsonContent


@eden_tool()
def agent_ping(agent_name: str):
    """
    Test hook for agent-level tools.
    """
    return [JsonContent(type="json", data={
        "agent": agent_name,
        "status": "acknowledged",
        "message": f"{agent_name} is reachable through MCP."
    })]
