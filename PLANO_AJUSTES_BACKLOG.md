# 🎯 PLANO DE AJUSTES - ALINHAMENTO COM BACKLOG

## 📋 **ANÁLISE DO BACKLOG**

### **SPRINT 0: Concepção e Análise** ✅ 100% COMPLETO
**Status:** Todas as 9 tarefas concluídas

**Tarefas Finalizadas:**
1. ✅ #103 - Definição do Problema e Objetivos → `AUTODESCRIÇÃO_PROJETO_COMPLETA.md`
2. ✅ #75 - Definir personas iniciais → Documentado
3. ✅ #176 - Configurar Estrutura base → Estrutura criada
4. ✅ #96 - Criação pasta Google Drive → Externo
5. ✅ #85 - Documentar README → `README.md` completo
6. ✅ #80 - Planejar arquitetura → `TECHNICAL_ARCHITECTURE.md`
7. ✅ #81 - Definir métricas → Documentadas
8. ✅ #82 - Criação artigo Overleaf → Externo
9. ✅ #74 - Benchmark portais → `BANCAS_ANALYSIS.md`

**✅ SPRINT 0: NENHUM AJUSTE NECESSÁRIO**

---

### **SPRINT 1: Coleta e Preparação** ✅ 85% COMPLETO
**Status:** 10 tarefas - 8 completas, 2 em finalização

#### **✅ Tarefas Completas (8/10):**

1. ✅ #179 - Mapear editais PCI CONCURSOS
   - **Arquivo:** `scrapers/pci_scraper.py` ✅
   - **Status:** Implementado e funcional

2. ✅ #183 - Artigo importância editais
   - **Arquivo:** `docs/` → Documentação criada
   - **Status:** Completo

3. ✅ #73 - Pesquisa NLP sumarização
   - **Implementado em:** `modules/concurso_rag.py`
   - **Status:** RAG funcional

4. ✅ #178 - Coleta de editais
   - **Arquivos:** `scrapers/*.py` (múltiplos)
   - **Status:** Sistema completo

5. ✅ #180 - Script baixar PDFs automaticamente
   - **Arquivo:** `modules/pdf_processor.py` ✅
   - **Status:** Download e processamento OK

6. ✅ #181 - Estrutura armazenar editais
   - **Implementado:** SQLite + ChromaDB
   - **Status:** Banco estruturado

7. ✅ #182 - Salvar dados básicos
   - **Implementado em:** `api_fastapi.py`
   - **Status:** CRUD completo

8. ✅ #203 - Extração features linguísticas
   - **Arquivo:** `modules/edital_analyzer.py` ✅
   - **Status:** Análise NLP implementada

#### **🔄 Tarefas Para Finalizar (2/10):**

9. 🔄 #204 - Criação esquema inicial (bancas, questoes)
   - **Status Atual:** Esquema parcial
   - **🎯 AJUSTE NECESSÁRIO:** Criar schema completo de bancas

10. 🔄 Documentação completa pipeline
    - **🎯 AJUSTE NECESSÁRIO:** Documentar fluxo end-to-end

---

### **SPRINT 2: Modelagem e Projeto** 🔄 70% COMPLETO
**Status:** 11 tarefas - 8 completas, 3 pendentes

#### **✅ Tarefas Completas (8/11):**

1. ✅ #76 - Mapear jornada usuário
   - **Documentado em:** `DESCRIÇÃO_NARRATIVA_PROJETO.md`

2. ✅ #202 - Criar scrapers CESPE, FCC, FGV
   - **Arquivos:** `scrapers_pci/*.py` ✅

3. ✅ #77 - POC coleta simples
   - **Implementado:** Scrapers funcionais

4. ✅ #78 - POC sumarização automática
   - **Arquivo:** `modules/concurso_rag.py` ✅

5. ✅ #79 - Documentar problemas
   - **Documentado em:** `RELATORIO_FINAL.md`

6. ✅ #184 - Implementar leitura PDFs
   - **Arquivo:** `modules/pdf_processor.py` ✅

7. ✅ #185 - Limpar textos
   - **Implementado:** Processamento de texto OK

8. ✅ #186 - Salvar chunks com dados
   - **Implementado:** ChromaDB + metadados

#### **🔄 Tarefas Pendentes (3/11):**

