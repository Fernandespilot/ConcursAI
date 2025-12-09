#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo RAG simplificado - sem dependências complexas"""

import pandas as pd
import os
import re
from typing import List, Dict, Any

def buscar_documentos_simples(pergunta: str, df_chunks: pd.DataFrame, limite: int = 5) -> List[Dict]:
    """Busca documentos usando busca textual simples"""
    if df_chunks.empty:
        return []
    
    try:
        pergunta_lower = pergunta.lower()
        
        # Criar score baseado em ocorrências de palavras
        scores = []
        for idx, row in df_chunks.iterrows():
            score = 0
            texto_completo = str(row.get('conteudo', '')) + ' ' + str(row.get('titulo', ''))
            texto_lower = texto_completo.lower()
            
            # Buscar palavras-chave
            palavras = pergunta_lower.split()
            for palavra in palavras:
                if len(palavra) > 2:  # Ignorar palavras muito curtas
                    score += texto_lower.count(palavra)
            
            scores.append((idx, score, row))
        
        # Ordenar por score e pegar os melhores
        scores.sort(key=lambda x: x[1], reverse=True)
        
        resultados = []
        for idx, score, row in scores[:limite]:
            if score > 0:  # Só incluir se encontrou algo
                resultados.append({
                    'conteudo': row.get('conteudo', ''),
                    'titulo': row.get('titulo', ''),
                    'orgao': row.get('orgao', ''),
                    'ano': row.get('ano', ''),
                    'cargo': row.get('cargo', ''),
                    'score': score
                })
        
        return resultados
        
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        return []

def responder_interface_simples(pergunta: str, orgao: str = "Todos", ano: str = "Todos", cargo: str = "Todos") -> str:
    """Responde perguntas usando busca textual simples"""
    try:
        # Carregar dados
        if os.path.exists("concursos_chunks.csv"):
            df_chunks = pd.read_csv("concursos_chunks.csv")
        else:
            return "❌ **Dados não encontrados.** Por favor, carregue os dados de concursos primeiro."
        
        if df_chunks.empty:
            return "❌ **Nenhum dado disponível.** Por favor, adicione dados de concursos ao sistema."
        
        # Aplicar filtros
        df_filtrado = df_chunks.copy()
        
        if orgao != "Todos" and orgao:
            df_filtrado = df_filtrado[df_filtrado['orgao'].str.contains(orgao, case=False, na=False)]
        
        if ano != "Todos" and ano:
            df_filtrado = df_filtrado[df_filtrado['ano'].astype(str) == str(ano)]
        
        if cargo != "Todos" and cargo:
            df_filtrado = df_filtrado[df_filtrado['cargo'].str.contains(cargo, case=False, na=False)]
        
        # Buscar documentos relevantes
        documentos = buscar_documentos_simples(pergunta, df_filtrado)
        
        if not documentos:
            return f"""
❌ **Não encontrei informações específicas sobre: "{pergunta}"**

**Sugestões:**
- Tente usar termos mais gerais
- Verifique se os filtros não estão muito restritivos
- Experimente palavras-chave diferentes

**Dados disponíveis:** {len(df_chunks)} registros de concursos
"""
        
        # Gerar resposta baseada nos documentos encontrados
        resposta = f"✅ **Encontrei {len(documentos)} resultado(s) para sua pergunta.**\n\n"
        
        for i, doc in enumerate(documentos[:3], 1):
            resposta += f"**{i}. {doc['titulo']}**\n"
            resposta += f"   - **Órgão:** {doc['orgao']}\n"
            resposta += f"   - **Cargo:** {doc['cargo']}\n"
            resposta += f"   - **Ano:** {doc['ano']}\n"
            
            # Mostrar trecho relevante
            conteudo = doc['conteudo'][:200] + "..." if len(doc['conteudo']) > 200 else doc['conteudo']
            resposta += f"   - **Resumo:** {conteudo}\n\n"
        
        if len(documentos) > 3:
            resposta += f"... e mais {len(documentos) - 3} resultado(s).\n\n"
        
        resposta += "💡 **Dica:** Use filtros específicos (órgão, ano, cargo) para resultados mais precisos."
        
        return resposta
        
    except Exception as e:
        return f"❌ **Erro ao processar pergunta:** {str(e)}"

# Função principal compatível com o sistema original
def responder_interface(pergunta, orgao="Todos", ano="Todos", cargo="Todos"):
    """Função principal para compatibilidade"""
    return responder_interface_simples(pergunta, orgao, ano, cargo)
