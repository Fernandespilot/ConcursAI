# 📋 PLANO DE MELHORIAS - ConcursAI

## 🎯 Objetivo
Resolver problemas identificados e implementar novas funcionalidades para o sistema ConcursAI.

---

## ❌ PROBLEMAS IDENTIFICADOS

### 1. Chat com Erros ao Ler PDF
**Status:** 🔴 Crítico  
**Descrição:** Sistema apresenta erros ao responder perguntas sobre editais em PDF  
**Impacto:** Funcionalidade principal não está operacional  

**Causa Raiz:**
- Módulo `conversational_rag` pode não estar inicializado
- Chunking do PDF pode estar incorreto
- Contexto não está sendo passado corretamente para a IA
- Falta tratamento de erros específicos

### 2. Scraper Limitado a 1 Página
**Status:** 🟡 Médio  
**Descrição:** Scraper coletando apenas página 1, embora código suporte múltiplas páginas  
**Impacto:** Base de dados limitada  

**Causa Raiz:**
- Parâmetro `pages` pode não estar sendo respeitado
- Possível erro na navegação entre páginas
- Loop pode estar quebrando prematuramente

### 3. Falta Separação por Regiões
**Status:** 🟡 Médio  
**Descrição:** Não há organização geográfica dos concursos  
**Impacto:** Usuários não conseguem filtrar por região  

**Necessário:**
- Mapeamento de estados para regiões
- Filtros regionais no frontend
- Armazenamento estruturado por região

### 4. Falta Estudo de Bancas
**Status:** 🟢 Baixo (Nova Funcionalidade)  
**Descrição:** Sistema não analisa padrões de bancas organizadoras  
**Impacto:** Falta inteligência para preparação direcionada  

**Necessário:**
- Database de bancas conhecidas
- Análise de padrões por banca
- Estatísticas e recomendações

---

## 🚀 FASES DE IMPLEMENTAÇÃO

### **FASE 1: Corrigir Chat com PDF** ⏱️ 2-3 dias
#### Etapas:
1. **Criar Módulo de Análise de Edital Robusto**
   - [ ] Implementar `modules/edital_chat_rag.py`
   - [ ] Sistema de chunking inteligente (1000 tokens por chunk)
   - [ ] Embeddings com Sentence Transformers
   - [ ] Vector store com ChromaDB

2. **Melhorar Extração de Texto de PDF**
   - [ ] Usar PyMuPDF (fitz) para extração
   - [ ] Limpeza de texto (remover cabeçalhos, rodapés)
   - [ ] OCR opcional para PDFs escaneados

3. **Sistema de Q&A Contextual**
   - [ ] Retrieval dos chunks mais relevantes
   - [ ] Prompt engineering para respostas precisas
   - [ ] Integração com OpenAI/Groq/Ollama
   - [ ] Histórico de conversação

4. **Tratamento de Erros**
   - [ ] Validação de PDF
   - [ ] Fallback para quando não encontrar resposta
   - [ ] Logs detalhados

#### Arquivos a Criar:
- `modules/edital_chat_rag.py` - Sistema RAG específico para editais
- `modules/pdf_processor.py` - Processamento avançado de PDFs
- `tests/test_chat_edital.py` - Testes automatizados

#### Endpoints API:
- `POST /chat/upload-pdf` - Upload e processamento
- `POST /chat/pergunta` - Fazer pergunta sobre edital
- `GET /chat/historico/{session_id}` - Histórico da conversa
- `DELETE /chat/limpar/{session_id}` - Limpar sessão

---

### **FASE 2: Melhorar Scraper - 3 Páginas e Regiões** ⏱️ 1-2 dias
#### Etapas:
1. **Debugar Scraper de Páginas**
   - [ ] Adicionar logs detalhados de navegação
   - [ ] Verificar botão "Próxima página"
   - [ ] Testar com diferentes queries
   - [ ] Garantir coleta de 3 páginas

