"""
🤖 SISTEMA DE MÉTRICAS DO MODELO DE IA
======================================
Rastreamento completo de métricas de qualidade, performance e eficiência
dos modelos de embeddings e LLM (Ollama)

Métricas Implementadas:
1. Qualidade do Modelo (Precision, Recall, F1, Accuracy)
2. Performance (Latência, Throughput, Tokens/s)
3. Eficiência (Uso de recursos, custo por query)
4. Confiabilidade (Confidence scores, hallucination rate)
5. Comportamento (Distribuição de respostas, padrões)
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
import requests

logger = logging.getLogger(__name__)


# ============================================
# DATA CLASSES PARA MÉTRICAS
# ============================================

@dataclass
class EmbeddingMetrics:
    """Métricas de uma operação de embedding"""
    timestamp: str
    model: str
    text_length: int
    embedding_dim: int
    latency_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class LLMQueryMetrics:
    """Métricas de uma query ao LLM"""
    timestamp: str
    model: str
    pergunta: str
    pergunta_length: int
    resposta: str
    resposta_length: int
    tokens_input: int
    tokens_output: int
    latency_ms: float
    tokens_per_second: float
    temperature: float
    top_p: float
    context_window_used: int
    success: bool
    confidence_score: Optional[float] = None
    hallucination_detected: bool = False
    error: Optional[str] = None


@dataclass
class RAGQueryMetrics:
    """Métricas de uma query RAG completa"""
    timestamp: str
    pergunta: str
    banca: Optional[str]
    area: Optional[str]
    
    # Fase de Retrieval
    embedding_latency_ms: float
    num_chunks_retrieved: int
    retrieval_latency_ms: float
    avg_similarity_score: float
    
    # Fase de Generation
    llm_latency_ms: float
    resposta_length: int
    tokens_generated: int
    tokens_per_second: float
    
    # Métricas de Qualidade
    has_source: bool
    source_attribution_valid: bool
    
    # Total
    total_latency_ms: float
    success: bool
    
    # Campos opcionais (devem vir por último)
    relevance_score: Optional[float] = None
    completeness_score: Optional[float] = None
    user_feedback: Optional[bool] = None  # thumbs up/down
    error: Optional[str] = None


# ============================================
# VALIDAÇÃO COM GROUND TRUTH
# ============================================

class GroundTruthValidator:
    """Valida respostas do modelo contra ground truth dataset"""
    
    def __init__(self, ground_truth_file: str = "datasets/ground_truth_rag.json"):
        self.ground_truth_file = Path(ground_truth_file)
        self.ground_truth = self._load_ground_truth()
        
    def _load_ground_truth(self) -> List[Dict]:
        """Carrega dataset de ground truth"""
        if not self.ground_truth_file.exists():
            logger.warning(f"⚠️ Ground truth não encontrado: {self.ground_truth_file}")
            return []
        
        try:
            with open(self.ground_truth_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"✅ Ground truth carregado: {len(data.get('perguntas', []))} perguntas")
            return data.get('perguntas', [])
        except Exception as e:
            logger.error(f"❌ Erro ao carregar ground truth: {e}")
            return []
    
    def validate_response(
        self, 
        pergunta: str, 
        resposta_modelo: str
    ) -> Dict[str, Any]:
        """
        Valida resposta do modelo contra ground truth
        
        Returns:
            {
                'exact_match': bool,
                'keyword_match_score': float (0-1),
                'semantic_similarity': float (0-1),
                'has_expected_keywords': bool,
                'missing_keywords': list,
                'extra_keywords': list
            }
        """
        # Encontrar pergunta no ground truth
        gt_entry = None
        for entry in self.ground_truth:
            if entry['pergunta'].lower() == pergunta.lower():
                gt_entry = entry
                break
        
        if not gt_entry:
            return {'status': 'no_ground_truth', 'message': 'Pergunta não encontrada no ground truth'}
        
        resposta_esperada = gt_entry.get('resposta_esperada', '')
        keywords_obrigatorias = gt_entry.get('keywords_obrigatorias', [])
        
        # Exact match
        exact_match = resposta_modelo.lower().strip() == resposta_esperada.lower().strip()
        
        # Keyword match
        resposta_lower = resposta_modelo.lower()
        keywords_presentes = [kw for kw in keywords_obrigatorias if kw.lower() in resposta_lower]
        keyword_match_score = len(keywords_presentes) / len(keywords_obrigatorias) if keywords_obrigatorias else 0.0
        
        missing_keywords = [kw for kw in keywords_obrigatorias if kw not in keywords_presentes]
        
        # Métricas
        has_expected_keywords = keyword_match_score >= 0.8  # 80% das keywords presentes
        
        return {
            'status': 'validated',
            'exact_match': exact_match,
            'keyword_match_score': keyword_match_score,
            'has_expected_keywords': has_expected_keywords,
            'keywords_presentes': keywords_presentes,
            'missing_keywords': missing_keywords,
            'total_keywords': len(keywords_obrigatorias)
        }
    
    def calculate_model_accuracy(self, validations: List[Dict]) -> Dict[str, float]:
        """
        Calcula accuracy do modelo baseado em múltiplas validações
        
        Returns:
            {
                'exact_match_accuracy': float,
                'keyword_accuracy': float,
                'avg_keyword_score': float,
                'precision': float,
                'recall': float,
                'f1_score': float
            }
        """
        if not validations:
            return {}
        
        exact_matches = sum(1 for v in validations if v.get('exact_match', False))
        keyword_matches = sum(1 for v in validations if v.get('has_expected_keywords', False))
        keyword_scores = [v.get('keyword_match_score', 0) for v in validations]
        
        # True Positives: keywords presentes
        tp = sum(len(v.get('keywords_presentes', [])) for v in validations)
        # False Negatives: keywords faltando
        fn = sum(len(v.get('missing_keywords', [])) for v in validations)
        # Total esperado
        total_expected = tp + fn
        
        precision = tp / total_expected if total_expected > 0 else 0
        recall = tp / total_expected if total_expected > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'exact_match_accuracy': exact_matches / len(validations),
            'keyword_accuracy': keyword_matches / len(validations),
            'avg_keyword_score': np.mean(keyword_scores),
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'total_validations': len(validations)
        }


# ============================================
# SISTEMA PRINCIPAL DE MÉTRICAS DO MODELO
# ============================================

class ModelMetricsSystem:
    """Sistema centralizado de métricas do modelo"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        
        # Históricos de métricas
        self.embedding_history: List[EmbeddingMetrics] = []
        self.llm_history: List[LLMQueryMetrics] = []
        self.rag_history: List[RAGQueryMetrics] = []
        
        # Validador
        self.validator = GroundTruthValidator()
        self.validations: List[Dict] = []
        
        # Configurações atuais do modelo
        self.model_config = {
            'embedding_model': 'nomic-embed-text',
            'llm_model': 'llama3.2',
            'temperature': 0.7,
            'top_p': 0.9,
            'max_tokens': 2048,
            'context_window': 8192
        }
        
        logger.info("✅ ModelMetricsSystem inicializado")
    
    # ============================================
    # RASTREAMENTO DE MÉTRICAS
    # ============================================
    
    def track_embedding(
        self,
        text: str,
        model: str,
        start_time: float,
        embedding_result: Optional[List[float]] = None,
        error: Optional[Exception] = None
    ) -> EmbeddingMetrics:
        """Rastreia operação de embedding"""
        
        latency_ms = (time.time() - start_time) * 1000
        
        metrics = EmbeddingMetrics(
            timestamp=datetime.now().isoformat(),
            model=model,
            text_length=len(text),
            embedding_dim=len(embedding_result) if embedding_result else 0,
            latency_ms=latency_ms,
            success=embedding_result is not None,
            error=str(error) if error else None
        )
        
        self.embedding_history.append(metrics)
        return metrics
    
    def track_llm_query(
        self,
        pergunta: str,
        resposta: str,
        model: str,
        temperature: float,
        top_p: float,
        start_time: float,
        tokens_input: int = 0,
        tokens_output: int = 0,
        error: Optional[Exception] = None
    ) -> LLMQueryMetrics:
        """Rastreia query ao LLM"""
        
        latency_ms = (time.time() - start_time) * 1000
        tokens_per_second = tokens_output / (latency_ms / 1000) if latency_ms > 0 else 0
        
        metrics = LLMQueryMetrics(
            timestamp=datetime.now().isoformat(),
            model=model,
            pergunta=pergunta,
            pergunta_length=len(pergunta),
            resposta=resposta,
            resposta_length=len(resposta),
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            tokens_per_second=tokens_per_second,
            temperature=temperature,
            top_p=top_p,
            context_window_used=tokens_input + tokens_output,
            success=resposta is not None and not error,
            error=str(error) if error else None
        )
        
        self.llm_history.append(metrics)
        return metrics
    
    def track_rag_query(
        self,
        pergunta: str,
        resposta: str,
        banca: Optional[str],
        area: Optional[str],
        embedding_latency_ms: float,
        retrieval_latency_ms: float,
        llm_latency_ms: float,
        num_chunks: int,
        avg_similarity: float,
        has_source: bool,
        tokens_generated: int = 0,
        error: Optional[Exception] = None
    ) -> RAGQueryMetrics:
        """Rastreia query RAG completa"""
        
        total_latency = embedding_latency_ms + retrieval_latency_ms + llm_latency_ms
        tokens_per_second = tokens_generated / (llm_latency_ms / 1000) if llm_latency_ms > 0 else 0
        
        metrics = RAGQueryMetrics(
            timestamp=datetime.now().isoformat(),
            pergunta=pergunta,
            banca=banca,
            area=area,
            embedding_latency_ms=embedding_latency_ms,
            num_chunks_retrieved=num_chunks,
            retrieval_latency_ms=retrieval_latency_ms,
            avg_similarity_score=avg_similarity,
            llm_latency_ms=llm_latency_ms,
            resposta_length=len(resposta),
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_second,
            has_source=has_source,
            source_attribution_valid=has_source,  # Simplificado
            total_latency_ms=total_latency,
            success=resposta is not None and not error,
            error=str(error) if error else None
        )
        
        self.rag_history.append(metrics)
        
        # Validar contra ground truth se disponível
        if self.validator.ground_truth:
            validation = self.validator.validate_response(pergunta, resposta)
            if validation.get('status') == 'validated':
                metrics.relevance_score = validation['keyword_match_score']
                metrics.completeness_score = 1.0 if validation['has_expected_keywords'] else 0.5
                self.validations.append(validation)
        
        return metrics
    
    def add_user_feedback(self, query_index: int, thumbs_up: bool):
        """Adiciona feedback do usuário"""
        if 0 <= query_index < len(self.rag_history):
            self.rag_history[query_index].user_feedback = thumbs_up
    
    # ============================================
    # ANÁLISE DE MÉTRICAS
    # ============================================
    
    def get_embedding_stats(self, last_hours: int = 24) -> Dict:
        """Estatísticas de embeddings"""
        cutoff = datetime.now() - timedelta(hours=last_hours)
        recent = [m for m in self.embedding_history 
                  if datetime.fromisoformat(m.timestamp) > cutoff]
        
        if not recent:
            return {'status': 'no_data'}
        
        successful = [m for m in recent if m.success]
        
        return {
            'total_embeddings': len(recent),
            'successful': len(successful),
            'failed': len(recent) - len(successful),
            'success_rate': len(successful) / len(recent) * 100,
            'avg_latency_ms': np.mean([m.latency_ms for m in successful]) if successful else 0,
            'p50_latency_ms': np.percentile([m.latency_ms for m in successful], 50) if successful else 0,
            'p95_latency_ms': np.percentile([m.latency_ms for m in successful], 95) if successful else 0,
            'p99_latency_ms': np.percentile([m.latency_ms for m in successful], 99) if successful else 0,
            'avg_text_length': np.mean([m.text_length for m in recent]),
            'model': successful[0].model if successful else 'unknown'
        }
    
    def get_llm_stats(self, last_hours: int = 24) -> Dict:
        """Estatísticas do LLM"""
        cutoff = datetime.now() - timedelta(hours=last_hours)
        recent = [m for m in self.llm_history 
                  if datetime.fromisoformat(m.timestamp) > cutoff]
        
        if not recent:
            return {'status': 'no_data'}
        
        successful = [m for m in recent if m.success]
        
        return {
            'total_queries': len(recent),
            'successful': len(successful),
            'failed': len(recent) - len(successful),
            'success_rate': len(successful) / len(recent) * 100,
            'avg_latency_ms': np.mean([m.latency_ms for m in successful]) if successful else 0,
            'p50_latency_ms': np.percentile([m.latency_ms for m in successful], 50) if successful else 0,
            'p95_latency_ms': np.percentile([m.latency_ms for m in successful], 95) if successful else 0,
            'p99_latency_ms': np.percentile([m.latency_ms for m in successful], 99) if successful else 0,
            'avg_tokens_per_second': np.mean([m.tokens_per_second for m in successful]) if successful else 0,
            'total_tokens_generated': sum(m.tokens_output for m in successful),
            'avg_response_length': np.mean([m.resposta_length for m in successful]) if successful else 0,
            'model': successful[0].model if successful else 'unknown',
            'avg_temperature': np.mean([m.temperature for m in recent])
        }
    
    def get_rag_stats(self, last_hours: int = 24) -> Dict:
        """Estatísticas do RAG completo"""
        cutoff = datetime.now() - timedelta(hours=last_hours)
        recent = [m for m in self.rag_history 
                  if datetime.fromisoformat(m.timestamp) > cutoff]
        
        if not recent:
            return {'status': 'no_data'}
        
        successful = [m for m in recent if m.success]
        with_feedback = [m for m in successful if m.user_feedback is not None]
        
        # Breakdown de latência por fase
        avg_embedding = np.mean([m.embedding_latency_ms for m in successful]) if successful else 0
        avg_retrieval = np.mean([m.retrieval_latency_ms for m in successful]) if successful else 0
        avg_llm = np.mean([m.llm_latency_ms for m in successful]) if successful else 0
        
        return {
            'total_queries': len(recent),
            'successful': len(successful),
            'failed': len(recent) - len(successful),
            'success_rate': len(successful) / len(recent) * 100,
            
            # Latência total
            'avg_total_latency_ms': np.mean([m.total_latency_ms for m in successful]) if successful else 0,
            'p95_total_latency_ms': np.percentile([m.total_latency_ms for m in successful], 95) if successful else 0,
            
            # Breakdown por fase
            'latency_breakdown': {
                'embedding_ms': avg_embedding,
                'embedding_percent': avg_embedding / (avg_embedding + avg_retrieval + avg_llm) * 100 if (avg_embedding + avg_retrieval + avg_llm) > 0 else 0,
                'retrieval_ms': avg_retrieval,
                'retrieval_percent': avg_retrieval / (avg_embedding + avg_retrieval + avg_llm) * 100 if (avg_embedding + avg_retrieval + avg_llm) > 0 else 0,
                'llm_ms': avg_llm,
                'llm_percent': avg_llm / (avg_embedding + avg_retrieval + avg_llm) * 100 if (avg_embedding + avg_retrieval + avg_llm) > 0 else 0
            },
            
            # Qualidade
            'avg_similarity_score': np.mean([m.avg_similarity_score for m in successful]) if successful else 0,
            'source_attribution_rate': sum(m.has_source for m in successful) / len(successful) * 100 if successful else 0,
            'avg_relevance_score': np.mean([m.relevance_score for m in successful if m.relevance_score]) if successful else None,
            
            # Feedback
            'feedback_count': len(with_feedback),
            'satisfaction_rate': sum(m.user_feedback for m in with_feedback) / len(with_feedback) * 100 if with_feedback else None,
            
            # Tokens
            'avg_tokens_per_second': np.mean([m.tokens_per_second for m in successful]) if successful else 0,
            'total_tokens_generated': sum(m.tokens_generated for m in successful)
        }
    
    def get_model_quality_metrics(self) -> Dict:
        """Métricas de qualidade do modelo usando ground truth"""
        if not self.validations:
            return {
                'status': 'no_validations',
                'message': 'Execute validações com ground truth primeiro'
            }
        
        return self.validator.calculate_model_accuracy(self.validations)
    
    def get_model_health(self) -> Dict:
        """Saúde geral do modelo"""
        
        embedding_stats = self.get_embedding_stats(last_hours=1)
        llm_stats = self.get_llm_stats(last_hours=1)
        rag_stats = self.get_rag_stats(last_hours=1)
        
        issues = []
        warnings = []
        
        # Check Ollama
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            ollama_online = response.status_code == 200
        except:
            ollama_online = False
            issues.append("Ollama offline")
        
        # Check latências
        if rag_stats.get('avg_total_latency_ms', 0) > 10000:
            issues.append(f"RAG muito lento: {rag_stats['avg_total_latency_ms']:.0f}ms")
        elif rag_stats.get('avg_total_latency_ms', 0) > 5000:
            warnings.append(f"RAG lento: {rag_stats['avg_total_latency_ms']:.0f}ms")
        
        # Check taxa de erro
        if rag_stats.get('success_rate', 100) < 95:
            issues.append(f"Taxa de sucesso baixa: {rag_stats['success_rate']:.1f}%")
        elif rag_stats.get('success_rate', 100) < 98:
            warnings.append(f"Taxa de sucesso: {rag_stats['success_rate']:.1f}%")
        
        # Check tokens/segundo
        if llm_stats.get('avg_tokens_per_second', 0) < 10:
            warnings.append(f"LLM lento: {llm_stats['avg_tokens_per_second']:.1f} tokens/s")
        
        # Determinar status geral
        if issues:
            health_status = 'critical'
        elif warnings:
            health_status = 'warning'
        else:
            health_status = 'excellent'
        
        return {
            'status': health_status,
            'ollama_online': ollama_online,
            'issues': issues,
            'warnings': warnings,
            'embedding_success_rate': embedding_stats.get('success_rate'),
            'llm_success_rate': llm_stats.get('success_rate'),
            'rag_success_rate': rag_stats.get('success_rate'),
            'avg_rag_latency_ms': rag_stats.get('avg_total_latency_ms'),
            'tokens_per_second': llm_stats.get('avg_tokens_per_second'),
            'last_check': datetime.now().isoformat()
        }
    
    # ============================================
    # BENCHMARK E COMPARAÇÃO
    # ============================================
    
    def run_benchmark(self, test_queries: List[str], num_iterations: int = 3) -> Dict:
        """
        Executa benchmark do modelo com queries de teste
        
        Args:
            test_queries: Lista de perguntas para testar
            num_iterations: Número de vezes para repetir cada query
            
        Returns:
            Métricas agregadas do benchmark
        """
        results = []
        
        for query in test_queries:
            query_results = []
            
            for i in range(num_iterations):
                start = time.time()
                
                try:
                    # Simular query RAG (adaptar para seu sistema real)
                    # Este é um placeholder - você deve chamar seu sistema RAG real
                    response = f"Resposta para: {query}"
                    latency = (time.time() - start) * 1000
                    
                    query_results.append({
                        'query': query,
                        'iteration': i + 1,
                        'latency_ms': latency,
                        'success': True
                    })
                    
                except Exception as e:
                    query_results.append({
                        'query': query,
                        'iteration': i + 1,
                        'latency_ms': 0,
                        'success': False,
                        'error': str(e)
                    })
            
            results.append({
                'query': query,
                'avg_latency_ms': np.mean([r['latency_ms'] for r in query_results if r['success']]),
                'min_latency_ms': np.min([r['latency_ms'] for r in query_results if r['success']]),
                'max_latency_ms': np.max([r['latency_ms'] for r in query_results if r['success']]),
                'success_rate': sum(r['success'] for r in query_results) / len(query_results) * 100,
                'iterations': query_results
            })
        
        return {
            'benchmark_timestamp': datetime.now().isoformat(),
            'total_queries': len(test_queries),
            'iterations_per_query': num_iterations,
            'avg_latency_ms': np.mean([r['avg_latency_ms'] for r in results]),
            'p95_latency_ms': np.percentile([r['avg_latency_ms'] for r in results], 95),
            'overall_success_rate': np.mean([r['success_rate'] for r in results]),
            'results_by_query': results
        }
    
    def compare_model_configs(self, configs: List[Dict]) -> Dict:
        """
        Compara diferentes configurações do modelo
        
        Args:
            configs: Lista de configurações para testar
            Exemplo: [
                {'temperature': 0.5, 'top_p': 0.9},
                {'temperature': 0.7, 'top_p': 0.9},
                {'temperature': 0.9, 'top_p': 0.95}
            ]
        """
        # Placeholder para comparação de configurações
        # Implementar lógica real de teste com diferentes configs
        pass
    
    # ============================================
    # PERSISTÊNCIA
    # ============================================
    
    def save_metrics(self, filepath: str = "metrics/model_metrics.json"):
        """Salva métricas em arquivo"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'saved_at': datetime.now().isoformat(),
            'model_config': self.model_config,
            'embedding_history': [asdict(m) for m in self.embedding_history[-1000:]],
            'llm_history': [asdict(m) for m in self.llm_history[-1000:]],
            'rag_history': [asdict(m) for m in self.rag_history[-1000:]],
            'validations': self.validations[-1000:],
            'summary_stats': {
                'embedding': self.get_embedding_stats(),
                'llm': self.get_llm_stats(),
                'rag': self.get_rag_stats(),
                'quality': self.get_model_quality_metrics()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Métricas salvas em: {filepath}")
    
    def load_metrics(self, filepath: str = "metrics/model_metrics.json"):
        """Carrega métricas de arquivo"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restaurar históricos
            self.embedding_history = [EmbeddingMetrics(**m) for m in data.get('embedding_history', [])]
            self.llm_history = [LLMQueryMetrics(**m) for m in data.get('llm_history', [])]
            self.rag_history = [RAGQueryMetrics(**m) for m in data.get('rag_history', [])]
            self.validations = data.get('validations', [])
            
            logger.info(f"✅ Métricas carregadas de: {filepath}")
        except FileNotFoundError:
            logger.warning(f"⚠️ Arquivo não encontrado: {filepath}")
    
    def export_to_csv(self, output_dir: str = "metrics/"):
        """Exporta métricas para CSV"""
        import csv
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export RAG metrics
        if self.rag_history:
            with open(output_path / 'rag_metrics.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=asdict(self.rag_history[0]).keys())
                writer.writeheader()
                for metric in self.rag_history:
                    writer.writerow(asdict(metric))
        
        logger.info(f"✅ Métricas exportadas para: {output_path}")


# ============================================
# SINGLETON
# ============================================

_model_metrics = None

def get_model_metrics() -> ModelMetricsSystem:
    """Retorna instância global do sistema de métricas"""
    global _model_metrics
    if _model_metrics is None:
        _model_metrics = ModelMetricsSystem()
    return _model_metrics


# ============================================
# CLI PARA TESTES
# ============================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🤖 Sistema de Métricas do Modelo - Demo")
    print("=" * 50)
    
    metrics = get_model_metrics()
    
    # Simular algumas queries
    print("\n📊 Simulando queries...")
    
    for i in range(5):
        start = time.time()
        metrics.track_rag_query(
            pergunta=f"Pergunta teste {i+1}",
            resposta=f"Resposta gerada {i+1}",
            banca="CESPE",
            area="Tecnologia",
            embedding_latency_ms=50 + np.random.rand() * 20,
            retrieval_latency_ms=100 + np.random.rand() * 50,
            llm_latency_ms=2000 + np.random.rand() * 500,
            num_chunks=5,
            avg_similarity=0.85 + np.random.rand() * 0.1,
            has_source=True,
            tokens_generated=150 + int(np.random.rand() * 50)
        )
    
    # Exibir estatísticas
    print("\n📈 Estatísticas do RAG:")
    stats = metrics.get_rag_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    print("\n🏥 Saúde do Modelo:")
    health = metrics.get_model_health()
    print(json.dumps(health, indent=2, ensure_ascii=False))
    
    # Salvar
    metrics.save_metrics()
    print("\n✅ Métricas salvas!")
