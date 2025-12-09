# 🎓 Sistema de Estudo de Bancas - ConcursAI

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Funcionalidades](#funcionalidades)
4. [Instalação](#instalação)
5. [Uso](#uso)
6. [Módulos](#módulos)
7. [Exemplos](#exemplos)
8. [API Reference](#api-reference)

---

## 🎯 Visão Geral

O Sistema de Estudo de Bancas é uma solução completa de IA para análise profunda de padrões de bancas organizadoras de concursos públicos. O sistema:

- **Identifica automaticamente** a banca organizadora a partir do texto
- **Analisa o estilo** de questões (complexidade, tipo, dificuldade)
- **Processa PDFs** de provas e gabaritos com chunking inteligente
- **Categoriza questões** por disciplina, tema, dificuldade e características
- **Gera recomendações** personalizadas de estudo
- **Compara bancas** para facilitar transição entre concursos

### 🔬 Tecnologias Utilizadas

- **Machine Learning**: Sentence-Transformers para embeddings semânticos
- **NLP**: Análise linguística e extração de padrões
- **Deep Learning**: Classificação automática de conteúdo
- **Computer Vision**: Extração de texto de PDFs com múltiplas estratégias

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│              Sistema de Estudo de Bancas                │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼───────┐                   ┌────────▼────────┐
│ Banca Analyzer│                   │ Smart PDF       │
│               │                   │ Chunker         │
│ • Identifica  │                   │                 │
│   bancas      │                   │ • Extrai texto  │
│ • Analisa     │                   │ • Identifica    │
│   estilos     │                   │   questões      │
│ • Compara     │                   │ • Categoriza    │
│ • Recomenda   │                   │ • Gera chunks   │
└───────┬───────┘                   └────────┬────────┘
        │                                     │
        └──────────────────┬──────────────────┘
                           │
                ┌──────────▼──────────┐
                │ Banca Study System  │
                │                     │
                │ • Integra módulos   │
                │ • Gera perfis       │
                │ • Relatórios        │
                │ • Exportação        │
                └─────────────────────┘
```

### Fluxo de Dados

1. **Entrada**: PDFs de provas/gabaritos
2. **Processamento**: Extração + Chunking + Categorização
3. **Análise**: Identificação de padrões + Estatísticas
4. **Saída**: Perfil completo + Recomendações + Relatórios

---

## ⚡ Funcionalidades

### 1. Identificação Automática de Banca

```python
from modules.banca_analyzer import get_banca_analyzer

analyzer = get_banca_analyzer()
banca, confianca = analyzer.identificar_banca(texto_questao)
# Output: ("CESPE/CEBRASPE", 0.92)
```

**Como funciona:**
- Análise de palavras-chave específicas
- Padrões regex característicos
- Análise estrutural do texto
- Score de confiança baseado em múltiplos fatores

### 2. Análise de Estilo de Questão

```python
analise = analyzer.analisar_estilo_questao(texto, "CESPE/CEBRASPE")
```

**Retorna:**
- Complexidade (1-10)
- Nível de dificuldade (Básico/Intermediário/Avançado)
- Disciplina provável
- Tipo de questão
- Características detectadas
- Score de aderência ao padrão da banca

### 3. Chunking Inteligente de PDFs

```python
from modules.smart_pdf_chunker import get_smart_chunker

chunker = get_smart_chunker()
resultado = chunker.process_pdf(
    "prova.pdf",
    tipo_doc="prova",
    banca="CESPE/CEBRASPE"
)
```

**Características do Chunking:**
- ✅ Identifica questões numeradas automaticamente
- ✅ Categoriza por disciplina usando NLP
- ✅ Detecta tipo de questão (Múltipla Escolha, Certo/Errado, etc.)
- ✅ Estima dificuldade (Básico, Intermediário, Avançado)
- ✅ Extrai temas específicos
- ✅ Identifica características (negação, exceção, jurisprudência)
- ✅ Gera embeddings para busca semântica

### 4. Processamento de Múltiplas Provas

```python
from modules.banca_study_system import get_study_system

system = get_study_system()
resultado = system.processar_provas_banca(
    pdf_paths=["prova1.pdf", "prova2.pdf", "prova3.pdf"],
    banca="CESPE/CEBRASPE",
    metadata={"ano": 2024, "cargo": "Analista"}
)
```

**Gera:**
- Perfil completo da banca
- Estatísticas agregadas
- Padrões identificados
- Distribuição de disciplinas/dificuldades/tipos

### 5. Geração de Relatórios Completos

```python
relatorio = system.gerar_relatorio_completo_banca("CESPE/CEBRASPE")
```

**Conteúdo do Relatório:**
- Resumo executivo
- Parâmetros da banca
- Perfil detalhado com estatísticas
- Análise comparativa com outras bancas
- Plano de estudo sugerido (3 fases)
- Recomendações personalizadas

### 6. Recomendações Personalizadas

```python
recomendacoes = analyzer.recomendar_estrategia_estudo(
    "CESPE/CEBRASPE",
    disciplinas=["Direito Constitucional", "Português"]
)
```

**Inclui:**
- Prioridade de disciplinas
- Distribuição de tempo de estudo
- Estratégias específicas
- Materiais recomendados
- Alertas importantes

### 7. Comparação entre Bancas

```python
comparacao = analyzer.comparar_bancas("CESPE/CEBRASPE", "FCC")
```

**Mostra:**
- Diferenças principais (tipo, complexidade, estilo)
- Semelhanças
- Recomendação de transição

---

## 📦 Instalação

### Requisitos

```bash
Python 3.8+
```

### Dependências

```bash
pip install -r requirements_banca.txt
```

**requirements_banca.txt:**
```
sentence-transformers>=2.2.0
numpy>=1.24.0
scikit-learn>=1.3.0
PyMuPDF>=1.23.0
pypdf>=3.0.0
requests>=2.28.0
```

### Instalação dos Módulos

```bash
# Copiar módulos para o diretório do projeto
cp modules/banca_analyzer.py seu_projeto/modules/
cp modules/smart_pdf_chunker.py seu_projeto/modules/
cp modules/banca_study_system.py seu_projeto/modules/
```

---

## 🚀 Uso

### Exemplo Básico

```python
# 1. Importar sistema
from modules.banca_study_system import get_study_system

# 2. Inicializar
system = get_study_system()

# 3. Processar provas
resultado = system.processar_provas_banca(
    pdf_paths=[
        "provas/cespe_2024_trf.pdf",
        "provas/cespe_2024_pf.pdf"
    ],
    banca="CESPE/CEBRASPE",
    metadata={"ano": 2024}
)

# 4. Gerar relatório
relatorio = system.gerar_relatorio_completo_banca("CESPE/CEBRASPE")

# 5. Acessar informações
print(f"Total de questões: {relatorio['resumo_executivo']['total_questoes']}")
print(f"Disciplina principal: {relatorio['resumo_executivo']['disciplina_principal']}")
print(f"Nível: {relatorio['resumo_executivo']['nivel_dificuldade_geral']}")

# 6. Exportar
relatorio_json = system.exportar_perfil("CESPE/CEBRASPE", formato="json")
with open("cespe_perfil.json", "w") as f:
    f.write(relatorio_json)
```

### Exemplo: Análise de Questão Individual

```python
from modules.banca_analyzer import get_banca_analyzer

analyzer = get_banca_analyzer()

questao = """
Considerando a jurisprudência do STF sobre direitos fundamentais,
assinale a alternativa INCORRETA, exceto nos casos em que...
"""

# Identificar banca
banca, conf = analyzer.identificar_banca(questao)
print(f"Banca: {banca} (confiança: {conf:.1%})")

# Analisar estilo
analise = analyzer.analisar_estilo_questao(questao, banca)
print(f"Complexidade: {analise['complexidade_estimada']:.1f}/10")
print(f"Nível: {analise['nivel_dificuldade']}")
print(f"Disciplina: {analise['disciplina_provavel']}")

# Características
if analise['caracteristicas_detectadas']['tem_negacao']:
    print("⚠️ ATENÇÃO: Questão com negação!")
if analise['caracteristicas_detectadas']['tem_jurisprudencia']:
    print("⚖️ Menciona jurisprudência")
```

### Exemplo: Busca em Chunks Processados

```python
from modules.smart_pdf_chunker import get_smart_chunker

chunker = get_smart_chunker()

# Processar PDF
resultado = chunker.process_pdf("prova.pdf", banca="CESPE/CEBRASPE")

# Buscar chunks específicos
chunks_portugues = chunker.buscar_chunks(
    "prova.pdf",
    filtros={"disciplina": "Português", "dificuldade": "Avançado"},
    top_k=5
)

# Busca semântica
chunks_relevantes = chunker.buscar_chunks(
    "prova.pdf",
    query="direitos fundamentais e garantias constitucionais",
    top_k=3
)

for chunk in chunks_relevantes:
    print(f"Questão {chunk['numero_questao']}: {chunk['categoria']['disciplina']}")
    print(f"  Nível: {chunk['categoria']['dificuldade']}")
    print(f"  Conteúdo: {chunk['conteudo'][:100]}...")
```

---

## 📚 Módulos

### 1. `banca_analyzer.py`

**Classe Principal:** `BancaAnalyzer`

**Métodos:**
- `identificar_banca(texto)` - Identifica banca a partir do texto
- `analisar_estilo_questao(texto, banca)` - Análise completa de estilo
- `gerar_estatisticas_banca(questoes, banca)` - Estatísticas de conjunto
- `recomendar_estrategia_estudo(banca, disciplinas)` - Recomendações
- `comparar_bancas(banca1, banca2)` - Comparação detalhada

**Parâmetros de Bancas:**
```python
BANCA_PARAMETERS = {
    "CESPE/CEBRASPE": {
        "tipo_questao": "certo_errado",
        "complexidade_media": 8.5,
        "tamanho_medio_questao": 150,
        "caracteristicas": {...},
        "disciplinas_peso": {...},
        "palavras_chave": [...],
        "padroes_texto": [...]
    },
    # Outras bancas...
}
```

### 2. `smart_pdf_chunker.py`

**Classe Principal:** `SmartPDFChunker`

**Métodos:**
- `process_pdf(pdf_path, tipo_doc, banca, metadata)` - Processa PDF
- `buscar_chunks(pdf_path, filtros, query, top_k)` - Busca chunks
- `_extrair_texto_com_paginas(pdf_path)` - Extração de texto
- `_processar_prova(texto, paginas, banca)` - Processa prova
- `_categorizar_questao(chunk, banca)` - Categoriza questão
- `_adicionar_embeddings(chunks)` - Adiciona embeddings

**Estrutura de Chunk:**
```python
{
    "id": "questao_1",
    "tipo": "questao",
    "numero_questao": 1,
    "conteudo": "texto da questão...",
    "metadata": {
        "pagina_inicio": 1,
        "tamanho_palavras": 120,
        "arquivo_origem": "prova.pdf",
        "banca": "CESPE/CEBRASPE"
    },
    "categoria": {
        "disciplina": "Direito Constitucional",
        "tipo_questao": "Certo/Errado",
        "dificuldade": "Avançado",
        "temas": ["direitos fundamentais", "controle..."],
        "caracteristicas": {
            "tem_negacao": True,
            "tem_jurisprudencia": True,
            ...
        }
    },
    "tags": ["Direito Constitucional", "Avançado", ...],
    "embedding": [0.123, -0.456, ...]  # 384 dimensões
}
```

### 3. `banca_study_system.py`

**Classe Principal:** `BancaStudySystem`

**Métodos:**
- `processar_provas_banca(pdf_paths, banca, metadata)` - Processa múltiplas provas
- `gerar_relatorio_completo_banca(banca)` - Gera relatório completo
- `exportar_perfil(banca, formato)` - Exporta perfil (JSON ou TXT)
- `_gerar_perfil_banca(banca, chunks)` - Gera perfil da banca
- `_gerar_recomendacoes_personalizadas(perfil, banca)` - Recomendações
- `_gerar_plano_estudo(perfil, banca)` - Plano de estudo em 3 fases

**Estrutura de Perfil:**
```python
{
    "banca": "CESPE/CEBRASPE",
    "total_questoes_analisadas": 150,
    "distribuicao_disciplinas": {
        "Direito Constitucional": {"count": 40, "percentual": 26.67}
    },
    "distribuicao_dificuldade": {...},
    "distribuicao_tipos": {...},
    "temas_frequentes": [...],
    "caracteristicas_predominantes": {...},
    "padroes_identificados": {...},
    "estatisticas_avancadas": {...},
    "recomendacoes_estudo": {...}
}
```

---

## 🧪 Exemplos Avançados

### Exemplo 1: Pipeline Completo

```python
from modules.banca_study_system import get_study_system
import glob

# Inicializar
system = get_study_system()

# Buscar todos os PDFs de uma pasta
pdfs_cespe = glob.glob("provas/cespe/*.pdf")

# Processar
resultado = system.processar_provas_banca(
    pdf_paths=pdfs_cespe,
    banca="CESPE/CEBRASPE",
    metadata={
        "ano": 2024,
        "area": "Jurídica"
    }
)

# Relatório
relatorio = system.gerar_relatorio_completo_banca("CESPE/CEBRASPE")

# Análise
perfil = relatorio['perfil_detalhado']
print(f"\n📊 PERFIL CESPE/CEBRASPE")
print(f"="*60)

# Top disciplinas
print(f"\n🎯 Top 5 Disciplinas:")
disciplinas = sorted(
    perfil['distribuicao_disciplinas'].items(),
    key=lambda x: x[1]['percentual'],
    reverse=True
)[:5]

for disc, data in disciplinas:
    print(f"  {disc}: {data['percentual']:.1f}% ({data['count']} questões)")

# Dificuldade
print(f"\n📈 Distribuição de Dificuldade:")
for nivel, data in perfil['distribuicao_dificuldade'].items():
    print(f"  {nivel}: {data['percentual']:.1f}%")

# Padrões
padroes = perfil['padroes_identificados']
print(f"\n🔍 Padrões Identificados:")
print(f"  Tamanho médio: {padroes['tamanho_medio_questao']} palavras")
print(f"  Usa contextualização: {padroes['usa_contextualizacao']:.1f}%")
print(f"  Menciona jurisprudência: {padroes['menciona_jurisprudencia']:.1f}%")
print(f"  Tem pegadinhas: {padroes['tem_pegadinhas']:.1f}%")

# Recomendações
recom = perfil['recomendacoes_estudo']
print(f"\n💡 Recomendações:")
for estrategia in recom['estrategias_especificas']:
    print(f"  {estrategia}")

# Plano de estudo
plano = relatorio['plano_estudo_sugerido']
print(f"\n📚 Plano de Estudo:")
print(f"  Duração: {plano['duracao_sugerida']}")
print(f"  Horas semanais: {plano['horas_semanais']}")

for fase in plano['fases']:
    print(f"\n  {fase['fase']}")
    print(f"    Objetivo: {fase['objetivo']}")
```

### Exemplo 2: Comparação Multi-Banca

```python
from modules.banca_analyzer import get_banca_analyzer

analyzer = get_banca_analyzer()

bancas = ["CESPE/CEBRASPE", "FCC", "FGV", "VUNESP"]

print("⚖️ COMPARAÇÃO ENTRE BANCAS")
print("="*80)

# Matriz de comparação
import pandas as pd

dados = []
for banca in bancas:
    params = analyzer.BANCA_PARAMETERS.get(banca, {})
    dados.append({
        "Banca": banca,
        "Tipo": params.get("tipo_questao", "N/A"),
        "Complexidade": params.get("complexidade_media", 0),
        "Tam. Médio": params.get("tamanho_medio_questao", 0)
    })

df = pd.DataFrame(dados)
print(df.to_string(index=False))

# Comparações par-a-par
print(f"\n🔄 Comparações Detalhadas:")
for i, banca1 in enumerate(bancas[:-1]):
    for banca2 in bancas[i+1:]:
        comp = analyzer.comparar_bancas(banca1, banca2)
        print(f"\n{banca1} vs {banca2}:")
        print(f"  {comp['recomendacao_transicao']}")
```

### Exemplo 3: Análise Estatística Avançada

```python
from modules.banca_study_system import get_study_system
import matplotlib.pyplot as plt

system = get_study_system()

# Processar provas
system.processar_provas_banca(pdfs, "CESPE/CEBRASPE")

# Obter perfil
perfil = system.perfis_bancas["CESPE/CEBRASPE"]

# Visualizar distribuição de disciplinas
disciplinas = perfil['distribuicao_disciplinas']
nomes = list(disciplinas.keys())
valores = [d['percentual'] for d in disciplinas.values()]

plt.figure(figsize=(12, 6))
plt.bar(nomes, valores)
plt.xticks(rotation=45, ha='right')
plt.ylabel('Percentual (%)')
plt.title('Distribuição de Disciplinas - CESPE/CEBRASPE')
plt.tight_layout()
plt.savefig('distribuicao_disciplinas.png')

# Análise de complexidade
stats = perfil['estatisticas_avancadas']
print(f"\n📊 Estatísticas Avançadas:")
print(f"  Complexidade média: {stats['complexidade_media']:.2f}/10")
print(f"  Variação: {stats['variacao_dificuldade']:.2f}")
print(f"  Diversidade temática: {stats['diversidade_tematica']} disciplinas")
print(f"  Taxa avançadas: {stats['taxa_questoes_avancadas']:.1f}%")
```

---

## 🔧 API Reference

### BancaAnalyzer

```python
class BancaAnalyzer:
    def __init__(self, ollama_url: str = "http://localhost:11434")
    
    def identificar_banca(self, texto: str) -> Tuple[str, float]
    """
    Identifica banca a partir do texto.
    
    Args:
        texto: Texto da questão/prova
        
    Returns:
        Tupla (nome_banca, confianca)
    """
    
    def analisar_estilo_questao(
        self, 
        texto_questao: str, 
        banca: str
    ) -> Dict[str, Any]
    """
    Analisa estilo completo da questão.
    
    Args:
        texto_questao: Texto da questão
        banca: Nome da banca
        
    Returns:
        Dicionário com análise completa
    """
    
    def gerar_estatisticas_banca(
        self, 
        questoes: List[str], 
        banca: str
    ) -> Dict[str, Any]
    """
    Gera estatísticas de conjunto de questões.
    
    Args:
        questoes: Lista de textos de questões
        banca: Nome da banca
        
    Returns:
        Estatísticas agregadas
    """
    
    def recomendar_estrategia_estudo(
        self, 
        banca: str, 
        disciplinas: List[str] = None
    ) -> Dict[str, Any]
    """
    Recomenda estratégia de estudo.
    
    Args:
        banca: Nome da banca
        disciplinas: Disciplinas de interesse (opcional)
        
    Returns:
        Recomendações personalizadas
    """
    
    def comparar_bancas(self, banca1: str, banca2: str) -> Dict[str, Any]
    """
    Compara duas bancas.
    
    Args:
        banca1: Nome da primeira banca
        banca2: Nome da segunda banca
        
    Returns:
        Comparação detalhada
    """
```

### SmartPDFChunker

```python
class SmartPDFChunker:
    def __init__(self, use_embeddings: bool = True)
    
    def process_pdf(
        self,
        pdf_path: str,
        tipo_doc: str = "prova",
        banca: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]
    """
    Processa PDF e gera chunks categorizados.
    
    Args:
        pdf_path: Caminho para o PDF
        tipo_doc: "prova", "gabarito" ou "auto"
        banca: Nome da banca (opcional)
        metadata: Metadados adicionais
        
    Returns:
        Resultado do processamento com chunks
    """
    
    def buscar_chunks(
        self,
        pdf_path: str,
        filtros: Optional[Dict] = None,
        query: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]
    """
    Busca chunks com filtros e busca semântica.
    
    Args:
        pdf_path: Caminho do PDF processado
        filtros: Filtros (disciplina, dificuldade, etc.)
        query: Query para busca semântica
        top_k: Número de resultados
        
    Returns:
        Lista de chunks filtrados/rankeados
    """
```

### BancaStudySystem

```python
class BancaStudySystem:
    def __init__(self, ollama_url: str = "http://localhost:11434")
    
    def processar_provas_banca(
        self,
        pdf_paths: List[str],
        banca: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]
    """
    Processa múltiplas provas de uma banca.
    
    Args:
        pdf_paths: Lista de caminhos para PDFs
        banca: Nome da banca
        metadata: Metadados adicionais
        
    Returns:
        Relatório de processamento
    """
    
    def gerar_relatorio_completo_banca(self, banca: str) -> Dict[str, Any]
    """
    Gera relatório completo de uma banca.
    
    Args:
        banca: Nome da banca
        
    Returns:
        Relatório completo
    """
    
    def exportar_perfil(
        self, 
        banca: str, 
        formato: str = "json"
    ) -> str
    """
    Exporta perfil da banca.
    
    Args:
        banca: Nome da banca
        formato: "json" ou "txt"
        
    Returns:
        String com dados exportados
    """
```

---

## 🎯 Bancas Suportadas

### Principais Bancas

1. **CESPE/CEBRASPE**
   - Tipo: Certo/Errado predominante
   - Complexidade: 8.5/10 (Alta)
   - Características: Questões longas, contextualização, jurisprudência

2. **FCC**
   - Tipo: Múltipla Escolha
   - Complexidade: 7.0/10 (Média-Alta)
   - Características: Lei seca, objetividade, pouca contextualização

3. **FGV**
   - Tipo: Múltipla Escolha Interpretativa
   - Complexidade: 8.0/10 (Alta)
   - Características: Interpretação, contextualização, raciocínio

4. **VUNESP**
   - Tipo: Múltipla Escolha
   - Complexidade: 6.5/10 (Média)
   - Características: Conhecimentos específicos, técnica

---

## 📝 Notas de Desenvolvimento

### Próximas Funcionalidades (Roadmap)

- [ ] Integração com APIs de bancas para dados em tempo real
- [ ] Análise de gabaritos comentados com IA
- [ ] Geração automática de questões similares
- [ ] Dashboard interativo web com visualizações
- [ ] Exportação para formatos de LMS (Moodle, Canvas)
- [ ] API REST para integração externa
- [ ] Mobile app para estudo on-the-go

### Melhorias Planejadas

- [ ] Suporte a mais bancas (IBFC, IDECAN, AOCP, etc.)
- [ ] Fine-tuning de modelo específico para bancas
- [ ] Análise de evolução temporal de padrões
- [ ] Predição de temas prováveis por cargo/órgão
- [ ] Sistema de recomendação de questões para prática

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

## 📧 Contato

Para dúvidas, sugestões ou suporte:
- Email: suporte@concursai.com
- GitHub Issues: [link]

---

**Desenvolvido com ❤️ pela equipe ConcursAI**
