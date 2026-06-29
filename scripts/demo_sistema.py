"""
🎬 DEMONSTRAÇÃO DO SISTEMA CONCURSAI
====================================
Script para demonstrar funcionalidades principais
"""

import sys
import os
from datetime import datetime
import time

def demonstrar_scraper():
    """Demonstra o funcionamento do scraper PCI"""
    print("\n" + "="*70)
    print("🕷️ DEMONSTRAÇÃO DO SCRAPER PCI CONCURSOS")
    print("="*70)
    
    try:
        from scrapers.pci_scraper import PCIConcursoScraper
        
        # Inicializar scraper
        print("\n✅ Inicializando scraper PCI Concursos...")
        scraper = PCIConcursoScraper(delay_range=(0.5, 1))
        
        # Coletar concursos
        print("📊 Coletando concursos (aguarde ~10 segundos)...")
        print("   ⏳ Acessando https://www.pciconcursos.com.br...")
        
        concursos = scraper.search_concursos(query="", pages=1)
        
        if concursos and len(concursos) > 0:
            print(f"\n✅ SUCESSO! {len(concursos)} concursos coletados")
            
            # Mostrar estatísticas
            print("\n📊 ESTATÍSTICAS DA COLETA:")
            print("-"*70)
            
            # Contar por estado
            estados = {}
            orgaos = {}
            vagas_total = 0
            
            for c in concursos:
                # Estado
                loc = c.get('localizacao', 'N/A')
                estados[loc] = estados.get(loc, 0) + 1
                
                # Órgão
                org = c.get('orgao', 'N/A')
                orgaos[org] = orgaos.get(org, 0) + 1
                
                # Vagas
                vagas = c.get('vagas', 0)
                if isinstance(vagas, int):
                    vagas_total += vagas
            
            print(f"📍 Estados: {len(estados)} diferentes")
            print(f"🏛️ Órgãos: {len(orgaos)} diferentes")
            print(f"👥 Total de Vagas: {vagas_total}")
            
            # Mostrar top 5 concursos
            print("\n🏆 TOP 5 CONCURSOS COLETADOS:")
            print("-"*70)
            
            for i, concurso in enumerate(concursos[:5], 1):
                print(f"\n{i}. 📄 {concurso.get('titulo', 'Título não disponível')}")
                print(f"   🏛️  Órgão: {concurso.get('orgao', 'N/A')}")
                print(f"   📍 Local: {concurso.get('localizacao', 'N/A')}")
                print(f"   👥 Vagas: {concurso.get('vagas', 'N/A')}")
                print(f"   💰 Salário: {concurso.get('salario', 'N/A')}")
                print(f"   📚 Escolaridade: {concurso.get('escolaridade', 'N/A')}")
                print(f"   ⏰ Inscrições: {concurso.get('inscricoes', 'N/A')}")
                print(f"   🔗 Link: {concurso.get('link', 'N/A')[:60]}...")
            
            # Salvar em arquivo
            try:
                import json
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"demo_concursos_{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(concursos, f, ensure_ascii=False, indent=2)
                
                print(f"\n💾 Dados salvos em: {filename}")
                
            except Exception as e:
                print(f"⚠️ Não foi possível salvar arquivo: {e}")
            
            return True, concursos
            
        else:
            print("⚠️ Nenhum concurso foi coletado")
            return False, []
            
    except ImportError as e:
        print(f"❌ Erro ao importar módulo: {e}")
        print("💡 Verifique se o arquivo scrapers/pci_scraper.py existe")
        return False, []
        
    except Exception as e:
        print(f"❌ Erro durante a coleta: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def demonstrar_processamento_dados(concursos):
    """Demonstra processamento dos dados coletados"""
    if not concursos:
        print("\n⚠️ Sem dados para processar")
        return
    
    print("\n" + "="*70)
    print("📊 DEMONSTRAÇÃO DE ANÁLISE DE DADOS")
    print("="*70)
    
    try:
        import pandas as pd
        
        # Criar DataFrame
        df = pd.DataFrame(concursos)
        
        print(f"\n✅ DataFrame criado com {len(df)} registros")
        print(f"📋 Colunas: {', '.join(df.columns.tolist())}")
        
        # Análise por estado
        if 'localizacao' in df.columns:
            print("\n📍 TOP 5 ESTADOS COM MAIS CONCURSOS:")
            print("-"*70)
            top_estados = df['localizacao'].value_counts().head()
            for estado, count in top_estados.items():
                print(f"   {estado}: {count} concursos")
        
        # Análise por órgão
        if 'orgao' in df.columns:
            print("\n🏛️ TOP 5 ÓRGÃOS COM MAIS CONCURSOS:")
            print("-"*70)
            top_orgaos = df['orgao'].value_counts().head()
            for orgao, count in top_orgaos.items():
                print(f"   {orgao[:50]}: {count} concursos")
        
        # Análise de vagas
        if 'vagas' in df.columns:
            df_vagas = df[df['vagas'] > 0]
            if len(df_vagas) > 0:
                print("\n👥 ANÁLISE DE VAGAS:")
                print("-"*70)
                print(f"   Total de vagas: {df_vagas['vagas'].sum()}")
                print(f"   Média de vagas: {df_vagas['vagas'].mean():.1f}")
                print(f"   Maior concurso: {df_vagas['vagas'].max()} vagas")
        
        # Salvar CSV
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = f"demo_analise_{timestamp}.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"\n💾 Análise salva em: {csv_file}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar CSV: {e}")
        
    except ImportError:
        print("⚠️ Pandas não disponível")
    except Exception as e:
        print(f"❌ Erro na análise: {e}")

def verificar_arquivos_sistema():
    """Verifica os principais arquivos do sistema"""
    print("\n" + "="*70)
    print("📁 VERIFICAÇÃO DE ARQUIVOS DO SISTEMA")
    print("="*70)
    
    componentes = {
        "🚀 Sistema Principal": [
            "sistema_completo.py",
            "api_fastapi.py",
            "start_sistema_final.py"
        ],
        "🕷️ Scrapers": [
            "scrapers/pci_scraper.py",
            "scrapers/concursos_brasil_scraper.py",
            "scrapers/scraper_manager.py"
        ],
        "🌐 Interfaces": [
            "index.html",
            "dashboard_completo.html",
            "interface_pdf.html"
        ],
        "🧠 Módulos IA": [
            "modules/concurso_rag.py",
            "modules/concurso_embeddings.py",
            "modules/pdf_processor.py"
        ],
        "📊 Dados": [
            "concursos_chunks.csv",
            "data/concursos.db"
        ]
    }
    
    total_encontrados = 0
    total_arquivos = 0
    
    for categoria, arquivos in componentes.items():
        print(f"\n{categoria}")
        print("-"*70)
        
        for arquivo in arquivos:
            total_arquivos += 1
            existe = os.path.exists(arquivo)
            status = "✅" if existe else "❌"
            
            if existe:
                total_encontrados += 1
                # Mostrar tamanho do arquivo
                try:
                    size = os.path.getsize(arquivo)
                    if size > 1024*1024:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    elif size > 1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size} bytes"
                    print(f"{status} {arquivo} ({size_str})")
                except:
                    print(f"{status} {arquivo}")
            else:
                print(f"{status} {arquivo}")
    
    print("\n" + "="*70)
    print(f"📊 TOTAL: {total_encontrados}/{total_arquivos} arquivos encontrados")
    print("="*70)