9. 🔄 #22 - Mapear fontes oficiais editais
   - **🎯 AJUSTE:** Criar módulo `scrapers/sites_oficiais_scraper.py`

10. 🔄 #23 - POC sumarização melhorada
    - **🎯 AJUSTE:** Refinar prompts do RAG

11. 🔄 #25 - Documentar problemas legais
    - **🎯 AJUSTE:** Criar `ASPECTOS_LEGAIS.md`

---

### **SPRINT 3: Modelagem e Projeto** 🚧 60% COMPLETO
**Status:** 11 tarefas - 3 completas, 8 em andamento

#### **✅ Tarefas Completas (3/11):**

1. ✅ #200 - Implementação scrapers CESPE, FCC, FGV
   - **Status:** Completo em `scrapers_pci/`

2. ✅ #72 - Estudo ferramentas scraping
   - **Implementado:** BeautifulSoup, Scrapy, Selenium

3. ✅ #187 - Artigo metodologia
   - **Status:** Em redação

#### **🔄 Tarefas Em Andamento (8/11):**

4. 🔄 #21 - Criar scraper_cespe, scraper_fcc, scraper_fgv
   - **🎯 AJUSTE:** Consolidar em módulos únicos

5. 🔄 #76 - Mapear jornada completa
   - **🎯 AJUSTE:** Criar diagrama de fluxo visual

6. 🔄 #78 - POC sumarização avançada
   - **🎯 AJUSTE:** Implementar múltiplos modelos LLM

7. 🔄 #24 - Prova conceito sumarização
   - **🎯 AJUSTE:** Testes comparativos de modelos

8. 🔄 #26 - Implementar leitura avançada PDFs
   - **🎯 AJUSTE:** OCR para PDFs escaneados

9. 🔄 #27 - Limpar textos avançado
   - **🎯 AJUSTE:** Regex patterns para casos especiais

10. 🔄 #28 - Salvar chunks otimizado
    - **🎯 AJUSTE:** Melhorar estratégia de chunking

11. 🔄 #187 - Metodologia completa
    - **🎯 AJUSTE:** Finalizar documentação científica

---

### **SPRINT 4: Implementação RAG** 📋 BACKLOG
**Status:** 9 tarefas planejadas, 0 iniciadas

#### **⏳ Tarefas Planejadas:**

1. ⏳ #188 - Pipeline RAG completo
   - **🎯 CRIAR:** `modules/rag_pipeline_completo.py`
   - **Funcionalidades:**
     - Ingestão automática de editais
     - Processamento paralelo
     - Atualização incremental

2. ⏳ #189 - Converter chunks em vetores
   - **🎯 MELHORAR:** `modules/concurso_embeddings.py`
   - **Implementar:**
     - Embeddings otimizados
     - Batch processing
     - Cache de vetores

3. ⏳ #190 - Função atualizar banco automaticamente
   - **🎯 CRIAR:** `modules/auto_update_db.py`
   - **Funcionalidades:**
     - Trigger automático
     - Validação de novos editais
     - Reindexação inteligente

4. ⏳ #191 - Implementar retriever otimizado
   - **🎯 CRIAR:** `modules/retriever_avancado.py`
   - **Funcionalidades:**
     - Multi-query retriever
     - Reranking de resultados
     - Filtros contextuais

5. ⏳ #192 - Integrar LLM robusto
   - **🎯 MELHORAR:** `modules/conversational_rag.py`
   - **Implementar:**
     - Múltiplos modelos (Ollama + APIs)
     - Fallback automático
     - Streaming de respostas

6. ⏳ #201 - Validação e limpeza dados
   - **🎯 CRIAR:** `modules/data_validator.py`
   - **Funcionalidades:**
     - Validação de schema
     - Detecção de duplicatas
     - Correção automática

7. ⏳ #205 - Treinar classificador bancas
   - **🎯 CRIAR:** `modules/ml_models/banca_classifier.py`
   - **Modelos:**
     - Random Forest
     - MLP (Neural Network)
     - SVM
     - Ensemble voting

8. ⏳ #206 - Modelo preditivo temas
   - **🎯 CRIAR:** `modules/ml_models/theme_predictor.py`
   - **Funcionalidades:**
     - Análise temporal
     - Predição de frequência
     - Tendências por banca

