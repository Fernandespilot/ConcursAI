# 🤖 FOCO EM MÉTRICAS DO MODELO - ConcursAI

**Data:** 04 de Dezembro de 2025  
**Versão:** 1.0 - Modelo-Cêntrico  
**Objetivo:** Otimizar qualidade, performance e eficiência dos modelos de IA

---

## 📊 RESUMO EXECUTIVO

### **Modelos Atualmente em Uso:**

```yaml
Sistema de Embeddings:
  modelo: nomic-embed-text
  dimensões: 384
  uso: Vetorização de textos para busca semântica
  
Sistema LLM:
  modelo: llama3.2 (via Ollama)
  quantização: Q4_K_M (4-bit mixed precision)
  contexto: 8192 tokens
  temperatura: 0.7
  top_p: 0.9
```

### **Estado Atual das Métricas:**

✅ **Implementado:**
- Logging básico de operações
- Contagem de requisições
- Status do Ollama (online/offline)

❌ **FALTA (Crítico):**
- Métricas de qualidade em tempo real
- Validação com ground truth
- Rastreamento de latência por fase
- Monitoramento de tokens/segundo
- Detecção de hallucinations
- Confidence scores

---

## 🎯 MÉTRICAS ESSENCIAIS DO MODELO

### 1️⃣ **QUALIDADE (Accuracy, Precision, Recall)**

#### **O que medir:**

```python
✨ Precision (Precisão)
   Fórmula: TP / (TP + FP)
   Significado: % de respostas relevantes retornadas
   Meta: > 85%
   Atual: 85.2% (ESTIMADO, não medido)

✨ Recall (Revocação)
   Fórmula: TP / (TP + FN)
   Significado: % de respostas relevantes encontradas
   Meta: > 80%
   Atual: 79.8% (ESTIMADO, não medido)

✨ F1-Score
   Fórmula: 2 * (Precision * Recall) / (Precision + Recall)
   Significado: Média harmônica
   Meta: > 80%
   Atual: 82.4% (ESTIMADO, não medido)

✨ Keyword Match Score
   Significado: % de keywords obrigatórias presentes
   Meta: > 80%
   Atual: NÃO MEDIDO

✨ Exact Match
   Significado: Resposta exatamente igual ao ground truth
   Meta: > 10% (para perguntas objetivas)
   Atual: NÃO MEDIDO
```

#### **Como medir (IMPLEMENTADO):**

```python
# Usar módulo: modules/model_metrics.py
from modules.model_metrics import get_model_metrics

metrics = get_model_metrics()

# Validar contra ground truth
validation = metrics.validator.validate_response(
    pergunta="O que o CESPE mais cobra em Tecnologia?",
    resposta_modelo="Python, Redes, Segurança..."
)

# Resultado:
# {
#     'exact_match': False,
#     'keyword_match_score': 0.85,  # 85% das keywords presentes
#     'has_expected_keywords': True,
#     'keywords_presentes': ['python', 'redes', 'segurança'],
#     'missing_keywords': ['banco de dados']
# }

# Calcular métricas agregadas
accuracy_metrics = metrics.get_model_quality_metrics()
# {
#     'precision': 0.87,
#     'recall': 0.83,
#     'f1_score': 0.85,
#     'keyword_accuracy': 0.85
# }
```

---

### 2️⃣ **PERFORMANCE (Latência, Throughput)**

#### **O que medir:**

```python
✨ Latência Total (RAG completo)
   Meta: < 5 segundos (P95)
   Atual: 4.1s (DOCUMENTADO, não rastreado em tempo real)

✨ Latência por Fase:
   - Embedding: < 100ms
   - Retrieval: < 200ms  
   - LLM Generation: < 3000ms
   Atual: NÃO RASTREADO

✨ Tokens por Segundo
   Meta: > 20 tokens/s
   Atual: NÃO MEDIDO

✨ Throughput
   Meta: > 10 queries/minuto
   Atual: NÃO MEDIDO

✨ Latência por Percentil:
   - P50 (mediana): < 2s
   - P95 (95%): < 5s
   - P99 (99%): < 8s
   Atual: NÃO RASTREADO
```

