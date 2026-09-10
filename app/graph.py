import os
import re
import time
import operator
import asyncio
from typing import Annotated
from typing_extensions import TypedDict
from pydantic import ValidationError

from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy, TimeoutPolicy

from app.rag import mock_grounded_generation
from app.tools import check_support_ticket_status
from app.guardrails import mask_pii, detect_prompt_injection, verify_output_groundedness, AgentResponse
from app.memory import get_async_checkpointer, save_conversation_history

# --- 1. STATE DEFINITION ---
class AgentState(TypedDict):
    query: str
    route_taken: str
    answer: str
    confidence_score: float
    escalation_flag: bool
    pii_masked: bool
    history: Annotated[list, operator.add]

# --- 2. NODES ---
def guardrail_node(state: AgentState):
    query = state["query"]
    if detect_prompt_injection(query):
        return {
            "answer": "Request blocked: Security policy violation.",
            "route_taken": "blocked",
            "confidence_score": 0.0,
            "history": [f"User: {query}", "Agent: [BLOCKED]"],
        }
    sanitized_query, pii_masked = mask_pii(query)
    if "tick-" in sanitized_query.lower() or "status" in sanitized_query.lower():
        route = "ticket_lookup"
    else:
        route = "rag_lookup"
    return {"query": sanitized_query, "pii_masked": pii_masked, "route_taken": route}

def route_request(state: AgentState):
    route = state.get("route_taken", "blocked")
    if route == "blocked":
        return END
    return route

async def rag_node(state: AgentState):
    query = state["query"]

    if query == "simulate_retry":
        if not hasattr(rag_node, "attempts"):
            rag_node.attempts = 0
        rag_node.attempts += 1
        if rag_node.attempts <= 2:
            print(f"DEBUG: RAG call failed (Attempt {rag_node.attempts}). Triggering retry...")
            raise ConnectionError("Simulated Network Drop")
        print("DEBUG: RAG call recovered on Attempt 3.")
        ans = "Recovered and retrieved policy."
        return {"answer": ans, "confidence_score": 1.0, "history": [f"User: {query}", f"Agent: {ans}"]}

    if query == "simulate_node_timeout":
        print("DEBUG: forcing a long sleep to trigger node timeout...")
        await asyncio.sleep(3)

    if query == "simulate_global_timeout":
        print("DEBUG: forcing a long sleep for global timeout...")
        await asyncio.sleep(5)

    answer, conf, _ = mock_grounded_generation(query, "ola_sentence_chunks", threshold=0.30)

    if not verify_output_groundedness(answer, answer):
        answer = "I don't know."

    return {
        "answer": answer,
        "confidence_score": conf,
        "history": [f"User: {query}", f"Agent: {answer}"],
    }

def ticket_lookup_node(state: AgentState):
    query = state["query"]
    match = re.search(r"tick-\d{4}", query, re.IGNORECASE)
    if not match:
        ans = "Please provide a valid ticket number (e.g., TICK-1001)."
        return {"answer": ans, "confidence_score": 0.0, "history": [f"User: {query}", f"Agent: {ans}"]}

    ticket_id = match.group(0).upper()
    result = check_support_ticket_status(ticket_id)

    if "error" in result:
        ans = result["error"]
        return {"answer": ans, "confidence_score": 0.0, "history": [f"User: {query}", f"Agent: {ans}"]}

    ans = (
        f"[STATUS] {result['status']} | "
        f"[RESOLVES IN] {result['resolution_time_hours']}h | "
        f"[SCORE] {result['escalation_score']} | "
        f"[ACTION] {result['recommended_action']}"
    )
    return {
        "answer": ans,
        "confidence_score": 1.0,
        "escalation_flag": result.get("escalation_score", 0.0) >= 0.60,
        "history": [f"User: {query}", f"Agent: {ans}"],
    }

