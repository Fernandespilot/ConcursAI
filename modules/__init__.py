#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo de inicialização para os módulos do ConcursAI"""

__version__ = "1.0.0"
__author__ = "ConcursAI Team"

# Imports principais para facilitar o uso
try:
    from .concurso_rag import responder_interface
    from .concurso_embeddings import df_chunks, collection
    from .coletor_realtime import ColetorConcursosRealTime
    from .sistema_notificacoes import SistemaNotificacoes
    from .dashboard import DashboardConcursos
    from .agendador import AgendadorConcursos
except ImportError:
    # Em caso de erro de import, continuar sem falhar
    pass
