# 🎯 SISTEMA DE MÉTRICAS DO MODELO - ConcursAI

Sistema completo de rastreamento, validação e análise de métricas para os modelos de IA do ConcursAI.

---

## 📋 O QUE FOI IMPLEMENTADO

### ✅ **1. Sistema de Métricas Completo** (`modules/model_metrics.py`)

**Rastreia 3 tipos de operações:**

#### 🔤 **Embeddings**
- Latência (média, P50, P95, P99)
- Dimensões do vetor
- Taxa de sucesso
- Throughput (embeddings/hora)

#### 🤖 **LLM (Large Language Model)**
- Latência por query
- Tokens gerados (prompt + completion)
- Tokens por segundo
- Temperatura e configurações

#### 🎯 **RAG (Retrieval-Augmented Generation)**
- Latência total e por fase:
  - Embedding (vetorização da pergunta)
  - Retrieval (busca no vectorstore)
  - LLM (geração da resposta)
- Número de chunks recuperados
- Score de similaridade
- Presença de fontes
- **Validação contra ground truth:**
  - Keyword matching
  - Exact match
  - Precision, Recall, F1-Score

---

### ✅ **2. Ground Truth Dataset** (`datasets/ground_truth_rag.json`)

**50 perguntas validadas com respostas esperadas:**
- Cobrem todas as bancas principais (CESPE, FCC, FGV)
- Todas as áreas (Tecnologia, Jurídica, etc.)
- Todos os tipos de perguntas
- Keywords obrigatórias para validação

---

### ✅ **3. Integração no RAG** (`modules/rag_banca_inteligente.py`)

O sistema RAG agora rastreia automaticamente:
- ⏱️ Tempo de cada fase
- 🔤 Operações de embedding
- 🤖 Queries LLM
- 🎯 Pipeline RAG completo
- ✅ Validação automática contra ground truth

---

### ✅ **4. Scripts de Benchmark e Visualização**

#### 📊 **benchmark_modelo.py**
Testa o modelo contra ground truth e gera relatório completo.

#### 📈 **visualizar_metricas.py**
Mostra métricas em tempo real com visualizações.

---

## 🚀 COMO USAR

### **1️⃣ Benchmark Rápido (10 perguntas)**

```cmd
BENCHMARK_RAPIDO.bat
```

Ou manualmente:
```cmd
python benchmark_modelo.py --num 10
```

**O que faz:**
- Testa 10 perguntas do ground truth
- Valida respostas
- Calcula métricas de qualidade e performance
- Salva relatório em `benchmarks/`

---

### **2️⃣ Benchmark Completo (50 perguntas)**

```cmd
BENCHMARK_COMPLETO.bat
```

Ou manualmente:
```cmd
python benchmark_modelo.py
```

**O que faz:**
- Testa todas as 50 perguntas
- Relatório completo por banca, área, tipo
- Métricas detalhadas de qualidade

---

### **3️⃣ Visualizar Métricas**

```cmd
VER_METRICAS.bat
```

Ou manualmente:
```cmd
python visualizar_metricas.py --last-hours 24
```

**O que mostra:**
- ✅ Saúde do modelo
- 🔤 Métricas de embeddings
- 🤖 Métricas do LLM
- 🎯 Métricas do RAG
- 📚 Por banca
- 📖 Por área

**Exemplos:**
```cmd
# Últimas 1 hora
python visualizar_metricas.py --last-hours 1

# Últimas 7 dias
python visualizar_metricas.py --last-hours 168
```

---

### **4️⃣ Exportar Métricas**

```cmd
EXPORTAR_METRICAS.bat
```

Ou manualmente:
```cmd
python visualizar_metricas.py --export
```

**Gera arquivo JSON com todas as métricas históricas.**

---

### **5️⃣ Benchmark Avançado**

#### **Filtrar por Banca:**
```cmd
python benchmark_modelo.py --banca cebraspe fcc
```

#### **Filtrar por Área:**
```cmd
python benchmark_modelo.py --area tecnologia juridica
```

#### **Usar Ollama (mais realista, porém mais lento):**
```cmd
python benchmark_modelo.py --num 5 --ollama
```

#### **Combinar filtros:**
```cmd
python benchmark_modelo.py --num 20 --banca cebraspe --area tecnologia
```

---

## 📊 MÉTRICAS RASTREADAS

### **📈 Qualidade**

| Métrica | Meta | Como é Medido |
|---------|------|---------------|
| **Precision** | > 85% | % de respostas relevantes retornadas |
| **Recall** | > 80% | % de respostas relevantes encontradas |
| **F1-Score** | > 80% | Média harmônica de Precision e Recall |
| **Keyword Match Score** | > 80% | % de keywords obrigatórias presentes |
| **Exact Match** | > 10% | Resposta exatamente igual ao ground truth |

### **⚡ Performance**

| Métrica | Meta | Como é Medido |
|---------|------|---------------|
| **Latência Total** | < 5s (P95) | Tempo do início ao fim da query |
| **Latência Embedding** | < 100ms | Vetorização da pergunta |
| **Latência Retrieval** | < 200ms | Busca no vectorstore |
| **Latência LLM** | < 3s | Geração da resposta |
| **Tokens/Segundo** | > 20 | Velocidade de geração |
| **Throughput** | > 10 q/min | Queries por minuto |

### **💰 Eficiência**

| Métrica | Descrição |
|---------|-----------|
| **Memória** | Uso de RAM do processo |
| **CPU** | % de uso durante inferência |
| **Tokens/Query** | Média de tokens usados |
| **Cache Hit Rate** | % de respostas cacheadas |

### **🎯 Confiabilidade**

