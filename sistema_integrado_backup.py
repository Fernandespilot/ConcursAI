"""
🎯 SISTEMA INTEGRADO CONCURSAI - Versão Final
===========================================
Sistema completo integrando scrapers + API + Interface moderna
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import pandas as pd
import json
import asyncio
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict, Optional
import sys
import os

# Adicionar o diretório de scrapers ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scrapers'))

try:
    from scrapers.scraper_manager_v3 import ScraperManagerV3
    SCRAPER_V3_DISPONIVEL = True
    print("✅ ScraperManagerV3 (Híbrido) carregado")
except ImportError:
    try:
        from scrapers.scraper_manager_completo import ScraperManagerCompleto
        SCRAPER_V3_DISPONIVEL = False
        print("⚠️ Usando ScraperManagerCompleto (fallback)")
    except ImportError:
        try:
            from scrapers.scraper_resiliente import ScraperResiliente
            SCRAPER_V3_DISPONIVEL = False
            SCRAPER_RESILIENTE = True
            print("🛡️ Usando ScraperResiliente (sempre funciona)")
        except ImportError:
            print("⚠️ Erro ao importar scrapers. Criando versão mock...")
            
            class ScraperManagerCompleto:
                def __init__(self):
                    self.dados_por_fonte = {}
                    self.todos_concursos = []
                    self.concursos_coletados = []
                
                def coletar_todos_sites(self, pci_pages=25, brasil_pages=20):
                    return {
                        'pci_concurso': [],
                        'concursos_brasil': [],
                        'total_geral': 0,
                        'sucesso': True
                    }
            
            SCRAPER_V3_DISPONIVEL = False
            SCRAPER_RESILIENTE = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="ConcursAI API",
    description="Sistema Inteligente de Coleta e Análise de Concursos Públicos",
    version="2.0.0"
)

# Variáveis globais
if SCRAPER_V3_DISPONIVEL:
    scraper_manager = ScraperManagerV3()
    print("🎯 Sistema usando ScraperManagerV3 (Híbrido Inteligente)")
elif 'SCRAPER_RESILIENTE' in globals() and SCRAPER_RESILIENTE:
    scraper_manager = ScraperResiliente()
    print("🛡️ Sistema usando ScraperResiliente (Sempre Funciona)")
else:
    scraper_manager = ScraperManagerCompleto()
    print("⚠️ Sistema usando ScraperManagerCompleto (Fallback)")
dados_sistema = {
    'concursos': [],
    'estatisticas': {
        'total_concursos': 0,
        'total_vagas': 0,
        'pci_concursos': 0,
        'brasil_concursos': 0,
        'ultima_coleta': None
    },
    'status_coleta': {
        'em_progresso': False,
        'progresso': 0,
        'mensagem': ''
    }
}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Servir dashboard moderno"""
    try:
        dashboard_path = Path(__file__).parent / "dashboard_moderno.html"
        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="""
                <h1>ConcursAI Dashboard</h1>
                <p>Dashboard não encontrado. Certifique-se de que o arquivo dashboard_moderno.html existe.</p>
            """)
    except Exception as e:
        logger.error(f"Erro ao carregar dashboard: {e}")
        return HTMLResponse(content=f"<h1>Erro</h1><p>{str(e)}</p>")

@app.get("/api/status")
async def obter_status():
    """Obter status atual do sistema"""
    return {
        'sistema': 'ConcursAI v2.0',
        'status': 'ativo',
        'timestamp': datetime.now().isoformat(),
        'estatisticas': dados_sistema['estatisticas'],
        'coleta_em_progresso': dados_sistema['status_coleta']['em_progresso']
    }

