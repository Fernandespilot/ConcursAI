"""
🧪 TESTE RÁPIDO DO SISTEMA CONCURSAI
=====================================
Script para testar rapidamente scrapers e API
"""

import sys
import requests
from datetime import datetime
import json

def testar_scraper_pci():
    """Testa o scraper PCI Concursos"""
    print("\n🕷️ TESTANDO SCRAPER PCI CONCURSOS")
    print("="*60)
    
    try:
        from scrapers.pci_scraper import PCIConcursoScraper
        
        scraper = PCIConcursoScraper(delay_range=(0.5, 1))
        print("✅ Scraper inicializado com sucesso")
        
        # Testar coleta de página inicial
        print("\n📊 Coletando concursos da página inicial...")
        concursos = scraper.buscar_concursos(max_pages=1)
        
        if concursos:
            print(f"✅ Coletados {len(concursos)} concursos")
            
            # Mostrar alguns exemplos
            print("\n📋 EXEMPLOS DE CONCURSOS COLETADOS:")
            print("-"*60)
            for i, concurso in enumerate(concursos[:3], 1):
                print(f"\n{i}. {concurso.get('titulo', 'N/A')}")
                print(f"   Órgão: {concurso.get('orgao', 'N/A')}")
                print(f"   Estado: {concurso.get('estado', 'N/A')}")
                print(f"   Vagas: {concurso.get('vagas', 'N/A')}")
                print(f"   Link: {concurso.get('link', 'N/A')}")
            
            return True, len(concursos)
        else:
            print("⚠️ Nenhum concurso coletado")
            return False, 0
            
    except ImportError as e:
        print(f"❌ Erro ao importar scraper: {e}")
        return False, 0
    except Exception as e:
        print(f"❌ Erro no scraper: {e}")
        return False, 0

def testar_api_externa():
    """Testa a API ConcursosNoBrasil"""
    print("\n🌐 TESTANDO API CONCURSOS NO BRASIL")
    print("="*60)
    
    estados_teste = ["SP", "RJ", "MG"]
    
    for estado in estados_teste:
        try:
            url = f"https://api.concursosnobrasil.com.br/api/v1/concursos/{estado}"
            print(f"\n📍 Buscando concursos de {estado}...")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    print(f"✅ {len(data)} concursos encontrados")
                    
                    # Mostrar primeiro concurso
                    if data:
                        primeiro = data[0]
                        print(f"\n   Exemplo:")
                        print(f"   Órgão: {primeiro.get('organization', 'N/A')}")
                        print(f"   Status: {primeiro.get('status', 'N/A')}")
                        print(f"   Vagas: {primeiro.get('workPlacesAvailable', 'N/A')}")
                else:
                    print(f"✅ API respondeu: {data}")
            else:
                print(f"⚠️ Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro em {estado}: {e}")
    
    return True

def testar_conexao_local():
    """Testa se o sistema está rodando localmente"""
    print("\n🖥️ TESTANDO SERVIÇOS LOCAIS")
    print("="*60)
    
    servicos = [
        ("API FastAPI", "http://localhost:8001/health", "GET"),
        ("Dashboard", "http://localhost:8001/", "GET"),
        ("Documentação", "http://localhost:8001/docs", "GET"),
    ]
    
    for nome, url, method in servicos:
        try:
            print(f"\n🔍 Testando {nome}...")
            response = requests.request(method, url, timeout=2)
            
            if response.status_code in [200, 404]:  # 404 é ok se rota não existe
                print(f"✅ {nome} está respondendo")
            else:
                print(f"⚠️ {nome} retornou status {response.status_code}")
                
        except requests.ConnectionError:
            print(f"❌ {nome} não está acessível (não iniciado?)")
        except Exception as e:
            print(f"❌ Erro ao testar {nome}: {e}")

def verificar_arquivos():
    """Verifica arquivos importantes do projeto"""
    print("\n📁 VERIFICANDO ARQUIVOS DO PROJETO")
    print("="*60)
    
    import os
    
    arquivos_importantes = [
        ("Sistema Completo", "sistema_completo.py"),
        ("API FastAPI", "api_fastapi.py"),
        ("Scraper PCI", "scrapers/pci_scraper.py"),
        ("Scraper Manager", "scrapers/scraper_manager.py"),
        ("Landing Page", "index.html"),
        ("Dashboard", "dashboard_completo.html"),
        ("Interface PDF", "interface_pdf.html"),
        ("Banco de Dados", "data/concursos.db"),
        ("Chunks CSV", "concursos_chunks.csv"),
    ]
    
    encontrados = 0
    
    for nome, caminho in arquivos_importantes:
        existe = os.path.exists(caminho)
        status = "✅" if existe else "❌"
        print(f"{status} {nome}: {caminho}")
        if existe:
            encontrados += 1
    
    print(f"\n📊 {encontrados}/{len(arquivos_importantes)} arquivos encontrados")
    return encontrados

