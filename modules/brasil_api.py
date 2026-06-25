# -*- coding: utf-8 -*-
"""
Enriquecimento via BrasilAPI — ConcursAI
========================================
BrasilAPI (https://brasilapi.com.br) é pública e gratuita, SEM chave.
Usada como complemento (não é fonte de concursos):

  - feriados nacionais  -> útil para montar o cronograma de estudos
  - CNPJ                 -> dados do órgão (razão social, município, etc.)

Tudo com cache simples em memória e timeouts curtos para não travar a API.
"""
from __future__ import annotations
import time
import requests

BASE = "https://brasilapi.com.br/api"
_HEADERS = {"User-Agent": "ConcursAI/1.0"}
_cache: dict = {}
_TTL = 60 * 60 * 12  # 12h


def _get(url: str):
    """GET com cache em memória e timeout curto."""
    agora = time.time()
    hit = _cache.get(url)
    if hit and (agora - hit[0] < _TTL):
        return hit[1]
    r = requests.get(url, headers=_HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()
    _cache[url] = (agora, data)
    return data


def feriados(ano: int) -> dict:
    """Feriados nacionais do ano (via BrasilAPI). Útil para o cronograma."""
    try:
        dados = _get(f"{BASE}/feriados/v1/{int(ano)}")
        return {"ano": int(ano), "total": len(dados), "feriados": dados}
    except Exception as e:
        return {"ano": ano, "total": 0, "feriados": [], "erro": str(e)}


def cnpj(numero: str) -> dict:
    """Dados de um órgão pelo CNPJ (via BrasilAPI)."""
    num = "".join(ch for ch in str(numero) if ch.isdigit())
    if len(num) != 14:
        return {"erro": "CNPJ deve ter 14 dígitos."}
    try:
        d = _get(f"{BASE}/cnpj/v1/{num}")
        return {
            "cnpj": num,
            "razao_social": d.get("razao_social") or d.get("nome"),
            "nome_fantasia": d.get("nome_fantasia"),
            "municipio": d.get("municipio"),
            "uf": d.get("uf"),
            "situacao": d.get("descricao_situacao_cadastral") or d.get("situacao"),
        }
    except Exception as e:
        return {"cnpj": num, "erro": str(e)}
