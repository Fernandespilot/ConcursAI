"""Teste simples de detecção de áreas nos PDFs"""
import os
from pathlib import Path

print("\n🔍 ANALISANDO ESTRUTURA DE PDFs")
print("="*60)

base = Path("provas")
bancas = ["cebraspe", "fcc", "fgv", "vunesp"]

for banca in bancas:
    banca_path = base / banca
    
    if not banca_path.exists():
        print(f"\n❌ {banca.upper()}: pasta não existe")
        continue
    
    print(f"\n🏛️  {banca.upper()}:")
    
    # Verificar se tem subpastas (áreas)
    subdirs = [d for d in banca_path.iterdir() if d.is_dir()]
    
    if subdirs:
        print(f"   📁 Organizado por áreas:")
        for subdir in subdirs:
            pdfs = list(subdir.glob("*.pdf"))
            print(f"      • {subdir.name}: {len(pdfs)} PDFs")
    else:
        # PDFs diretos
        pdfs = list(banca_path.glob("*.pdf"))
        print(f"   📄 {len(pdfs)} PDFs na pasta raiz (não organizados)")
        
        if pdfs:
            print(f"   💡 Exemplos:")
            for pdf in pdfs[:3]:
                nome = pdf.name[:60] + "..." if len(pdf.name) > 60 else pdf.name
                print(f"      • {nome}")

print("\n" + "="*60)
print("✅ Análise concluída")
print("\n💡 Para organizar automaticamente:")
print("   python -c \"from modules.banca_area_analyzer import *; get_banca_area_analyzer().organizar_pdfs_existentes()\"")
