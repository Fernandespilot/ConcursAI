"""
📊 VISUALIZADOR DE MÉTRICAS DO MODELO
======================================
Mostra estatísticas em tempo real do modelo

Uso:
    python visualizar_metricas.py
    python visualizar_metricas.py --last-hours 24
    python visualizar_metricas.py --export
"""

import logging
from datetime import datetime
from pathlib import Path
import json
from typing import Dict

from modules.model_metrics import get_model_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def formatar_tempo(ms: float) -> str:
    """Formata tempo em ms para legível"""
    if ms < 1000:
        return f"{ms:.0f}ms"
    else:
        return f"{ms/1000:.2f}s"


def barra_progresso(valor: float, max_valor: float = 100, largura: int = 20) -> str:
    """Cria barra de progresso visual"""
    percentual = min(valor / max_valor, 1.0) if max_valor > 0 else 0
    num_blocos = int(percentual * largura)
    barra = "█" * num_blocos + "░" * (largura - num_blocos)
    return f"{barra} {valor:.1f}"


def visualizar_metricas_embedding(last_hours: int = 24):
    """Visualiza métricas de embeddings"""
    
    metrics = get_model_metrics()
    stats = metrics.get_embedding_stats(last_hours=last_hours)
    
    if stats['total_operations'] == 0:
        print("⚠️  Nenhuma operação de embedding registrada")
        return
    
    print(f"""
{'='*70}
🔤 MÉTRICAS DE EMBEDDINGS (Últimas {last_hours}h)
{'='*70}

📊 VOLUME
  Total de Operações: {stats['total_operations']:,}
  Taxa de Sucesso: {stats['success_rate']:.1%}

⚡ LATÊNCIA
  Média: {formatar_tempo(stats['avg_latency_ms'])}
  P50 (Mediana): {formatar_tempo(stats['p50_latency_ms'])}
  P95: {formatar_tempo(stats['p95_latency_ms'])}
  P99: {formatar_tempo(stats['p99_latency_ms'])}

  Distribuição:
  P50  {barra_progresso(stats['p50_latency_ms'], 500)}
  P95  {barra_progresso(stats['p95_latency_ms'], 500)}
  P99  {barra_progresso(stats['p99_latency_ms'], 500)}

📏 DIMENSÕES
  Média: {stats['avg_dimensions']:.0f}

⏱️  THROUGHPUT
  Embeddings/hora: {stats.get('embeddings_per_hour', 0):.1f}
""")


def visualizar_metricas_llm(last_hours: int = 24):
    """Visualiza métricas do LLM"""
    
    metrics = get_model_metrics()
    stats = metrics.get_llm_stats(last_hours=last_hours)
    
    if stats['total_queries'] == 0:
        print("⚠️  Nenhuma query LLM registrada")
        return
    
    print(f"""
{'='*70}
🤖 MÉTRICAS DO LLM (Últimas {last_hours}h)
{'='*70}

📊 VOLUME
  Total de Queries: {stats['total_queries']:,}
  Total de Tokens: {stats['total_tokens']:,}

⚡ LATÊNCIA
  Média: {formatar_tempo(stats['avg_latency_ms'])}
  P50 (Mediana): {formatar_tempo(stats['p50_latency_ms'])}
  P95: {formatar_tempo(stats['p95_latency_ms'])}
  P99: {formatar_tempo(stats['p99_latency_ms'])}

  Distribuição:
  P50  {barra_progresso(stats['p50_latency_ms'], 10000)}
  P95  {barra_progresso(stats['p95_latency_ms'], 10000)}
  P99  {barra_progresso(stats['p99_latency_ms'], 10000)}

🔤 TOKENS
  Média por Query: {stats['avg_tokens_per_query']:.0f}
  Tokens/Segundo: {stats['tokens_per_second']:.1f}

📈 EFICIÊNCIA
  Queries/Hora: {stats.get('queries_per_hour', 0):.1f}
  Tokens/Hora: {stats.get('tokens_per_hour', 0):,.0f}
""")