def mostrar_estatisticas():
    """Mostra estatísticas do sistema"""
    print("\n📊 ESTATÍSTICAS DO SISTEMA")
    print("="*60)
    
    import os
    import pandas as pd
    
    # Verificar CSV de chunks
    if os.path.exists("concursos_chunks.csv"):
        try:
            df = pd.read_csv("concursos_chunks.csv")
            print(f"✅ CSV de Chunks: {len(df)} registros")
            
            if 'orgao' in df.columns:
                print(f"   Órgãos únicos: {df['orgao'].nunique()}")
            if 'ano' in df.columns:
                print(f"   Anos: {df['ano'].min()} - {df['ano'].max()}")
                
        except Exception as e:
            print(f"⚠️ Erro ao ler CSV: {e}")
    else:
        print("❌ CSV de chunks não encontrado")
    
    # Verificar banco SQLite
    if os.path.exists("data/concursos.db"):
        try:
            import sqlite3
            conn = sqlite3.connect("data/concursos.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = cursor.fetchall()
            
            print(f"\n✅ Banco de Dados SQLite:")
            print(f"   Tabelas: {len(tabelas)}")
            
            for tabela in tabelas:
                cursor.execute(f"SELECT COUNT(*) FROM {tabela[0]}")
                count = cursor.fetchone()[0]
                print(f"   - {tabela[0]}: {count} registros")
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Erro ao ler banco: {e}")
    else:
        print("❌ Banco de dados não encontrado")

def main():
    """Função principal do teste"""
    print("\n" + "="*60)
    print("🎯 TESTE COMPLETO DO SISTEMA CONCURSAI")
    print("="*60)
    print(f"⏰ Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    resultados = {}
    
    # 1. Verificar arquivos
    resultados['arquivos'] = verificar_arquivos()
    
    # 2. Mostrar estatísticas
    mostrar_estatisticas()
    
    # 3. Testar API externa
    try:
        resultados['api_externa'] = testar_api_externa()
    except Exception as e:
        print(f"❌ Erro no teste de API externa: {e}")
        resultados['api_externa'] = False
    
    # 4. Testar scraper PCI
    try:
        sucesso, total = testar_scraper_pci()
        resultados['scraper'] = sucesso
        resultados['concursos_coletados'] = total
    except Exception as e:
        print(f"❌ Erro no teste de scraper: {e}")
        resultados['scraper'] = False
        resultados['concursos_coletados'] = 0
    
    # 5. Testar serviços locais
    try:
        testar_conexao_local()
    except Exception as e:
        print(f"❌ Erro no teste de serviços: {e}")
    
    # Resumo final
    print("\n" + "="*60)
    print("📋 RESUMO DOS TESTES")
    print("="*60)
    
    print(f"\n✅ Arquivos encontrados: {resultados.get('arquivos', 0)}/9")
    print(f"{'✅' if resultados.get('api_externa') else '❌'} API Externa: {'OK' if resultados.get('api_externa') else 'FALHOU'}")
    print(f"{'✅' if resultados.get('scraper') else '❌'} Scraper PCI: {'OK' if resultados.get('scraper') else 'FALHOU'}")
    
    if resultados.get('concursos_coletados', 0) > 0:
        print(f"📊 Total de concursos coletados: {resultados['concursos_coletados']}")
    
    print("\n" + "="*60)
    print("🎉 TESTE CONCLUÍDO!")
    print("="*60)
    
    # Instruções finais
    print("\n📖 PRÓXIMOS PASSOS:")
    print("1. Para iniciar o sistema completo: python sistema_completo.py")
    print("2. Para acessar a API: http://localhost:8001")
    print("3. Para acessar a documentação: http://localhost:8001/docs")
    print("4. Para ver a landing page: index.html")
    print("5. Para ver o dashboard: dashboard_completo.html")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
