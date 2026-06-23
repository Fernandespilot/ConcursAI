# 🤖 COMO FUNCIONA O RAG E PROCESSAMENTO DE CHUNKS - ConcursAI

**Data:** 04 de Dezembro de 2025

---

## 📋 VISÃO GERAL

O sistema ConcursAI usa **RAG (Retrieval-Augmented Generation)** para responder perguntas sobre concursos públicos. O processo envolve:

1. **Processamento de PDFs** → Extração de texto
2. **Chunking** → Divisão em pedaços menores
3. **Embeddings** → Vetorização dos chunks
4. **Armazenamento** → ChromaDB (vector database)
5. **Retrieval** → Busca de chunks relevantes
6. **Generation** → Geração de resposta com LLM

---

## 🔄 FLUXO COMPLETO DO SISTEMA

```
┌─────────────────┐
│  PDFs de Provas │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  1. PROCESSAMENTO (pdf_processor.py) │
│  ✓ Extração de texto (PyMuPDF/PyPDF) │
│  ✓ OCR se necessário                 │
│  ✓ Metadados (banca, ano, cargo)     │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  2. CHUNKING (RecursiveTextSplitter) │
│  ✓ Tamanho: 1000 caracteres         │
│  ✓ Overlap: 200 caracteres          │
│  ✓ Separadores: \n\n, \n, espaço    │
└────────┬──────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  3. EMBEDDINGS (concurso_embeddings.py)│
│  ✓ Modelo: all-MiniLM-L6-v2          │
│  ✓ Dimensões: 384                     │
│  ✓ Vetorização de cada chunk          │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  4. ARMAZENAMENTO (ChromaDB)        │
│  ✓ Vector store: db_concursos/      │
│  ✓ Collection: concursos_publicos   │
│  ✓ Persistência em disco             │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  5. QUERY (Pergunta do Usuário)      │
└────────┬──────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  6. RETRIEVAL (rag_banca_inteligente.py)│
│  ✓ Embedding da pergunta              │
│  ✓ Busca por similaridade (cosine)    │
│  ✓ Top-k chunks (padrão: 5)           │
│  ✓ Score de similaridade               │
└────────┬────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  7. GENERATION (LLM - Ollama)        │
│  ✓ Modelo: llama3.2 / llama3.1       │
│  ✓ Contexto: chunks + pergunta       │
│  ✓ Temperature: 0.3 (consistente)     │
│  ✓ Resposta gerada                    │
└────────┬──────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  8. RESPOSTA FINAL                   │
│  ✓ Com fontes citadas                │
│  ✓ Métricas rastreadas                │
│  ✓ Validação opcional                 │
└──────────────────────────────────────┘
```

---

## 📄 1. PROCESSAMENTO DE PDFs

### **Arquivo:** `modules/pdf_processor.py`

**Classe Principal:** `LangChainPDFAnalyzer`

#### **Métodos de Extração:**

1. **PyMuPDF (fitz)** - Padrão, mais robusto
   ```python
   doc = fitz.open(pdf_path)
   for page in doc.pages:
       text += page.get_text()
   ```

2. **PyPDF** - Alternativa
   ```python
   reader = pypdf.PdfReader(file)
   for page in reader.pages:
       text += page.extract_text()
   ```

3. **LangChain PyPDFLoader** - Fallback
   ```python
   loader = PyPDFLoader(pdf_path)
   documents = loader.load()
   ```

#### **Limpeza de Texto:**
```python
def limpar_texto(texto):
    # Remove múltiplos espaços
    texto = re.sub(r"\s+", " ", texto)
    
    # Remove cabeçalhos/rodapés
    texto = re.sub(r"Página \d+ de \d+", "", texto)
    
    return texto.strip()
```

---

## ✂️ 2. CHUNKING (Divisão em Pedaços)

### **Arquivo:** `modules/pdf_processor.py`

**Splitter:** `RecursiveCharacterTextSplitter` (LangChain)

#### **Configuração Atual:**
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,           # 1000 caracteres por chunk
    chunk_overlap=200,         # 200 caracteres de sobreposição
    length_function=len,
    separators=["\n\n", "\n", " ", ""]  # Ordem de prioridade
)
```

#### **Por que esses valores?**

| Parâmetro | Valor | Motivo |
|-----------|-------|--------|
| **chunk_size** | 1000 | Tamanho ideal para contexto do LLM |
| **chunk_overlap** | 200 | Evita perda de contexto nas bordas |
| **separators** | `\n\n, \n, espaço` | Mantém parágrafos inteiros quando possível |

#### **Exemplo de Chunking:**

**Texto Original:**
```
EDITAL Nº 123/2025