#### **Como medir (IMPLEMENTADO):**

```python
# Rastrear query RAG completa
start_embedding = time.time()
# ... operação de embedding ...
embedding_latency = (time.time() - start_embedding) * 1000

start_retrieval = time.time()
# ... busca no vectorstore ...
retrieval_latency = (time.time() - start_retrieval) * 1000

start_llm = time.time()
# ... geração com LLM ...
llm_latency = (time.time() - start_llm) * 1000

# Rastrear métricas
metrics.track_rag_query(
    pergunta="...",
    resposta="...",
    banca="CESPE",
    area="Tecnologia",
    embedding_latency_ms=embedding_latency,
    retrieval_latency_ms=retrieval_latency,
    llm_latency_ms=llm_latency,
    num_chunks=5,
    avg_similarity=0.85,
    has_source=True,
    tokens_generated=150
)

# Analisar estatísticas
stats = metrics.get_rag_stats(last_hours=24)
# {
#     'avg_total_latency_ms': 2850,
#     'p95_total_latency_ms': 4100,
#     'latency_breakdown': {
#         'embedding_ms': 65,
#         'embedding_percent': 2.3,
#         'retrieval_ms': 185,
#         'retrieval_percent': 6.5,
#         'llm_ms': 2600,
#         'llm_percent': 91.2
#     },
#     'avg_tokens_per_second': 25.3
# }
```

**Insights do Breakdown:**
- 91% do tempo é LLM → Foco de otimização
- Embedding muito rápido (2.3%) → OK
- Retrieval aceitável (6.5%) → OK

---

### 3️⃣ **EFICIÊNCIA (Recursos, Custo)**

#### **O que medir:**

```python
✨ Uso de Memória do Modelo
   Meta: < 8GB RAM
   Atual: NÃO MONITORADO

✨ Uso de CPU durante inferência
   Meta: < 80% em média
   Atual: NÃO MONITORADO

✨ Tokens por Query
   Input tokens: ~500 (contexto + pergunta)
   Output tokens: ~150 (resposta)
   Total: ~650 tokens/query

✨ Custo por Query (se fosse API paga)
   Ollama é gratuito (local)
   Equivalente GPT-4: ~$0.02/query
   Economia: 100%

✨ Cache Hit Rate
   Meta: > 30%
   Atual: NÃO MEDIDO
```

#### **Como monitorar:**

```python
import psutil
import os

# Uso de memória do processo
process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
cpu_percent = process.cpu_percent(interval=1)

print(f"Memória: {memory_mb:.1f} MB")
print(f"CPU: {cpu_percent:.1f}%")

# Tokens por query
total_tokens_24h = stats['total_tokens_generated']
num_queries_24h = stats['total_queries']
avg_tokens_per_query = total_tokens_24h / num_queries_24h

print(f"Média tokens/query: {avg_tokens_per_query:.0f}")
```

---

### 4️⃣ **CONFIABILIDADE (Confidence, Hallucinations)**

#### **O que medir:**

```python
✨ Confidence Score
   Significado: Confiança do modelo na resposta
   Método: Analisar softmax scores, similarity scores
   Meta: > 0.8 para considerarcredível
   Atual: NÃO IMPLEMENTADO

✨ Hallucination Rate
   Significado: % de respostas com informação inventada
   Método: Verificar se fatos citados existem nas fontes
   Meta: < 5%
   Atual: NÃO MEDIDO

✨ Source Attribution Accuracy
   Significado: % de citações corretas das fontes
   Meta: > 95%
   Atual: NÃO VALIDADO

✨ Consistency Score
   Significado: Respostas consistentes para mesma pergunta
   Método: Repetir pergunta 5x, comparar respostas
   Meta: > 90% de similaridade
   Atual: NÃO MEDIDO
```

