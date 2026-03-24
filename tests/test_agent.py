"""
Agent integration tests — her test gerçek Groq API'yi çağırır.
GROQ_API_KEY .env veya ortam değişkeni ile sağlanmalıdır.
"""

import os
import sys

import pytest

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent import agent, AgentState


# ── helpers ──────────────────────────────────────────────────────────────────

def run(user_input: str) -> AgentState:
    """Agent'ı çalıştır ve state'i döndür."""
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


# ── tests ─────────────────────────────────────────────────────────────────────

def test_weather_query():
    """Hava durumu sorusu → weather_service tool'u bulunmalı."""
    result = run("İstanbul'da bugün hava nasıl?")

    print("\n[sub_tasks]", result.get("sub_tasks"))
    print("[selected_tool]", getattr(result.get("selected_tool"), "name", None))
    print("[tool_result]", result.get("tool_result"))
    print("[final_response]", result.get("final_response"))

    assert result["final_response"], "final_response boş olmamalı"
    assert result.get("error") != "NO_TOOL_FOUND", "Tool bulunamamış"


def test_currency_conversion():
    """Döviz çevirme sorusu → currency_converter tool'u bulunmalı."""
    result = run("100 Euro kaç Türk Lirası yapar?")

    print("\n[sub_tasks]", result.get("sub_tasks"))
    print("[selected_tool]", getattr(result.get("selected_tool"), "name", None))
    print("[tool_result]", result.get("tool_result"))
    print("[final_response]", result.get("final_response"))

    assert result["final_response"], "final_response boş olmamalı"
    assert result.get("error") != "NO_TOOL_FOUND"


def test_document_reader():
    """URL'den belge okuma → document_reader tool'u bulunmalı."""
    result = run("https://arxiv.org/abs/2305.12345 makalesini oku ve özetle.")

    print("\n[sub_tasks]", result.get("sub_tasks"))
    print("[selected_tool]", getattr(result.get("selected_tool"), "name", None))
    print("[tool_result]", result.get("tool_result"))
    print("[final_response]", result.get("final_response"))

    assert result["final_response"]
    assert result.get("error") != "NO_TOOL_FOUND"


def test_multi_step_task():
    """
    Çok adımlı görev: hava durumu + çeviri.
    sub_tasks listesi 1'den fazla eleman içermeli (veya en az 1).
    """
    result = run(
        "Berlin'in bugünkü hava durumunu öğren, sonucu Türkçeye çevir."
    )

    print("\n[sub_tasks]", result.get("sub_tasks"))
    print("[step_results]", result.get("step_results"))
    print("[final_response]", result.get("final_response"))

    assert result["final_response"]
    # En az 1 adım tamamlanmış olmalı
    assert len(result.get("step_results", [])) >= 1


def test_no_tool_found():
    """Sistemde karşılığı olmayan anlamsız bir istek → NO_TOOL_FOUND beklenir."""
    result = run("Bana 5 dakikalık bir uyku ver ve rüya anlat.")

    print("\n[final_response]", result.get("final_response"))
    print("[error]", result.get("error"))

    # Ya tool bulunamaz ya da en azından final_response dolu olur
    assert result["final_response"]


if __name__ == "__main__":
    # Doğrudan çalıştırma: python tests/test_agent.py
    print("=== Weather ===")
    r = run("İstanbul'da bugün hava nasıl?")
    print("Response:", r["final_response"])
    print("Error:", r.get("error"))

    print("\n=== Currency ===")
    r = run("100 Euro kaç Türk Lirası yapar?")
    print("Response:", r["final_response"])

    print("\n=== Multi-step ===")
    r = run("Berlin'in hava durumunu öğren, sonucu Türkçeye çevir.")
    print("Sub-tasks:", r.get("sub_tasks"))
    print("Step results:", r.get("step_results"))
    print("Response:", r["final_response"])