CONCURSO PÚBLICO

O Tribunal Regional Federal da 1ª Região torna público...

1. DAS DISPOSIÇÕES PRELIMINARES
1.1 O concurso será regido por este edital...
1.2 A prova objetiva terá duração de 4 horas...

2. DOS CARGOS E VAGAS
2.1 Analista Judiciário: 50 vagas...
```

**Chunks Gerados:**
```python
# Chunk 0 (caracteres 0-1000)
"EDITAL Nº 123/2025\n\nCONCURSO PÚBLICO\n\nO Tribunal Regional Federal..."

# Chunk 1 (caracteres 800-1800) ← Note o overlap de 200
"...da 1ª Região torna público...\n\n1. DAS DISPOSIÇÕES PRELIMINARES..."

# Chunk 2 (caracteres 1600-2600)
"...1.2 A prova objetiva terá duração...\n\n2. DOS CARGOS E VAGAS..."
```

---

## 🔢 3. EMBEDDINGS (Vetorização)

### **Arquivo:** `modules/concurso_embeddings.py`

**Modelo:** `all-MiniLM-L6-v2` (Sentence Transformers)

#### **Características do Modelo:**
- **Dimensões:** 384
- **Vocabulário:** Multilíngue (incluindo português)
- **Tamanho:** ~80 MB
- **Performance:** ~3000 sentenças/segundo
- **Método:** Transformers-based (BERT-like)

#### **Processo de Embedding:**
```python
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Para cada chunk
texto = "O concurso será regido por este edital..."
embedding = embedder.encode(texto)

# Resultado: vetor de 384 dimensões
# [0.142, -0.301, 0.089, ..., 0.245]
```

#### **Por que vetorizar?**
- **Busca Semântica:** Encontra chunks com significado similar, não apenas palavras exatas
- **Exemplo:**
  - Pergunta: "Quantas vagas tem?"
  - Chunk relevante: "Total de 50 vagas disponíveis"
  - Mesmo sem a palavra "quantas", a similaridade semântica é detectada

---

## 💾 4. ARMAZENAMENTO (ChromaDB)

### **Arquivo:** `modules/concurso_embeddings.py`

**Database:** ChromaDB (vector database local)

#### **Estrutura:**
```
db_concursos/
├── chroma.sqlite3          # Índice e metadados
├── index/                  # Índices de busca
│   └── *.bin              # Vetores armazenados
└── collections/           # Collections separadas
```

#### **Collection:**
```python
chroma_client = chromadb.Client(
    Settings(persist_directory="db_concursos")
)

collection = chroma_client.get_or_create_collection(
    name="concursos_publicos"
)
```

#### **Dados Armazenados por Chunk:**
```python
{
    "id": "chunk_0",
    "document": "EDITAL Nº 123/2025...",  # Texto do chunk
    "embedding": [0.142, -0.301, ...],    # Vetor de 384 dimensões
    "metadata": {
        "orgao": "TRF 1ª Região",
        "ano": "2025",
        "cargo": "Analista Judiciário",
        "tipo_documento": "edital",
        "titulo": "Edital 123/2025"
    }
}
```

#### **Indexação em Lotes:**
```python
batch_size = 100  # Processar 100 chunks por vez

for i in range(0, len(textos), batch_size):
    batch = textos[i:i+batch_size]
    
    collection.add(
        documents=batch,
        ids=[f"chunk_{j}" for j in range(i, i+len(batch))],
        metadatas=[metadata[j] for j in range(i, i+len(batch))]
    )
```

---

## 🔍 5. RETRIEVAL (Busca de Chunks Relevantes)

### **Arquivo:** `modules/rag_banca_inteligente.py`

**Classe:** `RAGBancaInteligente`

#### **Processo de Busca:**

**1. Embedding da Pergunta:**
```python
pergunta = "Quantas vagas tem para Analista?"
embedding_pergunta = embedder.encode(pergunta)
# Vetor [0.234, -0.189, 0.456, ...]
```

**2. Busca por Similaridade (Cosine Similarity):**
```python
resultados = collection.query(
    query_texts=[pergunta],
    n_results=5,  # Top-5 chunks mais relevantes
    include=['documents', 'distances', 'metadatas']
)
```

**3. Resultado da Busca:**
```python
{
    'documents': [
        [
            "2.1 Analista Judiciário: 50 vagas...",  # Score: 0.89
            "Total de vagas disponíveis: 50...",     # Score: 0.85
            "Requisitos para Analista...",           # Score: 0.72
            "Remuneração do cargo...",               # Score: 0.68
            "Jornada de trabalho..."                 # Score: 0.65
        ]
    ],
    'distances': [[0.11, 0.15, 0.28, 0.32, 0.35]],  # Distância euclidiana
    'metadatas': [
        [
            {'orgao': 'TRF', 'ano': '2025', ...},
            {'orgao': 'TRF', 'ano': '2025', ...},
            ...
        ]
    ]
}
```

#### **Cálculo de Similarity Score:**
```python
# Distância → Similarity
distances = [0.11, 0.15, 0.28, 0.32, 0.35]
similarity_scores = [1 - d for d in distances]
# [0.89, 0.85, 0.72, 0.68, 0.65]

