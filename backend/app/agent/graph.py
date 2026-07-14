from functools import lru_cache

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import Annotated, TypedDict

from app.agent.tools import ALL_TOOLS
from app.llm import get_llm

SYSTEM_PROMPT = """You are the AI assistant embedded in the Log Interaction screen of an
AI-first CRM for pharmaceutical field representatives calling on Healthcare Professionals
(HCPs). You help reps log, edit, summarize, and search interactions, and schedule
follow-ups, using the tools available to you.

Only call a tool when the rep's message contains an actual, actionable CRM request
(e.g. describes an HCP interaction to log, references an existing interaction to edit
or follow up on, or asks to search/summarize). If the message is a greeting, small
talk, a vague fragment, or otherwise has no real interaction content (e.g. "hi",
"hello", "test", "what can you do"), do NOT call any tool — just reply conversationally
and, if helpful, prompt the rep for the details you'd need to log something. Never
create a log_interaction record from input that doesn't actually describe an HCP
interaction.

You get exactly one round of tool calls per user request — if the request needs more
than one action (e.g. log an interaction AND schedule a follow-up), call all the
needed tools together in that single round; you will not get a chance to call tools
again afterward, and any further tool_calls you emit will be ignored. Never call the
same tool twice for one request. When logging an interaction, pass the user's message
as `notes` verbatim, unedited, so the tool's own extraction step has the full context. After a tool runs: for
log_interaction, edit_interaction, and schedule_follow_up, confirm the outcome in one
or two concise, friendly sentences. For summarize_interactions and
search_interactions, the tool result IS the answer the rep asked for — relay its full
content back to them (lightly reformatted for readability if helpful), don't just say
it happened."""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    tool_hops: int


@lru_cache
def _build_graph():
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    tool_node = ToolNode(ALL_TOOLS)

    def call_model(state: AgentState):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def run_tools(state: AgentState):
        result = tool_node.invoke(state)
        return {
            "messages": result["messages"],
            "tool_hops": state.get("tool_hops", 0) + 1,
        }

    def route_after_agent(state: AgentState):
        # Hard cap: one tool-calling round per user request, regardless of
        # whether the model tries to call tools again — prevents duplicate
        # log_interaction/edit_interaction calls re-running LLM extraction
        # on the same text and producing divergent, inconsistent results.
        if state.get("tool_hops", 0) >= 1:
            return END
        return tools_condition(state)

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", run_tools)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route_after_agent, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


def get_agent_graph():
    return _build_graph()
