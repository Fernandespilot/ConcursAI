# 🚀 GUIA RÁPIDO - SISTEMA DE MÉTRICAS DO MODELO

**3 minutos para começar!**

---

## ⚡ INÍCIO RÁPIDO

### **1. Teste se tudo está funcionando (30 segundos)**

```cmd
TESTAR_METRICAS.bat
```

**O que esperar:**
```
✅ Importações
✅ Ground Truth
✅ Sistema de Métricas
✅ Validação
✅ Integração RAG
```

---

### **2. Execute seu primeiro benchmark (2 minutos)**

```cmd
BENCHMARK_RAPIDO.bat
```

**O que vai acontecer:**
- Testa 10 perguntas do ground truth
- Valida respostas
- Calcula métricas de qualidade
- Mostra relatório na tela
- Salva em `benchmarks/benchmark_resultado_*.json`

**Resultado:**
```
📊 QUALIDADE
Total de Perguntas: 10
Respostas com Sucesso: 8 (80.0%)
Keyword Match Score Médio: 82.5%

⚡ PERFORMANCE
Latência Média: 2650ms
Latência P95: 3800ms
```

---

### **3. Veja as métricas (10 segundos)**

```cmd
VER_METRICAS.bat
```

**O que vai mostrar:**
- ✅ Saúde do modelo
- 🔤 Métricas de embeddings
- 🤖 Métricas do LLM
- 🎯 Métricas do RAG
- 📚 Por banca
- 📖 Por área

---

## 📊 COMANDOS PRINCIPAIS

| Comando | O que faz | Tempo |
|---------|-----------|-------|
| `TESTAR_METRICAS.bat` | Valida instalação | 30s |
| `BENCHMARK_RAPIDO.bat` | Testa 10 perguntas | 2min |
| `BENCHMARK_COMPLETO.bat` | Testa 50 perguntas | 8min |
| `VER_METRICAS.bat` | Mostra estatísticas | 10s |
| `EXPORTAR_METRICAS.bat` | Salva em JSON | 5s |

---

## 🎯 MÉTRICAS MAIS IMPORTANTES

### **Qualidade do Modelo:**
- **Keyword Match Score:** % de keywords corretas (meta: > 80%)
- **F1-Score:** Qualidade geral (meta: > 80%)
- **Taxa de Sucesso:** % de respostas boas (meta: > 85%)

### **Performance:**
- **Latência P95:** 95% das queries são mais rápidas que isso (meta: < 5s)
- **Tokens/Segundo:** Velocidade de geração (meta: > 20)

### **Breakdown (onde o tempo é gasto):**
- **Embedding:** ~2-5% (vetorização da pergunta)
- **Retrieval:** ~5-10% (busca no vectorstore)
- **LLM:** ~85-93% (geração da resposta) ← **Principal gargalo**

---

## 🔍 INTERPRETANDO RESULTADOS

### ✅ **Bom Resultado:**
```
Keyword Match Score: 85%+
Latência P95: < 5s
Taxa de Sucesso: 85%+
```
→ **Modelo está performando bem!**

### ⚠️ **Precisa Melhorar:**
```
Keyword Match Score: 60-80%
Latência P95: 5-8s
Taxa de Sucesso: 70-85%
```
→ **Considere otimizações (ver seção abaixo)**

### ❌ **Problema Sério:**
```
Keyword Match Score: < 60%
Latência P95: > 8s
Taxa de Sucesso: < 70%
```
→ **Revise configuração do modelo**

---

## ⚙️ OTIMIZAÇÕES RÁPIDAS

### **1. Reduzir Latência**

**Problema:** P95 > 5s

**Soluções:**
```python
# Em modules/rag_banca_inteligente.py

# Opção 1: Reduzir temperatura (mais rápido, menos criativo)
"temperature": 0.3  # Atual: 0.7

# Opção 2: Usar menos chunks
limite_contexto = 3  # Atual: 5

# Opção 3: Cache de respostas frequentes
# (já tem cache_contexto no código)
```

---

### **2. Melhorar Qualidade**

**Problema:** Keyword Match < 80%

**Soluções:**
```python
# Opção 1: Aumentar chunks (mais contexto)
limite_contexto = 7  # Atual: 5

# Opção 2: Ajustar temperatura (mais consistente)
"temperature": 0.5  # Atual: 0.7

# Opção 3: Adicionar mais perguntas ao ground truth
# Editar: datasets/ground_truth_rag.json
```

---

### **3. Aumentar Tokens/Segundo**

**Problema:** Tokens/s < 20

**Soluções:**
- Usar modelo menor (llama3.2 em vez de llama3.1)
- Aumentar quantização (Q4_K_M é atual, Q5_K_M seria melhor qualidade mas mais lento)
- Verificar se Ollama está com GPU habilitada

---

## 📈 ACOMPANHAMENTO CONTÍNUO

### **Diário:**
```cmd
VER_METRICAS.bat
```
- Verifica se tudo está OK
- Identifica problemas rapidamente

### **Semanal:**
```cmd
BENCHMARK_COMPLETO.bat
```
- Valida qualidade do modelo
- Compara com semana anterior
- Ajusta se necessário

### **Mensal:**
```cmd
python benchmark_modelo.py --export
```
- Análise profunda
- Tendências de longo prazo
- Planejamento de melhorias

---

## 🎨 VISUALIZAÇÃO DOS DADOS

### **Console (Rápido):**
```cmd
VER_METRICAS.bat
```

### **JSON (Análise Detalhada):**
```cmd
EXPORTAR_METRICAS.bat
# Abre: metricas_export_TIMESTAMP.json
```

### **Relatório de Benchmark:**
```cmd
BENCHMARK_COMPLETO.bat
# Abre: benchmarks/benchmark_resultado_TIMESTAMP.json
```

---

## 🆘 PROBLEMAS COMUNS

### **"Ground truth não encontrado"**
- Verifique se `datasets/ground_truth_rag.json` existe
- Execute `TESTAR_METRICAS.bat` para validar

### **"Ollama não está rodando"**
- Sistema funciona SEM Ollama (respostas simples)
- Para usar Ollama: inicie o serviço antes

### **"Nenhuma métrica registrada"**
- Execute algumas queries primeiro
- Use `BENCHMARK_RAPIDO.bat` para gerar dados

### **"Latência muito alta"**
- Normal na primeira execução (cold start)
- Execute 2-3 vezes para estabilizar
- Veja seção "Otimizações Rápidas"

---

## 📚 MAIS INFORMAÇÕES

- **Guia Completo:** `README_METRICAS_MODELO.md`
- **Documentação Técnica:** `FOCO_METRICAS_MODELO.md`
- **Resumo de Implementação:** `RESUMO_IMPLEMENTACAO.md`

---

## ✅ CHECKLIST INICIAL

- [ ] Executei `TESTAR_METRICAS.bat` (todos os testes passaram)
- [ ] Executei `BENCHMARK_RAPIDO.bat` (vi o relatório)
- [ ] Executei `VER_METRICAS.bat` (vi as estatísticas)
- [ ] Entendi as métricas principais (Keyword Match, Latência P95)
- [ ] Sei como otimizar se necessário

---

**🎉 Pronto! Você agora tem controle total sobre a qualidade do seu modelo!**

**Próximo passo:**
```cmd
BENCHMARK_COMPLETO.bat
```

Depois, analise os resultados e veja se precisa de otimizações! 🚀