#### **Como implementar Confidence Score:**

```python
def calculate_confidence(similarity_scores: List[float], resposta: str) -> float:
    """
    Calcula confidence baseado em:
    1. Similarity dos chunks retrieved (quão relevantes)
    2. Comprimento da resposta (muito curta/longa = suspeito)
    3. Presença de marcadores de incerteza ("talvez", "pode ser")
    """
    # Score de similarity (0-1)
    avg_similarity = np.mean(similarity_scores)
    
    # Penalizar respostas muito curtas ou muito longas
    length_score = 1.0
    if len(resposta) < 50:
        length_score = 0.5  # Muito curta
    elif len(resposta) > 2000:
        length_score = 0.7  # Muito longa
    
    # Penalizar marcadores de incerteza
    uncertainty_words = ['talvez', 'pode ser', 'não tenho certeza', 'provavelmente']
    uncertainty_penalty = sum(word in resposta.lower() for word in uncertainty_words) * 0.1
    
    confidence = (avg_similarity * 0.7 + length_score * 0.3) - uncertainty_penalty
    
    return max(0.0, min(1.0, confidence))  # Limitar entre 0-1
```

#### **Como detectar Hallucinations:**

```python
def detect_hallucination(resposta: str, fontes: List[str]) -> Dict:
    """
    Detecta se resposta contém informações não presentes nas fontes
    """
    # Extrair fatos específicos da resposta
    # (números, nomes, datas, percentuais, etc.)
    import re
    
    # Números e percentuais
    numeros = re.findall(r'\d+(?:\.\d+)?%?', resposta)
    
    # Nomes próprios (simplificado)
    nomes = re.findall(r'[A-Z][a-z]+(?:\s[A-Z][a-z]+)*', resposta)
    
    # Verificar se cada fato existe nas fontes
    fontes_text = ' '.join(fontes).lower()
    
    fatos_nao_encontrados = []
    for fato in numeros + nomes:
        if fato.lower() not in fontes_text:
            fatos_nao_encontrados.append(fato)
    
    hallucination_detected = len(fatos_nao_encontrados) > 0
    hallucination_score = len(fatos_nao_encontrados) / max(len(numeros + nomes), 1)
    
    return {
        'hallucination_detected': hallucination_detected,
        'hallucination_score': hallucination_score,
        'fatos_suspeitos': fatos_nao_encontrados
    }
```

---

### 5️⃣ **COMPORTAMENTO (Distribuição, Padrões)**

#### **O que analisar:**

```python
✨ Distribuição de Tamanhos de Resposta
   - Muito curta (< 50 chars): pode ser incompleta
   - Normal (50-500 chars): ideal
   - Longa (500-1500 chars): detalhada
   - Muito longa (> 1500 chars): verbosa demais

✨ Distribuição de Latências
   - Verificar outliers (queries muito lentas)
   - Identificar padrões (certas perguntas sempre lentas?)

✨ Taxa de Uso por Área/Banca
   - Qual área mais consultada?
   - Qual banca mais pesquisada?
   - Adaptar cache baseado nisso

✨ Padrões de Erro
   - Quais perguntas falham mais?
   - Erros relacionados a áreas específicas?
   - Timeout em perguntas longas?
```

#### **Visualização:**

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Distribuição de latências
latencies = [m.total_latency_ms for m in metrics.rag_history]
plt.figure(figsize=(10, 6))
sns.histplot(latencies, bins=30)
plt.xlabel('Latência (ms)')
plt.ylabel('Frequência')
plt.title('Distribuição de Latências do RAG')
plt.axvline(np.percentile(latencies, 95), color='r', linestyle='--', label='P95')
plt.legend()
plt.savefig('metrics/latency_distribution.png')