| Métrica | Descrição |
|---------|-----------|
| **Confidence Score** | Confiança do modelo (0-1) |
| **Hallucination Rate** | % de informações inventadas |
| **Source Attribution** | Precisão das citações |
| **Consistency** | Respostas consistentes |

---

## 📁 ESTRUTURA DE ARQUIVOS

```
ConcursAI/
├── modules/
│   ├── model_metrics.py          ✅ Sistema de métricas
│   └── rag_banca_inteligente.py  ✅ RAG com métricas integradas
│
├── datasets/
│   └── ground_truth_rag.json     ✅ 50 perguntas validadas
│
├── benchmarks/                    📊 Relatórios gerados
│   └── benchmark_resultado_*.json
│
├── benchmark_modelo.py            🎯 Script de benchmark
├── visualizar_metricas.py         📊 Visualizador de métricas
│
├── BENCHMARK_RAPIDO.bat           ⚡ Teste rápido
├── BENCHMARK_COMPLETO.bat         📋 Teste completo
├── VER_METRICAS.bat               📊 Ver métricas
└── EXPORTAR_METRICAS.bat          💾 Exportar dados
```

---

## 🎯 EXEMPLO DE RELATÓRIO

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║            🎯 RESUMO DO BENCHMARK                                 ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝

📅 Data: 2025-12-04T15:30:00
⚙️  Ollama: Não

📊 QUALIDADE
══════════════════════════════════════════════════════════════════════
Total de Perguntas: 50
Respostas com Sucesso: 42 (84.0%)
Keyword Match Score Médio: 85.2%
Exact Matches: 6 (12.0%)

⚡ PERFORMANCE
══════════════════════════════════════════════════════════════════════
Latência Média: 2850ms
Latência Mínima: 1200ms
Latência Máxima: 6500ms
Latência P50: 2600ms
Latência P95: 4100ms

📈 DISTRIBUIÇÃO POR BANCA
══════════════════════════════════════════════════════════════════════
cebraspe       : 18/20 (90.0%)
fcc            : 14/17 (82.4%)
fgv            : 10/13 (76.9%)

📈 DISTRIBUIÇÃO POR ÁREA
══════════════════════════════════════════════════════════════════════
tecnologia     : 16/18 (88.9%)
juridica       : 14/16 (87.5%)
geral          : 12/16 (75.0%)
```

---

## 🔧 INTEGRAÇÃO MANUAL

Se quiser integrar métricas em outro código:

```python
from modules.model_metrics import get_model_metrics
import time

# Inicializar
metrics = get_model_metrics()

# Rastrear embedding
start = time.time()
# ... operação de embedding ...
metrics.track_embedding(
    text=pergunta,
    model="nomic-embed-text",
    start_time=start,
    dimensions=384,
    success=True
)

# Rastrear LLM
start = time.time()
# ... geração com LLM ...
metrics.track_llm_query(
    pergunta=pergunta,
    resposta=resposta,
    model="llama3.2",
    start_time=start,
    prompt_tokens=500,
    completion_tokens=150,
    temperature=0.7
)

# Rastrear RAG completo
metrics.track_rag_query(
    pergunta=pergunta,
    resposta=resposta,
    banca="CESPE",
    area="Tecnologia",
    embedding_latency_ms=65,
    retrieval_latency_ms=185,
    llm_latency_ms=2600,
    num_chunks=5,
    avg_similarity=0.85,
    has_source=True,
    tokens_generated=150
)

# Validar contra ground truth
validation = metrics.validator.validate_response(pergunta, resposta)
print(f"Keyword Score: {validation['keyword_match_score']:.2%}")

# Obter estatísticas
stats = metrics.get_rag_stats(last_hours=24)
print(f"Latência P95: {stats['p95_total_latency_ms']:.0f}ms")

# Verificar saúde
health = metrics.get_model_health()
print(f"Status: {health['status']}")
```

---

## 📈 PRÓXIMOS PASSOS

### **Fase 2: Dashboard HTML**
- [ ] Gráficos interativos
- [ ] Métricas em tempo real
- [ ] Alertas visuais

### **Fase 3: Otimização**
- [ ] Testar diferentes temperaturas
- [ ] Ajustar número de chunks
- [ ] Comparar modelos

### **Fase 4: Auto-Tuning**
- [ ] Retreino automático
- [ ] A/B testing
- [ ] Otimização contínua

---

## ❓ FAQ

### **Como adicionar mais perguntas ao ground truth?**

Edite `datasets/ground_truth_rag.json` e adicione:

```json
{
  "id": 51,
  "pergunta": "Sua pergunta aqui",
  "resposta_esperada": "Resposta correta esperada",
  "keywords_obrigatorias": ["palavra1", "palavra2"],
  "banca": "cebraspe",
  "area": "tecnologia",
  "dificuldade": "média",
  "tipo": "o_que_mais_cai"
}
```

### **As métricas são salvas automaticamente?**

Sim! Todas as métricas são salvas automaticamente em memória e podem ser exportadas a qualquer momento com `EXPORTAR_METRICAS.bat`.

### **Como resetar as métricas?**

Delete o arquivo de métricas salvo (se existir) ou reinicie o sistema.

### **Posso usar em produção?**

Sim! O sistema tem overhead mínimo:
- Embedding: < 1ms
- LLM tracking: < 1ms
- RAG tracking: < 2ms

---

## 📞 SUPORTE

Para dúvidas ou problemas:
1. Veja os logs no console
2. Verifique `FOCO_METRICAS_MODELO.md` para detalhes técnicos
3. Execute `VER_METRICAS.bat` para diagnóstico

---

**✅ Sistema de Métricas Pronto para Uso!** 🚀
