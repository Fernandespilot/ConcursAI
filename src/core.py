# src/core.py - ConcursAI com Groq API (LLM na nuvem - muito mais rápido!)
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import os

# Importar Groq e llama_cpp (ambos disponíveis)
try:
    from groq import Groq
    USE_GROQ = True
except ImportError:
    USE_GROQ = False
    Groq = None

# Sempre importar llama_cpp para fallback
try:
    from llama_cpp import Llama
    USE_LOCAL = True
except ImportError:
    USE_LOCAL = False
    Llama = None

DB_PATH = "db_concursos"
EMBEDDING_MODEL = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
GGUF_PATH = "./models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"  # Fallback local

embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vectordb = None
llm = None
groq_client = None

def init_llm():
    """Inicializa o modelo - prioriza Groq API, fallback para local"""
    global llm, groq_client
    
    # Ler preferência do usuário
    use_model = os.getenv("USE_MODEL", "auto").lower()
    
    # Forçar modelo local
    if use_model == "local":
        print("[IA] 🤖 Configuração: Usando APENAS modelo local (Llama 8B)")
        _init_local_llm()
        return
    
    # Tentar Groq (auto ou forçado)
    if USE_GROQ and use_model in ["auto", "groq"]:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key and api_key != "SUA_CHAVE_AQUI":
            try:
                # Usar variáveis globais
                global groq_client, llm
                groq_client = Groq(api_key=api_key)
                llm = "groq"  # Flag indicando uso do Groq
                print("[IA] ⚡ GROQ API ATIVADA! (Llama-3.1-70B na nuvem)")
                print("[IA] 🚀 Respostas ultra-rápidas (1-2 segundos)!")
                if use_model == "auto":
                    print("[IA] 🔄 Modo AUTO: Groq principal, fallback local disponível")
                else:
                    print("[IA] ⚡ Modo GROQ: Apenas nuvem (máxima velocidade)")
                return
            except Exception as e:
                print(f"[IA] ⚠️ Erro ao configurar Groq: {e}")
                if use_model == "groq":
                    print("[IA] ❌ Modo GROQ forçado mas falhou! Abortando...")
                    raise
                print("[IA] 🔄 Modo AUTO: Usando modelo local como fallback...")
        else:
            if use_model == "groq":
                print("[IA] ❌ Modo GROQ forçado mas GROQ_API_KEY não configurada!")
                raise ValueError("GROQ_API_KEY não configurada")
            print("[IA] ⚠️ GROQ_API_KEY não configurada, usando modelo local")
    
    # Fallback para modelo local
    _init_local_llm()

def _init_local_llm():
    """Inicializa modelo local GGUF"""
    global llm
    if os.path.exists(GGUF_PATH):
        print("[IA] Carregando Llama-3.1 8B (GGUF) na CPU...")
        print(f"[IA] Usando {os.path.getsize(GGUF_PATH) / (1024**3):.2f} GB de modelo")
        llm = Llama(
            model_path=GGUF_PATH,
            n_ctx=4096,
            n_threads=8,
            n_batch=512,
            verbose=False
        )
        print("[IA] ✓ Modelo local carregado! (Llama-3.1 Q4_K_M)")
    else:
        raise FileNotFoundError(
            f"❌ Modelo não encontrado em: {GGUF_PATH}\n"
            f"Configure GROQ_API_KEY no .env ou baixe o modelo local."
        )

def init_db():
    """Inicializa o banco vetorial ChromaDB"""
    global vectordb
    if os.path.exists(DB_PATH):
        vectordb = Chroma(persist_directory=DB_PATH, embedding_function=embedder)
        print(f"[DB] ✓ Banco carregado: {DB_PATH}")
    else:
        vectordb = Chroma(embedding_function=embedder, persist_directory=DB_PATH)
        print(f"[DB] ✓ Novo banco criado: {DB_PATH}")
    vectordb.persist()

def indexar_pdf(pdf_path, metadados={}):
    """
    Indexa um PDF de edital no banco vetorial
    
    Args:
        pdf_path: Caminho do PDF
        metadados: Dict com 'banca', 'cargo', 'ano', etc.
    """
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    
    # Adiciona metadados aos documentos
    for doc in docs:
        doc.metadata.update(metadados)
    
    # Divide em chunks de 800 caracteres (otimizado para editais)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    
    if vectordb is None:
        init_db()
    
    vectordb.add_documents(chunks)
    vectordb.persist()
    print(f"[OK] {os.path.basename(pdf_path)} → {len(chunks)} chunks indexados")
    return len(chunks)

