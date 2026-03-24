from agent.main_agent import tool_manager
import sys

with open('debug_out.txt', 'w', encoding='utf-8') as f:
    sys.stdout = f
    
    queries = [
        "100 dolar kaç TL ediyor?",
        "Bunu İngilizceye çevir: Merhaba",
        "2026 Oscar ödüllerini kim kazandı?",
        "motivasyonum düşük",
        "İstanbul hava durumu",
    ]

    for q in queries:
        print(f"\n--- {q} ---")
        hits = tool_manager.vector_store.search(q, n_results=5)
        for h in hits:
            d = h["distance"]
            sim = 1.0 - (d / 2.0)
            inertial = tool_manager._inertial_score(h["tool_name"])
            combined = sim * inertial
            print(f"  {h['tool_name']:25s} dist={d:.4f}  sim={sim:.4f}  combined={combined:.4f}")
