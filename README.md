# 🎯 ConcursAI - Assistente de Concursos Públicos

## 📋 Descrição
ConcursAI é um assistente virtual inteligente para consultas sobre editais de concursos públicos. Utiliza tecnologias de IA, incluindo RAG (Retrieval-Augmented Generation), para responder perguntas específicas sobre concursos de forma precisa e contextualizada.

## 🚀 Funcionalidades

### ✨ Principais Recursos
- **Busca Inteligente**: Encontra informações específicas em editais usando busca semântica
- **Filtros Avançados**: Filtre por órgão, ano e cargo para resultados precisos
- **Interface Amigável**: Interface web desenvolvida com Gradio
- **Histórico de Conversa**: Mantém contexto das perguntas anteriores
- **Múltiplas Fontes**: Suporte para dados de diferentes sites de concursos

### 🔍 Tipos de Perguntas Suportadas
- Requisitos para cargos específicos
- Informações sobre salários e remuneração
- Prazos e cronogramas de inscrição
- Disciplinas e conteúdo das provas
- Documentação necessária
- Reserva de vagas (PCD, cotas)
- Processo de posse e nomeação

## 🛠️ Tecnologias Utilizadas

### 🧠 IA e Machine Learning
- **Groq API**: LLM na nuvem (Llama-3.1-70B) - respostas ultra-rápidas ⚡
- **ChromaDB**: Banco de dados vetorial para busca semântica
- **Sentence-Transformers**: Geração de embeddings textuais (multi-qa-mpnet-base-dot-v1)
- **Llama 3.1 8B**: Modelo local (fallback) via llama-cpp-python

### 🌐 Interface e Web
- **Gradio**: Interface web interativa
- **Pandas**: Manipulação e análise de dados
- **BeautifulSoup**: Extração de dados web

### 📄 Processamento de Documentos
- **PyPDF2**: Extração de texto de PDFs
- **Requests**: Coleta de dados via HTTP

## 📦 Instalação

### 1️⃣ Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### 2️⃣ Clonar o Repositório
```bash
git clone <url-do-repositorio>
cd ConcursAI
```

### 3️⃣ Criar Ambiente Virtual
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 4️⃣ Instalar Dependências
```bash
pip install -r requirements.txt
```

### 5️⃣ Configurar Groq API (RECOMENDADO) ⚡
```bash
# Obtenha sua chave grátis em: https://console.groq.com/keys
# Crie arquivo .env na raiz do projeto:
GROQ_API_KEY=gsk_sua_chave_aqui
USE_MODEL=auto
```

📖 **Documentação completa**: Veja `GROQ_SETUP.md` e `ESCOLHER_MODELO.md`

### 6️⃣ Preparar Dados
```bash
# Executar o processador para criar dados de exemplo
python modules/processar_concursos.py
```

## 🚀 Execução

### Iniciar a Aplicação
```bash
python concurso_app.py
```

### Acessar a Interface
Após a inicialização, acesse: `http://localhost:7860`

## 📊 Estrutura do Projeto

```
ConcursAI/
├── concurso_app.py              # Aplicação principal
├── requirements.txt             # Dependências
├── README.md                   # Este arquivo
├── concursos_chunks.csv        # Dados processados (gerado automaticamente)
├── db_concursos/              # Banco de dados ChromaDB
└── modules/
    ├── concurso_embeddings.py  # Gerenciamento de embeddings
    ├── concurso_rag.py         # Sistema RAG
    └── processar_concursos.py  # Processamento de dados
```

## 📝 Uso da Interface

### 🔍 Filtros de Busca
1. **Órgão/Instituição**: Filtre por órgão específico
2. **Ano**: Selecione o ano do concurso
3. **Cargo**: Escolha o cargo de interesse

### 💬 Chat com o Assistente
1. Digite sua pergunta no campo de texto
2. Clique em "Enviar" ou pressione Enter
3. Aguarde a resposta baseada nos dados disponíveis

### 🛠️ Funcionalidades Extras
- **Tentar Novamente**: Regenera a última resposta
- **Limpar Chat**: Remove o histórico da conversa
- **Exemplos**: Clique nos exemplos para inserir perguntas prontas

## 📈 Adicionando Novos Dados

### Formato dos Dados
O sistema espera dados no formato CSV com as seguintes colunas:
- `conteudo`: Texto do edital ou documento
- `orgao`: Nome do órgão responsável
- `ano`: Ano do concurso
- `cargo`: Cargo oferecido
- `tipo_documento`: Tipo do documento (edital, retificação, etc.)
- `titulo`: Título do concurso
- `url`: URL original do documento
- `data_publicacao`: Data de publicação

### Importar Dados
1. Prepare seus dados no formato CSV
2. Substitua ou adicione ao arquivo `concursos_chunks.csv`
3. Reinicie a aplicação para reindexar os dados

## 🔧 Configuração Avançada

### Personalizar Modelo de IA
Edite o arquivo `modules/concurso_rag.py` para usar diferentes modelos:
```python
# Trocar modelo de embeddings
embedder = SentenceTransformer("nome-do-modelo")

# Usar modelo GPT4All diferente
modelo = GPT4All("nome-do-modelo.gguf")
```

### Ajustar Parâmetros de Busca
No arquivo `modules/concurso_rag.py`, modifique:
```python
# Aumentar número de resultados
resultados = collection.query(query_texts=[pergunta], n_results=10)

# Ajustar temperatura do modelo
resposta = modelo.generate(prompt, max_tokens=500, temp=0.2)
```

## 🐛 Solução de Problemas

### Problemas Comuns

#### Erro "No module named 'gradio'"
```bash
pip install gradio
```

#### Erro de memória durante indexação
Reduza o tamanho do lote no arquivo `concurso_embeddings.py`:
```python
batch_size = 50  # Reduzir de 100 para 50
```

#### Interface não carrega
Verifique se a porta 7860 está disponível ou mude a porta:
```python
app.launch(server_port=8080)  # Usar porta diferente
```

### Logs e Debug
Para ativar logs detalhados, adicione no início do `concurso_app.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contribuição

### Como Contribuir
1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Áreas para Contribuição
- 🌐 Novos coletores de dados (sites de concursos)
- 🎨 Melhorias na interface
- 🧠 Otimizações nos modelos de IA
- 📝 Documentação e exemplos
- 🧪 Testes automatizados

## 📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte
- 📧 Email: [seu-email]
- 🐛 Issues: Use o sistema de issues do GitHub
- 💬 Discussões: Use o tab "Discussions" do repositório

## 🙏 Agradecimentos
- Comunidade open source
- Desenvolvedores das bibliotecas utilizadas
- Contribuidores do projeto

---

**⚠️ Disclaimer**: Este sistema é para fins educacionais e de pesquisa. Sempre consulte as fontes oficiais dos editais para informações definitivas.