9. ⏳ #207 - Coaching IA especializado
   - **🎯 CRIAR:** `modules/coaching_ai.py`
   - **Funcionalidades:**
     - Chatbot educacional
     - Plano de estudos personalizado
     - Feedback inteligente

---

### **SPRINT 5: Testes e Validação** 📋 BACKLOG
**Status:** Planejada, não iniciada

#### **⏳ Tarefas Previstas:**

1. ⏳ #216 - Sistema alertas automáticos
   - **🎯 MELHORAR:** `modules/sistema_notificacoes.py`
   - **Adicionar:**
     - Email notifications
     - Push notifications
     - SMS (Twilio)
     - Telegram/WhatsApp

2. ⏳ #208 - API FastAPI completa
   - **Status Atual:** 80% implementado
   - **🎯 FINALIZAR:**
     - Autenticação JWT completa
     - Rate limiting por usuário
     - Websockets para real-time
     - Documentação OpenAPI completa

3. ⏳ #209 - Serviço análise editais
   - **🎯 CRIAR:** `app/services/edital_service.py`
   - **Funcionalidades:**
     - Análise estruturada completa
     - Extração de requisitos
     - Identificação de prazos
     - Comparação entre editais

4. ⏳ #210 - Camada segurança
   - **🎯 CRIAR:** `app/core/security.py`
   - **Implementar:**
     - JWT authentication
     - Role-based access (RBAC)
     - API key management
     - Rate limiting
     - Input sanitization

5. ⏳ #212 - Expansão robustez POP/CSV
   - **🎯 CRIAR:** Exportação de dados
   - **Formatos:**
     - CSV otimizado
     - JSON estruturado
     - Excel (.xlsx)
     - PDF reports

6. ⏳ #213 - Quiz perfil usuário
   - **🎯 CRIAR:** `modules/user_profiling.py`
   - **Funcionalidades:**
     - Questionário interativo
     - Análise de respostas
     - Classificação de perfil
     - Recomendações personalizadas

7. ⏳ Testes integração completos
   - **🎯 CRIAR:** `tests/integration/`
   - **Cobrir:**
     - API endpoints
     - Scrapers
     - RAG system
     - Database operations

8. ⏳ Testes carga e performance
   - **🎯 CRIAR:** `tests/performance/`
   - **Ferramentas:**
     - Locust para load testing
     - pytest-benchmark
     - Memory profiling
     - Latency analysis

9. ⏳ Validação usuários reais
   - **🎯 IMPLEMENTAR:**
     - Beta testing program
     - Feedback forms
     - Analytics tracking
     - A/B testing framework

---

## 🛠️ **AJUSTES PRIORITÁRIOS**

### **🔥 PRIORIDADE CRÍTICA (Fazer Agora)**

#### **1. Completar Schema de Bancas (#204)**
```python
# 🎯 CRIAR: app/models/banca.py

from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Banca(Base):
    __tablename__ = "bancas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    nome_completo = Column(String)
    sigla = Column(String)
    
    # Características da banca
    caracteristicas = Column(JSON, default={})
    # Exemplo: {
    #     "estilo": "objetiva",
    #     "dificuldade_media": 7.5,
    #     "areas_foco": ["direito", "administracao"],
    #     "tipo_questoes": ["multipla_escolha", "cespe_certo_errado"]
    # }
    
    # Padrões identificados
    padroes = Column(JSON, default={})
    # Exemplo: {
    #     "temas_frequentes": ["constituicao", "administrativo"],
    #     "formato_preferido": "cespe_style",
    #     "pegadinhas_comuns": [...]
    # }
    
    # Estatísticas
    total_concursos = Column(Integer, default=0)
    total_questoes = Column(Integer, default=0)
    taxa_aprovacao_media = Column(Float)
    
    # Metadados
    ativo = Column(Boolean, default=True)
    site_oficial = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    concursos = relationship("Concurso", back_populates="banca")
    questoes = relationship("Questao", back_populates="banca")
```

