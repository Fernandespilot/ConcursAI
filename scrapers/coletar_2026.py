# -*- coding: utf-8 -*-
"""
Coletor de concursos do ano corrente (concursosnobrasil.com)
============================================================
Faz scraping da listagem de concursos, filtra os do ano-alvo, faz dedupe
contra o concursos_chunks.csv existente e reindexa o ChromaDB.

Uso:
    python scrapers/coletar_2026.py            # ano corrente, 5 páginas
    python scrapers/coletar_2026.py 2026 8     # ano 2026, 8 páginas
"""
from __future__ import annotations
import os
import re
import sys
import time
from datetime import datetime

import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE = "https://www.concursosnobrasil.com.br"
CSV = "concursos_chunks.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
# /concursos/{uf}/{ano}/{mes}/{dia}/{slug}
LINK_RE = re.compile(r"/concursos/([a-z]{2})/(20\d\d)/(\d{2})/(\d{2})/([a-z0-9-]+)/?", re.I)


def coletar(ano_alvo: int, paginas: int = 5) -> list[dict]:
    """Coleta concursos do ano-alvo a partir das páginas de listagem."""
    vistos: set[str] = set()
    itens: list[dict] = []
    sess = requests.Session()
    sess.headers.update(HEADERS)

    urls = [f"{BASE}/concursos/"] + [f"{BASE}/concursos/?page={p}" for p in range(2, paginas + 1)]
    for url in urls:
        try:
            r = sess.get(url, timeout=30)
            if r.status_code != 200:
                print(f"⚠️ {url} -> HTTP {r.status_code}")
                continue
            soup = BeautifulSoup(r.text, "lxml")
            achados = 0
            for a in soup.find_all("a", href=True):
                m = LINK_RE.search(a["href"])
                if not m:
                    continue
                uf, ano, mes, dia, slug = m.groups()
                if int(ano) != ano_alvo:
                    continue
                href = a["href"]
                if not href.startswith("http"):
                    href = "https://concursosnobrasil.com" + href
                if href in vistos:
                    continue
                titulo = a.get_text(strip=True)
                if not titulo or len(titulo) < 8:
                    continue
                vistos.add(href)
                itens.append({
                    "conteudo": titulo,
                    "orgao": "",
                    "ano": ano,
                    "cargo": "",
                    "tipo_documento": "concurso",
                    "titulo": titulo,
                    "url": href,
                    "data_publicacao": f"{ano}-{mes}-{dia}",
                })
                achados += 1
            print(f"📄 {url} -> {achados} concursos de {ano_alvo}")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ erro em {url}: {repr(e)[:120]}")
    return itens


def salvar_e_dedupe(itens: list[dict]) -> int:
    """Acrescenta apenas os concursos novos (por URL) ao CSV. Retorna nº adicionado."""
    cols = ["conteudo", "orgao", "ano", "cargo", "tipo_documento",
            "titulo", "url", "data_publicacao"]
    if os.path.exists(CSV):
        df = pd.read_csv(CSV)
    else:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ""

    existentes = set(df["url"].astype(str)) if "url" in df.columns else set()
    novos = [it for it in itens if it["url"] not in existentes]
    if not novos:
        return 0
    df = pd.concat([df, pd.DataFrame(novos)], ignore_index=True)
    df.to_csv(CSV, index=False)
    return len(novos)


def coletar_pci() -> list[dict]:
    """Coleta concursos recentes do PCI Concursos (pciconcursos.com.br)."""
    itens: list[dict] = []
    vistos: set[str] = set()
    sess = requests.Session()
    sess.headers.update(HEADERS)
    for url in [f"https://www.pciconcursos.com.br/ultimas/",
                f"https://www.pciconcursos.com.br/concursos/"]:
        try:
            r = sess.get(url, timeout=30)
            if r.status_code != 200:
                print(f"⚠️ PCI {url} -> HTTP {r.status_code}")
                continue
            soup = BeautifulSoup(r.text, "lxml")
            blocos = soup.find_all("div", class_="ca")
            achados = 0
            for b in blocos:
                a = b.find("a", href=True)
                if not a:
                    continue
                href = a["href"]
                if href in vistos:
                    continue
                titulo = (a.get("title") or a.get_text(strip=True)).strip()
                texto = b.get_text(" ", strip=True)
                if not titulo or len(titulo) < 8:
                    continue
                # órgão = antes do " - UF"; UF = sigla de 2 letras
                m_uf = re.search(r"\b([A-Z]{2})\b", texto)
                orgao = re.split(r"\s+-\s+", titulo)[0][:120]
                vistos.add(href)
                itens.append({
                    "conteudo": texto[:600],
                    "orgao": orgao,
                    "ano": str(time.localtime().tm_year),
                    "cargo": "",
                    "tipo_documento": "concurso",
                    "titulo": titulo,
                    "url": href,
                    "data_publicacao": time.strftime("%Y-%m-%d"),
                })
                achados += 1
            print(f"📄 PCI {url} -> {achados} concursos")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ erro PCI {url}: {repr(e)[:120]}")
    return itens


def reindexar() -> int:
    """Reconstrói a coleção do ChromaDB a partir do CSV completo. Retorna nº indexado."""
    import chromadb
    from sentence_transformers import SentenceTransformer  # noqa: F401 (garante dep)

    df = pd.read_csv(CSV)
    df = df[df["conteudo"].notna() & (df["conteudo"].astype(str) != "")]
    if df.empty:
        print("⚠️ Nada para indexar")
        return 0

    client = chromadb.PersistentClient(path="db_concursos")
    # recria a coleção do zero para refletir os dados atuais
    try:
        client.delete_collection("concursos_publicos")
    except Exception:
        pass
    col = client.get_or_create_collection("concursos_publicos")

    textos = df["conteudo"].astype(str).tolist()
    ids = [f"chunk_{i}" for i in range(len(textos))]
    metas = [{
        "orgao": str(r.get("orgao", "") or ""),
        "ano": str(r.get("ano", "") or ""),
        "cargo": str(r.get("cargo", "") or ""),
        "tipo_documento": str(r.get("tipo_documento", "") or ""),
        "titulo": str(r.get("titulo", "") or ""),
    } for _, r in df.iterrows()]

    for i in range(0, len(textos), 100):
        col.add(documents=textos[i:i+100], ids=ids[i:i+100], metadatas=metas[i:i+100])
    print(f"✅ ChromaDB reindexado: {len(textos)} documentos")
    return len(textos)


if __name__ == "__main__":
    ano = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.now().year
    paginas = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print(f"🔎 Fonte 1 — ConcursosNoBrasil (ano {ano}, {paginas} páginas)...")
    itens = coletar(ano, paginas)
    print(f"   coletados: {len(itens)}")

    print("🔎 Fonte 2 — PCI Concursos (últimos)...")
    itens_pci = coletar_pci()
    print(f"   coletados: {len(itens_pci)}")

    todos = itens + itens_pci
    print(f"📊 Total bruto: {len(todos)}")
    adicionados = salvar_e_dedupe(todos)
    print(f"💾 Novos concursos adicionados ao CSV: {adicionados}")
    if adicionados:
        reindexar()
    print("🎉 Concluído.")