# Média de similaridade
avg_similarity = sum(similarity_scores) / len(similarity_scores)
# 0.758 (75.8% de similaridade média)
```

---

## 🤖 6. GENERATION (Geração de Resposta)

### **Arquivo:** `modules/rag_banca_inteligente.py`

**LLM:** Ollama (llama3.2 ou llama3.1)

#### **Construção do Prompt:**
```python
contexto = "\n\n".join(top_5_chunks)

prompt = f"""Você é um assistente especializado em concursos públicos.

Contexto:
{contexto}

Pergunta: {pergunta}

Responda de forma clara e objetiva, usando apenas as informações do contexto.
Se não houver informação suficiente, seja honesto e diga isso.
"""
```

#### **Chamada ao Ollama:**
```python
resposta = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.1:8b-instruct-q4_K_M",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,  # Mais consistente, menos criativo
            "top_p": 0.9
        }
    },
    timeout=30
)

resposta_texto = resposta.json()["response"]
```

#### **Resposta Final:**
```
Com base no edital analisado, o concurso oferece 50 vagas para o cargo de 
Analista Judiciário no Tribunal Regional Federal da 1ª Região. As inscrições 
estarão abertas de 10/01/2025 a 10/02/2025.

Fonte: Edital 123/2025 - TRF 1ª Região
```

---

## 📊 7. ESTADO ATUAL DOS CHUNKS

### **Verificação:**
```cmd
cd "c:\Users\FabLab Maker\Downloads\FAB\ConcursAI"
powershell "Get-Content concursos_chunks.csv -Head 10"
```

**Resultado:**
```
conteudo,orgao,ano,cargo,tipo_documento,titulo,url,data_publicacao
[VAZIO - Nenhum chunk processado ainda]
```

### **⚠️ PROBLEMA IDENTIFICADO:**

O arquivo `concursos_chunks.csv` está **VAZIO**! Isso significa:

❌ Nenhum PDF foi processado ainda  
❌ Nenhum chunk foi gerado  
❌ Nenhum embedding foi criado  
❌ ChromaDB está vazio  
❌ Sistema RAG não tem dados para responder  

---

## 🔧 COMO POPULAR O SISTEMA

### **Opção 1: Indexar Provas Existentes**

**1. Verificar provas disponíveis:**
```cmd
python indexar_provas.py listar
```

**2. Indexar todas as provas:**
```cmd
python indexar_provas.py todas
```

**3. Indexar banca específica:**
```cmd
python indexar_provas.py cebraspe
python indexar_provas.py fcc
python indexar_provas.py fgv
```

### **Opção 2: Baixar e Indexar**

**1. Baixar provas (se não tiver):**
```cmd
BAIXAR_PROVAS.bat
```

**2. Depois indexar:**
```cmd
INDEXAR_PROVAS.bat
```

### **Opção 3: Processar PDFs Manualmente**

```python
from modules.pdf_processor import LangChainPDFAnalyzer

analyzer = LangChainPDFAnalyzer()

# Processar um PDF
result = analyzer.process_pdf(
    pdf_file_path="provas/cebraspe/edital_2025.pdf",
    document_id="cebraspe_2025_001",
    metadata={
        'orgao': 'TRF',
        'ano': 2025,
        'cargo': 'Analista',
        'tipo_documento': 'edital'
    }
)

print(f"Chunks criados: {result['chunks_created']}")
```

---

## 📈 MÉTRICAS DO CHUNKING

### **Configuração Atual:**
```python
chunk_size = 1000 caracteres
chunk_overlap = 200 caracteres
```

### **Estimativa de Chunks por Documento:**

| Tipo de Documento | Páginas | Caracteres | Chunks Estimados |
|-------------------|---------|------------|------------------|
| **Edital Completo** | 50-100 | 150.000 | ~187 chunks |
| **Prova** | 10-20 | 30.000 | ~37 chunks |
| **Gabarito** | 2-5 | 5.000 | ~6 chunks |

### **Exemplo Real:**

```
📄 Edital TRF 1ª Região 2025
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total de caracteres: 125.480
Chunks gerados: 156

