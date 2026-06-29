# -*- coding: utf-8 -*-
"""
BENCHMARK DO MODELO - ConcursAI
================================
Testa o sistema (agentes + Groq) contra ground truth e gera relatório.

Uso:
    python scripts/benchmark_modelo.py
    python scripts/benchmark_modelo.py --num 10
"""

import json
import time
import sys
import os
import requests
from datetime import datetime
from pathlib import Path

API_URL = "http://localhost:8000"
GT_PATH = Path("datasets/ground_truth_rag.json")
OUT_DIR = Path("benchmarks")


def carregar_ground_truth(num=None, bancas=None, areas=None):
    with open(GT_PATH, "r", encoding="utf-8") as f:
        perguntas = json.load(f).get("perguntas", [])
    if bancas:
        bl = [b.lower() for b in bancas]
        perguntas = [p for p in perguntas if p.get("banca", "").lower() in bl]
    if areas:
        al = [a.lower() for a in areas]
        perguntas = [p for p in perguntas if p.get("area", "").lower() in al]
    if num:
        perguntas = perguntas[:num]
    return perguntas


def perguntar(pergunta: str) -> tuple[str, float]:
    t0 = time.time()
    r = requests.post(
        f"{API_URL}/agente/perguntar",
        json={"pergunta": pergunta},
        timeout=120,
    )
    latency = (time.time() - t0) * 1000
    if r.status_code != 200:
        return f"[ERRO HTTP {r.status_code}]", latency
    data = r.json()
    return data.get("resposta", ""), latency


def validar(resposta: str, gt_entry: dict) -> dict:
    keywords = gt_entry.get("keywords_obrigatorias", [])
    resp_lower = resposta.lower()
    presentes = [kw for kw in keywords if kw.lower() in resp_lower]
    faltando = [kw for kw in keywords if kw.lower() not in resp_lower]
    score = len(presentes) / len(keywords) if keywords else 0.0
    return {
        "keyword_match_score": round(score, 3),
        "has_expected_keywords": score >= 0.8,
        "keywords_presentes": presentes,
        "missing_keywords": faltando,
        "total_keywords": len(keywords),
    }