2. **Implementar Mapeamento Regional**
   - [ ] Criar `modules/regioes_brasil.py`
   - [ ] Dicionário Estado → Região
   - [ ] Validação de estados

3. **Adicionar Filtro Regional**
   - [ ] Campo `regiao` na database
   - [ ] Filtro no endpoint `/concursos/buscar`
   - [ ] UI com seletor de regiões

4. **Estatísticas por Região**
   - [ ] Dashboard com mapa do Brasil
   - [ ] Gráficos por região
   - [ ] Ranking de estados

#### Arquivos a Criar/Modificar:
- `modules/regioes_brasil.py` - Mapeamento de regiões
- `scrapers/pci_scraper.py` - Corrigir coleta de múltiplas páginas
- `concursos.html` - Adicionar filtro de região

#### Estrutura Regional:
```python
REGIOES = {
    'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
    'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
    'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
    'Sul': ['PR', 'RS', 'SC']
}
```

---

### **FASE 3: Sistema de Estudo de Bancas** ⏱️ 3-4 dias
#### Etapas:
1. **Criar Database de Bancas**
   - [ ] Tabela `bancas` com informações
   - [ ] Scraping de informações sobre bancas
   - [ ] Histórico de concursos por banca

2. **Análise de Padrões**
   - [ ] Identificar banca em cada concurso
   - [ ] Extrair estatísticas por banca
   - [ ] Machine Learning para análise de padrões

3. **Dashboard de Bancas**
   - [ ] Página `bancas.html`
   - [ ] Perfil de cada banca
   - [ ] Comparação entre bancas
   - [ ] Recomendações de estudo

4. **Inteligência de Preparação**
   - [ ] Disciplinas mais cobradas por banca
   - [ ] Nível de dificuldade
   - [ ] Temas recorrentes
   - [ ] Material de estudo recomendado

#### Arquivos a Criar:
- `modules/analise_bancas.py` - Sistema de análise
- `modules/database_bancas.py` - Database de bancas
- `scrapers/banca_scraper.py` - Coletor de informações de bancas
- `bancas.html` - Interface de análise de bancas
- `data/bancas_conhecidas.json` - Database inicial

#### Bancas Principais:
```json
{
  "bancas": [
    {
      "nome": "CESPE/CEBRASPE",
      "caracteristicas": "Questões longas, assertivas C/E, multidisciplinar",
      "dificuldade": "Alta",
      "areas_fortes": ["Direito", "Administração", "Tecnologia"],
      "concursos_recentes": 450
    },
    {
      "nome": "FCC",
      "caracteristicas": "Questões objetivas, foco em lei seca",
      "dificuldade": "Média-Alta",
      "areas_fortes": ["Direito", "Português", "Raciocínio"],
      "concursos_recentes": 380
    },
    {
      "nome": "FGV",
      "caracteristicas": "Questões interpretativas, contextualizadas",
      "dificuldade": "Alta",
      "areas_fortes": ["Todas as áreas"],
      "concursos_recentes": 320
    },
    {
      "nome": "VUNESP",
      "caracteristicas": "Questões diretas, cobranças específicas",
      "dificuldade": "Média",
      "areas_fortes": ["SP principalmente"],
      "concursos_recentes": 280
    }
  ]
}
```

#### Endpoints API para Bancas:
- `GET /bancas/listar` - Lista todas as bancas
- `GET /bancas/{nome}/perfil` - Perfil detalhado
- `GET /bancas/{nome}/concursos` - Concursos organizados
- `GET /bancas/{nome}/estatisticas` - Estatísticas da banca
- `GET /bancas/comparar?bancas=FCC,CESPE` - Comparação

---

## 📊 CRONOGRAMA

### Semana 1
- ✅ Identificação de problemas
- ✅ Planejamento completo
- 🔄 **Dia 1-2:** Fase 1 - Corrigir Chat PDF
- 🔄 **Dia 3-4:** Fase 1 - Testes e refinamento

