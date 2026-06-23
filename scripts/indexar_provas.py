"""
Indexa provas baixadas no ChromaDB para o modelo RAG
"""

import os
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importa função de indexação
try:
    from src.core import indexar_pdf
    logger.info("Modulo de indexacao carregado")
except ImportError:
    try:
        from modules.pdf_processor import indexar_pdf
        logger.info("Modulo alternativo de indexacao carregado")
    except ImportError:
        logger.error("Nao foi possivel importar funcao de indexacao")
        indexar_pdf = None


def indexar_provas_banca(banca, collection_name="concursos_provas"):
    """Indexa todas as provas de uma banca"""
    
    provas_dir = Path("provas") / banca
    
    if not provas_dir.exists():
        logger.warning(f"Diretorio {provas_dir} nao encontrado")
        return {'sucesso': 0, 'erros': 0, 'total': 0}
    
    pdfs = list(provas_dir.glob("*.pdf"))
    
    if not pdfs:
        logger.warning(f"Nenhum PDF encontrado em {provas_dir}")
        return {'sucesso': 0, 'erros': 0, 'total': 0}
    
    logger.info(f"\n{'='*70}")
    logger.info(f"INDEXANDO PROVAS - {banca.upper()}")
    logger.info(f"Total de PDFs: {len(pdfs)}")
    logger.info(f"{'='*70}\n")
    
    stats = {'sucesso': 0, 'erros': 0, 'total': len(pdfs)}
    
    for i, pdf_path in enumerate(pdfs, 1):
        try:
            logger.info(f"[{i}/{len(pdfs)}] {pdf_path.name[:60]}...")
            
            # Extrai metadados do nome do arquivo
            nome = pdf_path.stem
            partes = nome.split('_')
            
            metadata = {
                'banca': banca,
                'tipo': 'gabarito' if 'gabarito' in nome else 'prova',
                'fonte': 'PCI Concursos',
                'data_coleta': datetime.now().isoformat(),
                'arquivo': pdf_path.name
            }
            
            # Tenta extrair ano
            for parte in partes:
                if parte.isdigit() and len(parte) == 4:
                    metadata['ano'] = int(parte)
                    break
            
            # Indexa no ChromaDB
            if indexar_pdf:
                resultado = indexar_pdf(
                    str(pdf_path),
                    metadados=metadata
                )
                
                logger.info(f"  OK - Indexado com sucesso")
                stats['sucesso'] += 1
            else:
                logger.error(f"  ERRO - Funcao de indexacao nao disponivel")
                stats['erros'] += 1
                
        except Exception as e:
            logger.error(f"  ERRO - {e}")
            stats['erros'] += 1
    
    logger.info(f"\n{'='*70}")
    logger.info(f"RELATORIO - {banca.upper()}")
    logger.info(f"{'='*70}")
    logger.info(f"Total: {stats['total']}")
    logger.info(f"Sucesso: {stats['sucesso']}")
    logger.info(f"Erros: {stats['erros']}")
    logger.info(f"{'='*70}\n")
    
    return stats


def indexar_todas_provas(collection_name="concursos_provas"):
    """Indexa provas de todas as bancas"""
    
    bancas = ['cebraspe', 'fcc', 'fgv']
    
    logger.info(f"\n{'='*70}")
    logger.info(f"INDEXACAO COMPLETA DE PROVAS")
    logger.info(f"Collection: {collection_name}")
    logger.info(f"{'='*70}\n")
    
    stats_geral = {'total': 0, 'sucesso': 0, 'erros': 0, 'por_banca': {}}
    
    for banca in bancas:
        stats = indexar_provas_banca(banca, collection_name)
        stats_geral['por_banca'][banca] = stats
        stats_geral['total'] += stats['total']
        stats_geral['sucesso'] += stats['sucesso']
        stats_geral['erros'] += stats['erros']
    
    logger.info(f"\n{'='*70}")
    logger.info(f"RELATORIO FINAL")
    logger.info(f"{'='*70}")
    logger.info(f"Total de PDFs: {stats_geral['total']}")
    logger.info(f"Indexados: {stats_geral['sucesso']}")
    logger.info(f"Erros: {stats_geral['erros']}")
    logger.info(f"\nPor banca:")
    for banca, stats in stats_geral['por_banca'].items():
        logger.info(f"  {banca.upper()}: {stats['sucesso']}/{stats['total']}")
    logger.info(f"{'='*70}\n")
    
    return stats_geral


def listar_provas_disponiveis():
    """Lista todas as provas baixadas"""
    
    provas_dir = Path("provas")
    bancas = ['cebraspe', 'fcc', 'fgv']
    
    print("\n" + "="*70)
    print("PROVAS DISPONIVEIS PARA INDEXACAO")
    print("="*70 + "\n")
    
    total_geral = 0
    
    for banca in bancas:
        banca_dir = provas_dir / banca
        if banca_dir.exists():
            pdfs = list(banca_dir.glob("*.pdf"))
            provas = [f for f in pdfs if '_prova_' in f.name]
            gabaritos = [f for f in pdfs if '_gabarito_' in f.name]
            
            print(f"[{banca.upper()}]")
            print(f"  Total: {len(pdfs)} arquivos")
            print(f"  Provas: {len(provas)}")
            print(f"  Gabaritos: {len(gabaritos)}")
            print(f"  Diretorio: {banca_dir}")
            print()
            
            total_geral += len(pdfs)
        else:
            print(f"[{banca.upper()}]")
            print(f"  Diretorio nao encontrado")
            print()
    
    print("="*70)
    print(f"TOTAL GERAL: {total_geral} arquivos")
    print("="*70 + "\n")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == 'listar':
            listar_provas_disponiveis()
        elif comando == 'todas':
            indexar_todas_provas()
        elif comando in ['cebraspe', 'fcc', 'fgv']:
            indexar_provas_banca(comando)
        else:
            print("\nUso:")
            print("  python indexar_provas.py listar       - Lista provas disponiveis")
            print("  python indexar_provas.py todas        - Indexa todas as bancas")
            print("  python indexar_provas.py cebraspe     - Indexa so Cebraspe")
            print("  python indexar_provas.py fcc          - Indexa so FCC")
            print("  python indexar_provas.py fgv          - Indexa so FGV")
            print()
    else:
        # Modo interativo
        listar_provas_disponiveis()
        
        resposta = input("Deseja indexar todas as provas? (s/n): ")
        if resposta.lower() == 's':
            indexar_todas_provas()
