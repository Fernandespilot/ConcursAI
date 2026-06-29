"""
🔄 PROCESSADOR DE PDFs PARA CHUNKS - ConcursAI
===============================================
Processa todos os PDFs de provas e gera chunks para o RAG
"""

import os
import sys
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime
import re

# Imports para processamento de PDF
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️ PyMuPDF não disponível - tentando pypdf")

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("⚠️ pypdf não disponível")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extrair_texto_pdf(pdf_path: str) -> str:
    """Extrai texto de PDF usando PyMuPDF ou pypdf"""
    
    texto = ""
    
    # Tentar PyMuPDF primeiro (mais robusto)
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                texto += f"\n{page_text}"
            doc.close()
            
            if len(texto.strip()) > 100:
                return texto.strip()
        except Exception as e:
            logger.warning(f"PyMuPDF falhou: {e}")
    
    # Fallback para pypdf
    if PYPDF_AVAILABLE:
        try:
            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    texto += f"\n{page_text}"
            
            if len(texto.strip()) > 100:
                return texto.strip()
        except Exception as e:
            logger.warning(f"pypdf falhou: {e}")
    
    # Se nenhum método funcionou
    if not texto.strip():
        raise Exception("Não foi possível extrair texto do PDF")
    
    return texto.strip()


def limpar_texto(texto: str) -> str:
    """Limpa e normaliza o texto extraído"""
    
    # Remove múltiplos espaços
    texto = re.sub(r'\s+', ' ', texto)
    
    # Remove quebras de linha excessivas
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    
    # Remove cabeçalhos/rodapés comuns
    texto = re.sub(r'Página \d+ de \d+', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'www\.\S+', '', texto)
    
    return texto.strip()


def criar_chunks(texto: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """
    Divide texto em chunks com overlap
    
    Args:
        texto: Texto completo
        chunk_size: Tamanho de cada chunk em caracteres
        overlap: Sobreposição entre chunks
        
    Returns:
        Lista de chunks
    """
    
    chunks = []
    start = 0
    
    while start < len(texto):
        end = start + chunk_size
        chunk = texto[start:end]
        
        # Tentar quebrar em fim de sentença
        if end < len(texto):
            # Procurar último ponto final
            last_period = chunk.rfind('.')
            if last_period > chunk_size * 0.7:  # Se encontrar ponto após 70% do chunk
                end = start + last_period + 1
                chunk = texto[start:end]
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks


def extrair_metadados_do_nome(pdf_path: Path) -> dict:
    """Extrai metadados do nome do arquivo e estrutura de pastas"""
    
    # Nome do arquivo
    nome = pdf_path.stem
    
    # Estrutura: banca/area/arquivo
    partes_caminho = pdf_path.parts
    
    metadata = {
        'arquivo': pdf_path.name,
        'caminho_completo': str(pdf_path)
    }
    
    # Identificar banca
    if 'cebraspe' in str(pdf_path).lower():
        metadata['banca'] = 'cebraspe'
    elif 'fcc' in str(pdf_path).lower():
        metadata['banca'] = 'fcc'
    elif 'fgv' in str(pdf_path).lower():
        metadata['banca'] = 'fgv'
    else:
        metadata['banca'] = 'desconhecida'
    
    # Identificar área (da pasta)
    for parte in partes_caminho:
        if parte in ['tecnologia', 'jurídica', 'língua_portuguesa', 'conhecimentos_gerais']:
            metadata['area'] = parte.replace('_', ' ').title()
            break
    else:
        metadata['area'] = 'Geral'
    
    # Extrair ano
    anos = re.findall(r'20\d{2}', nome)
    if anos:
        metadata['ano'] = anos[0]
    else:
        metadata['ano'] = 'desconhecido'
    
    # Identificar tipo (prova ou gabarito)
    if 'gabarito' in nome.lower():
        metadata['tipo_documento'] = 'gabarito'
    else:
        metadata['tipo_documento'] = 'prova'
    
    # Extrair cargo (entre tipo e ano/banca)
    partes_nome = nome.split('_')
    if len(partes_nome) >= 3:
        # Formato: banca_ano_tipo_Cargo - Órgão
        cargo_parte = ' '.join(partes_nome[3:])
        # Limpar
        cargo_parte = re.sub(r'\s*-\s*Ver.*', '', cargo_parte)
        cargo_parte = re.sub(r'\s*-\s*Baixar.*', '', cargo_parte)
        cargo_parte = re.sub(r'\.pdf$', '', cargo_parte, flags=re.IGNORECASE)
        metadata['cargo'] = cargo_parte.strip()
    else:
        metadata['cargo'] = 'Não especificado'
    
    # Extrair órgão
    orgao_match = re.search(r'-\s*([A-Z]+)\s*\d{4}', nome)
    if orgao_match:
        metadata['orgao'] = orgao_match.group(1)
    else:
        metadata['orgao'] = 'Não especificado'
    
    # Título do documento
    metadata['titulo'] = f"{metadata['banca'].upper()} {metadata['ano']} - {metadata['cargo']} - {metadata['tipo_documento'].title()}"
    
    return metadata


def processar_pdf(pdf_path: Path) -> list:
    """
    Processa um PDF e retorna lista de chunks com metadados
    
    Returns:
        Lista de dicionários com chunks e metadados
    """
    
    logger.info(f"Processando: {pdf_path.name}")
    
    try:
        # 1. Extrair texto
        texto = extrair_texto_pdf(str(pdf_path))
        
        if not texto or len(texto) < 100:
            logger.warning(f"Texto muito curto ou vazio: {pdf_path.name}")
            return []
        
        # 2. Limpar texto
        texto_limpo = limpar_texto(texto)
        
        # 3. Extrair metadados
        metadata = extrair_metadados_do_nome(pdf_path)
        
        # 4. Criar chunks
        chunks = criar_chunks(texto_limpo, chunk_size=1000, overlap=200)
        
        logger.info(f"  ✅ {len(chunks)} chunks criados - {len(texto_limpo):,} caracteres")
        
        # 5. Criar registros para cada chunk
        registros = []
        for i, chunk in enumerate(chunks):
            registro = {
                'conteudo': chunk,
                'orgao': metadata.get('orgao', ''),
                'ano': metadata.get('ano', ''),
                'cargo': metadata.get('cargo', ''),
                'tipo_documento': metadata.get('tipo_documento', ''),
                'titulo': metadata.get('titulo', ''),
                'banca': metadata.get('banca', ''),
                'area': metadata.get('area', ''),
                'arquivo': metadata.get('arquivo', ''),
                'parte': i,
                'data_publicacao': metadata.get('ano', ''),
                'url': ''  # Pode ser preenchido depois se disponível
            }
            registros.append(registro)
        
        return registros
        
    except Exception as e:
        logger.error(f"  ❌ Erro ao processar {pdf_path.name}: {e}")
        return []


def processar_todos_pdfs(provas_dir: str = "provas") -> pd.DataFrame:
    """
    Processa todos os PDFs e retorna DataFrame com chunks
    
    Args:
        provas_dir: Diretório raiz das provas
        
    Returns:
        DataFrame com todos os chunks
    """
    
    provas_path = Path(provas_dir)
    
    if not provas_path.exists():
        logger.error(f"Diretório não encontrado: {provas_dir}")
        return pd.DataFrame()
    
    # Encontrar todos os PDFs
    pdfs = list(provas_path.glob("**/*.pdf"))
    
    if not pdfs:
        logger.warning(f"Nenhum PDF encontrado em {provas_dir}")
        return pd.DataFrame()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"PROCESSAMENTO DE PDFs - ConcursAI")
    logger.info(f"Total de PDFs encontrados: {len(pdfs)}")
    logger.info(f"{'='*70}\n")
    
    # Processar cada PDF
    todos_registros = []
    sucessos = 0
    erros = 0
    
    for i, pdf_path in enumerate(pdfs, 1):
        logger.info(f"[{i}/{len(pdfs)}] {pdf_path.name[:60]}...")
        
        registros = processar_pdf(pdf_path)
        
        if registros:
            todos_registros.extend(registros)
            sucessos += 1
        else:
            erros += 1
    
    # Criar DataFrame
    if todos_registros:
        df = pd.DataFrame(todos_registros)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"RELATÓRIO DE PROCESSAMENTO")
        logger.info(f"{'='*70}")
        logger.info(f"PDFs processados com sucesso: {sucessos}")
        logger.info(f"PDFs com erro: {erros}")
        logger.info(f"Total de chunks gerados: {len(df)}")
        logger.info(f"Tamanho médio dos chunks: {df['conteudo'].str.len().mean():.0f} caracteres")
        logger.info(f"{'='*70}\n")
        
        # Estatísticas por banca
        logger.info("Chunks por Banca:")
        for banca, count in df['banca'].value_counts().items():
            logger.info(f"  {banca.upper()}: {count} chunks")
        
        # Estatísticas por área
        logger.info("\nChunks por Área:")
        for area, count in df['area'].value_counts().items():
            logger.info(f"  {area}: {count} chunks")
        
        return df
    else:
        logger.error("Nenhum chunk foi gerado!")
        return pd.DataFrame()