def executar_benchmark(num=None, bancas=None, areas=None):
    perguntas = carregar_ground_truth(num, bancas, areas)
    total = len(perguntas)
    print(f"\n{'='*70}")
    print(f"  BENCHMARK ConcursAI — {total} perguntas via Groq (llama-3.3-70b)")
    print(f"{'='*70}\n")

    resultados = []
    for i, gt in enumerate(perguntas, 1):
        p = gt["pergunta"]
        print(f"[{i}/{total}] {p}")

        resposta, latency = perguntar(p)
        val = validar(resposta, gt)

        icon = "✅" if val["has_expected_keywords"] else ("⚠️" if val["keyword_match_score"] >= 0.5 else "❌")
        print(f"  {icon} score={val['keyword_match_score']:.2f}  latência={latency:.0f}ms  faltando={val['missing_keywords']}")

        resultados.append({
            "id": gt["id"],
            "pergunta": p,
            "banca": gt.get("banca", ""),
            "area": gt.get("area", ""),
            "dificuldade": gt.get("dificuldade", ""),
            "tipo": gt.get("tipo", ""),
            "resposta": resposta[:300],
            "latency_ms": round(latency, 1),
            "validation": val,
            "sucesso": val["has_expected_keywords"],
        })

    # --- Estatísticas ---
    sucessos = [r for r in resultados if r["sucesso"]]
    scores = [r["validation"]["keyword_match_score"] for r in resultados]
    latencies = [r["latency_ms"] for r in resultados]

    # Precision/Recall por keywords
    tp = sum(len(r["validation"]["keywords_presentes"]) for r in resultados)
    fn = sum(len(r["validation"]["missing_keywords"]) for r in resultados)
    total_kw = tp + fn
    precision = tp / total_kw if total_kw else 0
    recall = tp / total_kw if total_kw else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    # Distribuições
    dist = {"por_banca": {}, "por_area": {}, "por_tipo": {}, "por_dificuldade": {}}
    for r in resultados:
        for chave in dist:
            campo = chave.replace("por_", "")
            val_campo = r.get(campo, "N/A")
            if val_campo not in dist[chave]:
                dist[chave][val_campo] = {"total": 0, "sucesso": 0}
            dist[chave][val_campo]["total"] += 1
            if r["sucesso"]:
                dist[chave][val_campo]["sucesso"] += 1

    stats = {
        "total_perguntas": total,
        "perguntas_com_sucesso": len(sucessos),
        "taxa_sucesso": round(len(sucessos) / total, 3) if total else 0,
        "qualidade": {
            "keyword_match_score_medio": round(sum(scores) / len(scores), 3) if scores else 0,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3),
        },
        "performance": {
            "latency_media_ms": round(sum(latencies) / len(latencies)) if latencies else 0,
            "latency_min_ms": round(min(latencies)) if latencies else 0,
            "latency_max_ms": round(max(latencies)) if latencies else 0,
            "latency_p50_ms": round(sorted(latencies)[len(latencies) // 2]) if latencies else 0,
            "latency_p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)]) if latencies else 0,
        },
        "distribuicao": dist,
    }

    relatorio = {
        "timestamp": datetime.now().isoformat(),
        "configuracao": {
            "modelo": "llama-3.3-70b-versatile (Groq)",
            "sistema": "agentes + RAG + ChromaDB",
            "num_perguntas": total,
        },
        "estatisticas": stats,
        "resultados_detalhados": resultados,
    }

    # Salvar
    OUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUT_DIR / f"benchmark_{ts}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)

    # Imprimir resumo
    print(f"""
{'='*70}
  RESUMO DO BENCHMARK
{'='*70}

  Modelo: llama-3.3-70b-versatile (Groq)
  Data:   {relatorio['timestamp']}

  QUALIDADE
  {'─'*40}
  Total perguntas:       {stats['total_perguntas']}
  Sucesso (≥80% kw):     {stats['perguntas_com_sucesso']} ({stats['taxa_sucesso']:.1%})
  Keyword Match médio:   {stats['qualidade']['keyword_match_score_medio']:.1%}
  Precision:             {stats['qualidade']['precision']:.1%}
  Recall:                {stats['qualidade']['recall']:.1%}
  F1 Score:              {stats['qualidade']['f1_score']:.1%}

  PERFORMANCE
  {'─'*40}
  Latência média:        {stats['performance']['latency_media_ms']}ms
  Latência P50:          {stats['performance']['latency_p50_ms']}ms
  Latência P95:          {stats['performance']['latency_p95_ms']}ms
  Latência min/max:      {stats['performance']['latency_min_ms']}/{stats['performance']['latency_max_ms']}ms

  POR BANCA
  {'─'*40}""")
    for b, d in sorted(dist["por_banca"].items(), key=lambda x: str(x[0])):
        t = d["sucesso"] / d["total"] if d["total"] else 0
        print(f"  {str(b or 'N/A'):15s}  {d['sucesso']:2d}/{d['total']:2d}  ({t:.0%})")

    print(f"\n  POR ÁREA\n  {'─'*40}")
    for a, d in sorted(dist["por_area"].items(), key=lambda x: str(x[0])):
        t = d["sucesso"] / d["total"] if d["total"] else 0
        print(f"  {str(a or 'N/A'):20s}  {d['sucesso']:2d}/{d['total']:2d}  ({t:.0%})")

    print(f"\n{'='*70}")
    print(f"  Relatório salvo: {out}")
    print(f"{'='*70}\n")

    return relatorio


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark ConcursAI")
    parser.add_argument("--num", type=int, default=None)
    parser.add_argument("--banca", nargs="+", default=None)
    parser.add_argument("--area", nargs="+", default=None)
    args = parser.parse_args()
    executar_benchmark(num=args.num, bancas=args.banca, areas=args.area)