def visualizar_metricas_rag(last_hours: int = 24):
    """Visualiza métricas do RAG completo"""
    
    metrics = get_model_metrics()
    stats = metrics.get_rag_stats(last_hours=last_hours)
    
    if stats['total_queries'] == 0:
        print("⚠️  Nenhuma query RAG registrada")
        return
    
    breakdown = stats.get('latency_breakdown', {})
    quality = stats.get('quality_metrics', {})
    
    print(f"""
{'='*70}
🎯 MÉTRICAS DO RAG (Últimas {last_hours}h)
{'='*70}

📊 VOLUME
  Total de Queries: {stats['total_queries']:,}

⚡ LATÊNCIA TOTAL
  Média: {formatar_tempo(stats['avg_total_latency_ms'])}
  P50: {formatar_tempo(stats['p50_total_latency_ms'])}
  P95: {formatar_tempo(stats['p95_total_latency_ms'])}
  P99: {formatar_tempo(stats['p99_total_latency_ms'])}

  Distribuição:
  P50  {barra_progresso(stats['p50_total_latency_ms'], 10000)}
  P95  {barra_progresso(stats['p95_total_latency_ms'], 10000)}
  P99  {barra_progresso(stats['p99_total_latency_ms'], 10000)}

⏱️  BREAKDOWN POR FASE
  Embedding: {formatar_tempo(breakdown.get('embedding_ms', 0))} ({breakdown.get('embedding_percent', 0):.1f}%)
  Retrieval: {formatar_tempo(breakdown.get('retrieval_ms', 0))} ({breakdown.get('retrieval_percent', 0):.1f}%)
  LLM: {formatar_tempo(breakdown.get('llm_ms', 0))} ({breakdown.get('llm_percent', 0):.1f}%)

  Visualização:
  Embedding  {barra_progresso(breakdown.get('embedding_percent', 0), 100)}
  Retrieval  {barra_progresso(breakdown.get('retrieval_percent', 0), 100)}
  LLM        {barra_progresso(breakdown.get('llm_percent', 0), 100)}

🔍 RETRIEVAL
  Chunks Médio: {stats['avg_chunks_retrieved']:.1f}
  Similarity Média: {stats['avg_similarity_score']:.2%}
  Com Fonte: {stats['queries_with_source']} ({stats['queries_with_source']/stats['total_queries']:.1%})

🎯 QUALIDADE (Ground Truth)
  Queries Validadas: {quality.get('validated_queries', 0)}
  Precision: {quality.get('precision', 0):.1%}
  Recall: {quality.get('recall', 0):.1%}
  F1-Score: {quality.get('f1_score', 0):.1%}
  Keyword Match Score: {quality.get('keyword_match_score', 0):.1%}

📈 EFICIÊNCIA
  Queries/Hora: {stats.get('queries_per_hour', 0):.1f}
  Tokens Gerados: {stats['total_tokens_generated']:,}
""")


def visualizar_metricas_por_banca(last_hours: int = 24):
    """Visualiza métricas agrupadas por banca"""
    
    metrics = get_model_metrics()
    
    # Agrupar por banca
    bancas = {}
    
    for query in metrics.rag_history:
        # Filtrar por tempo
        idade_horas = (datetime.now() - query.timestamp).total_seconds() / 3600
        if idade_horas > last_hours:
            continue
        
        banca = query.banca or "desconhecida"
        
        if banca not in bancas:
            bancas[banca] = {
                'total': 0,
                'latencias': [],
                'tokens': 0
            }
        
        bancas[banca]['total'] += 1
        bancas[banca]['latencias'].append(query.total_latency_ms)
        bancas[banca]['tokens'] += query.tokens_generated
    
    if not bancas:
        print("⚠️  Nenhuma query por banca registrada")
        return
    
    print(f"""
{'='*70}
📚 MÉTRICAS POR BANCA (Últimas {last_hours}h)
{'='*70}
""")
    
    for banca, dados in sorted(bancas.items(), key=lambda x: x[1]['total'], reverse=True):
        latencia_media = sum(dados['latencias']) / len(dados['latencias'])
        tokens_medio = dados['tokens'] / dados['total']
        
        print(f"""
{banca.upper()}:
  Queries: {dados['total']:,}
  Latência Média: {formatar_tempo(latencia_media)}
  Tokens Médio: {tokens_medio:.0f}
""")