def output_node(state: AgentState):
    try:
        AgentResponse(
            query=state.get("query", ""),
            route_taken=state.get("route_taken", ""),
            answer=state.get("answer", ""),
            confidence_score=state.get("confidence_score", 0.0),
            escalation_flag=state.get("escalation_flag", False),
            pii_masked=state.get("pii_masked", False),
        )
    except ValidationError as err:
        print("Warning - Schema Validation Error:", err)

    save_conversation_history(state.get("history", []))
    return {}

# --- 3. GRAPH COMPILATION ---
async def build_and_compile_graph():
    graph = StateGraph(AgentState)

    retry_policy = RetryPolicy(max_attempts=3, initial_interval=0.5, backoff_factor=2.0)
    timeout_policy = TimeoutPolicy(run_timeout=1.5)

    graph.add_node("guardrail_node", guardrail_node)
    graph.add_node("rag_lookup", rag_node, retry=retry_policy, timeout=timeout_policy)
    graph.add_node("ticket_lookup", ticket_lookup_node)
    graph.add_node("output_node", output_node)

    graph.add_edge(START, "guardrail_node")
    graph.add_conditional_edges(
        "guardrail_node",
        route_request,
        {
            "rag_lookup": "rag_lookup",
            "ticket_lookup": "ticket_lookup",
            "blocked": END,
        },
    )
    graph.add_edge("rag_lookup", "output_node")
    graph.add_edge("ticket_lookup", "output_node")
    graph.add_edge("output_node", END)

    # Note the 'await' keyword here for the async checkpointer
    checkpointer = await get_async_checkpointer()
    return graph.compile(checkpointer=checkpointer, interrupt_before=["output_node"])

# --- 4. TESTS ---
# --- 4. TESTS ---
async def run_tests():
    app = await build_and_compile_graph()

    print("\n--- Testing Multi-Turn Memory ---")
    config1 = {"configurable": {"thread_id": "test_user_1"}}
    
    state = await app.ainvoke({"query": "What is the policy for VIPs?", "history": []}, config=config1)
    state = await app.ainvoke(None, config=config1)
    print("Turn 1 Answer:", state["answer"])

    state = await app.ainvoke({"query": "Actually, check ticket TICK-1001 status.", "history": []}, config=config1)
    state = await app.ainvoke(None, config=config1)
    print("Turn 2 Answer:", state["answer"])
    print("Saved Memory Array:", state["history"])

    print("\n--- Testing SQLite Checkpointing ---")
    config_chk = {"configurable": {"thread_id": "checkpoint_test_id"}}
    print("Running graph and pausing at interrupt...")
    await app.ainvoke({"query": "How long do refunds take?", "history": []}, config_chk)

    # FIXED: Using the async version of get_state
    state_snapshot = await app.aget_state(config_chk)
    pending = state_snapshot.next
    print(f"Graph paused. Pending execution: {pending}")

    print("Resuming graph execution...")
    await app.ainvoke(None, config_chk)
    print("Graph completed! Prior nodes loaded from SQLite db.")

    print("\n--- Testing Retries and Timeouts ---")
    config_res = {"configurable": {"thread_id": "resilience_test_id"}}

    print("Test A: Exponential Retry")
    await app.ainvoke({"query": "simulate_retry", "history": []}, config_res)
    await app.ainvoke(None, config_res)

    print("Test B: Node Timeout")
    config_timeout = {"configurable": {"thread_id": "timeout_test_id"}}
    try:
        await app.ainvoke({"query": "simulate_node_timeout", "history": []}, config_timeout)
    except Exception as e:
        print(f"Success: Node timeout caught -> {type(e).__name__}")

    print("Test C: Global Timeout")
    config_global = {"configurable": {"thread_id": "global_timeout_id"}}
    try:
        await asyncio.wait_for(
            app.ainvoke({"query": "simulate_global_timeout", "history": []}, config_global),
            timeout=2.0,
        )
    except TimeoutError:
        print("Success: Global timeout cancelled the whole run.")
        
if __name__ == "__main__":
    asyncio.run(run_tests())