def salvar_chunks(df: pd.DataFrame, output_file: str = "concursos_chunks.csv"):
    """Salva DataFrame de chunks em CSV"""
    
    if df.empty:
        logger.error("DataFrame vazio - nada para salvar")
        return False
    
    try:
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"\n✅ Chunks salvos em: {output_file}")
        logger.info(f"📊 Total de registros: {len(df)}")
        
        # Mostrar preview
        logger.info(f"\n📄 Preview dos primeiros chunks:")
        logger.info(f"{'='*70}")
        for i, row in df.head(3).iterrows():
            logger.info(f"\nChunk {i+1}:")
            logger.info(f"  Banca: {row['banca']}")
            logger.info(f"  Área: {row['area']}")
            logger.info(f"  Cargo: {row['cargo']}")
            logger.info(f"  Conteúdo: {row['conteudo'][:100]}...")
        logger.info(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar chunks: {e}")
        return False


def main():
    """Função principal"""
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║            🔄 PROCESSADOR DE PDFs PARA RAG                        ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar dependências
    if not PYMUPDF_AVAILABLE and not PYPDF_AVAILABLE:
        print("❌ ERRO: Nenhuma biblioteca de PDF disponível!")
        print("\nInstale uma das seguintes:")
        print("  pip install pymupdf")
        print("  pip install pypdf")
        sys.exit(1)
    
    # Processar PDFs
    df = processar_todos_pdfs()
    
    if not df.empty:
        # Salvar chunks
        if salvar_chunks(df):
            print("\n✅ Processamento concluído com sucesso!")
            print("\nPróximos passos:")
            print("  1. Execute: python -m modules.concurso_embeddings")
            print("  2. Ou use: INDEXAR_PROVAS.bat")
            print("  3. Teste: BENCHMARK_RAPIDO.bat")
        else:
            print("\n❌ Erro ao salvar chunks")
            sys.exit(1)
    else:
        print("\n❌ Nenhum chunk foi gerado")
        sys.exit(1)


if __name__ == "__main__":
    main()
