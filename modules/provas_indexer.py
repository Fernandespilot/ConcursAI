# -*- coding: utf-8 -*-
"""
Pipeline de Provas e Gabaritos — ConcursAI
==========================================
O sistema "estuda o que já caiu": indexa provas/gabaritos reais (PDF) para que
o RAG e a Análise de Banca se baseiem em conteúdo de exames anteriores.

Fluxo:
  1. PDFs ficam em  provas/<banca>/arquivo.pdf   (baixados ou adicionados à mão)
  2. indexar_provas() extrai o texto, detecta prova vs gabarito e indexa no
     ChromaDB (coleção `provas_concursos`), com metadados {banca, tipo, arquivo}
  3. consultar_provas(banca, termo) recupera trechos reais para a análise

Obs.: agregadores (PCI etc.) protegem o download por JS/hash; por isso o
downloader aqui trata URLs de PDF DIRETO (sites oficiais) — confiável e legal.
"""
from __future__ import annotations
import os
import glob
import re
import requests

PROVAS_DIR = "provas"
COLECAO = "provas_concursos"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}


# ── ChromaDB (coleção dedicada a provas) ──
def _get_colecao():
    import chromadb
    client = chromadb.PersistentClient(path="db_concursos")
    return client.get_or_create_collection(COLECAO)


def _extrair_texto(caminho: str, max_paginas: int = 30) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(caminho) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages[:max_paginas])
    except Exception as e:
        print(f"⚠️ Falha ao ler {caminho}: {e}")
        return ""


def _tipo(nome: str) -> str:
    n = nome.lower()
    if "gabarito" in n:
        return "gabarito"
    return "prova"


def baixar_pdf(url: str, banca: str) -> str | None:
    """Baixa um PDF DIRETO para provas/<banca>/. Retorna o caminho ou None."""
    banca = re.sub(r"[^a-z0-9]+", "_", banca.lower()).strip("_") or "geral"
    pasta = os.path.join(PROVAS_DIR, banca)
    os.makedirs(pasta, exist_ok=True)
    nome = url.split("/")[-1].split("?")[0]
    if not nome.lower().endswith(".pdf"):
        nome = nome + ".pdf"
    destino = os.path.join(pasta, nome)
    if os.path.exists(destino):
        return destino
    try:
        r = requests.get(url, headers=_HEADERS, timeout=40, stream=True)
        ct = r.headers.get("Content-Type", "").lower()
        if r.status_code != 200 or ("pdf" not in ct and not url.lower().endswith(".pdf")):
            print(f"⚠️ {url} não é PDF direto (HTTP {r.status_code}, {ct})")
            return None
        with open(destino, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        print(f"✅ baixado: {destino}")
        return destino
    except Exception as e:
        print(f"⚠️ erro ao baixar {url}: {e}")
        return None


def baixar_lote(urls: list[str], banca: str) -> dict:
    ok = [c for u in urls if (c := baixar_pdf(u, banca))]
    return {"baixados": len(ok), "arquivos": [os.path.basename(c) for c in ok]}


def indexar_provas() -> dict:
    """Indexa todos os PDFs em provas/<banca>/ no ChromaDB. Idempotente por id."""
    col = _get_colecao()
    try:
        existentes = set(col.get().get("ids", []))
    except Exception:
        existentes = set()

    novos, bancas = 0, set()
    docs, ids, metas = [], [], []
    for caminho in glob.glob(os.path.join(PROVAS_DIR, "*", "*.pdf")):
        banca = os.path.basename(os.path.dirname(caminho))
        arquivo = os.path.basename(caminho)
        bancas.add(banca)
        chunk_id = f"prova_{banca}_{arquivo}".replace(" ", "_")
        if chunk_id in existentes:
            continue
        texto = _extrair_texto(caminho)
        if not texto.strip():
            continue
        # indexa em blocos de ~1500 chars para granularidade
        blocos = [texto[i:i+1500] for i in range(0, min(len(texto), 15000), 1500)]
        for j, b in enumerate(blocos):
            docs.append(b)
            ids.append(f"{chunk_id}_{j}")
            metas.append({"banca": banca, "tipo_documento": _tipo(arquivo),
                          "arquivo": arquivo})
        novos += 1

    if docs:
        for i in range(0, len(docs), 100):
            col.add(documents=docs[i:i+100], ids=ids[i:i+100], metadatas=metas[i:i+100])

    return {"provas_indexadas": novos, "blocos": len(docs),
            "bancas": sorted(bancas), "total_colecao": col.count()}


def consultar_provas(banca: str = "", termo: str = "", limite: int = 5) -> list[dict]:
    """Recupera trechos de provas/gabaritos reais (para aterrar a Análise de Banca)."""
    try:
        col = _get_colecao()
        if col.count() == 0:
            return []
        where = None
        if banca:
            b = banca.lower().split("/")[0].strip()
            # filtro por banca (case-insensitive aproximado feito depois)
        res = col.query(query_texts=[termo or banca or "questão"], n_results=limite * 2)
        out = []
        docs = (res.get("documents") or [[]])[0]
        mts = (res.get("metadatas") or [[]])[0]
        for d, m in zip(docs, mts):
            if banca:
                bb = (m.get("banca", "") or "").lower()
                if banca.lower().split("/")[0].strip() not in bb:
                    continue
            out.append({"banca": m.get("banca"), "tipo": m.get("tipo_documento"),
                        "arquivo": m.get("arquivo"), "trecho": d[:500]})
            if len(out) >= limite:
                break
        return out
    except Exception as e:
        print(f"⚠️ consultar_provas: {e}")
        return []


def estatisticas() -> dict:
    """Resumo do acervo de provas (arquivos em disco + indexados)."""
    por_banca = {}
    for caminho in glob.glob(os.path.join(PROVAS_DIR, "*", "*.pdf")):
        banca = os.path.basename(os.path.dirname(caminho))
        por_banca[banca] = por_banca.get(banca, 0) + 1
    total = sum(por_banca.values())
    indexados = 0
    try:
        indexados = _get_colecao().count()
    except Exception:
        pass
    return {"total_pdfs": total, "por_banca": por_banca, "blocos_indexados": indexados}