@app.get("/api/estatisticas")
async def obter_estatisticas():
    """Obter estatísticas detalhadas"""
    try:
        concursos = dados_sistema['concursos']
        
        if not concursos:
            return {
                'total_concursos': 0,
                'total_vagas': 0,
                'pci_concursos': 0,
                'brasil_concursos': 0,
                'media_vagas': 0,
                'maior_salario': 0,
                'top_escolaridade': 'Nenhum dado',
                'distribuicao_fontes': {},
                'top_orgaos': {},
                'ultima_atualizacao': None
            }
        
        df = pd.DataFrame(concursos)
        
        # Calcular estatísticas
        stats = {
            'total_concursos': len(df),
            'total_vagas': int(df['vagas'].sum()) if 'vagas' in df.columns else 0,
            'pci_concursos': len(df[df['fonte'] == 'PCI Concurso']) if 'fonte' in df.columns else 0,
            'brasil_concursos': len(df[df['fonte'] == 'Concursos Brasil']) if 'fonte' in df.columns else 0,
            'media_vagas': float(df['vagas'].mean()) if 'vagas' in df.columns else 0,
            'maior_salario': float(df['salario_numerico'].max()) if 'salario_numerico' in df.columns else 0,
            'top_escolaridade': df['escolaridade'].value_counts().index[0] if 'escolaridade' in df.columns and len(df) > 0 else 'Nenhum dado',
            'distribuicao_fontes': df['fonte'].value_counts().to_dict() if 'fonte' in df.columns else {},
            'top_orgaos': df['orgao'].value_counts().head(10).to_dict() if 'orgao' in df.columns else {},
            'ultima_atualizacao': dados_sistema['estatisticas']['ultima_coleta']
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        return {
            'erro': str(e),
            'total_concursos': 0,
            'total_vagas': 0
        }

@app.get("/api/concursos")
async def listar_concursos(limite: int = 100, fonte: Optional[str] = None):
    """Listar concursos com filtros opcionais"""
    try:
        concursos = dados_sistema['concursos']
        
        # Aplicar filtro de fonte se especificado
        if fonte:
            concursos = [c for c in concursos if c.get('fonte', '').lower() == fonte.lower()]
        
        # Limitar resultados
        concursos = concursos[:limite]
        
        return {
            'concursos': concursos,
            'total': len(concursos),
            'filtros_aplicados': {'fonte': fonte, 'limite': limite}
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar concursos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coletar/todos")
async def coletar_todos_sites(background_tasks: BackgroundTasks, pci_pages: int = 25, brasil_pages: int = 20):
    """Iniciar coleta de todos os sites"""
    
    if dados_sistema['status_coleta']['em_progresso']:
        raise HTTPException(status_code=409, detail="Coleta já em progresso")
    
    # Marcar coleta como em progresso
    dados_sistema['status_coleta']['em_progresso'] = True
    dados_sistema['status_coleta']['progresso'] = 0
    dados_sistema['status_coleta']['mensagem'] = 'Iniciando coleta...'
    
    # Executar coleta em background
    background_tasks.add_task(executar_coleta_completa, pci_pages, brasil_pages)
    
    return {
        'sucesso': True,
        'mensagem': 'Coleta iniciada em background',
        'estimativa_tempo': '5-10 minutos'
    }

@app.post("/api/coletar/pci")
async def coletar_pci(background_tasks: BackgroundTasks, max_pages: int = 25):
    """Coletar apenas PCI Concurso"""
    
    if dados_sistema['status_coleta']['em_progresso']:
        raise HTTPException(status_code=409, detail="Coleta já em progresso")
    
    dados_sistema['status_coleta']['em_progresso'] = True
    background_tasks.add_task(executar_coleta_pci, max_pages)
    
    return {'sucesso': True, 'mensagem': 'Coleta PCI iniciada'}

@app.post("/api/coletar/brasil")
async def coletar_brasil(background_tasks: BackgroundTasks, max_pages: int = 20):
    """Coletar apenas Concursos Brasil"""
    
    if dados_sistema['status_coleta']['em_progresso']:
        raise HTTPException(status_code=409, detail="Coleta já em progresso")
    
    dados_sistema['status_coleta']['em_progresso'] = True
    background_tasks.add_task(executar_coleta_brasil, max_pages)
    
    return {'sucesso': True, 'mensagem': 'Coleta Brasil iniciada'}

@app.get("/api/progresso")
async def obter_progresso():
    """Obter progresso da coleta atual"""
    return dados_sistema['status_coleta']

@app.get("/api/exportar/{formato}")
async def exportar_dados(formato: str):
    """Exportar dados em diferentes formatos"""
    
    if not dados_sistema['concursos']:
        raise HTTPException(status_code=404, detail="Nenhum dado para exportar")
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)
        
        df = pd.DataFrame(dados_sistema['concursos'])
        
        if formato.lower() == 'csv':
            filename = output_dir / f"concursos_export_{timestamp}.csv"
            df.to_csv(filename, index=False, encoding='utf-8')
            
        elif formato.lower() == 'json':
            filename = output_dir / f"concursos_export_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dados_sistema['concursos'], f, ensure_ascii=False, indent=2)
                
        elif formato.lower() == 'excel':
            filename = output_dir / f"concursos_export_{timestamp}.xlsx"
            df.to_excel(filename, index=False)
            
        else:
            raise HTTPException(status_code=400, detail="Formato não suportado")
        
        return FileResponse(
            path=str(filename),
            filename=filename.name,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Erro na exportação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/dados")
async def limpar_dados():
    """Limpar todos os dados coletados"""
    dados_sistema['concursos'] = []
    dados_sistema['estatisticas'] = {
        'total_concursos': 0,
        'total_vagas': 0,
        'pci_concursos': 0,
        'brasil_concursos': 0,
        'ultima_coleta': None
    }
    
    return {'sucesso': True, 'mensagem': 'Dados limpos com sucesso'}

# Funções de background
async def executar_coleta_completa(pci_pages: int, brasil_pages: int):
    """Executar coleta completa em background"""
    try:
        logger.info("🚀 Iniciando coleta completa")
        
        # Atualizar progresso
        dados_sistema['status_coleta']['mensagem'] = 'Coletando dados...'
        dados_sistema['status_coleta']['progresso'] = 10
        
        # Executar coleta
        if SCRAPER_V3_DISPONIVEL:
            resultados = scraper_manager.coletar_todos_sites(pci_pages, brasil_pages)
            
            # Atualizar dados do sistema com resultado V3
            if resultados['sucesso']:
                dados_sistema['concursos'] = scraper_manager.concursos_coletados
        else:
            # Fallback para manager antigo
            resultados = scraper_manager.coletar_todos_sites(pci_pages, brasil_pages)
            
            if resultados['sucesso']:
                dados_sistema['concursos'] = scraper_manager.todos_concursos
        
        if resultados['sucesso']:
            # Atualizar dados do sistema
            if not dados_sistema['concursos']:  # Se não foi atualizado acima
                if SCRAPER_V3_DISPONIVEL and hasattr(scraper_manager, 'concursos_coletados'):
                    dados_sistema['concursos'] = scraper_manager.concursos_coletados
                elif hasattr(scraper_manager, 'todos_concursos'):
                    dados_sistema['concursos'] = scraper_manager.todos_concursos
                else:
                    # Para scraper resiliente, montar lista unificada
                    dados_sistema['concursos'] = resultados['pci_concurso'] + resultados['concursos_brasil']
            
            # Atualizar estatísticas
            atualizar_estatisticas()
            
            dados_sistema['status_coleta']['progresso'] = 100
            
            # Mensagem personalizada baseada na estratégia
            estrategia = resultados.get('estrategia_usada', 'desconhecida')
            if 'exemplo' in estrategia:
                dados_sistema['status_coleta']['mensagem'] = f'Coleta finalizada com dados de exemplo! {resultados["total_geral"]} concursos (sites inacessíveis)'
            else:
                dados_sistema['status_coleta']['mensagem'] = f'Coleta finalizada! {resultados["total_geral"]} concursos coletados'
            
            logger.info(f"✅ Coleta completa finalizada: {resultados['total_geral']} concursos")
            
        else:
            dados_sistema['status_coleta']['mensagem'] = 'Erro na coleta'
            logger.error("❌ Falha na coleta completa")
            
    except Exception as e:
        logger.error(f"❌ Erro na coleta: {e}")
        dados_sistema['status_coleta']['mensagem'] = f'Erro: {str(e)}'
    
    finally:
        # Resetar status após 30 segundos
        await asyncio.sleep(30)
        dados_sistema['status_coleta']['em_progresso'] = False
        dados_sistema['status_coleta']['progresso'] = 0

async def executar_coleta_pci(max_pages: int):
    """Executar coleta PCI em background"""
    try:
        logger.info("🚀 Iniciando coleta PCI")
        dados_sistema['status_coleta']['mensagem'] = 'Coletando PCI Concurso...'
        
        concursos = scraper_manager.coletar_pci_concurso(max_pages)
        
        if concursos:
            # Adicionar aos dados existentes
            dados_sistema['concursos'].extend(concursos)
            atualizar_estatisticas()
            dados_sistema['status_coleta']['mensagem'] = f'PCI: {len(concursos)} concursos coletados'
            
        dados_sistema['status_coleta']['progresso'] = 100
        
    except Exception as e:
        logger.error(f"❌ Erro na coleta PCI: {e}")
        dados_sistema['status_coleta']['mensagem'] = f'Erro PCI: {str(e)}'
    
    finally:
        await asyncio.sleep(10)
        dados_sistema['status_coleta']['em_progresso'] = False

async def executar_coleta_brasil(max_pages: int):
    """Executar coleta Brasil em background"""
    try:
        logger.info("🚀 Iniciando coleta Brasil")
        dados_sistema['status_coleta']['mensagem'] = 'Coletando Concursos Brasil...'
        
        concursos = scraper_manager.coletar_concursos_brasil(max_pages)
        
        if concursos:
            dados_sistema['concursos'].extend(concursos)
            atualizar_estatisticas()
            dados_sistema['status_coleta']['mensagem'] = f'Brasil: {len(concursos)} concursos coletados'
            
        dados_sistema['status_coleta']['progresso'] = 100
        
    except Exception as e:
        logger.error(f"❌ Erro na coleta Brasil: {e}")
        dados_sistema['status_coleta']['mensagem'] = f'Erro Brasil: {str(e)}'
    
    finally:
        await asyncio.sleep(10)
        dados_sistema['status_coleta']['em_progresso'] = False

def atualizar_estatisticas():
    """Atualizar estatísticas do sistema"""
    concursos = dados_sistema['concursos']
    
    if not concursos:
        return
    
    df = pd.DataFrame(concursos)
    
    dados_sistema['estatisticas'] = {
        'total_concursos': len(df),
        'total_vagas': int(df['vagas'].sum()) if 'vagas' in df.columns else 0,
        'pci_concursos': len(df[df['fonte'] == 'PCI Concurso']) if 'fonte' in df.columns else 0,
        'brasil_concursos': len(df[df['fonte'] == 'Concursos Brasil']) if 'fonte' in df.columns else 0,
        'ultima_coleta': datetime.now().isoformat()
    }

def main():
    """Função principal"""
    print("🚀 INICIANDO CONCURSAI SISTEMA INTEGRADO")
    print("=" * 60)
    print("🌐 Dashboard: http://localhost:8003")
    print("📊 API Docs: http://localhost:8003/docs")
    print("=" * 60)
    
    try:
        uvicorn.run(
            "sistema_integrado:app",
            host="0.0.0.0",
            port=8003,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n⏹️ Sistema encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar sistema: {e}")

if __name__ == "__main__":
    main()