def mostrar_informacoes_sistema():
    """Mostra informações sobre o sistema"""
    print("\n" + "="*70)
    print("ℹ️ INFORMAÇÕES DO SISTEMA")
    print("="*70)
    
    import sys
    import platform
    
    print(f"\n🐍 Python: {sys.version.split()[0]}")
    print(f"💻 Sistema: {platform.system()} {platform.release()}")
    print(f"📂 Diretório: {os.getcwd()}")
    
    # Verificar pacotes importantes
    print("\n📦 PACOTES INSTALADOS:")
    print("-"*70)
    
    pacotes = [
        'requests', 'beautifulsoup4', 'pandas', 'fastapi', 
        'uvicorn', 'streamlit', 'langchain', 'pypdf'
    ]
    
    for pacote in pacotes:
        try:
            mod = __import__(pacote)
            version = getattr(mod, '__version__', 'versão desconhecida')
            print(f"✅ {pacote}: {version}")
        except ImportError:
            print(f"❌ {pacote}: não instalado")

def main():
    """Função principal da demonstração"""
    
    print("\n" + "="*70)
    print("🎯 DEMONSTRAÇÃO COMPLETA DO SISTEMA CONCURSAI")
    print("="*70)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}")
    print(f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}")
    
    # 1. Informações do sistema
    mostrar_informacoes_sistema()
    
    # 2. Verificar arquivos
    verificar_arquivos_sistema()
    
    # 3. Demonstrar scraper
    print("\n⏳ Pressione Enter para iniciar demonstração do scraper...")
    input()
    
    sucesso, concursos = demonstrar_scraper()
    
    # 4. Análise de dados
    if sucesso and concursos:
        print("\n⏳ Pressione Enter para ver análise dos dados...")
        input()
        demonstrar_processamento_dados(concursos)
    
    # 5. Informações finais
    print("\n" + "="*70)
    print("🎉 DEMONSTRAÇÃO CONCLUÍDA!")
    print("="*70)
    
    print("\n📖 COMO USAR O SISTEMA:")
    print("-"*70)
    print("1. 🚀 Iniciar sistema completo:")
    print("   python sistema_completo.py")
    print()
    print("2. 🌐 Acessar interfaces:")
    print("   - Landing Page: file:///index.html")
    print("   - Dashboard: file:///dashboard_completo.html")
    print("   - API: http://localhost:8001")
    print("   - Documentação: http://localhost:8001/docs")
    print()
    print("3. 🕷️ Executar scrapers manualmente:")
    print("   from scrapers.pci_scraper import PCIConcursoScraper")
    print("   scraper = PCIConcursoScraper()")
    print("   concursos = scraper.search_concursos(pages=5)")
    print()
    print("4. 🤖 Usar RAG/IA:")
    print("   from modules.concurso_rag import responder_interface")
    print("   resposta = responder_interface('Qual o salário...')")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Demonstração interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
