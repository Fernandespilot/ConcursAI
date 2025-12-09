# 🚀 ConcursAI - Assistente de Editais com Llama-3.1

Sistema de RAG (Retrieval-Augmented Generation) para análise de editais de concursos públicos usando **Meta Llama-3.1 8B Instruct** rodando 100% local na CPU.

## 🎯 Funcionalidades

- ✅ **Perguntas sobre Editais**: Faça perguntas e receba respostas baseadas nos PDFs indexados
- ✅ **Indexação de PDFs**: Adicione editais com metadados (banca, cargo, ano, órgão)
- ✅ **Análise de Bancas**: Gere relatórios de temas mais cobrados por disciplina
- ✅ **100% Local**: Sem internet, sem APIs pagas, total privacidade

## 🖥️ Requisitos

- **CPU**: Intel i7 ou superior (testado no i7-1255U)
- **RAM**: 16 GB (usa ~8-10 GB durante execução)
- **Armazenamento**: ~6 GB (modelo + dependências)
- **Python**: 3.10 ou 3.11

## 📦 Instalação

### 1. Clone o repositório e instale dependências

```bash
cd ConcursAI
pip install -r src/requirements.txt
```

### 2. Instale llama-cpp-python para CPU

```bash
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### 3. Baixe o modelo Llama-3.1 (4.92 GB)

```bash
pip install huggingface_hub[cli]
huggingface-cli download bartowski/Meta-Llama-3.1-8B-Instruct-GGUF --include "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" --local-dir ./models/
```

**Alternativamente**, baixe manualmente:
- Link: [Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/blob/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf)
- Salve em: `ConcursAI/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`

## 🚀 Como Usar

### Iniciar a Interface Web

```bash
streamlit run src/app.py
```

Abrirá automaticamente no navegador: `http://localhost:8501`

### Fluxo de Uso

1. **Adicionar PDFs** (Aba "Adicionar PDF"):
   - Faça upload de um edital em PDF
   - Preencha metadados: banca, cargo, ano, órgão
   - Clique em "Indexar PDF"
   - Aguarde processamento (20-40 seg por edital de ~50 páginas)

2. **Fazer Perguntas** (Aba "Perguntas"):
   - Digite: "Qual o salário inicial?"
   - O sistema busca nos editais e responde com base no conteúdo
   - Mostra a fonte da resposta

3. **Análise de Banca** (Aba "Análise de Banca"):
   - Selecione uma banca (ex: Cebraspe)
   - Clique em "Gerar Análise"
   - Recebe relatório de temas mais cobrados por disciplina
   - Baixe o relatório em .txt

## 📊 Desempenho Esperado (i7-1255U + 16 GB RAM)

| Operação | Tempo | RAM Usada |
|----------|-------|-----------|
| Carregar modelo | 1-2 min | 7-9 GB |
| Indexar PDF (50 pág) | 20-40 seg | +1 GB |
| Responder pergunta | 2-5 seg | ~10 GB |
| Gerar análise de banca | 5-10 seg | ~10 GB |

## 🛠️ Estrutura do Projeto

```
ConcursAI/
├── src/
│   ├── core.py          # Lógica RAG + Llama-3.1
│   ├── app.py           # Interface Streamlit
│   └── requirements.txt # Dependências
├── models/
│   └── Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf  # Modelo (4.92 GB)
├── db_concursos/        # Banco vetorial ChromaDB (criado automaticamente)
└── README.md
```

## 🔧 Configurações Avançadas

### Ajustar threads CPU (src/core.py):

```python
llm = Llama(
    model_path=GGUF_PATH,
    n_threads=6,  # Reduza se estiver lento (padrão: 8)
    ...
)
```

### Alterar tamanho de contexto:

```python
llm = Llama(
    ...
    n_ctx=4096,  # Dobra contexto (usa mais RAM)
    ...
)
```

## 🐛 Troubleshooting

**Erro: "Modelo não encontrado"**
- Certifique-se que o arquivo está em `./models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`
- Verifique o tamanho: deve ter ~4.92 GB

**Erro: "Out of Memory"**
- Feche outros aplicativos
- Reduza `n_ctx` de 2048 para 1024
- Reduza `n_threads` de 8 para 4

**Respostas lentas**
- Reduza `n_threads` (paradoxalmente pode acelerar)
- Verifique se há outros processos pesados rodando

**Erro ao instalar llama-cpp-python**
- No Windows: Instale Visual Studio Build Tools
- No Linux: `sudo apt install build-essential`

## 📝 Exemplos de Perguntas

- "Qual o salário inicial do cargo?"
- "Quais os requisitos mínimos para o cargo?"
- "Quantas vagas estão disponíveis?"
- "Qual a carga horária semanal?"
- "Quando são as inscrições?"
- "Quais disciplinas caem na prova de TI?"
- "Qual o valor da taxa de inscrição?"

## 🤖 Sobre o Modelo

**Meta Llama-3.1 8B Instruct (Q4_K_M)**
- Versão quantizada para CPU
- 4.92 GB (Q4_K_M = 4 bits com mix de precisão)
- Otimizado para português e textos jurídicos
- Lançado em 2025 pela Meta AI
- Licença: Llama 3.1 Community License

## 📄 Licença

Este projeto é open-source. O modelo Llama-3.1 segue a [Llama 3.1 Community License](https://ai.meta.com/llama/license/).

## 🙏 Créditos

- **Modelo**: [bartowski/Meta-Llama-3.1-8B-Instruct-GGUF](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF)
- **Framework**: LangChain, llama-cpp-python, ChromaDB
- **Interface**: Streamlit

---

**Desenvolvido para concurseiros que buscam uma ferramenta gratuita, local e privada para estudar editais! 🚀📚**
