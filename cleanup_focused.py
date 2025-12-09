#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 LIMPEZA DIRECIONADA - CONCURSAI
==================================
Remove arquivos definitivamente desnecessários identificados
"""

import os
import shutil
from pathlib import Path

def safe_remove(file_path, category, force=False):
    """Remove arquivo com segurança"""
    try:
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        if file_path.exists():
            if file_path.is_dir():
                shutil.rmtree(file_path)
                print(f"✅ Diretório removido: {file_path.name} ({category})")
            else:
                if not force:
                    # Verificar se arquivo está vazio ou muito pequeno
                    size = file_path.stat().st_size
                    if size > 10000:  # > 10KB
                        print(f"⚠️  PULADO (muito grande): {file_path.name} ({size/1024:.1f}KB)")
                        return False
                
                file_path.unlink()
                print(f"✅ Arquivo removido: {file_path.name} ({category})")
            return True
        else:
            print(f"⚠️  Não encontrado: {file_path}")
            return False
    except Exception as e:
        print(f"❌ Erro removendo {file_path}: {e}")
        return False

def main():
    """Executa limpeza direcionada"""
    
    print("🧹 LIMPEZA DIRECIONADA - PROJETO CONCURSAI")
    print("=" * 50)
    
    project_root = Path(".")
    os.chdir(project_root)
    
    removed_count = 0
    
    # 1. SCRIPTS PONTUAIS JÁ EXECUTADOS (100% seguros)
    print("\n🗑️  Removendo scripts pontuais já executados...")
    pontual_scripts = [
        'cleanup_obsolete.py',        # Script de limpeza antigo
        'migrate_to_v2.py',          # Migração já realizada
        'gerar_csv_exemplo.py',      # Dados exemplo já gerados
        'adicionar_dados_exemplo.py', # Dados exemplo já adicionados
        'fix_langchain_deps.py',     # Fix já aplicado
        'fix_sqlite.py',             # Fix já aplicado
        'relatorio_correcoes.py',    # Relatório já gerado
        'corrigir_porta.py',         # Correção já aplicada
        'corrigir_sistema.py',       # Correção já aplicada
        'organize_project.py',       # Organização já feita
        'organize_project_simple.py' # Organização já feita
    ]
    
    for script_file in pontual_scripts:
        if safe_remove(script_file, "Script Pontual Executado", force=True):
            removed_count += 1
    
    # 2. DEMOS E EXEMPLOS REDUNDANTES
    print("\n🗑️  Removendo demos e exemplos redundantes...")
    demo_files = [
        'demo_api_integracao.py',    # Demo, não é o sistema principal
        'demo_fastapi.py',           # Demo, não é o sistema principal  
        'demo_scrapers.py',          # Demo, não é o sistema principal
        'demo_interfaces.py',        # Demo, não é o sistema principal
        'demo_sistema_completo.py',  # Demo, não é o sistema principal
        'demo_sistema_resiliente.py', # Demo, não é o sistema principal
        'demonstracao_scrapers.py'   # Demo, não é o sistema principal
    ]
    
    for demo_file in demo_files:
        if safe_remove(demo_file, "Demo/Exemplo"):
            removed_count += 1
    
    # 3. VERSÕES ANTIGAS DE APIS (manter apenas api_simplificada.py)
    print("\n🗑️  Removendo versões antigas de APIs...")
    old_apis = [
        'api_fastapi_backup.py',     # Backup antigo
        'api_fastapi_old.py',        # Versão antiga
        'api_fast_simple.py',        # Versão simplificada anterior
        # 'api_fastapi.py',           # Pode ser mantido como referência
    ]
    
    for api_file in old_apis:
        if safe_remove(api_file, "API Antiga"):
            removed_count += 1
    
    # 4. APPS ANTIGOS (manter apenas sistema principal)
    print("\n🗑️  Removendo aplicações antigas...")
    old_apps = [
        'app_completo.py',           # App Gradio antigo
        'app_simples.py',            # App Gradio simples
        'app_simples_rag.py',        # App Gradio RAG
        'concurso_app.py',           # App antigo
        'concursai_final_garantido.py', # Versão antiga
        'concursai_corrigido.py'     # Versão corrigida antiga
    ]
    
    for app_file in old_apps:
        if safe_remove(app_file, "App Antigo"):
            removed_count += 1
    
    # 5. SCRIPTS DE ANÁLISE E DIAGNÓSTICO ANTIGOS
    print("\n🗑️  Removendo scripts de análise antigos...")
    analysis_scripts = [
        'analise_scraping_estrategias.py',  # Análise já feita
        'analise_projeto_completa.py',      # Análise já feita
        'analise_final_estrategias.py',     # Análise já feita
        'diagnostico.py',                   # Diagnóstico antigo
        'diagnostico_simples.py',           # Diagnóstico antigo
        'diagnostico_sistema.py',           # Diagnóstico antigo
        'diagnostico_erros.py'              # Diagnóstico antigo
    ]
    
    for script_file in analysis_scripts:
        if safe_remove(script_file, "Script de Análise Antigo"):
            removed_count += 1
    
    # 6. INTERFACES E DASHBOARDS REDUNDANTES (manter apenas static/)
    print("\n🗑️  Removendo interfaces redundantes...")
    old_interfaces = [
        'interface_corrigida.py',       # Interface antiga
        'interface_pdf.py',             # Interface antiga
        'interface_pdf_test.py',        # Teste antigo
        # HTMLs redundantes na raiz (manter apenas em static/)
        'dashboard.html',               # Redundante (existe em static/)
        'dashboard_novo.html',          # Redundante
        'dashboard_moderno.html',       # Redundante  
        'dashboard_funcionando.html',   # Redundante
        'interface_pdf.html',           # Redundante
        'interface_pdf_nova.html',      # Redundante
        'interface_pdf_final.html',     # Redundante
        'interface_html5_moderna.html', # Redundante
        'index.html'                    # Redundante (existe em static/)
    ]
    
    for interface_file in old_interfaces:
        if safe_remove(interface_file, "Interface Redundante"):
            removed_count += 1
    
    # 7. SCRIPTS DE INICIALIZAÇÃO ANTIGOS
    print("\n🗑️  Removendo scripts de inicialização antigos...")
    init_scripts = [
        'iniciar_sistema.py',           # Inicialização antiga
        'iniciar_rapido.py',            # Inicialização antiga
        'iniciar_concursai.py'          # Inicialização antiga
    ]
    
    for script_file in init_scripts:
        if safe_remove(script_file, "Script Inicialização Antigo"):
            removed_count += 1
    
    # 8. CACHE PYTHON E ARQUIVOS TEMPORÁRIOS
    print("\n🗑️  Removendo cache e arquivos temporários...")
    
    # Cache Python
    cache_dirs = list(Path(".").rglob("__pycache__"))
    for cache_dir in cache_dirs:
        if safe_remove(cache_dir, "Cache Python"):
            removed_count += 1
    
    # Arquivos .pyc
    pyc_files = list(Path(".").rglob("*.pyc"))
    for pyc_file in pyc_files:
        if safe_remove(pyc_file, "Bytecode Python"):
            removed_count += 1
    
    # 9. LOGS ANTIGOS E ARQUIVOS DE STATUS
    print("\n🗑️  Removendo logs antigos...")
    old_logs = [
        'concursai_agendador.log',
        'concursai_sistema_v2.log', 
        'concursai_sistema.log',
        'STATUS_SISTEMA.txt'
    ]
    
    for log_file in old_logs:
        if safe_remove(log_file, "Log Antigo"):
            removed_count += 1
    
    # 10. ARQUIVOS DE CONFIGURAÇÃO DUPLICADOS
    print("\n🗑️  Removendo configurações duplicadas...")
    config_duplicates = [
        'config_notificacoes.json'  # Se não usado
    ]
    
    for config_file in config_duplicates:
        file_path = Path(config_file)
        if file_path.exists():
            # Verificar se é pequeno (provavelmente não usado)
            size = file_path.stat().st_size
            if size < 1000:  # < 1KB
                if safe_remove(config_file, "Config Pequeno/Não Usado"):
                    removed_count += 1
    
    # 11. SCRIPTS DE TESTES ANTIGOS (manter apenas tests/)
    print("\n🗑️  Removendo scripts de teste antigos...")
    old_test_scripts = [
        'analisador_pdf_editais.py',  # Se for apenas teste
        'coleta_ativa.py'             # Se for apenas teste
    ]
    
    for test_file in old_test_scripts:
        file_path = Path(test_file)
        if file_path.exists():
            # Verificar conteúdo para decidir se é apenas teste
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if 'test' in content.lower() or len(content) < 2000:
                    if safe_remove(test_file, "Script Teste Antigo"):
                        removed_count += 1
            except:
                pass
    
    print("\n" + "=" * 50)
    print("🎉 LIMPEZA DIRECIONADA CONCLUÍDA!")
    print("=" * 50)
    print(f"✅ {removed_count} arquivos/diretórios removidos")
    
    # Verificar estrutura resultante
    print("\n📁 ESTRUTURA PRINCIPAL RESTANTE:")
    main_files = [
        'api_simplificada.py',
        'coletor_pci_real.py', 
        'integrador_pci.py',
        'static/',
        'scrapers/',
        'tests/',
        'requirements.txt'
    ]
    
    for item in main_files:
        path = Path(item)
        if path.exists():
            if path.is_dir():
                count = len(list(path.iterdir()))
                print(f"   📁 {item} ({count} itens)")
            else:
                size = path.stat().st_size / 1024
                print(f"   📄 {item} ({size:.1f}KB)")
        else:
            print(f"   ❌ {item} (não encontrado)")
    
    print("\n📋 PRÓXIMOS PASSOS RECOMENDADOS:")
    print("1. Testar sistema principal: python api_simplificada.py")
    print("2. Verificar se scrapers funcionam: python -c 'from scrapers.pci_scraper_atual import *'")
    print("3. Mover documentação MD para docs/ se necessário")
    print("4. Organizar arquivos CSV para data/ se necessário")
    
    return removed_count

if __name__ == "__main__":
    try:
        removed = main()
        print(f"\n🏁 Limpeza finalizada: {removed} itens removidos")
        
        # Sugerir próxima ação
        print("\n❓ TESTE RÁPIDO:")
        print("Execute: python api_simplificada.py")
        print("E acesse: http://localhost:8002")
        
    except KeyboardInterrupt:
        print("\n\n🚫 Limpeza cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante limpeza: {e}")
