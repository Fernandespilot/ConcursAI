"""
🎯 BENCHMARK DO MODELO - ConcursAI
===================================
Testa o modelo contra ground truth e gera relatório de métricas

Uso:
    python benchmark_modelo.py
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import time

from modules.rag_banca_inteligente import get_rag_inteligente
from modules.model_metrics import get_model_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def carregar_ground_truth() -> List[Dict]:
    """Carrega dataset de ground truth"""
    
    gt_path = Path("datasets/ground_truth_rag.json")
    
    if not gt_path.exists():
        logger.error(f"❌ Ground truth não encontrado: {gt_path}")
        return []
    
    with open(gt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    perguntas = data.get('perguntas', [])
    logger.info(f"✅ Carregadas {len(perguntas)} perguntas do ground truth")
    
    return perguntas


def executar_benchmark(
    num_perguntas: int = None,
    bancas: List[str] = None,
    areas: List[str] = None,
    usar_ollama: bool = False
) -> Dict:
    """
    Executa benchmark do modelo
    
    Args:
        num_perguntas: Número de perguntas a testar (None = todas)
        bancas: Filtrar por bancas específicas
        areas: Filtrar por áreas específicas
        usar_ollama: Se True, usa Ollama (mais lento mas mais realista)
        
    Returns:
        Dicionário com resultados do benchmark
    """
    
    logger.info("🚀 Iniciando Benchmark do Modelo...")
    logger.info(f"⚙️  Configuração: usar_ollama={usar_ollama}")
    
    # Carregar ground truth
    perguntas_gt = carregar_ground_truth()
    
    if not perguntas_gt:
        return {"erro": "Ground truth não carregado"}
    
    # Filtrar perguntas
    if bancas:
        perguntas_gt = [p for p in perguntas_gt if p.get('banca', '').lower() in [b.lower() for b in bancas]]
        logger.info(f"🔍 Filtrado para bancas: {bancas}")
    
    if areas:
        perguntas_gt = [p for p in perguntas_gt if p.get('area', '').lower() in [a.lower() for a in areas]]
        logger.info(f"🔍 Filtrado para áreas: {areas}")
    
    if num_perguntas:
        perguntas_gt = perguntas_gt[:num_perguntas]
    
    logger.info(f"📊 Testando {len(perguntas_gt)} perguntas...")
    
    # Inicializar RAG e métricas
    rag = get_rag_inteligente()
    metrics = get_model_metrics()
    
    # Executar perguntas
    resultados = []
    
    for i, pergunta_gt in enumerate(perguntas_gt, 1):
        pergunta = pergunta_gt['pergunta']
        
        logger.info(f"\n{'='*70}")
        logger.info(f"[{i}/{len(perguntas_gt)}] ❓ {pergunta}")
        
        start = time.time()
        
        try:
            # Gerar resposta
            resposta = rag.responder(pergunta, usar_ollama=usar_ollama)
            
            latency = (time.time() - start) * 1000
            
            # Validar contra ground truth
            validation = metrics.validator.validate_response(pergunta, resposta)
            
            resultado = {
                'id': pergunta_gt['id'],
                'pergunta': pergunta,
                'banca': pergunta_gt.get('banca', 'N/A'),
                'area': pergunta_gt.get('area', 'N/A'),
                'dificuldade': pergunta_gt.get('dificuldade', 'N/A'),
                'tipo': pergunta_gt.get('tipo', 'N/A'),
                'resposta': resposta[:200] + "..." if len(resposta) > 200 else resposta,
                'resposta_esperada': pergunta_gt['resposta_esperada'][:100] + "...",
                'latency_ms': latency,
                'validation': validation,
                'sucesso': validation['has_expected_keywords'] if validation else False
            }
            
            resultados.append(resultado)
            
            # Log resultado
            if validation:
                score = validation['keyword_match_score']
                match = "✅" if score >= 0.8 else "⚠️" if score >= 0.5 else "❌"
                logger.info(f"{match} Score: {score:.2f} | Latência: {latency:.0f}ms")
            else:
                logger.info(f"⚠️  Sem validação | Latência: {latency:.0f}ms")
        
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            resultados.append({
                'id': pergunta_gt['id'],
                'pergunta': pergunta,
                'erro': str(e),
                'sucesso': False
            })
    
    # Calcular estatísticas
    logger.info(f"\n{'='*70}")
    logger.info("📊 CALCULANDO ESTATÍSTICAS...")
    
    sucessos = [r for r in resultados if r.get('sucesso')]
    total = len(resultados)
    
    # Métricas de qualidade
    keyword_scores = [r['validation']['keyword_match_score'] for r in resultados if 'validation' in r and r['validation']]
    exact_matches = sum(1 for r in resultados if r.get('validation', {}).get('exact_match'))
    
    # Métricas de performance
    latencies = [r['latency_ms'] for r in resultados if 'latency_ms' in r]
    
    estatisticas = {
        'total_perguntas': total,
        'perguntas_com_sucesso': len(sucessos),
        'taxa_sucesso': len(sucessos) / total if total > 0 else 0,
        'qualidade': {
            'keyword_match_score_medio': sum(keyword_scores) / len(keyword_scores) if keyword_scores else 0,
            'exact_matches': exact_matches,
            'exact_match_rate': exact_matches / total if total > 0 else 0,
        },
        'performance': {
            'latency_media_ms': sum(latencies) / len(latencies) if latencies else 0,
            'latency_min_ms': min(latencies) if latencies else 0,
            'latency_max_ms': max(latencies) if latencies else 0,
            'latency_p50_ms': sorted(latencies)[len(latencies)//2] if latencies else 0,
            'latency_p95_ms': sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0,
        },
        'distribuicao': {
            'por_banca': {},
            'por_area': {},
            'por_dificuldade': {},
            'por_tipo': {}
        }
    }
    
    # Distribuições
    for resultado in resultados:
        banca = resultado.get('banca', 'N/A')
        area = resultado.get('area', 'N/A')
        dificuldade = resultado.get('dificuldade', 'N/A')
        tipo = resultado.get('tipo', 'N/A')
        sucesso = resultado.get('sucesso', False)
        
        # Por banca
        if banca not in estatisticas['distribuicao']['por_banca']:
            estatisticas['distribuicao']['por_banca'][banca] = {'total': 0, 'sucesso': 0}
        estatisticas['distribuicao']['por_banca'][banca]['total'] += 1
        if sucesso:
            estatisticas['distribuicao']['por_banca'][banca]['sucesso'] += 1
        
        # Por área
        if area not in estatisticas['distribuicao']['por_area']:
            estatisticas['distribuicao']['por_area'][area] = {'total': 0, 'sucesso': 0}
        estatisticas['distribuicao']['por_area'][area]['total'] += 1
        if sucesso:
            estatisticas['distribuicao']['por_area'][area]['sucesso'] += 1
        
        # Por dificuldade
        if dificuldade not in estatisticas['distribuicao']['por_dificuldade']:
            estatisticas['distribuicao']['por_dificuldade'][dificuldade] = {'total': 0, 'sucesso': 0}
        estatisticas['distribuicao']['por_dificuldade'][dificuldade]['total'] += 1
        if sucesso:
            estatisticas['distribuicao']['por_dificuldade'][dificuldade]['sucesso'] += 1
        
        # Por tipo
        if tipo not in estatisticas['distribuicao']['por_tipo']:
            estatisticas['distribuicao']['por_tipo'][tipo] = {'total': 0, 'sucesso': 0}
        estatisticas['distribuicao']['por_tipo'][tipo]['total'] += 1
        if sucesso:
            estatisticas['distribuicao']['por_tipo'][tipo]['sucesso'] += 1
    
    # Gerar relatório
    relatorio = {
        'timestamp': datetime.now().isoformat(),
        'configuracao': {
            'usar_ollama': usar_ollama,
            'num_perguntas_testadas': total,
            'bancas_filtradas': bancas,
            'areas_filtradas': areas
        },
        'estatisticas': estatisticas,
        'resultados_detalhados': resultados
    }
    
    return relatorio


def salvar_relatorio(relatorio: Dict, nome_arquivo: str = None):
    """Salva relatório em JSON"""
    
    if nome_arquivo is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"benchmark_resultado_{timestamp}.json"
    
    output_dir = Path("benchmarks")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / nome_arquivo
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Relatório salvo: {output_path}")
    
    return output_path


def imprimir_resumo(relatorio: Dict):
    """Imprime resumo do benchmark"""
    
    stats = relatorio['estatisticas']
    
    print(f"""
{'='*70}
🎯 RESUMO DO BENCHMARK
{'='*70}