def visualizar_metricas_por_area(last_hours: int = 24):
    """Visualiza métricas agrupadas por área"""
    
    metrics = get_model_metrics()
    
    # Agrupar por área
    areas = {}
    
    for query in metrics.rag_history:
        # Filtrar por tempo
        idade_horas = (datetime.now() - query.timestamp).total_seconds() / 3600
        if idade_horas > last_hours:
            continue
        
        area = query.area or "geral"
        
        if area not in areas:
            areas[area] = {
                'total': 0,
                'latencias': [],
                'tokens': 0
            }
        
        areas[area]['total'] += 1
        areas[area]['latencias'].append(query.total_latency_ms)
        areas[area]['tokens'] += query.tokens_generated
    
    if not areas:
        print("⚠️  Nenhuma query por área registrada")
        return
    
    print(f"""
{'='*70}
📖 MÉTRICAS POR ÁREA (Últimas {last_hours}h)
{'='*70}
""")
    
    for area, dados in sorted(areas.items(), key=lambda x: x[1]['total'], reverse=True):
        latencia_media = sum(dados['latencias']) / len(dados['latencias'])
        tokens_medio = dados['tokens'] / dados['total']
        
        print(f"""
{area.upper()}:
  Queries: {dados['total']:,}
  Latência Média: {formatar_tempo(latencia_media)}
  Tokens Médio: {tokens_medio:.0f}
""")


def visualizar_saude_modelo():
    """Visualiza saúde do modelo"""
    
    metrics = get_model_metrics()
    health = metrics.get_model_health()
    
    status_emoji = {
        'healthy': '✅',
        'warning': '⚠️',
        'critical': '❌'
    }
    
    emoji = status_emoji.get(health['status'], '❓')
    
    print(f"""
{'='*70}
{emoji} SAÚDE DO MODELO
{'='*70}

Status: {health['status'].upper()}
Última Atualização: {health['last_check'].strftime('%Y-%m-%d %H:%M:%S')}
""")
    
    if health['issues']:
        print("\n❌ PROBLEMAS CRÍTICOS:")
        for issue in health['issues']:
            print(f"  • {issue}")
    
    if health['warnings']:
        print("\n⚠️  AVISOS:")
        for warning in health['warnings']:
            print(f"  • {warning}")
    
    if not health['issues'] and not health['warnings']:
        print("\n✅ Tudo funcionando perfeitamente!")
    
    print()


def exportar_metricas(output_path: str = None):
    """Exporta métricas para JSON"""
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"metricas_export_{timestamp}.json"
    
    metrics = get_model_metrics()
    metrics.save_metrics(output_path)
    
    print(f"💾 Métricas exportadas para: {output_path}")


def main():
    """Função principal"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualizar Métricas do Modelo')
    parser.add_argument('--last-hours', type=int, default=24, help='Últimas N horas')
    parser.add_argument('--export', action='store_true', help='Exportar métricas para JSON')
    parser.add_argument('--output', type=str, default=None, help='Arquivo de saída')
    
    args = parser.parse_args()
    
    print(f"""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║            📊 MÉTRICAS DO MODELO - CONCURSAI 🤖                   ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")
    
    # Saúde do modelo
    visualizar_saude_modelo()
    
    # Métricas de embeddings
    visualizar_metricas_embedding(args.last_hours)
    
    # Métricas de LLM
    visualizar_metricas_llm(args.last_hours)
    
    # Métricas de RAG
    visualizar_metricas_rag(args.last_hours)
    
    # Métricas por banca
    visualizar_metricas_por_banca(args.last_hours)
    
    # Métricas por área
    visualizar_metricas_por_area(args.last_hours)
    
    # Exportar se solicitado
    if args.export:
        exportar_metricas(args.output)
    
    print(f"""
{'='*70}
✅ Visualização concluída!
{'='*70}
""")


if __name__ == "__main__":
    main()