def perguntar(texto, k=5):
    """
    Faz uma pergunta sobre os editais indexados
    
    Args:
        texto: Pergunta do usuário
        k: Número de documentos a recuperar (padrão: 5)
    
    Returns:
        tupla (resposta, fonte)
    """
    global llm, groq_client
    
    # Inicializar LLM se necessário (lazy loading)
    if llm is None:
        print("🤖 Inicializando modelo Llama-3.1 (primeira consulta)...")
        init_llm()
    
    if vectordb is None:
        init_db()
    
    # Busca os documentos mais relevantes
    docs = vectordb.as_retriever(search_kwargs={"k": k}).invoke(texto)
    
    if not docs:
        return "Não encontrei informações relevantes nos documentos indexados.", "Nenhum documento"
    
    # Limitar contexto para evitar exceder janela
    contexto_parts = [d.page_content[:400] for d in docs[:min(k, 5)]]  # Max 5 docs, 400 chars cada
    contexto = "\n\n".join(contexto_parts)
    
    # Prompt inteligente - combina documentos + conhecimento próprio
    prompt = (
        "<|start_header_id|>system<|end_header_id|>\n\n"
        "Você é ConcursAI, um assistente especializado em concursos públicos do Brasil.\n\n"
        "Suas capacidades:\n"
        "- Responder perguntas sobre concursos, bancas examinadoras, e estudos\n"
        "- Analisar editais e provas anteriores\n"
        "- Dar dicas e métodos de estudo personalizados\n"
        "- Explicar conceitos e tirar dúvidas\n"
        "- Fazer análises comparativas entre bancas\n\n"
        "IMPORTANTE: Você deve combinar as informações dos documentos com seu conhecimento geral para dar respostas completas e úteis. "
        "Não se limite apenas ao que está nos documentos!\n"
        "<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
        f"Documentos relevantes encontrados:\n{contexto}\n\n"
        f"Pergunta: {texto}\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    )
    
    # Gerar resposta com Groq ou modelo local
    if llm == "groq" and groq_client:
        # Usar Groq API (rápido!)
        print("[IA] ⚡ Usando Groq API (Llama-3.1-70B na nuvem)...")
        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",  # Modelo maior e mais inteligente!
                messages=[
                    {"role": "system", "content": (
                        "Você é ConcursAI, assistente especializado em concursos públicos do Brasil. "
                        "Combine informações dos documentos com seu conhecimento para dar respostas completas."
                    )},
                    {"role": "user", "content": f"Documentos:\n{contexto}\n\nPergunta: {texto}"}
                ],
                temperature=0.7,
                max_tokens=512,
                top_p=0.95
            )
            resposta = completion.choices[0].message.content.strip()
            print(f"[IA] ✓ Resposta gerada pelo Groq ({len(resposta)} caracteres)")
        except Exception as e:
            print(f"[IA] ⚠️ Erro no Groq: {e}, usando fallback")
            resposta = f"Desculpe, houve um erro ao processar sua pergunta. Tente novamente."
    else:
        # Usar modelo local
        print(f"[IA] 🤖 Usando modelo local (llm={llm}, groq_client={groq_client is not None})...")
        output = llm(
            prompt, 
            max_tokens=512,
            temperature=0.7,
            top_p=0.95,
            repeat_penalty=1.1
        )
        resposta = output["choices"][0]["text"].strip()
    
    fonte = docs[0].metadata.get("source", "Desconhecido") if docs else "Nenhum documento encontrado"
    
    return resposta, fonte

def estudo_banca(banca):
    """
    Gera análise de temas mais cobrados por uma banca específica
    
    Args:
        banca: Nome da banca (ex: 'cebraspe', 'fcc', 'vunesp')
    
    Returns:
        str: Relatório de temas por disciplina
    """
    if vectordb is None:
        init_db()
    
    # Busca documentos filtrados pela banca
    try:
        docs = vectordb.as_retriever(
            search_kwargs={
                "k": 10, 
                "filter": {"banca": banca.lower()}
            }
        ).invoke("temas mais cobrados disciplinas conteúdo programático")
    except:
        # Fallback se o filtro não funcionar
        docs = vectordb.as_retriever(search_kwargs={"k": 10}).invoke(f"banca {banca} temas disciplinas")
    
    contexto = "\n\n".join([d.page_content for d in docs])
    
    prompt = (
        "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
        f"Analise o contexto abaixo e gere um relatório de estudo para a banca {banca.upper()}.\n\n"
        "FORMATO OBRIGATÓRIO:\n"
        "- Liste as principais disciplinas encontradas\n"
        "- Para cada disciplina, identifique os 3-5 temas mais frequentes\n"
        "- Estime a frequência relativa (%) de cada tema\n"
        "- Seja objetivo e prático\n\n"
        f"Contexto dos editais:\n{contexto}\n\n"
        "Gere o relatório agora:\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        f"📊 ANÁLISE DE TEMAS - BANCA {banca.upper()}\n\n"
    )
    
    output = llm(
        prompt, 
        max_tokens=600, 
        stop=["<|eot_id|>"], 
        temperature=0.1
    )
    
    return output["choices"][0]["text"].strip()

def listar_bancas():
    """
    Lista todas as bancas indexadas no banco de dados
    
    Returns:
        list: Lista de bancas únicas
    """
    if vectordb is None:
        init_db()
    
    # Tenta obter metadados únicos
    try:
        collection = vectordb._collection
        metadatas = collection.get()['metadatas']
        bancas = set()
        for meta in metadatas:
            if 'banca' in meta:
                bancas.add(meta['banca'])
        return sorted(list(bancas))
    except:
        return []

# Inicialização automática ao importar
if __name__ != "__main__":
    try:
        init_llm()
        init_db()
    except Exception as e:
        print(f"[AVISO] Inicialização parcial: {e}")
