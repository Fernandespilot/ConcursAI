#!/usr/bin/env python3
"""
Script de inicialização ConcursAI v2.0 - Simplificado
"""

import sys
import os
from pathlib import Path

# Adicionar diretórios ao path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "app"))

print("🚀 Iniciando ConcursAI v2.0...")

try:
    # Tentar importar a nova API
    os.chdir(current_dir)
    
    # Executar uvicorn diretamente
    import uvicorn
    
    print("✅ Iniciando servidor...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("📦 Instalando dependências necessárias...")
    
    # Instalar dependências básicas
    os.system('pip install fastapi uvicorn python-multipart')
    
    print("🔄 Tentando novamente...")
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
except Exception as e:
    print(f"❌ Erro ao iniciar: {e}")
    print("\n🔧 Solução:")
    print("1. cd app")
    print("2. pip install -r requirements.txt") 
    print("3. python main.py")
