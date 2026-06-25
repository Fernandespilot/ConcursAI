# -*- coding: utf-8 -*-
"""
Inteligência de Banca — ConcursAI
=================================

Coração do projeto: o sistema "estuda" a banca a partir das provas e conteúdos
raspados e produz:

  1. INCIDÊNCIA por tema (métrica do que mais cai nos últimos N anos)
  2. PERFIL DE ESTUDO personalizado para a banca
  3. Tendências e pegadinhas típicas

A incidência é gerada pela IA (Groq) analisando o histórico da banca, ancorada
nos dados realmente raspados (concursos/provas no acervo). Quanto mais provas
forem raspadas e indexadas, mais precisa fica a análise.
"""
from __future__ import annotations
import os
import re
import json
import glob

try:
    from modules.concurso_rag import _get_groq_client
except Exception:  # pragma: no cover
    from .concurso_rag import _get_groq_client

MODELO_LLM = "llama-3.3-70b-versatile"
CSV = "concursos_chunks.csv"


def _coletar_evidencias(banca: str, anos: int) -> dict:
    """Reúne sinais reais do acervo sobre a banca (para ancorar a análise)."""
    banca_low = banca.lower().split("/")[0].strip()
    ev = {"concursos_relacionados": 0, "provas_pdf": 0, "amostras": []}

    # 1) concursos no CSV que mencionam a banca
    try:
        import pandas as pd
        if os.path.exists(CSV):
            df = pd.read_csv(CSV)
            campos = ["titulo", "orgao", "conteudo", "cargo"]
            mask = False
            for c in campos:
                if c in df.columns:
                    m = df[c].astype(str).str.lower().str.contains(banca_low, na=False)
                    mask = m if mask is False else (mask | m)
            if mask is not False:
                rel = df[mask]
                ev["concursos_relacionados"] = int(len(rel))
                ev["amostras"] = rel["titulo"].astype(str).head(8).tolist() if "titulo" in rel else []
    except Exception:
        pass

    # 2) PDFs de provas baixados para a banca (provas/<banca>/*.pdf)
    try:
        for pasta in glob.glob("provas/*"):
            if banca_low in os.path.basename(pasta).lower():
                ev["provas_pdf"] += len(glob.glob(os.path.join(pasta, "*.pdf")))
    except Exception:
        pass

    # 3) trechos REAIS de provas/gabaritos indexados (o "que já caiu")
    ev["trechos_provas"] = []
    try:
        from modules.provas_indexer import consultar_provas
        trechos = consultar_provas(banca=banca, termo="questão prova conteúdo", limite=6)
        ev["trechos_provas"] = [t["trecho"] for t in trechos]
    except Exception:
        pass

    return ev


def _extrair_json(texto: str):
    """Extrai o primeiro objeto JSON de um texto (a IA às vezes adiciona prosa)."""
    if not texto:
        return None
    m = re.search(r"\{.*\}", texto, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _fallback(banca: str, cargo: str, anos: int, ev: dict) -> dict:
    """Resposta sem LLM: estrutura honesta baseada apenas nas evidências."""
    return {
        "banca": banca,
        "cargo": cargo or "Geral",
        "periodo": f"últimos {anos} anos",
        "incidencia": [],
        "perfil_estudo": (
            "⚠️ Análise por IA indisponível (configure a GROQ_API_KEY no .env).\n\n"
            f"Acervo atual para **{banca}**: {ev['concursos_relacionados']} concursos "
            f"relacionados e {ev['provas_pdf']} provas em PDF. Quanto mais provas "
            "forem raspadas, mais rica fica a análise de incidência e o perfil."
        ),
        "pegadinhas": [],
        "fontes": ev,
        "gerado_por": "fallback (sem IA)",
    }


def analisar_banca(banca: str, cargo: str = "", anos: int = 5) -> dict:
    """Gera a análise completa da banca: incidência + perfil de estudo."""
    if not banca or not banca.strip():
        return {"erro": "Informe a banca."}

    ev = _coletar_evidencias(banca, anos)
    cliente = _get_groq_client()
    if not cliente:
        return _fallback(banca, cargo, anos, ev)

    contexto = (
        f"Banca: {banca}\nCargo/área de interesse: {cargo or 'geral'}\n"
        f"Período de análise: últimos {anos} anos.\n"
        f"Acervo do sistema: {ev['concursos_relacionados']} concursos relacionados, "
        f"{ev['provas_pdf']} provas em PDF.\n"
    )
    if ev["amostras"]:
        contexto += "Exemplos de concursos no acervo:\n- " + "\n- ".join(ev["amostras"][:6])
    if ev.get("trechos_provas"):
        contexto += ("\n\nTRECHOS REAIS DE PROVAS/GABARITOS DESTA BANCA (use-os como "
                     "base concreta para a incidência — isto é o que JÁ CAIU):\n---\n"
                     + "\n---\n".join(t[:400] for t in ev["trechos_provas"][:6]))

    system = (
        "Você é um analista especialista em bancas de concursos públicos "
        "brasileiros. Com base no seu conhecimento consolidado sobre a banca e no "
        "acervo informado, produza uma análise de INCIDÊNCIA dos temas mais "
        "cobrados e um PERFIL DE ESTUDO. Responda SOMENTE com um JSON válido, sem "
        "texto fora do JSON, no formato exato:\n"
        "{\n"
        '  "incidencia": [{"tema": "string", "percentual": number, "tendencia": "subindo|estavel|caindo"}],\n'
        '  "perfil_estudo": "string em markdown com como estudar para esta banca",\n'
        '  "pegadinhas": ["string", "string"],\n'
        '  "resumo": "string curta (1-2 frases)"\n'
        "}\n"
        "Regras: 6 a 10 temas em 'incidencia'; percentuais somando ~100; foque nas "
        "disciplinas/assuntos típicos da banca e do cargo; seja específico e realista."
    )
    user = (
        f"{contexto}\n\nGere a análise de incidência (últimos {anos} anos) e o "
        f"perfil de estudo para a banca {banca}"
        + (f", cargo {cargo}." if cargo else ".")
    )

    try:
        resp = cliente.chat.completions.create(
            model=MODELO_LLM,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.3,
            max_tokens=1600,
            response_format={"type": "json_object"},
        )
        data = _extrair_json(resp.choices[0].message.content) or {}
    except Exception as e:
        # tenta sem response_format (modelos/versões que não suportam)
        try:
            resp = cliente.chat.completions.create(
                model=MODELO_LLM,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=0.3, max_tokens=1600,
            )
            data = _extrair_json(resp.choices[0].message.content) or {}
        except Exception as e2:
            print(f"⚠️ Erro na análise de banca: {e2}")
            return _fallback(banca, cargo, anos, ev)

    incid = data.get("incidencia") or []
    # normaliza/saneia
    limpa = []
    for it in incid:
        try:
            limpa.append({
                "tema": str(it.get("tema", "")).strip(),
                "percentual": round(float(it.get("percentual", 0)), 1),
                "tendencia": str(it.get("tendencia", "estavel")).lower(),
            })
        except Exception:
            continue
    limpa.sort(key=lambda x: x["percentual"], reverse=True)

    return {
        "banca": banca,
        "cargo": cargo or "Geral",
        "periodo": f"últimos {anos} anos",
        "incidencia": limpa,
        "perfil_estudo": data.get("perfil_estudo", ""),
        "pegadinhas": data.get("pegadinhas", []) or [],
        "resumo": data.get("resumo", ""),
        "fontes": ev,
        "gerado_por": "IA (Groq / llama-3.3-70b)",
    }