📅 Data: {relatorio['timestamp']}
⚙️  Ollama: {'Sim' if relatorio['configuracao']['usar_ollama'] else 'Não'}

📊 QUALIDADE
{'='*70}
Total de Perguntas: {stats['total_perguntas']}
Respostas com Sucesso: {stats['perguntas_com_sucesso']} ({stats['taxa_sucesso']:.1%})
Keyword Match Score Médio: {stats['qualidade']['keyword_match_score_medio']:.2%}
Exact Matches: {stats['qualidade']['exact_matches']} ({stats['qualidade']['exact_match_rate']:.1%})

⚡ PERFORMANCE
{'='*70}
Latência Média: {stats['performance']['latency_media_ms']:.0f}ms
Latência Mínima: {stats['performance']['latency_min_ms']:.0f}ms
Latência Máxima: {stats['performance']['latency_max_ms']:.0f}ms
Latência P50: {stats['performance']['latency_p50_ms']:.0f}ms
Latência P95: {stats['performance']['latency_p95_ms']:.0f}ms

📈 DISTRIBUIÇÃO POR BANCA
{'='*70}
""")
    
    for banca, dados in stats['distribuicao']['por_banca'].items():
        taxa = dados['sucesso'] / dados['total'] if dados['total'] > 0 else 0
        print(f"{banca:15s}: {dados['sucesso']:2d}/{dados['total']:2d} ({taxa:.1%})")
    
    print(f"""