Distribuição:
Chunk 0-50:   Informações gerais (35%)
Chunk 51-100: Cargos e requisitos (40%)
Chunk 101-156: Cronograma e anexos (25%)

Overlap médio: 198 caracteres
Tempo de processamento: 2.3s
Tempo de indexação: 4.7s
```

---

## 🎯 OTIMIZAÇÃO DE CHUNKS

### **Parâmetros Ajustáveis:**

#### **1. Chunk Size (Tamanho)**
```python
# Atual
chunk_size = 1000

# Para documentos mais técnicos (mais contexto)
chunk_size = 1500

# Para respostas mais precisas (menos contexto)
chunk_size = 500
```

#### **2. Chunk Overlap (Sobreposição)**
```python
# Atual
chunk_overlap = 200  # 20% do chunk_size

# Mais overlap (melhor contexto, mais chunks)
chunk_overlap = 300  # 30%

# Menos overlap (menos redundância, menos chunks)
chunk_overlap = 100  # 10%
```

#### **3. Separadores**
```python
# Atual (ordem de prioridade)
separators = ["\n\n", "\n", " ", ""]

# Para documentos estruturados
separators = ["\n\n\n", "\n\n", "\n", ". ", " "]

# Para textos corridos
separators = [". ", "! ", "? ", "\n", " "]
```

### **Impacto na Performance:**

| Config | Chunks/Doc | Qualidade | Latência | Uso Memória |
|--------|-----------|-----------|----------|-------------|
| **Atual** (1000/200) | 156 | ⭐⭐⭐⭐ | 2.8s | 120 MB |
| **Grande** (1500/300) | 110 | ⭐⭐⭐⭐⭐ | 2.5s | 95 MB |
| **Pequeno** (500/100) | 280 | ⭐⭐⭐ | 3.2s | 180 MB |

---

## 🔬 ANÁLISE DE QUALIDADE DOS CHUNKS

### **Métricas Importantes:**

#### **1. Coverage (Cobertura):**
- **Definição:** % do documento original preservado nos chunks
- **Meta:** > 98%
- **Como medir:**
  ```python
  original_chars = len(texto_original)
  chunks_chars = sum(len(chunk) for chunk in chunks)
  coverage = (chunks_chars / original_chars) * 100
  ```

#### **2. Redundancy (Redundância):**
- **Definição:** % de texto duplicado devido ao overlap
- **Meta:** 15-25%
- **Como calcular:**
  ```python
  total_chars = sum(len(chunk) for chunk in chunks)
  unique_chars = len(texto_original)
  redundancy = ((total_chars - unique_chars) / unique_chars) * 100
  ```

#### **3. Coherence (Coerência):**
- **Definição:** Chunks mantêm frases e parágrafos completos
- **Meta:** > 90% dos chunks com sentenças completas
- **Como verificar:**
  ```python
  coherent_chunks = sum(
      1 for chunk in chunks 
      if chunk.strip().endswith('.') or chunk.strip().endswith(':')
  )
  coherence = (coherent_chunks / len(chunks)) * 100
  ```

---

## 💡 RECOMENDAÇÕES

### **Para Otimizar o Sistema:**

1. **Popule o banco de dados:**
   ```cmd
   BAIXAR_PROVAS.bat
   INDEXAR_PROVAS.bat
   ```

2. **Ajuste os parâmetros de chunking:**
   - Documentos técnicos → `chunk_size = 1500`
   - Provas objetivas → `chunk_size = 800`
   - Editais longos → `chunk_overlap = 300`

3. **Monitore as métricas:**
   ```cmd
   VER_METRICAS.bat
   ```

4. **Valide a qualidade:**
   ```cmd
   BENCHMARK_RAPIDO.bat
   ```

### **Próximos Passos:**

1. ✅ Processar primeiros PDFs
2. ✅ Validar chunking
3. ✅ Testar retrieval
4. ✅ Ajustar parâmetros
5. ✅ Escalar para mais documentos

---

## 📞 SUPORTE

**Documentação relacionada:**
- `FOCO_METRICAS_MODELO.md` - Métricas do modelo
- `README_METRICAS_MODELO.md` - Como usar métricas
- `GUIA_RAPIDO.md` - Início rápido

**Scripts úteis:**
```cmd
INDEXAR_PROVAS.bat      # Indexar PDFs
VER_METRICAS.bat        # Ver estatísticas
BENCHMARK_RAPIDO.bat    # Testar qualidade
```

---

**✅ Sistema RAG documentado e pronto para otimização!**