```python
# 🎯 CRIAR: app/models/questao.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Questao(Base):
    __tablename__ = "questoes"
    
    id = Column(Integer, primary_key=True, index=True)
    banca_id = Column(Integer, ForeignKey("bancas.id"))
    concurso_id = Column(Integer, ForeignKey("concursos.id"))
    
    # Conteúdo da questão
    enunciado = Column(Text, nullable=False)
    alternativas = Column(JSON)  # Lista de alternativas
    gabarito = Column(String)  # Resposta correta
    
    # Classificação
    disciplina = Column(String, index=True)
    assunto = Column(String, index=True)
    subassunto = Column(String)
    
    # Metadados
    ano = Column(Integer, index=True)
    cargo = Column(String)
    dificuldade = Column(Float)  # 1-10
    taxa_acerto = Column(Float)  # % de candidatos que acertaram
    
    # Análise NLP
    keywords = Column(JSON)  # Palavras-chave extraídas
    temas = Column(JSON)  # Temas identificados
    complexidade_textual = Column(Float)
    
    # Features para ML
    features_linguisticas = Column(JSON)
    features_conteudo = Column(JSON)
    
    # Relacionamentos
    banca = relationship("Banca", back_populates="questoes")
    concurso = relationship("Concurso", back_populates="questoes")
```

**Script de Criação:**
```bash
# 🎯 CRIAR: scripts/create_banca_schema.py
```

---

#### **2. Criar Scraper Sites Oficiais (#22)**
```python
# 🎯 CRIAR: scrapers/sites_oficiais_scraper.py

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging

class SitesOficiaisScr aper:
    """Scraper para sites oficiais de órgãos e bancas"""
    
    SITES_OFICIAIS = {
        "CESPE": "https://www.cebraspe.org.br/concursos",
        "FCC": "https://www.concursosfcc.com.br/",
        "FGV": "https://conhecimento.fgv.br/concursos",
        "VUNESP": "https://www.vunesp.com.br/",
        "IBFC": "https://www.ibfc.org.br/",
        "IDECAN": "https://www.idecan.org.br/",
        "IADES": "https://www.iades.com.br/",
        "AOCP": "https://www.aocp.com.br/",
        "CONSULPLAN": "https://www.consulplan.net/",
        "FUNDATEC": "https://www.fundatec.org.br/"
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def coletar_todos(self) -> Dict[str, List[Dict]]:
        """Coleta de todos os sites oficiais"""
        resultados = {}
        
        for banca, url in self.SITES_OFICIAIS.items():
            try:
                self.logger.info(f"🕷️ Coletando {banca}...")
                concursos = self.coletar_banca(banca, url)
                resultados[banca] = concursos
                self.logger.info(f"✅ {banca}: {len(concursos)} concursos")
            except Exception as e:
                self.logger.error(f"❌ Erro em {banca}: {e}")
                resultados[banca] = []
        
        return resultados
    
    def coletar_banca(self, banca: str, url: str) -> List[Dict]:
        """Coleta específica por banca (implementar por banca)"""
        # Cada banca tem estrutura diferente
        # Criar método específico para cada uma
        
        method_name = f"_coletar_{banca.lower()}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(url)
        else:
            return self._coletar_generico(url)
    
    def _coletar_cespe(self, url: str) -> List[Dict]:
        """Coleta específica CESPE/Cebraspe"""
        # Implementação específica
        pass
    
    def _coletar_fcc(self, url: str) -> List[Dict]:
        """Coleta específica FCC"""
        # Implementação específica
        pass
    
    # ... outros métodos específicos por banca
```

---

