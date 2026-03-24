"""
Dynamic Tool Agent — Interactive CLI
=====================================
Kullanıcıdan girdi alır, LangGraph agent'ını çalıştırır ve sonucu basar.
Çıkmak için 'q' veya 'exit' yazın.
"""

from agent import agent, AgentState


def run(user_input: str) -> AgentState:
    """Agent'ı verilen girdiyle çalıştır ve state'i döndür."""
    initial: AgentState = {
        "user_input": user_input,
        "search_query": "",
        "found_tools": [],
        "selected_tool": None,
        "tool_params": {},
        "tool_result": None,
        "final_response": "",
        "error": None,
        "sub_tasks": [],
        "current_step": 0,
        "step_results": [],
    }
    return agent.invoke(initial)


def main() -> None:
    print("=" * 60)
    print("  Dynamic Tool Agent — Zero-Knowledge LangGraph")
    print("  Çıkmak için 'q' veya 'exit' yazın.")
    print("=" * 60)

    while True:
        user_input = input("\n🧑 Sen: ").strip()
        if not user_input or user_input.lower() in ("q", "exit", "quit"):
            print("Görüşmek üzere! 👋")
            break

        result = run(user_input)
        print(f"\n🤖 Agent: {result['final_response']}")


if __name__ == "__main__":
    main()
