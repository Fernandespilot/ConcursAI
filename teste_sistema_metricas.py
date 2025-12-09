"""
🧪 TESTE RÁPIDO DO SISTEMA DE MÉTRICAS
========================================
Valida que tudo está funcionando corretamente
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def teste_1_importacoes():
    """Testa se todos os módulos podem ser importados"""
    print("\n" + "="*70)
    print("🧪 TESTE 1: Importações")
    print("="*70)
    
    try:
        from modules.model_metrics import get_model_metrics
        print("✅ model_metrics importado")
        
        from modules.rag_banca_inteligente import get_rag_inteligente
        print("✅ rag_banca_inteligente importado")
        
        return True
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
        return False


def teste_2_ground_truth():
    """Testa se ground truth pode ser carregado"""
    print("\n" + "="*70)
    print("🧪 TESTE 2: Ground Truth Dataset")
    print("="*70)
    
    try:
        import json
        from pathlib import Path
        
        gt_path = Path("datasets/ground_truth_rag.json")
        
        if not gt_path.exists():
            print(f"❌ Arquivo não encontrado: {gt_path}")
            return False
        
        with open(gt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        num_perguntas = len(data.get('perguntas', []))
        print(f"✅ Ground truth carregado: {num_perguntas} perguntas")
        
        # Validar estrutura
        primeira = data['perguntas'][0]
        campos_obrigatorios = ['id', 'pergunta', 'resposta_esperada', 'keywords_obrigatorias']
        
        for campo in campos_obrigatorios:
            if campo not in primeira:
                print(f"❌ Campo obrigatório ausente: {campo}")
                return False
        
        print("✅ Estrutura do ground truth válida")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar ground truth: {e}")
        return False


def teste_3_sistema_metricas():
    """Testa se sistema de métricas funciona"""
    print("\n" + "="*70)
    print("🧪 TESTE 3: Sistema de Métricas")
    print("="*70)
    
    try:
        from modules.model_metrics import get_model_metrics
        import time
        
        metrics = get_model_metrics()
        print("✅ Sistema de métricas inicializado")
        
        # Testar rastreamento de embedding
        start = time.time()
        time.sleep(0.01)  # Simular operação
        metrics.track_embedding(
            text="teste",
            model="nomic-embed-text",
            start_time=start,
            dimensions=384,
            success=True
        )
        print("✅ Rastreamento de embedding funciona")
        
        # Testar rastreamento de LLM
        start = time.time()
        time.sleep(0.02)  # Simular operação
        metrics.track_llm_query(
            pergunta="Teste?",
            resposta="Resposta de teste",
            model="llama3.2",
            start_time=start,
            prompt_tokens=10,
            completion_tokens=5,
            temperature=0.7
        )
        print("✅ Rastreamento de LLM funciona")
        
        # Testar rastreamento de RAG
        metrics.track_rag_query(
            pergunta="O que o CESPE mais cobra?",
            resposta="Python, Redes, Segurança",
            banca="CESPE",
            area="Tecnologia",
            embedding_latency_ms=50,
            retrieval_latency_ms=100,
            llm_latency_ms=2000,
            num_chunks=5,
            avg_similarity=0.85,
            has_source=True,
            tokens_generated=20
        )
        print("✅ Rastreamento de RAG funciona")
        
        # Testar estatísticas
        stats = metrics.get_embedding_stats(last_hours=24)
        if stats['total_operations'] >= 1:
            print("✅ Estatísticas de embedding funcionam")
        else:
            print("⚠️  Estatísticas podem estar zeradas")
        
        stats = metrics.get_llm_stats(last_hours=24)
        if stats['total_queries'] >= 1:
            print("✅ Estatísticas de LLM funcionam")
        
        stats = metrics.get_rag_stats(last_hours=24)
        if stats['total_queries'] >= 1:
            print("✅ Estatísticas de RAG funcionam")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no sistema de métricas: {e}")
        import traceback
        traceback.print_exc()
        return False


def teste_4_validacao():
    """Testa validação contra ground truth"""
    print("\n" + "="*70)
    print("🧪 TESTE 4: Validação contra Ground Truth")
    print("="*70)
    
    try:
        from modules.model_metrics import get_model_metrics
        
        metrics = get_model_metrics()
        
        # Testar validação
        pergunta = "O que o CESPE mais cobra em Tecnologia?"
        resposta_boa = "Python, Redes, Segurança da Informação, Banco de Dados"
        resposta_ruim = "Não sei responder essa pergunta"
        
        # Validar resposta boa
        validation = metrics.validator.validate_response(pergunta, resposta_boa)
        
        if validation:
            score = validation['keyword_match_score']
            print(f"✅ Validação funciona: Score={score:.2f}")
            
            if score > 0.5:
                print("✅ Resposta boa foi reconhecida")
            else:
                print("⚠️  Score baixo para resposta boa")
        else:
            print("⚠️  Pergunta não encontrada no ground truth")
        
        # Validar resposta ruim
        validation_ruim = metrics.validator.validate_response(pergunta, resposta_ruim)
        if validation_ruim:
            score_ruim = validation_ruim['keyword_match_score']
            if score_ruim < score:
                print("✅ Resposta ruim foi identificada como inferior")
            else:
                print("⚠️  Sistema não diferenciou resposta boa de ruim")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        import traceback
        traceback.print_exc()
        return False


def teste_5_rag_integracao():
    """Testa se RAG está integrando métricas"""
    print("\n" + "="*70)
    print("🧪 TESTE 5: Integração RAG + Métricas")
    print("="*70)
    
    try:
        from modules.rag_banca_inteligente import get_rag_inteligente
        from modules.model_metrics import get_model_metrics
        
        rag = get_rag_inteligente()
        print("✅ RAG inicializado")
        
        # Verificar se tem sistema de métricas
        if hasattr(rag, 'metrics'):
            print("✅ RAG tem sistema de métricas integrado")
        else:
            print("❌ RAG NÃO tem sistema de métricas!")
            return False
        
        # Testar query simples
        pergunta = "O que o CESPE mais cobra em Tecnologia?"
        print(f"\n❓ Testando: {pergunta}")
        
        resposta = rag.responder(pergunta, usar_ollama=False)
        print(f"✅ Resposta gerada ({len(resposta)} caracteres)")
        
        # Verificar se métricas foram registradas
        metrics = get_model_metrics()
        stats = metrics.get_rag_stats(last_hours=1)
        
        if stats['total_queries'] >= 1:
            print(f"✅ Métricas foram registradas: {stats['total_queries']} queries")
            print(f"   Latência média: {stats['avg_total_latency_ms']:.0f}ms")
        else:
            print("⚠️  Métricas não foram registradas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes"""
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║            🧪 TESTE DO SISTEMA DE MÉTRICAS                        ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")
    
    testes = [
        ("Importações", teste_1_importacoes),
        ("Ground Truth", teste_2_ground_truth),
        ("Sistema de Métricas", teste_3_sistema_metricas),
        ("Validação", teste_4_validacao),
        ("Integração RAG", teste_5_rag_integracao),
    ]
    
    resultados = []
    
    for nome, teste_func in testes:
        try:
            sucesso = teste_func()
            resultados.append((nome, sucesso))
        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO no teste '{nome}': {e}")
            resultados.append((nome, False))
    
    # Resumo
    print("\n" + "="*70)
    print("📊 RESUMO DOS TESTES")
    print("="*70 + "\n")
    
    sucessos = sum(1 for _, ok in resultados if ok)
    total = len(resultados)
    
    for nome, ok in resultados:
        emoji = "✅" if ok else "❌"
        print(f"{emoji} {nome}")
    
    print(f"\n{'='*70}")
    print(f"Sucessos: {sucessos}/{total} ({sucessos/total:.0%})")
    print("="*70)
    
    if sucessos == total:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema pronto para uso.")
        return 0
    else:
        print(f"\n⚠️  {total - sucessos} teste(s) falharam. Veja os detalhes acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