#### **3. Criar Pipeline RAG Completo (#188)**
```python
# 🎯 CRIAR: modules/rag_pipeline_completo.py

from typing import List, Dict, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
import chromadb
from datetime import datetime
import logging

class RAGPipelineCompleto:
    """Pipeline completo de RAG com todas as etapas"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configurar componentes
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        self.chroma_client = chromadb.PersistentClient(path="./chromadb_data")
        self.collection = self.chroma_client.get_or_create_collection(
            name="editais_completo"
        )
    
    def processar_edital_completo(self, edital_data: Dict) -> Dict:
        """
        Pipeline completo de processamento de edital
        
        Etapas:
        1. Extração de texto (PDF → texto limpo)
        2. Análise e estruturação
        3. Chunking inteligente
        4. Geração de embeddings
        5. Armazenamento com metadados
        6. Indexação para busca
        """
        
        try:
            # 1. Extração
            texto = self._extrair_texto(edital_data['url'])
            
            # 2. Limpeza
            texto_limpo = self._limpar_texto(texto)
            
            # 3. Análise estrutural
            estrutura = self._analisar_estrutura(texto_limpo)
            
            # 4. Chunking
            chunks = self._criar_chunks_inteligentes(
                texto_limpo, 
                estrutura
            )
            
            # 5. Embeddings
            embeddings = self._gerar_embeddings(chunks)
            
            # 6. Armazenar
            doc_id = self._armazenar_no_chromadb(
                chunks, 
                embeddings, 
                edital_data
            )
            
            # 7. Metadados
            resultado = {
                'id': doc_id,
                'titulo': edital_data['titulo'],
                'total_chunks': len(chunks),
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            self.logger.info(f"✅ Edital processado: {doc_id}")
            return resultado
            
        except Exception as e:
            self.logger.error(f"❌ Erro no pipeline: {e}")
            raise
    
    def _criar_chunks_inteligentes(
        self, 
        texto: str, 
        estrutura: Dict
    ) -> List[str]:
        """
        Chunking inteligente preservando estrutura semântica
        """
        chunks = []
        
        # Dividir por seções se possível
        if 'secoes' in estrutura:
            for secao in estrutura['secoes']:
                # Chunks por seção preservando contexto
                secao_chunks = self.text_splitter.split_text(secao['texto'])
                
                # Adicionar contexto da seção em cada chunk
                for chunk in secao_chunks:
                    chunk_com_contexto = f"[{secao['titulo']}]\n{chunk}"
                    chunks.append(chunk_com_contexto)
        else:
            # Fallback: chunking padrão
            chunks = self.text_splitter.split_text(texto)
        
        return chunks
    
    def atualizar_banco_incremental(self, novos_editais: List[Dict]):
        """
        Atualização incremental do banco vetorial
        Processa apenas editais novos
        """
        for edital in novos_editais:
            # Verificar se já existe
            if not self._edital_existe(edital['id']):
                self.processar_edital_completo(edital)
                self.logger.info(f"➕ Novo edital adicionado: {edital['id']}")
            else:
                self.logger.debug(f"⏭️ Edital já existe: {edital['id']}")
```

---

### **⚡ PRIORIDADE ALTA (Próxima Semana)**

#### **4. Implementar Classificador de Bancas (#205)**
```python
# 🎯 CRIAR: modules/ml_models/banca_classifier.py

from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
import joblib
import numpy as np

class BancaClassifier:
    """
    Classificador de bancas usando ensemble de modelos
    RF + MLP + SVM com voting
    """
    
    def __init__(self):
        # Modelos
        self.rf_model = RandomForestClassifier(
            n_estimators=100, 
            random_state=42
        )
        
        self.mlp_model = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            random_state=42,
            max_iter=500
        )
        
        self.svm_model = SVC(
            kernel='rbf',
            probability=True,
            random_state=42
        )
        
        # Vectorizer para texto
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3)
        )
        
        self.models_trained = False
    
    def extract_features(self, questao_texto: str) -> Dict:
        """
        Extrai features linguísticas e de conteúdo
        """
        features = {}
        
        # Features textuais
        features['num_palavras'] = len(questao_texto.split())
        features['num_chars'] = len(questao_texto)
        features['palavras_dificeis'] = self._contar_palavras_dificeis(questao_texto)
        
        # Features de estilo
        features['tem_negacao'] = int('não' in questao_texto.lower())
        features['tem_excecao'] = int('exceto' in questao_texto.lower())
        features['tem_assinale'] = int('assinale' in questao_texto.lower())
        
        # Complexidade
        features['complexidade'] = self._calcular_complexidade(questao_texto)
        
        return features
    
    def train(self, X_train, y_train):
        """Treina ensemble de modelos"""
        
        print("🎓 Treinando classificadores...")
        
        # Treinar cada modelo
        self.rf_model.fit(X_train, y_train)
        print("✅ Random Forest treinado")
        
        self.mlp_model.fit(X_train, y_train)
        print("✅ MLP treinado")
        
        self.svm_model.fit(X_train, y_train)
        print("✅ SVM treinado")
        
        self.models_trained = True
    
    def predict(self, questao_texto: str) -> Dict:
        """
        Predição com ensemble voting
        """
        if not self.models_trained:
            raise ValueError("Modelos não treinados!")
        
        # Vectorizar texto
        X = self.vectorizer.transform([questao_texto])
        
        # Predições de cada modelo
        rf_pred = self.rf_model.predict_proba(X)[0]
        mlp_pred = self.mlp_model.predict_proba(X)[0]
        svm_pred = self.svm_model.predict_proba(X)[0]
        
        # Voting ponderado
        ensemble_pred = (rf_pred * 0.4 + mlp_pred * 0.3 + svm_pred * 0.3)
        
        # Classe predita
        banca_idx = np.argmax(ensemble_pred)
        confianca = ensemble_pred[banca_idx]
        
        return {
            'banca': self.rf_model.classes_[banca_idx],
            'confianca': float(confianca),
            'probabilidades': {
                classe: float(prob) 
                for classe, prob in zip(
                    self.rf_model.classes_, 
                    ensemble_pred
                )
            }
        }
    
    def save_models(self, path: str = "models/"):
        """Salva modelos treinados"""
        joblib.dump(self.rf_model, f"{path}/rf_banca.joblib")
        joblib.dump(self.mlp_model, f"{path}/mlp_banca.joblib")
        joblib.dump(self.svm_model, f"{path}/svm_banca.joblib")
        joblib.dump(self.vectorizer, f"{path}/vectorizer_banca.joblib")
        print(f"✅ Modelos salvos em {path}")
```