### Semana 2
- 🔄 **Dia 5:** Fase 2 - Scraper múltiplas páginas
- 🔄 **Dia 6-7:** Fase 2 - Sistema de regiões

### Semana 3
- 🔄 **Dia 8-10:** Fase 3 - Database e análise de bancas
- 🔄 **Dia 11-12:** Fase 3 - Dashboard de bancas

### Semana 4
- 🔄 **Dia 13-14:** Integração e testes gerais
- 🔄 **Dia 15:** Documentação final

---

## 🎯 MÉTRICAS DE SUCESSO

### Chat com PDF
- ✅ Taxa de resposta correta > 90%
- ✅ Tempo de resposta < 3 segundos
- ✅ Zero erros críticos em 100 consultas

### Scraper
- ✅ Coleta consistente de 3 páginas
- ✅ Mínimo 90 concursos coletados por execução
- ✅ Taxa de erro < 5%

### Regiões
- ✅ 100% dos concursos com região identificada
- ✅ Filtro regional funcionando em todas as páginas
- ✅ Dashboard regional implementado

### Bancas
- ✅ Database com mínimo 20 bancas
- ✅ Análise de padrões para top 10 bancas
- ✅ Sistema de recomendações ativo

---

## 🛠️ TECNOLOGIAS

### Chat/RAG
- LangChain ou LlamaIndex
- ChromaDB (vector store)
- Sentence Transformers (embeddings)
- OpenAI GPT-4 ou Groq (LLM)
- PyMuPDF (PDF processing)

### Scraping
- BeautifulSoup4
- Requests
- Selenium (se necessário)

### Análise de Bancas
- Pandas (análise de dados)
- Scikit-learn (ML)
- Matplotlib/Plotly (visualização)

### Frontend
- Chart.js (gráficos)
- Leaflet (mapa do Brasil)

---

## 📝 PRÓXIMOS PASSOS IMEDIATOS

### Agora (Próximas 2 horas):
1. ✅ Criar este documento de planejamento
2. 🔄 Implementar `modules/edital_chat_rag.py`
3. 🔄 Criar `modules/pdf_processor.py`
4. 🔄 Testar chat com PDF de exemplo

### Hoje:
1. 🔄 Debugar scraper para 3 páginas
2. 🔄 Implementar mapeamento de regiões
3. 🔄 Adicionar filtro regional no frontend

### Amanhã:
1. 🔄 Iniciar database de bancas
2. 🔄 Criar scraper de informações de bancas
3. 🔄 Prototipar dashboard de bancas

---

## 🤝 SUPORTE E MANUTENÇÃO

### Logs e Monitoramento
- Todos os erros logados em `logs/errors.log`
- Métricas em `logs/metrics.log`
- Dashboard de monitoramento em tempo real

### Testes
- Testes unitários para cada módulo
- Testes de integração end-to-end
- Testes de carga para scraper

### Documentação
- README atualizado
- Docstrings em todas as funções
- Exemplos de uso
- Troubleshooting guide

---

## 💡 IDEIAS FUTURAS (Backlog)

1. **Sistema de Alerta Inteligente**
   - Notificações personalizadas por perfil
   - ML para recomendar concursos

2. **Geração Automática de Cronograma de Estudos**
   - Baseado no edital e tempo disponível
   - Priorização de disciplinas

3. **Análise de Provas Anteriores**
   - Scraping de questões
   - Banco de questões filtrado por banca
   - Simulados automáticos

4. **Comunidade**
   - Fórum de discussão
   - Compartilhamento de materiais
   - Ranking de desempenho

5. **App Mobile**
   - React Native ou Flutter
   - Notificações push
   - Modo offline

---

## 📞 CONTATO E FEEDBACK

Para dúvidas, sugestões ou reportar bugs:
- GitHub Issues
- Email: suporte@concursai.com
- Telegram: @concursai_bot

---

**Última Atualização:** 11/11/2025  
**Versão do Plano:** 1.0  
**Status Geral:** 🔄 Em Andamento

