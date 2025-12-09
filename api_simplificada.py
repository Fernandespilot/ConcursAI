#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API FastAPI SIMPLIFICADA para o sistema ConcursAI - SEM DEPENDÊNCIAS COMPLEXAS"""

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import uvicorn
import os
import sys
from datetime import datetime
import json

# Adicionar integrador PCI
try:
    from integrador_pci import IntegradorPCIConcursos
    PCI_DISPONIVEL = True
except ImportError:
    PCI_DISPONIVEL = False

# Adicionar coletor real
try:
    from coletor_pci_real import api_atualizar_dados
    COLETOR_REAL_DISPONIVEL = True
except ImportError:
    COLETOR_REAL_DISPONIVEL = False
    print("⚠️ Coletor real PCI não disponível")

# Models Pydantic simplificados
class ConcursoModel(BaseModel):
    titulo: str
    orgao: str
    cargo: str
    ano: str
    tipo_documento: str
    url: Optional[str] = None
    data_publicacao: Optional[str] = None
    fonte: Optional[str] = None

class BuscaSemanticaRequest(BaseModel):
    pergunta: str
    filtro_orgao: Optional[str] = None
    filtro_ano: Optional[str] = None
    filtro_cargo: Optional[str] = None

class StatusSistemaResponse(BaseModel):
    status: str
    total_concursos: int
    ultima_atualizacao: Optional[str] = None
    version: str = "2.0.1-simplificado"

