"""
Zero-Knowledge LangGraph Agent
================================
Inspired by:
  - ToolReAGt  : sub-task decomposition before tool search
  - TIG        : inertial scoring inside ToolManager
  - AutoTools  : schema-only prompting (no hard-coded tool names in system prompt)

The agent NEVER knows tool names or schemas upfront.
Tool schemas are injected into the LLM context only at the moment they are needed.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from registry.tools import TOOL_EXECUTORS
from search import ToolManager, VectorStore
from registry import ToolRegistry
from registry.tools import TOOL_LIST
from logs.execution_logger import ExecutionLogger

load_dotenv()

# ── Infrastructure setup ──────────────────────────────────────────────────────

_registry = ToolRegistry()
for schema in TOOL_LIST:
    _registry.register(schema)

_vector_store = VectorStore()
_vector_store.index_tools(_registry.to_index_documents())

tool_manager = ToolManager(registry=_registry, vector_store=_vector_store)
execution_logger = ExecutionLogger()

_llm = ChatGroq(
    model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY", ""),
)


# ── State ─────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    user_input: str
    search_query: str           # tool search query for the current sub-task
    found_tools: list           # list[ToolSchema] returned by ToolManager
    selected_tool: Any          # ToolSchema | None
    tool_params: dict           # parameters filled by LLM
    tool_result: Any            # execute() output
    final_response: str         # response shown to user
    error: str | None           # error message

    # ToolReAGt extensions
    sub_tasks: list[dict]       # decomposed steps: [{step, description, search_query}]
    current_step: int           # index into sub_tasks
    step_results: list[dict]    # accumulated results from each executed step


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> Any:
    """
    Robustly extract the first JSON object/array from an LLM response.
    Handles markdown code fences and stray text before/after the JSON.
    """
    # Strip markdown fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    # Try bare JSON (object or array)
    for pattern in (r"\{.*\}", r"\[.*\]"):
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    raise ValueError(f"No valid JSON found in LLM response: {text[:200]}")


# ── Node 1: analyze_task (ToolReAGt decomposition) ───────────────────────────

def analyze_task(state: AgentState) -> AgentState:
    """
    ToolReAGt-inspired: decompose the user request into sub-tasks.
    Each sub-task gets its own search query.

    System prompt deliberately omits ANY tool name or schema.
    """
    system = SystemMessage(content=(
        "Sen bir görev analiz uzmanısın. "
        "Tool isimlerini veya schemalarını bilmiyorsun. "
        "Kullanıcı görevini analiz et.\n\n"
        "ÖNEMLİ KURALLAR:\n"
        "1. Sadece somut bir araç gerektiren işlemler için adım oluştur "
        "(hava durumu sorgulama, döviz çevirme, hesaplama, veritabanı, internet araması vb.).\n"
        "2. Eğer kullanıcının isteği sohbet, motivasyon, hal hatır sorma gibi "
        "bir işlem gerektirmeyen konuysa, SADECE boş liste döndür: {\"sub_tasks\": []}.\n"
        "3. Gereksiz yere internet araması adımı üretme. Her adım somut bir kullanıcı talebi olmalı."
    ))
    human = HumanMessage(content=(
        f"Kullanıcı görevi: {state['user_input']}\n\n"
        "Bu görev somut bir araç gerektiriyor mu?\n"
        "- Evetse: gereken adımları listele, her adım için tek cümlelik arama sorgusu yaz.\n"
        "- Hayırsa (sohbet, motivasyon, selamlaşma): boş liste döndür: {\"sub_tasks\": []}\n\n"
        "SADECE geçerli JSON döndür:\n"
        '{"sub_tasks": ['
        '{"step": 1, "description": "...", "search_query": "..."}'
        "]}"
    ))

    response = _llm.invoke([system, human])

    try:
        data = _extract_json(response.content)
        sub_tasks: list[dict] = data.get("sub_tasks", [])
    except (ValueError, KeyError):
        # Parse error fallback: treat the whole task as one step
        sub_tasks = [
            {
                "step": 1,
                "description": state["user_input"],
                "search_query": state["user_input"],
            }
        ]

    # LLM explicitly returned empty sub_tasks → no tool needed
    if not sub_tasks:
        return {
            **state,
            "sub_tasks": [],
            "current_step": 0,
            "search_query": "",
            "found_tools": [],
            "step_results": [],
            "error": "NO_TOOL_NEEDED",
        }

    first_query = sub_tasks[0]["search_query"]

    return {
        **state,
        "sub_tasks": sub_tasks,
        "current_step": 0,
        "search_query": first_query,
        "step_results": [],
        "error": None,
    }


# ── Node 2: search_tools ──────────────────────────────────────────────────────

def search_tools(state: AgentState) -> AgentState:
    """
    Use the current sub-task's search_query to find relevant tools via
    ToolManager's 3-stage hybrid search + LLM re-ranking.
    """
    step_idx = state.get("current_step", 0)
    sub_tasks = state.get("sub_tasks", [])

    # Determine query: prefer the sub-task's own query, fallback to state query
    if sub_tasks and step_idx < len(sub_tasks):
        query = sub_tasks[step_idx]["search_query"]
    else:
        query = state["search_query"]

    found = tool_manager.search_and_rerank(query)

    return {**state, "found_tools": found, "search_query": query}


# ── Conditional edge: check_tools ────────────────────────────────────────────

def check_tools(state: AgentState) -> str:
    """Route to tool selection or no-tool handler."""
    return "select_tool" if state.get("found_tools") else "no_tool"


# ── Node 3: select_and_prepare ────────────────────────────────────────────────

def select_and_prepare(state: AgentState) -> AgentState:
    """
    Pick the top-ranked tool and ask the LLM to fill its parameters.
    The schema JSON is injected here — NOT in the initial system prompt.
    """
    selected = state["found_tools"][0]

    schema_json = selected.model_dump_json(indent=2)

    system = SystemMessage(content=(
        "Sana bir tool schema'sı veriyorum. "
        "Kullanıcının isteğine göre parametreleri doldur. "
        "Sadece parametreler için geçerli bir JSON nesnesi döndür."
    ))
    human = HumanMessage(content=(
        f"Kullanıcı: {state['user_input']}\n\n"
        f"Tool Schema:\n{schema_json}\n\n"
        "Parametreleri doldur. SADECE JSON döndür, başka bir şey değil."
    ))

    response = _llm.invoke([system, human])

    try:
        params = _extract_json(response.content)
        if not isinstance(params, dict):
            raise ValueError("Expected a JSON object for params")
    except (ValueError, KeyError):
        params = {}

    return {**state, "selected_tool": selected, "tool_params": params}


# ── Node 4: execute_tool ──────────────────────────────────────────────────────

def execute_tool(state: AgentState) -> AgentState:
    """
    Call the concrete executor for the selected tool.
    Also tracks latency and updates TIG inertial statistics via logger.
    """
    trace_id = execution_logger.start_trace(state.get("user_input", ""))
    
    selected = state["selected_tool"]
    if selected is None:
        state["error"] = "NO_TOOL_SELECTED"
        execution_logger.finish_trace(trace_id, state)
        return {**state, "tool_result": None}

    executor = TOOL_EXECUTORS.get(selected.name)
    if executor is None:
        state["error"] = f"NO_EXECUTOR: {selected.name}"
        execution_logger.finish_trace(trace_id, state)
        return {**state, "tool_result": None}

    try:
        result = executor(state["tool_params"])
        state["error"] = None
        state["tool_result"] = result
        
        # Accumulate step result
        step_results = list(state.get("step_results", []))
        step_idx = state.get("current_step", 0)
        sub_tasks = state.get("sub_tasks", [])
        step_desc = sub_tasks[step_idx]["description"] if step_idx < len(sub_tasks) else ""
        step_results.append({
            "step": step_idx + 1,
            "description": step_desc,
            "tool": selected.name,
            "result": result,
        })
        state["step_results"] = step_results

    except Exception as exc:  # noqa: BLE001
        state["error"] = f"EXECUTION_ERROR: {exc}"
        state["tool_result"] = None

    execution_logger.finish_trace(trace_id, state, tool_manager)
    return state


# ── Conditional edge: step_check ─────────────────────────────────────────────

def step_check(state: AgentState) -> str:
    """
    Decide whether to continue to the next sub-task or finalize.
    Advances current_step and updates search_query for the next iteration.
    """
    current = state.get("current_step", 0)
    sub_tasks = state.get("sub_tasks", [])
    next_step = current + 1

    if next_step < len(sub_tasks):
        return "more_steps"
    return "done"


def _advance_step(state: AgentState) -> AgentState:
    """Helper node: increment current_step and set next search_query."""
    current = state.get("current_step", 0)
    sub_tasks = state.get("sub_tasks", [])
    next_step = current + 1
    next_query = sub_tasks[next_step]["search_query"] if next_step < len(sub_tasks) else ""
    return {**state, "current_step": next_step, "search_query": next_query}


# ── Node 5: format_response ───────────────────────────────────────────────────

def format_response(state: AgentState) -> AgentState:
    """
    Synthesize all step results into a final natural-language response.
    """
    step_results = state.get("step_results", [])

    if step_results:
        results_text = "\n\n".join(
            f"Adım {r['step']} ({r['description']}):\n{json.dumps(r['result'], ensure_ascii=False, indent=2)}"
            for r in step_results
        )
    else:
        results_text = json.dumps(state.get("tool_result", {}), ensure_ascii=False, indent=2)

    system = SystemMessage(content=(
        "Sen yardımsever bir asistansın. "
        "Kullanıcıya doğal ve anlaşılır bir Türkçe yanıt ver."
    ))
    human = HumanMessage(content=(
        f"Kullanıcı: {state['user_input']}\n\n"
        f"Tool çıktıları:\n{results_text}\n\n"
        "Kullanıcıya öz ve doğal dilde yanıt ver."
    ))

    response = _llm.invoke([system, human])

    return {**state, "final_response": response.content}


# ── Node 6: handle_no_tool ────────────────────────────────────────────────────

def handle_no_tool(state: AgentState) -> AgentState:
    """Gracefully inform the user that no matching tool was found and log the interaction."""
    trace_id = execution_logger.start_trace(state.get("user_input", ""))
    new_state = {
        **state,
        "final_response": "Bu işlem için sistemde uygun bir araç bulunamadı.",
        "error": state.get("error") or "NO_TOOL_FOUND",
    }
    execution_logger.finish_trace(trace_id, new_state)
    return new_state


# ── Graph assembly ────────────────────────────────────────────────────────────

def _build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    # Nodes
    g.add_node("analyze_task", analyze_task)
    g.add_node("search_tools", search_tools)
    g.add_node("select_and_prepare", select_and_prepare)
    g.add_node("execute_tool", execute_tool)
    g.add_node("advance_step", _advance_step)
    g.add_node("format_response", format_response)
    g.add_node("handle_no_tool", handle_no_tool)

    # Edges
    g.add_edge(START, "analyze_task")

    # After analysis: if no tool needed → handle directly, else → search
    g.add_conditional_edges(
        "analyze_task",
        lambda s: "no_tool" if s.get("error") == "NO_TOOL_NEEDED" else "search",
        {
            "no_tool": "handle_no_tool",
            "search": "search_tools",
        },
    )

    g.add_conditional_edges(
        "search_tools",
        check_tools,
        {
            "select_tool": "select_and_prepare",
            "no_tool": "handle_no_tool",
        },
    )

    g.add_edge("select_and_prepare", "execute_tool")

    # ToolReAGt loop: after execution decide to loop or finish
    g.add_conditional_edges(
        "execute_tool",
        step_check,
        {
            "more_steps": "advance_step",
            "done": "format_response",
        },
    )

    # Loop back to search_tools for the next sub-task
    g.add_edge("advance_step", "search_tools")

    g.add_edge("format_response", END)
    g.add_edge("handle_no_tool", END)

    return g


# Public interface
agent = _build_graph().compile()

__all__ = ["agent", "AgentState", "tool_manager"]