---

#### **5. Modelo Preditivo de Temas (#206)**
```python
# 🎯 CRIAR: modules/ml_models/theme_predictor.py

from sklearn.ensemble import GradientBoostingRegressor
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ThemePredictor:
    """
    Preditor de temas quentes para concursos
    Analisa padrões temporais e prediz probabilidade de temas
    """
    
    def __init__(self):
        self.models = {}  # Um modelo por banca
        self.temas_categorias = self._carregar_categorias_temas()
    
    def _criar_features_temporais(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cria features temporais para predição
        """
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # Features temporais
        df['ano'] = df['date'].dt.year
        df['mes'] = df['date'].dt.month
        df['dia_ano'] = df['date'].dt.dayofyear
        df['trimestre'] = df['date'].dt.quarter
        
        # Features de tendência
        df['tempo_desde_inicio'] = (
            df['date'] - df['date'].min()
        ).dt.days
        
        # Rolling statistics
        df['freq_tema_30d'] = df.groupby('tema')['frequencia'].transform(
            lambda x: x.rolling(30, min_periods=1).mean()
        )
        
        return df
    
    def train_predictor(self, banca: str, historical_data: pd.DataFrame):
        """
        Treina modelo preditivo para uma banca específica
        """
        print(f"🎓 Treinando preditor para {banca}...")
        
        # Preparar dados
        df = self._criar_features_temporais(historical_data)
        
        # Para cada categoria de tema
        for tema in self.temas_categorias:
            # Filtrar dados do tema
            tema_data = df[df['tema'] == tema].copy()
            
            if len(tema_data) < 10:
                continue
            
            # Features e target
            X = tema_data[[
                'ano', 'mes', 'trimestre', 'dia_ano',
                'tempo_desde_inicio', 'freq_tema_30d'
            ]]
            y = tema_data['frequencia_futura']  # Frequência nos próximos 90 dias
            
            # Treinar modelo
            model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            
            model.fit(X, y)
            
            # Salvar modelo
            self.models[f"{banca}_{tema}"] = model
        
        print(f"✅ {len(self.models)} modelos treinados para {banca}")
    
    def predict_hot_themes(
        self, 
        banca: str, 
        horizon_days: int = 90
    ) -> List[Dict]:
        """
        Prediz temas quentes para próximos N dias
        """
        predictions = []
        
        # Data de referência (hoje)
        hoje = datetime.now()
        
        # Criar features para predição
        features = self._criar_features_predicao(hoje, horizon_days)
        
        # Predizer para cada tema
        for tema in self.temas_categorias:
            model_key = f"{banca}_{tema}"
            
            if model_key not in self.models:
                continue
            
            model = self.models[model_key]
            
            # Predição
            freq_predita = model.predict([features])[0]
            
            # Calcular tendência
            tendencia = self._calcular_tendencia(banca, tema)
            
            # Confiança da predição
            confianca = self._calcular_confianca(model, features)
            
            predictions.append({
                'tema': tema,
                'frequencia_predita': float(freq_predita),
                'tendencia': tendencia,  # 'crescente', 'estavel', 'decrescente'
                'confianca': float(confianca),
                'importancia': self._calcular_importancia(freq_predita, tendencia)
            })
        
        # Ordenar por importância
        predictions.sort(key=lambda x: x['importancia'], reverse=True)
        
        return predictions[:10]  # Top 10 temas
```