📈 DISTRIBUIÇÃO POR ÁREA
{'='*70}
""")
    
    for area, dados in stats['distribuicao']['por_area'].items():
        taxa = dados['sucesso'] / dados['total'] if dados['total'] > 0 else 0
        print(f"{area:20s}: {dados['sucesso']:2d}/{dados['total']:2d} ({taxa:.1%})")
    
    print(f"""
📈 DISTRIBUIÇÃO POR TIPO
{'='*70}
""")
    
    for tipo, dados in stats['distribuicao']['por_tipo'].items():
        taxa = dados['sucesso'] / dados['total'] if dados['total'] > 0 else 0
        print(f"{tipo:20s}: {dados['sucesso']:2d}/{dados['total']:2d} ({taxa:.1%})")
    
    print(f"\n{'='*70}\n")


def main():
    """Função principal"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Benchmark do Modelo ConcursAI')
    parser.add_argument('--num', type=int, default=None, help='Número de perguntas a testar')
    parser.add_argument('--banca', nargs='+', help='Filtrar por bancas específicas')
    parser.add_argument('--area', nargs='+', help='Filtrar por áreas específicas')
    parser.add_argument('--ollama', action='store_true', help='Usar Ollama (mais lento)')
    parser.add_argument('--output', type=str, default=None, help='Nome do arquivo de saída')
    
    args = parser.parse_args()
    
    # Executar benchmark
    relatorio = executar_benchmark(
        num_perguntas=args.num,
        bancas=args.banca,
        areas=args.area,
        usar_ollama=args.ollama
    )
    
    # Salvar relatório
    output_path = salvar_relatorio(relatorio, args.output)
    
    # Imprimir resumo
    imprimir_resumo(relatorio)
    
    logger.info(f"✅ Benchmark concluído! Relatório: {output_path}")


if __name__ == "__main__":
    main()