# Inicializar FastAPI
app = FastAPI(
    title="ConcursAI API",
    description="Sistema de análise inteligente de concursos públicos",
    version="2.0.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Montar arquivos estáticos
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print("✅ Arquivos estáticos montados")
except Exception as e:
    print(f"⚠️ Erro ao montar arquivos estáticos: {e}")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tentar montar arquivos estáticos
try:
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
        print("✅ Arquivos estáticos montados")
except Exception as e:
    print(f"⚠️ Erro ao montar arquivos estáticos: {e}")

# Função para carregar dados
def carregar_dados_concursos():
    """Carrega dados de concursos do CSV"""
    try:
        if os.path.exists("concursos_chunks.csv"):
            df = pd.read_csv("concursos_chunks.csv")
            print(f"✅ Carregados {len(df)} registros de concursos")
            return df
        else:
            print("⚠️ Arquivo concursos_chunks.csv não encontrado")
            return pd.DataFrame()
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Carregar dados na inicialização
df_concursos = carregar_dados_concursos()

@app.get("/", include_in_schema=False)
async def landing_page():
    """Página principal - Landing Page"""
    try:
        return FileResponse('static/landing.html')
    except Exception as e:
        # Fallback para resposta JSON se a landing page não existir
        return {
            "message": "🎯 ConcursAI API - Sistema Funcional",
            "version": "2.0.1",
            "status": "online",
            "acesso": {
                "docs": "/docs",
                "status": "/status", 
                "concursos": "/concursos",
                "buscar": "/buscar",
                "landing": "/static/landing.html"
            },
            "erro_landing": str(e)
        }

@app.get("/api", tags=["Sistema"])
async def api_info():
    """Informações da API"""
    return {
        "message": "ConcursAI API - Sistema Simplificado",
        "version": "2.0.1",
        "status": "online",
        "docs": "/docs",
        "endpoints": {
            "status": "/status",
            "concursos": "/concursos",
            "buscar": "/buscar",
            "orgaos": "/orgaos",
            "anos": "/anos",
            "cargos": "/cargos"
        }
    }

@app.get("/status", response_model=StatusSistemaResponse)
async def get_status():
    """Status do sistema"""
    return StatusSistemaResponse(
        status="online",
        total_concursos=len(df_concursos),
        ultima_atualizacao=datetime.now().isoformat(),
        version="2.0.1-simplificado"
    )

@app.get("/concursos")
async def listar_concursos(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    orgao: Optional[str] = Query(None),
    ano: Optional[str] = Query(None),
    cargo: Optional[str] = Query(None)
):
    """Lista concursos com filtros opcionais"""
    try:
        df_filtrado = df_concursos.copy()
        
        # Aplicar filtros se fornecidos
        if orgao:
            df_filtrado = df_filtrado[df_filtrado['orgao'].str.contains(orgao, case=False, na=False)]
        if ano:
            df_filtrado = df_filtrado[df_filtrado['ano'].astype(str) == str(ano)]
        if cargo:
            df_filtrado = df_filtrado[df_filtrado['cargo'].str.contains(cargo, case=False, na=False)]
        
        # Paginação
        total = len(df_filtrado)
        df_paginado = df_filtrado.iloc[offset:offset+limit]
        
        return {
            "concursos": df_paginado.to_dict('records'),
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar concursos: {str(e)}")

@app.post("/buscar")
async def busca_semantica(request: BuscaSemanticaRequest):
    """Busca semântica simplificada (sem IA)"""
    try:
        pergunta = request.pergunta.lower()
        df_resultado = df_concursos.copy()
        
        # Busca simples por palavras-chave no título e conteúdo
        mask = (
            df_resultado['titulo'].str.lower().str.contains(pergunta, na=False) |
            df_resultado.get('conteudo', pd.Series()).str.lower().str.contains(pergunta, na=False) |
            df_resultado['cargo'].str.lower().str.contains(pergunta, na=False) |
            df_resultado['orgao'].str.lower().str.contains(pergunta, na=False)
        )
        
        # Aplicar filtros adicionais
        if request.filtro_orgao:
            mask &= df_resultado['orgao'].str.contains(request.filtro_orgao, case=False, na=False)
        if request.filtro_ano:
            mask &= df_resultado['ano'].astype(str) == str(request.filtro_ano)
        if request.filtro_cargo:
            mask &= df_resultado['cargo'].str.contains(request.filtro_cargo, case=False, na=False)
        
        resultados = df_resultado[mask].head(10)
        
        return {
            "pergunta": request.pergunta,
            "resposta": f"Encontrei {len(resultados)} concursos relacionados à sua busca.",
            "documentos_relevantes": resultados.to_dict('records'),
            "metadados": {
                "total_encontrados": len(resultados),
                "tipo_busca": "textual_simples",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")

@app.get("/api-brasil/concursos")
async def api_brasil_concursos():
    """Endpoint compatível com API externa"""
    try:
        # Simular dados da API externa usando nossos dados
        concursos_api = []
        for _, row in df_concursos.head(20).iterrows():
            concursos_api.append({
                "link": row.get('url', f"https://exemplo.com/concurso-{row.get('titulo', 'sem-titulo')}"),
                "organization": row.get('orgao', 'Órgão não informado'),
                "status": "Ativo",
                "workPlacesAvailable": row.get('vagas', 'Não informado')
            })
        
        return concursos_api
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na API Brasil: {str(e)}")

@app.get("/api-brasil/concursos/{estado}")
async def api_brasil_por_estado(estado: str):
    """Concursos por estado"""
    try:
        # Filtrar por estado se a coluna existir
        if 'estado' in df_concursos.columns:
            df_estado = df_concursos[df_concursos['estado'].str.upper() == estado.upper()]
        else:
            # Se não houver coluna estado, retornar amostra
            df_estado = df_concursos.head(10)
        
        concursos_estado = []
        for _, row in df_estado.iterrows():
            concursos_estado.append({
                "link": row.get('url', f"https://exemplo.com/concurso-{estado}"),
                "organization": row.get('orgao', 'Órgão não informado'),
                "status": "Ativo",
                "workPlacesAvailable": row.get('vagas', 'Não informado'),
                "estado": estado.upper()
            })
        
        return concursos_estado
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca por estado: {str(e)}")

@app.get("/orgaos")
async def listar_orgaos():
    """Lista todos os órgãos disponíveis"""
    try:
        orgaos = df_concursos['orgao'].dropna().unique().tolist()
        orgaos.sort()
        
        return {
            "orgaos": orgaos,
            "total": len(orgaos),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar órgãos: {str(e)}")

@app.get("/anos")
async def listar_anos():
    """Lista todos os anos disponíveis"""
    try:
        anos = df_concursos['ano'].dropna().unique().tolist()
        anos = [str(ano) for ano in anos]  # Convert to string
        anos.sort(reverse=True)  # Most recent first
        
        return {
            "anos": anos,
            "total": len(anos),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar anos: {str(e)}")

@app.get("/cargos")
async def listar_cargos():
    """Lista todos os cargos disponíveis"""
    try:
        cargos = df_concursos['cargo'].dropna().unique().tolist()
        cargos.sort()
        
        return {
            "cargos": cargos,
            "total": len(cargos),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar cargos: {str(e)}")

@app.get("/estatisticas")
async def obter_estatisticas():
    """Estatísticas gerais do sistema"""
    try:
        estatisticas = {
            "total_concursos": len(df_concursos),
            "total_orgaos": len(df_concursos['orgao'].dropna().unique()),
            "total_cargos": len(df_concursos['cargo'].dropna().unique()),
            "total_anos": len(df_concursos['ano'].dropna().unique()),
            "concursos_por_ano": df_concursos['ano'].value_counts().to_dict(),
            "concursos_por_orgao": df_concursos['orgao'].value_counts().head(10).to_dict(),
            "cargos_mais_comuns": df_concursos['cargo'].value_counts().head(10).to_dict(),
            "ultima_atualizacao": datetime.now().isoformat(),
            "status": "online"
        }
        
        return estatisticas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@app.get("/info", tags=["Sistema"])
async def sistema_info():
    """Informações detalhadas do sistema para a landing page"""
    try:
        return {
            "sistema": "ConcursAI",
            "versao": "2.0.1-Corrigida",
            "status": "online",
            "modo": "simplificado_funcional",
            "total_concursos": len(df_concursos),
            "porta": 8001,
            "acessos": {
                "landing_page": "/",
                "api_info": "/api",
                "documentacao": "/docs",
                "status_sistema": "/status",
                "listar_concursos": "/concursos",
                "buscar_concursos": "/buscar",
                "orgaos": "/orgaos",
                "anos": "/anos", 
                "cargos": "/cargos"
            },
            "funcionalidades": [
                "Busca textual inteligente",
                "Filtros por órgão/cargo/ano",
                "API REST completa",
                "Landing page interativa",
                "Documentação automática",
                "Sistema resiliente"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"erro": str(e)}

# Servir arquivos HTML estáticos
@app.get("/interface_pdf.html")
async def interface_pdf():
    """Servir interface PDF"""
    if os.path.exists("interface_pdf.html"):
        return FileResponse("interface_pdf.html")
    else:
        raise HTTPException(status_code=404, detail="Interface PDF não encontrada")

@app.get("/interface_html5_moderna.html")
async def interface_moderna():
    """Servir interface moderna"""
    if os.path.exists("interface_html5_moderna.html"):
        return FileResponse("interface_html5_moderna.html")
    else:
        raise HTTPException(status_code=404, detail="Interface moderna não encontrada")

@app.get("/editais")
async def interface_editais():
    """Servir interface de visualização de editais"""
    try:
        return FileResponse("static/interface_editais.html")
    except Exception as e:
        raise HTTPException(status_code=404, detail="Interface de editais não encontrada")

@app.get("/interface_pdf_final.html")
async def interface_pdf_final():
    """Servir interface PDF final"""
    if os.path.exists("interface_pdf_final.html"):
        return FileResponse("interface_pdf_final.html")
    else:
        raise HTTPException(status_code=404, detail="Interface PDF final não encontrada")

@app.get("/api-docs.html")
async def api_docs():
    """Servir documentação da API"""
    if os.path.exists("api-docs.html"):
        return FileResponse("api-docs.html")
    else:
        raise HTTPException(status_code=404, detail="Documentação da API não encontrada")

# Endpoints para coleta de dados reais
@app.post("/admin/atualizar-dados")
async def atualizar_dados_pci(background_tasks: BackgroundTasks, max_paginas: int = 10):
    """Atualiza dados coletando do PCI Concursos (execução em background)"""
    if not PCI_DISPONIVEL:
        raise HTTPException(status_code=503, detail="Integrador PCI não disponível")
    
    try:
        # Executar em background para não bloquear a API
        background_tasks.add_task(executar_atualizacao_pci, max_paginas)
        
        return {
            "status": "iniciado",
            "mensagem": "Atualização iniciada em background",
            "max_paginas": max_paginas,
            "tempo_estimado": f"{max_paginas * 2} minutos",
            "verificar_status": "/admin/status-atualizacao"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar atualização: {str(e)}")

@app.get("/admin/coletar-pci-real")
async def coletar_dados_pci_real():
    """Coleta dados reais do PCI Concursos usando o coletor simplificado"""
    if not COLETOR_REAL_DISPONIVEL:
        raise HTTPException(status_code=503, detail="Coletor real PCI não disponível")
    
    try:
        resultado = api_atualizar_dados()
        
        if resultado['status'] == 'sucesso':
            # Recarregar dados na memória
            global df_concursos
            df_concursos = carregar_dados_concursos()
            
            return {
                "status": "sucesso",
                "dados": resultado,
                "mensagem": f"✅ Dados atualizados! {resultado['novos_concursos']} novos concursos coletados do PCI."
            }
        else:
            raise HTTPException(status_code=500, detail=resultado.get('mensagem', 'Erro na coleta'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na coleta: {str(e)}")

@app.get("/admin/atualizar-dados-direto")
async def atualizar_dados_direto(max_paginas: int = 5):
    """Atualiza dados coletando do PCI Concursos (execução direta)"""
    # Tentar primeiro o coletor real
    if COLETOR_REAL_DISPONIVEL:
        try:
            resultado = api_atualizar_dados()
            
            if resultado['status'] == 'sucesso':
                # Recarregar dados na memória
                global df_concursos
                df_concursos = carregar_dados_concursos()
                
                return {
                    "status": "concluido",
                    "dados": resultado,
                    "mensagem": f"Dados atualizados com coletor real! {resultado['novos_concursos']} novos concursos coletados."
                }
        except Exception as e:
            print(f"Erro no coletor real: {e}")
    
    # Fallback para integrador original
    if not PCI_DISPONIVEL:
        raise HTTPException(status_code=503, detail="Nenhum integrador PCI disponível")
    
    try:
        integrador = IntegradorPCIConcursos()
        resultado = integrador.atualizar_dados_concursos(max_paginas)
        
        if 'erro' in resultado:
            raise HTTPException(status_code=500, detail=resultado['erro'])
        
        # Recarregar dados na memória
        global df_concursos
        df_concursos = carregar_dados_concursos()
        
        return {
            "status": "concluido",
            "dados": resultado,
            "mensagem": f"Dados atualizados com sucesso! {resultado.get('novos_concursos', 0)} novos concursos coletados."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na atualização: {str(e)}")

@app.get("/admin/status-dados")
async def status_dados():
    """Status atual dos dados do sistema"""
    try:
        if PCI_DISPONIVEL:
            integrador = IntegradorPCIConcursos()
            status_pci = integrador.status_dados()
        else:
            status_pci = {"status": "indisponivel", "mensagem": "Integrador PCI não disponível"}
        
        # Status dos dados carregados na API
        status_api = {
            "concursos_carregados": len(df_concursos),
            "arquivo_csv": "concursos_chunks.csv" if os.path.exists("concursos_chunks.csv") else "não encontrado",
            "ultima_verificacao": datetime.now().isoformat()
        }
        
        return {
            "api": status_api,
            "pci_integrador": status_pci,
            "integrador_disponivel": PCI_DISPONIVEL
        }
        
    except Exception as e:
        return {"erro": str(e)}

def executar_atualizacao_pci(max_paginas: int):
    """Função para executar atualização em background"""
    try:
        integrador = IntegradorPCIConcursos()
        resultado = integrador.atualizar_dados_concursos(max_paginas)
        
        # Salvar status da última atualização
        status_file = "ultima_atualizacao.json"
        with open(status_file, 'w') as f:
            json.dump({
                "resultado": resultado,
                "timestamp": datetime.now().isoformat(),
                "status": "concluido"
            }, f, indent=2)
        
        # Recarregar dados
        global df_concursos
        df_concursos = carregar_dados_concursos()
        
    except Exception as e:
        # Salvar erro
        with open("ultima_atualizacao.json", 'w') as f:
            json.dump({
                "erro": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "erro"
            }, f, indent=2)

@app.get("/admin/status-atualizacao")
async def status_ultima_atualizacao():
    """Status da última atualização executada"""
    try:
        if os.path.exists("ultima_atualizacao.json"):
            with open("ultima_atualizacao.json", 'r') as f:
                return json.load(f)
        else:
            return {"status": "nenhuma_atualizacao", "mensagem": "Nenhuma atualização executada ainda"}
    except Exception as e:
        return {"erro": str(e)}

if __name__ == "__main__":
    print("🚀 Iniciando ConcursAI API Simplificada...")
    print("📚 Documentação disponível em: http://localhost:8000/docs")
    print("🏠 Landing Page em: http://localhost:8000/")
    print("📋 Interface de Editais em: http://localhost:8000/editais")
    print("� Interfaces disponíveis:")
    print("   - http://localhost:8000/interface_pdf_final.html")
    print("   - http://localhost:8000/interface_html5_moderna.html")
    print("   - http://localhost:8000/api-docs.html")
    
    try:
        uvicorn.run(
            "api_simplificada:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        input("Pressione Enter para continuar...")