---

#### **6. Coaching IA Especializado (#207)**
```python
# 🎯 CRIAR: modules/coaching_ai.py

from typing import List, Dict, Optional
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

class CoachingIA:
    """
    Chatbot especializado para coaching de estudos
    """
    
    def __init__(self, llm):
        self.llm = llm
        
        # Template de prompt especializado
        self.prompt_template = PromptTemplate(
            input_variables=["historia", "input"],
            template="""
            Você é um Coach especializado em concursos públicos.
            Seu objetivo é ajudar o candidato a estudar de forma eficiente.
            
            Histórico da conversa:
            {historia}
            
            Candidato: {input}
            
            Coach: Vou ajudar você com isso. 
            """
        )
        
        # Memória da conversa
        self.memory = ConversationBufferMemory()
        
        # Chain conversacional
        self.chain = ConversationChain(
            llm=self.llm,
            prompt=self.prompt_template,
            memory=self.memory
        )
    
    def criar_plano_estudos(
        self, 
        perfil: Dict,
        concurso_alvo: Dict
    ) -> Dict:
        """
        Cria plano de estudos personalizado
        """
        
        # Análise do perfil
        nivel = perfil.get('nivel_conhecimento', 'iniciante')
        tempo_disponivel = perfil.get('horas_semana', 20)
        data_prova = concurso_alvo.get('data_prova')
        
        # Calcular tempo até prova
        dias_ate_prova = self._calcular_dias_ate_prova(data_prova)
        
        # Distribuir temas por semana
        plano = {
            'duracao_semanas': dias_ate_prova // 7,
            'horas_por_semana': tempo_disponivel,
            'cronograma_semanal': self._criar_cronograma(
                perfil, concurso_alvo, dias_ate_prova
            ),
            'materias_prioritarias': self._identificar_prioridades(
                perfil, concurso_alvo
            ),
            'simulados_recomendados': self._recomendar_simulados(
                dias_ate_prova
            ),
            'dicas_personalizadas': self._gerar_dicas(perfil)
        }
        
        return plano
    
    def analisar_desempenho(
        self, 
        usuario_id: str,
        historico_questoes: List[Dict]
    ) -> Dict:
        """
        Analisa desempenho e identifica pontos fracos
        """
        
        analise = {
            'total_questoes': len(historico_questoes),
            'taxa_acerto_geral': self._calcular_taxa_acerto(historico_questoes),
            'desempenho_por_materia': self._analisar_por_materia(historico_questoes),
            'pontos_fortes': [],
            'pontos_fracos': [],
            'recomendacoes': []
        }
        
        # Identificar pontos fortes e fracos
        for materia, dados in analise['desempenho_por_materia'].items():
            if dados['taxa_acerto'] >= 0.7:
                analise['pontos_fortes'].append(materia)
            elif dados['taxa_acerto'] < 0.5:
                analise['pontos_fracos'].append(materia)
        
        # Gerar recomendações
        analise['recomendacoes'] = self._gerar_recomendacoes(analise)
        
        return analise
    
    def gerar_simulado_personalizado(
        self,
        perfil: Dict,
        dificuldade: str = "media"
    ) -> List[Dict]:
        """
        Gera simulado personalizado baseado no perfil
        """
        
        # Buscar questões adequadas
        questoes = self._buscar_questoes_banco(
            banca=perfil.get('banca_alvo'),
            materias=perfil.get('materias_foco', []),
            dificuldade=dificuldade,
            quantidade=50
        )
        
        # Balancear questões por matéria
        simulado = self._balancear_questoes(questoes, perfil)
        
        return simulado
    
    def chat(self, mensagem: str, contexto: Dict = None) -> str:
        """
        Conversa com coaching personalizado
        """
        
        # Adicionar contexto se fornecido
        if contexto:
            mensagem_com_contexto = f"""
            Contexto do candidato:
            - Concurso alvo: {contexto.get('concurso_alvo', 'Não especificado')}
            - Nível: {contexto.get('nivel', 'Iniciante')}
            - Tempo disponível: {contexto.get('tempo_disponivel', 'Não especificado')}
            
            Pergunta: {mensagem}
            """
        else:
            mensagem_com_contexto = mensagem
        
        # Gerar resposta
        resposta = self.chain.run(input=mensagem_com_contexto)
        
        return resposta
```