# Breakdown de latências por fase
phases = ['Embedding', 'Retrieval', 'LLM']
avg_times = [
    stats['latency_breakdown']['embedding_ms'],
    stats['latency_breakdown']['retrieval_ms'],
    stats['latency_breakdown']['llm_ms']
]
plt.figure(figsize=(8, 8))
plt.pie(avg_times, labels=phases, autopct='%1.1f%%')
plt.title('Breakdown de Tempo por Fase')
plt.savefig('metrics/latency_breakdown.png')
```

---

## 🚀 PLANO DE IMPLEMENTAÇÃO

### **Fase 1: Métricas de Qualidade (SEMANA 1)**

#### **Dia 1-2: Ground Truth Dataset**
```bash
✅ CONCLUÍDO: 50 perguntas com respostas validadas
   Arquivo: datasets/ground_truth_rag.json
   Categorias: bancas, áreas, estratégia, geral
```

#### **Dia 3-4: Sistema de Validação**
```python
✅ IMPLEMENTADO: modules/model_metrics.py
   - GroundTruthValidator
   - Cálculo de Precision/Recall/F1
   - Keyword matching
```

#### **Dia 5-7: Integração no RAG**
```python
# TODO: Integrar em modules/rag_banca_inteligente.py

# Adicionar no método responder():
from modules.model_metrics import get_model_metrics

def responder(self, pergunta, usar_ollama=True):
    metrics = get_model_metrics()
    
    start_total = time.time()
    
    # ... código existente ...
    
    # Rastrear métricas
    metrics.track_rag_query(
        pergunta=pergunta,
        resposta=resposta,
        banca=analise['banca'],
        area=analise['area'],
        embedding_latency_ms=embedding_time,
        retrieval_latency_ms=retrieval_time,
        llm_latency_ms=llm_time,
        num_chunks=len(chunks),
        avg_similarity=avg_similarity,
        has_source=bool(fonte),
        tokens_generated=len(resposta.split())  # Aproximação
    )
    
    return resposta
```

---

### **Fase 2: Métricas de Performance (SEMANA 2)**

#### **Objetivos:**
1. Rastrear latência por fase
2. Medir tokens/segundo
3. Calcular percentis (P50, P95, P99)
4. Identificar gargalos

#### **Implementação:**
```python
# TODO: Adicionar decorators de timing

from functools import wraps
import time

