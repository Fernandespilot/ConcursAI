#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo de embeddings para o sistema ConcursAI"""

import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
import os

# 🔹 Carregar os dados dos trechos de concursos
def carregar_dados():
    """Carrega dados de concursos, criando arquivo vazio se não existir"""
    arquivo_chunks = "concursos_chunks.csv"
    
    if not os.path.exists(arquivo_chunks):
        # Criar arquivo CSV vazio com colunas padrão
        df_vazio = pd.DataFrame(columns=[
            'conteudo', 'orgao', 'ano', 'cargo', 'tipo_documento', 
            'titulo', 'url', 'data_publicacao'
        ])
        df_vazio.to_csv(arquivo_chunks, index=False)
        print(f"📄 Arquivo {arquivo_chunks} criado. Adicione dados de concursos para usar o sistema.")
        return df_vazio
    
    try:
        df = pd.read_csv(arquivo_chunks)
        print(f"✅ Carregados {len(df)} chunks de concursos")
        return df
    except Exception as e:
        print(f"❌ Erro ao carregar {arquivo_chunks}: {e}")
        # Retornar DataFrame vazio em caso de erro
        return pd.DataFrame(columns=[
            'conteudo', 'orgao', 'ano', 'cargo', 'tipo_documento', 
            'titulo', 'url', 'data_publicacao'
        ])

# 🔹 Carregar dados
df_chunks = carregar_dados()

# 🔹 Verificar se a coluna 'conteudo' existe e preencher se necessário
if "conteudo" not in df_chunks.columns:
    print("⚠️ A coluna 'conteudo' não foi encontrada. Criando coluna vazia...")
    df_chunks['conteudo'] = ""

# 🔹 Preencher conteúdo vazio com título quando disponível
if len(df_chunks) > 0:
    mask_vazio = (df_chunks['conteudo'].isna()) | (df_chunks['conteudo'] == "")
    if mask_vazio.any() and 'titulo' in df_chunks.columns:
        df_chunks.loc[mask_vazio, 'conteudo'] = df_chunks.loc[mask_vazio, 'titulo']
        print(f"🔄 Preenchidos {mask_vazio.sum()} campos de conteúdo com títulos")

# 🔹 Inicializar o modelo de embeddings (lazy loading)
embedder = None

def get_embedder():
    """Carrega o modelo de embeddings apenas quando necessário"""
    global embedder
    if embedder is None:
        print("🔄 Carregando modelo de embeddings...")
        try:
            embedder = SentenceTransformer("all-MiniLM-L6-v2")
            print("✅ Modelo de embeddings carregado")
        except Exception as e:
            print(f"❌ Erro ao carregar modelo de embeddings: {e}")
            embedder = None
    return embedder

# 🔹 Inicializar o cliente Chroma com persistência
print("🔄 Inicializando banco de dados ChromaDB...")
try:
    os.makedirs("db_concursos", exist_ok=True)
    chroma_client = chromadb.PersistentClient(path="db_concursos")
    collection = chroma_client.get_or_create_collection(name="concursos_publicos")
    print("✅ ChromaDB inicializado")
except Exception as e:
    print(f"❌ Erro ao inicializar ChromaDB: {e}")
    collection = None

# 🔹 Função para indexar os dados
def indexar_dados():
    """Indexa os dados de concursos no ChromaDB"""
    embedder = get_embedder()
    if collection is None or embedder is None:
        print("❌ Impossível indexar: componentes não carregados")
        return
    
    try:
        # Verificar se já existem dados indexados
        existing_count = collection.count()
        if existing_count > 0 and existing_count >= len(df_chunks):
            print(f"✅ Dados já indexados ({existing_count} documentos)")
            return
        
        # Filtrar apenas registros com conteúdo não vazio
        df_validos = df_chunks[df_chunks['conteudo'].notna() & (df_chunks['conteudo'] != "")]
        
        if len(df_validos) == 0:
            print("⚠️ Nenhum dado válido para indexar")
            return
        
        print(f"🔄 Indexando {len(df_validos)} novos documentos...")
        
        # Preparar dados para indexação
        textos = df_validos['conteudo'].tolist()
        ids = [f"chunk_{i}" for i in range(len(textos))]
        
        # Criar metadados
        metadados = []
        for _, row in df_validos.iterrows():
            metadata = {
                "orgao": str(row.get('orgao', 'N/A')),
                "ano": str(row.get('ano', 'N/A')),
                "cargo": str(row.get('cargo', 'N/A')),
                "tipo_documento": str(row.get('tipo_documento', 'N/A')),
                "titulo": str(row.get('titulo', 'N/A'))
            }
            metadados.append(metadata)
        
        # Indexar em lotes para evitar problemas de memória
        batch_size = 100
        for i in range(0, len(textos), batch_size):
            batch_textos = textos[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            batch_metadados = metadados[i:i+batch_size]
            
            collection.add(
                documents=batch_textos,
                ids=batch_ids,
                metadatas=batch_metadados
            )
            
            print(f"✅ Processado lote {i//batch_size + 1}/{(len(textos)-1)//batch_size + 1}")
        
        print(f"✅ Indexação concluída! {len(textos)} documentos indexados")
        
    except Exception as e:
        print(f"❌ Erro durante indexação: {e}")

# 🔹 Executar indexação automaticamente
if __name__ == "__main__":
    indexar_dados()
else:
    # Indexar apenas se há dados válidos
    if len(df_chunks) > 0 and df_chunks['conteudo'].notna().sum() > 0:
        indexar_dados()
    else:
        print("ℹ️ Aguardando dados para indexar...")
