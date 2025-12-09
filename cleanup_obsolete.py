#!/usr/bin/env python3
"""
🧹 LIMPEZA AUTOMÁTICA - CONCURSAI
================================
Remove arquivos desnecessários identificados
"""

import os
import shutil
from pathlib import Path

def safe_remove(file_path, category):
    """Remove arquivo com segurança"""
    try:
        if file_path.exists():
            if file_path.is_dir():
                shutil.rmtree(file_path)
                print(f"✅ Diretório removido: {file_path.name} ({category})")
            else:
                file_path.unlink()
                print(f"✅ Arquivo removido: {file_path.name} ({category})")
            return True
        else:
            print(f"⚠️  Não encontrado: {file_path.name}")
            return False
    except Exception as e:
        print(f"❌ Erro removendo {file_path.name}: {e}")
        return False

def main():
    """Executa limpeza do projeto"""
    
    print("🧹 LIMPEZA AUTOMÁTICA - PROJETO CONCURSAI")
    print("=" * 50)
    
    project_root = Path(".")
    os.chdir(project_root)
    
    removed_count = 0
    
    # 1. APIs obsoletas
    print("\n🗑️  Removendo APIs obsoletas...")
    obsolete_apis = [
        'api_fastapi_backup.py',
        'api_fastapi_old.py', 
        'api_fast_simple.py'
    ]
    
    for api_file in obsolete_apis:
        if safe_remove(Path(api_file), "API Obsoleta"):
            removed_count += 1
    
    # 2. Apps antigos
    print("\n🗑️  Removendo apps antigos...")
    obsolete_apps = [
        'app_completo.py',
        'app_simples.py',
        'concurso_app.py'
    ]
    
    for app_file in obsolete_apps:
        if safe_remove(Path(app_file), "App Obsoleto"):
            removed_count += 1
    
    # 3. Scripts de organização já executados
    print("\n🗑️  Removendo scripts de organização...")
    org_scripts = [
        'organize_project.py',
        'organize_project_simple.py',
        'reorganizar.bat',
        'reorganize_direct.py',
        'migrate_to_v2.py'
    ]
    
    for script_file in org_scripts:
        if safe_remove(Path(script_file), "Script de Organização"):
            removed_count += 1
    
    # 4. Demos redundantes
    print("\n🗑️  Removendo demos redundantes...")
    demo_files = [
        'demo_api_integracao.py',
        'demo_fastapi.py', 
        'demo_scrapers.py',
        'demonstracao_scrapers.py'
    ]
    
    for demo_file in demo_files:
        if safe_remove(Path(demo_file), "Demo"):
            removed_count += 1
    
    # 5. Scripts pontuais já executados
    print("\n🗑️  Removendo scripts pontuais...")
    pontual_scripts = [
        'adicionar_dados_exemplo.py',
        'diagnostico.py',
        'fix_langchain_deps.py',
        'relatorio_correcoes.py'
    ]
    
    for script_file in pontual_scripts:
        if safe_remove(Path(script_file), "Script Pontual"):
            removed_count += 1
    
    # 6. Cache Python
    print("\n🗑️  Removendo cache Python...")
    cache_dirs = list(Path(".").rglob("__pycache__"))
    for cache_dir in cache_dirs:
        if safe_remove(cache_dir, "Cache Python"):
            removed_count += 1
    
    # 7. Arquivos .pyc
    pyc_files = list(Path(".").rglob("*.pyc"))
    for pyc_file in pyc_files:
        if safe_remove(pyc_file, "Bytecode Python"):
            removed_count += 1
    
    # 8. Logs antigos na raiz
    print("\n🗑️  Removendo logs antigos...")
    old_logs = [
        'concursai_agendador.log',
        'STATUS_SISTEMA.txt'
    ]
    
    for log_file in old_logs:
        if safe_remove(Path(log_file), "Log Antigo"):
            removed_count += 1
    
    # 9. Script de análise (este próprio arquivo após uso)
    print("\n🗑️  Removendo script de análise...")
    analysis_files = [
        'analyze_cleanup.py',
        'CODIGOS_DESNECESSARIOS.md'  # Mover para docs depois
    ]
    
    # Não remover este script ainda, deixar usuário decidir
    
    print("\n" + "=" * 50)
    print("🎉 LIMPEZA CONCLUÍDA!")
    print("=" * 50)
    print(f"✅ {removed_count} arquivos/diretórios removidos")
    print("📁 Projeto significativamente mais limpo!")
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Mover testes dispersos para tests/:")
    print("   - test_*.py, teste_*.py, verificar_*.py")
    print("2. Mover documentação para docs/:")
    print("   - *.md (exceto README.md)")
    print("3. Mover dados para data/:")
    print("   - *.csv, *.json")
    print("4. Testar sistema: python sistema_completo.py")
    
    return removed_count

if __name__ == "__main__":
    removed = main()
    print(f"\n🏁 Limpeza finalizada: {removed} itens removidos")