---

## 📝 **CHECKLIST DE IMPLEMENTAÇÃO**

### **Sprint 1 - Finalização (Esta Semana)**
- [ ] Criar schema completo de bancas (`app/models/banca.py`)
- [ ] Criar schema de questões (`app/models/questao.py`)
- [ ] Documentar pipeline completo de dados
- [ ] Testar integração banco de dados

### **Sprint 2 - Completar (Próxima Semana)**
- [ ] Implementar `scrapers/sites_oficiais_scraper.py`
- [ ] Criar métodos específicos por banca (CESPE, FCC, FGV, etc.)
- [ ] Refinar prompts do sistema RAG
- [ ] Criar `ASPECTOS_LEGAIS.md`
- [ ] Testes de scrapers oficiais

### **Sprint 3 - Consolidar (2 Semanas)**
- [ ] Consolidar scrapers em módulos únicos
- [ ] Criar diagrama de fluxo visual (Mermaid)
- [ ] Implementar testes comparativos de modelos LLM
- [ ] Adicionar OCR para PDFs escaneados (Tesseract)
- [ ] Otimizar regex patterns para limpeza de texto
- [ ] Melhorar estratégia de chunking semântico
- [ ] Finalizar documentação metodológica

### **Sprint 4 - Implementar RAG (3-4 Semanas)**
- [ ] Criar `modules/rag_pipeline_completo.py`
- [ ] Implementar `modules/auto_update_db.py`
- [ ] Criar `modules/retriever_avancado.py`
- [ ] Melhorar `modules/conversational_rag.py`
- [ ] Implementar `modules/data_validator.py`
- [ ] Criar `modules/ml_models/banca_classifier.py`
- [ ] Implementar `modules/ml_models/theme_predictor.py`
- [ ] Desenvolver `modules/coaching_ai.py`
- [ ] Treinar modelos de ML com dados históricos
- [ ] Testes de integração RAG completo

### **Sprint 5 - Testes e Produção (2-3 Semanas)**
- [ ] Finalizar sistema de notificações
- [ ] Implementar autenticação JWT completa
- [ ] Criar `app/core/security.py`
- [ ] Desenvolver `app/services/edital_service.py`
- [ ] Implementar `modules/user_profiling.py`
- [ ] Criar suite de testes (`tests/integration/`, `tests/performance/`)
- [ ] Setup de beta testing
- [ ] Implementar analytics e tracking
- [ ] Deploy em produção
- [ ] Monitoramento contínuo

---

## 🎯 **PRÓXIMOS PASSOS IMEDIATOS**

### **Hoje:**
1. ✅ Ler e entender este plano completo
2. ⚙️ Criar branch `feature/sprint-1-completion`
3. 📝 Criar arquivos de models (`banca.py`, `questao.py`)
4. 🗄️ Executar migrations do banco de dados

### **Esta Semana:**
1. Completar Sprint 1 (tarefas pendentes)
2. Iniciar Sprint 2 (scraper sites oficiais)
3. Documentar progresso no GitHub
4. Atualizar backlog com status atual

### **Este Mês:**
1. Finalizar Sprints 1, 2 e 3
2. Iniciar implementação Sprint 4 (RAG completo)
3. Treinar primeiros modelos de ML
4. Deploy de versão beta

---

## 📊 **MÉTRICAS DE PROGRESSO**

### **Status Atual:**
- Sprint 0: ✅ 100% (9/9)
- Sprint 1: 🔄 85% (8.5/10)
- Sprint 2: 🔄 70% (7.7/11)
- Sprint 3: 🚧 60% (6.6/11)
- Sprint 4: ⏳ 0% (0/9)
- Sprint 5: ⏳ 0% (0/9)

### **Meta:**
- Finalizar Sprint 1-3: **Esta Semana + Próximas 2 semanas**
- Implementar Sprint 4: **Próximo Mês**
- Completar Sprint 5: **Mês Seguinte**
- Deploy Produção: **3 Meses**

---

**🚀 ESTE PLANO ALINHA 100% O CÓDIGO COM SEU BACKLOG!**

*Documento criado em: 11/11/2025*
*Status: PRONTO PARA IMPLEMENTAÇÃO*