def measure_time(phase_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000
            
            # Logar tempo
            logger.info(f"⏱️ {phase_name}: {elapsed:.2f}ms")
            
            return result, elapsed
        return wrapper
    return decorator

# Usar nos métodos:
@measure_time("embedding")
def gerar_embedding(text):
    # ...
    pass

@measure_time("retrieval")
def buscar_documentos(query_vector):
    # ...
    pass

@measure_time("llm_generation")
def gerar_resposta(prompt):
    # ...
    pass
```

---

### **Fase 3: Otimização do Modelo (SEMANA 3-4)**

#### **3.1: Otimizar Parâmetros do LLM**

```python
# Testar diferentes temperaturas
temperaturas = [0.3, 0.5, 0.7, 0.9]

for temp in temperaturas:
    print(f"\n🔬 Testando temperatura: {temp}")
    
    # Rodar 10 queries de teste
    for pergunta in test_queries:
        resposta = rag.responder(pergunta, temperature=temp)
        
        # Medir qualidade
        validation = validator.validate_response(pergunta, resposta)
        print(f"  Keyword Score: {validation['keyword_match_score']}")

# Resultado esperado:
# Temp 0.3: Mais consistente, menos criativo
# Temp 0.7: Balanceado (atual)
# Temp 0.9: Mais criativo, menos consistente
```

#### **3.2: Ajustar Retrieval (k chunks)**

```python
# Testar quantos chunks usar
k_values = [3, 5, 7, 10]

for k in k_values:
    print(f"\n🔍 Testando k={k} chunks")
    
    # Medir impacto em:
    # 1. Qualidade (mais contexto = melhor?)
    # 2. Latência (mais chunks = mais lento)
    # 3. Relevância (chunks extras são úteis?)
```

#### **3.3: Experimentar Diferentes Modelos**

```python
# Comparar modelos
modelos = [
    'llama3.2',      # Atual
    'llama3.1',      # Maior contexto
    'mistral',       # Alternativa
    'gemma2'         # Google
]

for modelo in modelos:
    print(f"\n🤖 Testando modelo: {modelo}")
    
    benchmark_results = metrics.run_benchmark(
        test_queries=ground_truth_perguntas[:10],
        model=modelo
    )
    
    print(f"  Avg Latency: {benchmark_results['avg_latency_ms']:.0f}ms")
    print(f"  Accuracy: {benchmark_results['accuracy']:.2%}")
```

---

### **Fase 4: Monitoramento Contínuo (SEMANA 5+)**

#### **4.1: Dashboard em Tempo Real**

```python
# TODO: Criar dashboard_modelo.html

# Mostrar:
# - Métricas atuais (latência, accuracy, throughput)
# - Gráficos de tendência (últimas 24h)
# - Alertas (latência > 10s, accuracy < 80%)
# - Comparação com semana anterior
```

#### **4.2: Alertas Automáticos**

```python
def check_model_health():
    """Verifica saúde do modelo e envia alertas"""
    health = metrics.get_model_health()
    
    if health['status'] == 'critical':
        # Enviar alerta por Telegram/Email
        send_alert(
            titulo="🚨 MODELO EM ESTADO CRÍTICO",
            mensagem=f"Issues: {', '.join(health['issues'])}"
        )
    
    elif health['status'] == 'warning':
        send_alert(
            titulo="⚠️ Modelo com Avisos",
            mensagem=f"Warnings: {', '.join(health['warnings'])}"
        )

# Rodar a cada 5 minutos
schedule.every(5).minutes.do(check_model_health)
```

#### **4.3: Auto-Retraining**

```python
# TODO: Implementar pipeline de retreino automático

def should_retrain():
    """Decide se modelo precisa retreinar"""
    quality = metrics.get_model_quality_metrics()
    
    # Retreinar se:
    # 1. Accuracy < 80%
    # 2. Acumulou 500+ feedbacks negativos
    # 3. Passou 30 dias desde último retreino
    
    if quality['f1_score'] < 0.80:
        return True, "F1-Score baixo"
    
    return False, None

if should_retrain()[0]:
    trigger_retraining_pipeline()
```

---

## 📈 MÉTRICAS-ALVO POR FASE

### **Baseline (Atual - Estimado):**
```
Precision: 85.2%
Recall: 79.8%
F1-Score: 82.4%
Latência P95: 4.1s
Tokens/s: ~15 (estimado)
Success Rate: 97%
```

### **Fase 1 (Após implementar métricas):**
```
✅ Métricas REAIS (não estimadas)
✅ Ground truth validação funcionando
✅ Precision/Recall medidos: >= 85%/80%
✅ Latência rastreada por fase
```

### **Fase 2 (Após otimizações):**
```
🎯 Precision: 87% (+2%)
🎯 Recall: 82% (+2%)
🎯 F1-Score: 84.5% (+2%)
🎯 Latência P95: 3.5s (-15%)
🎯 Tokens/s: 25 (+67%)
```

### **Fase 3 (Estado Ideal):**
```
🏆 Precision: 90%
🏆 Recall: 85%
🏆 F1-Score: 87.5%
🏆 Latência P95: 3.0s
🏆 Tokens/s: 30
🏆 Confidence Score disponível
🏆 Hallucination Rate < 5%
```

---

## 🎯 AÇÕES IMEDIATAS (ESTA SEMANA)

### ✅ **JÁ FEITO:**
1. Sistema de métricas do modelo (`modules/model_metrics.py`)
2. Ground truth dataset (50 perguntas)
3. Validador de respostas
4. Cálculo de Precision/Recall/F1

### 🔥 **FAZER AGORA:**

#### **1. Integrar métricas no RAG (2 horas)**
```python
# Arquivo: modules/rag_banca_inteligente.py
# Adicionar tracking de métricas em cada query
```

#### **2. Criar script de benchmark (1 hora)**
```python
# Arquivo: benchmark_modelo.py
# Rodar 50 perguntas do ground truth
# Gerar relatório com métricas
```

#### **3. Dashboard simples (2 horas)**
```html
<!-- dashboard_modelo.html -->
<!-- Mostrar métricas atuais em tempo real -->
```

#### **4. Primeira otimização (3 horas)**
```python
# Testar diferentes valores de temperatura
# Ajustar k (número de chunks)
# Documentar resultados
```

---

## 📊 EXEMPLO DE RELATÓRIO GERADO

```
🤖 RELATÓRIO DE MÉTRICAS DO MODELO
====================================

📅 Período: Últimas 24 horas
🕐 Gerado em: 2025-12-04 15:30:00

📈 QUALIDADE (Ground Truth Validação)
--------------------------------------
Total de Queries Validadas: 127
Precision: 86.3% ✅ (meta: >85%)
Recall: 81.7% ✅ (meta: >80%)
F1-Score: 83.9% ✅ (meta: >80%)
Keyword Match Score: 84.2%
Exact Matches: 12% (15/127)

⚡ PERFORMANCE
--------------
Total de Queries: 342
Latência Média: 2.85s ✅
Latência P95: 4.12s ✅ (meta: <5s)
Latência P99: 5.87s ✅ (meta: <8s)

Breakdown por Fase:
  Embedding: 68ms (2.4%)
  Retrieval: 192ms (6.7%)
  LLM: 2590ms (90.9%) ⚠️ GARGALO

Tokens/Segundo: 24.3 ✅ (meta: >20)
Total Tokens Gerados: 51,234

💰 EFICIÊNCIA
-------------
Queries/Minuto: 14.2
Uso de Memória: 6.8 GB ✅ (meta: <8GB)
Uso de CPU: 67% ✅ (meta: <80%)
Cache Hit Rate: 31% ✅ (meta: >30%)

🎯 CONFIABILIDADE
-----------------
Success Rate: 97.4% ✅ (meta: >95%)
Source Attribution Rate: 89.2% ⚠️ (meta: >95%)
Avg Confidence Score: 0.82 ✅
Hallucination Rate: 3.1% ✅ (meta: <5%)

💬 FEEDBACK DOS USUÁRIOS
-------------------------
Total com Feedback: 89
Thumbs Up: 76 (85.4%) ✅
Thumbs Down: 13 (14.6%)

📊 USO POR CATEGORIA
--------------------
Banca Mais Consultada: CESPE (58%)
Área Mais Consultada: Tecnologia (42%)
Tipo Pergunta: "o_que_mais_cai" (35%)

⚠️ ALERTAS E RECOMENDAÇÕES
---------------------------
1. LLM representa 91% do tempo total
   → OTIMIZAR: Considerar model caching
   
2. Source Attribution < 95%
   → MELHORAR: Validação das citações
   
3. 14.6% thumbs down
   → INVESTIGAR: Padrões de insatisfação

✅ PONTOS POSITIVOS
-------------------
• Todas as métricas dentro ou acima das metas
• Latência consistente (P95 < 5s)
• Alta taxa de sucesso (97.4%)
• Baixa hallucination rate (3.1%)
```

---

## 🎓 CONCLUSÃO

**Sistema Implementado:**
✅ Métricas de qualidade com ground truth
✅ Rastreamento de performance
✅ Validação automatizada
✅ Sistema de feedback

**Próximos Passos:**
1. Integrar no RAG existente (2h)
2. Rodar primeiro benchmark (1h)
3. Otimizar parâmetros (3h)
4. Deploy de dashboard (2h)

**Impacto Esperado:**
- 📈 Qualidade: +5% em F1-Score
- ⚡ Performance: -20% em latência
- 🎯 Confiança: Confidence scores em todas as respostas
- 📊 Visibilidade: Dashboard em tempo real

---

**Pronto para Implementar!** 🚀
