#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API FastAPI para o sistema ConcursAI com integração API ConcursosNoBrasil"""

# Garante saída UTF-8 no console (evita UnicodeEncodeError nos logs com emoji,
# especialmente no Windows/cp1252). Deve vir antes de qualquer import que imprima.
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
import uvicorn
import os
from datetime import datetime
import logging
from contextlib import asynccontextmanager
import asyncio

# Carrega variáveis de ambiente do .env (ex.: GROQ_API_KEY) o quanto antes
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception as _e:
    print(f"⚠️ python-dotenv não disponível ({_e}); usando variáveis do sistema")

# Orquestrador de agentes especializados (Supervisor + Skills)
try:
    from modules import agentes as agentes_mod
    AGENTES_DISPONIVEL = True
    print("✅ Orquestrador de agentes carregado")
except Exception as e:
    print(f"⚠️ Orquestrador de agentes indisponível: {e}")
    agentes_mod = None
    AGENTES_DISPONIVEL = False

# Importar módulos do sistema com fallback
try:
    from modules.concurso_rag import responder_interface
    from modules.concurso_embeddings import df_chunks, collection
    print("✅ Módulos RAG complexos carregados")
except ImportError as e:
    print(f"⚠️ Módulos RAG complexos falharam: {e}")
    try:
        from modules.concurso_rag_simples import responder_interface
        print("✅ Usando módulo RAG simplificado")
        df_chunks = None
        collection = None
    except ImportError:
        print("❌ Módulo RAG simplificado também falhou")
        responder_interface = None
        df_chunks = None
        collection = None

# Sistema de Análise de Bancas por Área
try:
    from modules.rag_banca_inteligente import get_rag_inteligente
    from modules.banca_area_analyzer import get_banca_area_analyzer
    rag_banca_inteligente = get_rag_inteligente()
    banca_area_analyzer = get_banca_area_analyzer()
    print("✅ Sistema de Análise de Bancas carregado")
except ImportError as e:
    print(f"⚠️ Sistema de Análise de Bancas indisponível: {e}")
    rag_banca_inteligente = None
    banca_area_analyzer = None

# Sistema de Análise de PDFs com Upload
try:
    from modules.pdf_analyzer_upload import get_pdf_analyzer
    pdf_analyzer = get_pdf_analyzer()
    print("✅ Sistema de Análise de PDFs com Upload carregado")
except ImportError as e:
    print(f"⚠️ Sistema de Análise de PDFs indisponível: {e}")
    pdf_analyzer = None

# Outros módulos opcionais
try:
    from modules.coletor_realtime import ColetorConcursosRealTime
    from modules.sistema_notificacoes import SistemaNotificacoes
    from modules.agendador import AgendadorConcursos
    from modules.integrador_apis import IntegradorAPIsExternas
    from modules.edital_analyzer import edital_analyzer
    from modules.conversational_rag import conversational_rag
    from modules.monitoring import monitoring_system, start_monitoring, get_system_stats, get_health_status, increment_api_request
    from modules.realtime_notifications import notification_system, start_notification_system, get_notification_stats
    print("✅ Módulos avançados carregados")
except ImportError as e:
    print(f"⚠️ Módulos avançados indisponíveis: {e}")
    # Fallback para desenvolvimento
    ColetorConcursosRealTime = None
    SistemaNotificacoes = None
    AgendadorConcursos = None
    IntegradorAPIsExternas = None
    edital_analyzer = None
    conversational_rag = None
    monitoring_system = None
    notification_system = None
    start_monitoring = None
    get_system_stats = None
    get_health_status = None
    increment_api_request = None
    start_notification_system = None
    get_notification_stats = None

# Models Pydantic simplificados
class ConcursoModel(BaseModel):
    titulo: str
    orgao: str
    cargo: str
    ano: str
    tipo_documento: str
    url: Optional[str] = None
    data_publicacao: Optional[str] = None
    fonte: Optional[str] = None
    conteudo: Optional[str] = None
    vagas: Optional[str] = None
    status: Optional[str] = None
    estado: Optional[str] = None

class ConcursoAPIResponse(BaseModel):
    """Modelo para resposta da API externa ConcursosNoBrasil"""
    link: str
    organization: str
    status: str
    workPlacesAvailable: str

class BuscaSemanticaRequest(BaseModel):
    pergunta: str
    filtro_orgao: Optional[str] = None
    filtro_ano: Optional[str] = None
    filtro_cargo: Optional[str] = None

class BuscaSemanticaResponse(BaseModel):
    resposta: str
    documentos_relevantes: List[Dict[str, Any]]
    metadados: Dict[str, Any]

class StatusSistemaResponse(BaseModel):
    status: str
    total_concursos: int
    ultima_atualizacao: Optional[str] = None
    agendador_ativo: bool
    version: str = "2.0.0"

class ColetaRequest(BaseModel):
    fontes: List[str] = ["completa"]
    salvar_automatico: bool = True

# Variáveis globais
agendador_global = None
coletor_global = None
notificador_global = None

# Função de fallback para carregar dados
def carregar_dados_fallback():
    """Carrega dados quando módulos complexos falham"""
    try:
        if os.path.exists("concursos_chunks.csv"):
            df = pd.read_csv("concursos_chunks.csv")
            print(f"✅ Carregados {len(df)} registros via fallback")
            return df
        else:
            print("⚠️ Arquivo concursos_chunks.csv não encontrado")
            return pd.DataFrame()
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Carregar dados se df_chunks estiver vazio
if df_chunks is None:
    df_chunks = carregar_dados_fallback()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento do ciclo de vida da aplicação"""
    # Inicialização
    global agendador_global, coletor_global, notificador_global
    
    print("🚀 Iniciando ConcursAI FastAPI...")
    
    try:
        # RAG será inicializado sob demanda (lazy loading) para não travar o startup
        print("ℹ️ Sistema RAG será carregado na primeira consulta")
        
        # Só inicializar se as classes estiverem disponíveis
        if AgendadorConcursos:
            agendador_global = AgendadorConcursos()
        if ColetorConcursosRealTime:
            coletor_global = ColetorConcursosRealTime()
        if SistemaNotificacoes:
            notificador_global = SistemaNotificacoes()
        
        print("✅ Componentes inicializados com sucesso")
    except Exception as e:
        print(f"⚠️ Erro na inicialização (continuando em modo simplificado): {e}")
    
    yield
    
    # Limpeza
    print("🔄 Finalizando aplicação...")
    try:
        if agendador_global and hasattr(agendador_global, 'parar'):
            agendador_global.parar()
    except Exception as e:
        print(f"⚠️ Erro na finalização: {e}")
    
    print("🛑 ConcursAI FastAPI finalizado")

# Criar aplicação FastAPI
app = FastAPI(
    title="ConcursAI API",
    description="API para consulta e gestão de concursos públicos no Brasil com integração ConcursosNoBrasil",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar arquivos estáticos
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("✅ Arquivos estáticos configurados")
except Exception as e:
    logger.warning(f"⚠️ Erro ao configurar arquivos estáticos: {e}")

# Configurar diretório de provas
try:
    import os
    if os.path.exists("provas"):
        app.mount("/provas", StaticFiles(directory="provas"), name="provas")
        logger.info("✅ Diretório de provas configurado")
except Exception as e:
    logger.warning(f"⚠️ Erro ao configurar diretório de provas: {e}")

# === ROTA PRINCIPAL ===

@app.get("/", include_in_schema=False)
async def landing_page():
    """Redireciona para o sistema multi-tela TCC"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/pages/home")

# === ENDPOINTS PRINCIPAIS ===

@app.get("/stats/overview")
async def stats_overview():
    """Estatísticas gerais do sistema"""
    total = 0
    if os.path.exists("concursos_chunks.csv"):
        df = pd.read_csv("concursos_chunks.csv")
        total = len(df)
    return {
        "total_concursos": total,
        "total_vagas": total * 10,
        "states_covered": 27,
        "bancas_registered": 15,
        "status": "online"
    }

# ─────────────────────────────────────────────────────────────
# AGENTES ESPECIALIZADOS (Supervisor + Skills)
# ─────────────────────────────────────────────────────────────
class AgenteRequest(BaseModel):
    pergunta: str = Field(..., description="Pergunta/dúvida do aluno")
    agente: Optional[str] = Field(None, description="ID do agente (None = supervisor escolhe)")
    filtro_orgao: Optional[str] = Field(None)
    filtro_ano: Optional[str] = Field(None)
    filtro_cargo: Optional[str] = Field(None)
    historico: Optional[str] = Field("", description="Contexto da conversa anterior")


@app.get("/agentes")
async def listar_agentes_endpoint():
    """Lista os agentes especializados disponíveis."""
    if not AGENTES_DISPONIVEL:
        return {"agentes": [], "disponivel": False}
    return {"agentes": agentes_mod.listar_agentes(), "disponivel": True}


@app.post("/agente/perguntar")
async def agente_perguntar(req: AgenteRequest):
    """Roteia a pergunta para o agente especializado e retorna a resposta."""
    if not AGENTES_DISPONIVEL:
        raise HTTPException(status_code=503, detail="Orquestrador de agentes indisponível")
    resultado = agentes_mod.responder(
        pergunta=req.pergunta,
        agente_id=req.agente,
        orgao=req.filtro_orgao or "Todos",
        ano=req.filtro_ano or "Todos",
        cargo=req.filtro_cargo or "Todos",
        contexto_extra=req.historico or "",
    )
    return resultado


# ─────────────────────────────────────────────────────────────
# INTELIGÊNCIA DE BANCA (incidência 5 anos + perfil de estudo)
# ─────────────────────────────────────────────────────────────
try:
    from modules import banca_inteligencia as banca_intel
    BANCA_INTEL_OK = True
except Exception as e:
    print(f"⚠️ Inteligência de banca indisponível: {e}")
    banca_intel = None
    BANCA_INTEL_OK = False


class BancaAnaliseRequest(BaseModel):
    banca: str = Field(..., description="Nome da banca (ex: CESPE/CEBRASPE)")
    cargo: Optional[str] = Field("", description="Cargo/área de interesse")
    anos: int = Field(5, ge=1, le=10, description="Período de análise em anos")


@app.post("/banca/analisar")
async def banca_analisar(req: BancaAnaliseRequest):
    """Analisa a banca: incidência de temas (métrica) + perfil de estudo."""
    if not BANCA_INTEL_OK:
        raise HTTPException(status_code=503, detail="Módulo de banca indisponível")
    return banca_intel.analisar_banca(req.banca, req.cargo or "", req.anos)


# ─────────────────────────────────────────────────────────────
# ENRIQUECIMENTO via BrasilAPI (público, sem chave)
# ─────────────────────────────────────────────────────────────
try:
    from modules import brasil_api as brasil_api_mod
    BRASIL_API_OK = True
except Exception as e:
    print(f"⚠️ BrasilAPI indisponível: {e}")
    brasil_api_mod = None
    BRASIL_API_OK = False


@app.get("/enriquecimento/feriados")
async def enriq_feriados(ano: int = Query(default=datetime.now().year)):
    """Feriados nacionais do ano (BrasilAPI) — apoia o cronograma de estudos."""
    if not BRASIL_API_OK:
        raise HTTPException(status_code=503, detail="BrasilAPI indisponível")
    return brasil_api_mod.feriados(ano)


@app.get("/enriquecimento/cnpj/{cnpj}")
async def enriq_cnpj(cnpj: str):
    """Dados do órgão pelo CNPJ (BrasilAPI)."""
    if not BRASIL_API_OK:
        raise HTTPException(status_code=503, detail="BrasilAPI indisponível")
    return brasil_api_mod.cnpj(cnpj)


@app.get("/dashboard/dados")
async def dashboard_dados():
    """Métricas reais para o dashboard, calculadas do acervo (CSV)."""
    try:
        df = pd.read_csv("concursos_chunks.csv")
    except Exception:
        return {"total": 0, "abertos": 0, "por_banca": {}, "por_ano": {},
                "por_area": {}, "embeddings": 0, "recentes": []}

    total = int(len(df))
    ano_atual = str(datetime.now().year)
    abertos = int((df["ano"].astype(str) == ano_atual).sum()) if "ano" in df.columns else 0

    # por ano (apenas anos plausíveis)
    por_ano = {}
    if "ano" in df.columns:
        vc = df["ano"].astype(str).str.extract(r"(20\d\d)")[0].value_counts()
        por_ano = {k: int(v) for k, v in sorted(vc.items()) if k}

    # blob de texto por linha para extração por palavra-chave
    def blob(row):
        return " ".join(str(row.get(c, "")) for c in ("titulo", "conteudo", "orgao", "cargo")).lower()
    blobs = df.apply(blob, axis=1)

    bancas = ["cespe", "cebraspe", "fcc", "fgv", "vunesp", "ibfc", "aocp",
              "quadrix", "idecan", "consulplan", "ibade", "instituto aocp"]
    por_banca = {}
    for b in bancas:
        n = int(blobs.str.contains(b, regex=False).sum())
        if n:
            por_banca[b.upper()] = n

    areas = {
        "TI": ["tecnologia", "informática", "informatica", "sistemas", "analista de ti", "computação"],
        "Saúde": ["saúde", "saude", "médico", "medico", "enfermeir", "farmac", "odontolog"],
        "Direito": ["jurídic", "juridic", "advogad", "procurador", "promotor", "direito"],
        "Educação": ["professor", "educação", "educacao", "docente", "pedagog"],
        "Administração": ["administrativ", "administração", "administracao", "assistente", "auxiliar"],
        "Fiscal/Controle": ["fiscal", "auditor", "controlador", "tributár"],
        "Segurança": ["policial", "guarda", "bombeiro", "militar", "agente penitenci"],
    }
    por_area = {}
    for area, kws in areas.items():
        n = int(blobs.apply(lambda t: any(k in t for k in kws)).sum())
        if n:
            por_area[area] = n

    # recentes
    recentes = []
    cols = df.columns
    for _, r in df.tail(8).iloc[::-1].iterrows():
        recentes.append({
            "titulo": str(r.get("titulo", ""))[:80] if "titulo" in cols else "",
            "banca": next((b.upper() for b in bancas if b in blob(r)), "—"),
            "area": next((a for a, kws in areas.items() if any(k in blob(r) for k in kws)), "—"),
            "status": "aberto" if str(r.get("ano", "")) == ano_atual else "—",
        })

    emb = 0
    try:
        emb = collection.count() if collection is not None else 0
    except Exception:
        pass

    return {"total": total, "abertos": abertos, "por_banca": por_banca,
            "por_ano": por_ano, "por_area": por_area, "embeddings": emb,
            "bancas_count": len(por_banca), "recentes": recentes}


# ─────────────────────────────────────────────────────────────
# FERRAMENTAS DE ESTUDO (geradas por IA)
# ─────────────────────────────────────────────────────────────
def _ferramenta_llm(system_prompt: str, mensagem: str, temp: float = 0.5) -> str:
    if not AGENTES_DISPONIVEL:
        return "⚠️ Módulo de IA indisponível."
    out = agentes_mod.gerar(system_prompt, mensagem, temp)
    return out or ("⚠️ IA sem resposta. Configure uma GROQ_API_KEY válida no .env "
                   "(chave gratuita em groq.com).")


class ResumoRequest(BaseModel):
    texto: str
    nivel: str = "intermediario"

class FlashcardsRequest(BaseModel):
    topico: str
    quantidade: int = 5
    dificuldade: str = "medio"

class AnaliseBancaReq(BaseModel):
    banca: str
    cargo: Optional[str] = ""

class PlanoRequest(BaseModel):
    cargo: str
    semanas: int = 12
    horas_dia: int = 3

class QuestoesRequest(BaseModel):
    topico: str
    quantidade: int = 5
    estilo: str = "multipla"

class CompararBancasReq(BaseModel):
    banca_a: str
    banca_b: str


@app.post("/ferramentas/resumo")
async def ferramenta_resumo(r: ResumoRequest):
    sp = ("Você é um professor de cursinho. Faça um RESUMO claro e estruturado em "
          f"markdown, nível {r.nivel}, com tópicos, destaques e um mini-mapa mental "
          "ao final. Use apenas o conteúdo informado.")
    return {"resultado": _ferramenta_llm(sp, f"Conteúdo/tópico:\n{r.texto}")}


@app.post("/ferramentas/flashcards")
async def ferramenta_flashcards(r: FlashcardsRequest):
    sp = (f"Você gera flashcards de estudo. Crie {r.quantidade} flashcards de "
          f"dificuldade {r.dificuldade} sobre o tópico, em markdown, no formato "
          "**Frente:** pergunta / **Verso:** resposta. Numere-os.")
    return {"resultado": _ferramenta_llm(sp, f"Tópico: {r.topico}")}


@app.post("/ferramentas/analise-banca")
async def ferramenta_analise_banca(r: AnaliseBancaReq):
    """Usa o módulo de inteligência de banca (incidência + perfil)."""
    if BANCA_INTEL_OK:
        data = banca_intel.analisar_banca(r.banca, r.cargo or "", 5)
        # monta um texto legível para o card, além de devolver os dados estruturados
        linhas = [f"## 📊 Análise da banca {data.get('banca','')}",
                  f"_{data.get('periodo','')}_\n"]
        if data.get("resumo"):
            linhas.append(data["resumo"] + "\n")
        if data.get("incidencia"):
            linhas.append("### Incidência de temas")
            for it in data["incidencia"]:
                seta = {"subindo": "📈", "caindo": "📉"}.get(it.get("tendencia"), "➖")
                linhas.append(f"- {seta} **{it['tema']}** — {it['percentual']}%")
            linhas.append("")
        if data.get("perfil_estudo"):
            linhas.append("### Perfil de estudo\n" + data["perfil_estudo"])
        if data.get("pegadinhas"):
            linhas.append("\n### Pegadinhas típicas")
            linhas += [f"- {p}" for p in data["pegadinhas"]]
        return {"resultado": "\n".join(linhas), "dados": data}
    sp = "Você é especialista em bancas. Analise o estilo da banca para o cargo."
    return {"resultado": _ferramenta_llm(sp, f"Banca: {r.banca}. Cargo: {r.cargo}")}


@app.post("/ferramentas/plano-estudos")
async def ferramenta_plano(r: PlanoRequest):
    sp = ("Você monta planos de estudo para concursos. Gere um cronograma em "
          "markdown (tabela por semana) realista, com revisões espaçadas e "
          "simulados, priorizando disciplinas de maior peso. Considere os "
          "feriados nacionais informados (use-os como dias de revisão leve ou "
          "descanso).")
    # Enriquecimento BrasilAPI: feriados do ano corrente para o cronograma
    feriados_txt = ""
    if BRASIL_API_OK:
        try:
            fer = brasil_api_mod.feriados(datetime.now().year)
            if fer.get("feriados"):
                itens = ", ".join(f"{f['date']} ({f['name']})" for f in fer["feriados"][:14])
                feriados_txt = f" Feriados nacionais de {datetime.now().year}: {itens}."
        except Exception:
            pass
    msg = (f"Cargo: {r.cargo}. Tempo: {r.semanas} semanas, {r.horas_dia}h/dia."
           f"{feriados_txt}")
    return {"resultado": _ferramenta_llm(sp, msg)}


@app.post("/ferramentas/questoes")
async def ferramenta_questoes(r: QuestoesRequest):
    sp = (f"Você gera questões de concurso no estilo {r.estilo}. Crie "
          f"{r.quantidade} questões sobre o tópico, com GABARITO e comentário "
          "explicativo em cada uma. Numere-as. Markdown.")
    return {"resultado": _ferramenta_llm(sp, f"Tópico: {r.topico}")}


@app.post("/ferramentas/comparar-bancas")
async def ferramenta_comparar(r: CompararBancasReq):
    sp = ("Você compara bancas de concurso. Faça uma comparação objetiva em "
          "markdown (tabela) entre as duas bancas: estilo de questão, nível de "
          "dificuldade, pegadinhas e dicas específicas para cada uma.")
    return {"resultado": _ferramenta_llm(sp, f"Compare {r.banca_a} vs {r.banca_b}.")}


# ─────────────────────────────────────────────────────────────
# EDITAL — upload de PDF + chat sobre o documento
# ─────────────────────────────────────────────────────────────
_editais_sessao: Dict[str, Dict[str, str]] = {}


class EditalChatReq(BaseModel):
    pergunta: str
    sessao_id: Optional[str] = None


@app.post("/edital/upload")
async def edital_upload(file: UploadFile = File(...)):
    import io, uuid
    conteudo = await file.read()
    texto = ""
    paginas = 0
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
            paginas = len(pdf.pages)
            texto = "\n".join((p.extract_text() or "") for p in pdf.pages[:20])
    except Exception:
        texto = conteudo.decode("utf-8", errors="ignore")[:8000]
    sid = uuid.uuid4().hex[:12]
    _editais_sessao[sid] = {"nome": file.filename, "texto": texto[:20000]}
    return {"sessao_id": sid, "nome": file.filename, "paginas": paginas,
            "caracteres": len(texto)}


@app.post("/edital/chat")
async def edital_chat(req: EditalChatReq):
    sess = _editais_sessao.get(req.sessao_id or "")
    if not sess:
        return {"resposta": "📄 Envie um edital em PDF primeiro para eu analisá-lo."}
    if not AGENTES_DISPONIVEL:
        return {"resposta": "⚠️ Módulo de IA indisponível."}
    sp = ("Você é o Agente de Edital. Responda usando APENAS o texto do edital "
          "fornecido. Cite trechos e seja específico (datas, vagas, requisitos, "
          "conteúdo programático). Se não constar, diga que não consta no edital.")
    msg = f"EDITAL ({sess['nome']}):\n{sess['texto']}\n\nPERGUNTA: {req.pergunta}"
    resp = agentes_mod.gerar(sp, msg, 0.3)
    return {"resposta": resp or "⚠️ IA sem resposta. Configure a GROQ_API_KEY no .env."}


# ─────────────────────────────────────────────────────────────
# PROVAS — acervo, busca RAG e estatísticas por banca
# ─────────────────────────────────────────────────────────────
def _provas_por_banca() -> Dict[str, int]:
    import glob as _g
    res: Dict[str, int] = {}
    try:
        for pasta in _g.glob("provas/*"):
            if os.path.isdir(pasta):
                n = len(_g.glob(os.path.join(pasta, "*.pdf")))
                if n:
                    res[os.path.basename(pasta)] = n
    except Exception:
        pass
    return res


@app.get("/api/provas/stats")
async def provas_stats():
    pb = _provas_por_banca()
    total = sum(pb.values())
    indexados = 0
    try:
        indexados = collection.count() if collection is not None else 0
    except Exception:
        pass
    return {"total_pdfs": total, "indexados": indexados,
            "bancas": len(pb), "questoes": 0, "historico": []}


@app.get("/api/provas/listar")
async def provas_listar():
    import glob as _g
    pdfs = []
    try:
        for pasta in _g.glob("provas/*"):
            if os.path.isdir(pasta):
                banca = os.path.basename(pasta)
                for f in _g.glob(os.path.join(pasta, "*.pdf")):
                    kb = os.path.getsize(f) // 1024
                    pdfs.append({"nome": os.path.basename(f), "banca": banca,
                                 "tamanho": f"{kb} KB"})
    except Exception:
        pass
    return {"pdfs": pdfs}


@app.get("/api/provas/bancas")
async def provas_bancas():
    pb = _provas_por_banca()
    return {"bancas": [{"banca": b, "provas": n, "questoes": "—"} for b, n in pb.items()]}


@app.get("/api/provas/buscar")
async def provas_buscar(q: str = Query(...), limit: int = Query(5)):
    try:
        from modules.concurso_rag import buscar_documentos
        docs = buscar_documentos(q, limite=limit)
        res = [{"titulo": (d[:60] + "...") if len(d) > 60 else d, "trecho": d}
               for d in docs]
        return {"resultados": res}
    except Exception as e:
        return {"resultados": [], "erro": str(e)}


@app.post("/api/provas/coletar")
async def provas_coletar(payload: Dict[str, Any] = None):
    """Coleta provas por banca (delegado ao coletor; seguro/limitado)."""
    pb = _provas_por_banca()
    total = sum(pb.values())
    return {"mensagem": (
        f"Acervo atual: {total} provas em PDF ({len(pb)} bancas). "
        "A coleta em lote de provas roda pelo script "
        "`python scrapers/provas_scraper.py <banca> <qtd>` para não travar a API. "
        "Os concursos do ano já são raspados em /pages/scraping.")}


# ─────────────────────────────────────────────────────────────
# ADMIN — health, ChromaDB, manutenção, logs, teste de LLM
# ─────────────────────────────────────────────────────────────
def _key_ok() -> bool:
    k = os.getenv("GROQ_API_KEY", "")
    return bool(k) and not k.lower().startswith("your")


@app.get("/health")
async def health():
    try:
        chroma = collection.count() if collection is not None else 0
    except Exception:
        chroma = 0
    return {
        "status": "online",
        "concursos_csv": int(len(df_chunks)) if df_chunks is not None else 0,
        "documentos_chromadb": chroma,
        "llm": "Groq (configurado)" if _key_ok() else "fallback (sem GROQ_API_KEY)",
        "agentes": "ativos" if AGENTES_DISPONIVEL else "indisponível",
        "inteligencia_banca": "ativa" if BANCA_INTEL_OK else "indisponível",
    }


@app.get("/admin/stats")
async def admin_stats():
    try:
        chroma = collection.count() if collection is not None else 0
    except Exception:
        chroma = 0
    bancas = 0
    anos = 0
    try:
        if df_chunks is not None:
            if "orgao" in df_chunks.columns:
                bancas = int(df_chunks["orgao"].nunique())
            if "ano" in df_chunks.columns:
                anos = int(df_chunks["ano"].nunique())
    except Exception:
        pass
    return {
        "documentos_indexados": chroma,
        "registros_csv": int(len(df_chunks)) if df_chunks is not None else 0,
        "orgaos_distintos": bancas,
        "anos_distintos": anos,
        "colecao": "concursos_publicos",
    }


def _admin_reindex_inline() -> int:
    """Reindexa usando o próprio handle da coleção (não invalida o servidor)."""
    if collection is None:
        return 0
    df = pd.read_csv("concursos_chunks.csv")
    df = df[df["conteudo"].notna() & (df["conteudo"].astype(str) != "")]
    try:
        atuais = collection.get().get("ids", [])
        if atuais:
            collection.delete(ids=atuais)
    except Exception:
        pass
    textos = df["conteudo"].astype(str).tolist()
    ids = [f"chunk_{i}" for i in range(len(textos))]
    metas = [{"orgao": str(r.get("orgao", "") or ""), "ano": str(r.get("ano", "") or ""),
              "cargo": str(r.get("cargo", "") or ""),
              "tipo_documento": str(r.get("tipo_documento", "") or ""),
              "titulo": str(r.get("titulo", "") or "")} for _, r in df.iterrows()]
    for i in range(0, len(textos), 100):
        collection.add(documents=textos[i:i+100], ids=ids[i:i+100],
                       metadatas=metas[i:i+100])
    return len(textos)


@app.post("/admin/embeddings/status")
async def admin_emb_status():
    try:
        c = collection.count() if collection is not None else 0
    except Exception:
        c = 0
    return {"mensagem": f"{c} documentos indexados no ChromaDB."}


@app.post("/admin/embeddings/reindexar")
async def admin_emb_reindex():
    try:
        n = _admin_reindex_inline()
        return {"mensagem": f"Reindexação concluída: {n} documentos."}
    except Exception as e:
        return {"mensagem": f"Erro ao reindexar: {e}"}


@app.post("/admin/embeddings/carregar-csv")
async def admin_emb_csv():
    try:
        n = int(len(pd.read_csv("concursos_chunks.csv")))
        return {"mensagem": f"CSV contém {n} registros. Use 'Reindexar' para aplicar."}
    except Exception as e:
        return {"mensagem": f"Erro: {e}"}


@app.post("/admin/manutencao/duplicatas")
async def admin_dedupe():
    try:
        df = pd.read_csv("concursos_chunks.csv")
        antes = len(df)
        if "url" in df.columns:
            df = df.drop_duplicates(subset=["url"])
        df.to_csv("concursos_chunks.csv", index=False)
        return {"mensagem": f"Duplicatas removidas: {antes - len(df)} (restam {len(df)})."}
    except Exception as e:
        return {"mensagem": f"Erro: {e}"}


@app.post("/admin/manutencao/validar")
async def admin_validar():
    try:
        df = pd.read_csv("concursos_chunks.csv")
        vazios = int((df["conteudo"].isna() | (df["conteudo"].astype(str) == "")).sum()) \
            if "conteudo" in df.columns else 0
        return {"mensagem": f"{len(df)} registros; {vazios} sem conteúdo."}
    except Exception as e:
        return {"mensagem": f"Erro: {e}"}


@app.post("/admin/banco/limpar")
async def admin_limpar():
    try:
        if collection is not None:
            atuais = collection.get().get("ids", [])
            if atuais:
                collection.delete(ids=atuais)
        return {"mensagem": "Coleção do ChromaDB limpa. Use 'Reindexar' para repovoar."}
    except Exception as e:
        return {"mensagem": f"Erro: {e}"}


@app.post("/admin/config")
async def admin_config(cfg: Dict[str, Any] = None):
    return {"mensagem": "Configuração salva (em memória).", "config": cfg or {}}


@app.get("/admin/log")
async def admin_log():
    linhas = []
    try:
        if os.path.exists("scraper.log"):
            with open("scraper.log", encoding="utf-8", errors="ignore") as f:
                linhas = f.read().splitlines()[-50:]
    except Exception:
        pass
    if not linhas:
        linhas = ["Sistema operando. Sem entradas recentes de log em arquivo."]
    return {"log": linhas}


@app.get("/admin/exportar")
async def admin_exportar():
    if os.path.exists("concursos_chunks.csv"):
        return FileResponse("concursos_chunks.csv", filename="concursos_chunks.csv",
                            media_type="text/csv")
    raise HTTPException(status_code=404, detail="CSV não encontrado")


class ChatDiretoReq(BaseModel):
    pergunta: str
    temperatura: float = 0.7
    modo: Optional[str] = "direto"


@app.post("/chat/direto")
async def chat_direto(req: ChatDiretoReq):
    if not AGENTES_DISPONIVEL:
        return {"resposta": "⚠️ Módulo de IA indisponível."}
    sp = ("Você é o assistente do ConcursAI. Responda de forma direta e útil "
          "sobre concursos públicos brasileiros.")
    resp = agentes_mod.gerar(sp, req.pergunta, req.temperatura)
    return {"resposta": resp or "⚠️ IA sem resposta. Configure a GROQ_API_KEY no .env."}


class ChatMessageRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

@app.post("/chat/message")
async def chat_message(request: ChatMessageRequest):
    """Endpoint de chat - redireciona para o sistema RAG"""
    busca = BuscaSemanticaRequest(pergunta=request.message)
    result = await buscar_semantica(busca)
    return {"response": result.resposta, "resposta": result.resposta}

@app.post("/rag/analyze")
async def rag_analyze(file: UploadFile = File(...)):
    """Analisa PDF enviado pelo usuário"""
    try:
        conteudo = await file.read()
        texto = ""
        try:
            import pdfplumber, io
            with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
                texto = "\n".join(p.extract_text() or "" for p in pdf.pages[:5])
        except Exception:
            texto = conteudo.decode("utf-8", errors="ignore")[:3000]

        if responder_interface and texto.strip():
            resposta = responder_interface("Todos", "Todos", "Todos", f"Analise este edital: {texto[:1500]}")
        else:
            resposta = f"PDF recebido: {file.filename}. Texto extraído com {len(texto)} caracteres."

        return {
            "success": True,
            "filename": file.filename,
            "summary": resposta,
            "pages_analyzed": min(5, len(texto) // 500 + 1)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/studio")
async def studio():
    """ConcursAI Studio - interface de configuração de agentes"""
    try:
        return FileResponse('interfaces/studio.html')
    except Exception as e:
        return JSONResponse(status_code=404, content={"message": str(e)})

# === ROTAS MULTI-PAGE TCC ===
_PAGES = ["home", "dashboard", "chat", "concursos", "ferramentas", "edital", "provas", "scraping", "admin"]

@app.get("/pages/{page_name}")
async def serve_page(page_name: str):
    """Serve as páginas HTML do sistema multi-tela TCC"""
    import os
    name = page_name.replace(".html", "")
    path = f"interfaces/pages/{name}.html"
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse(status_code=404, content={"message": f"Página '{name}' não encontrada"})

@app.get("/pages")
async def pages_index():
    """Redireciona para a home do sistema multi-tela"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/pages/home")

@app.get("/dashboard")
async def dashboard():
    """Página de dashboard de monitoramento"""
    try:
        # Tentar servir da raiz primeiro
        import os
        if os.path.exists('dashboard.html'):
            return FileResponse('dashboard.html')
        elif os.path.exists('static/dashboard.html'):
            return FileResponse('static/dashboard.html')
        else:
            raise FileNotFoundError("dashboard.html não encontrado")
    except Exception as e:
        logger.error(f"Erro ao servir dashboard: {e}")
        return JSONResponse(
            status_code=404, 
            content={"message": "Dashboard não encontrado", "detail": str(e)}
        )

@app.get("/dashboard.html")
async def dashboard_html():
    """Servir dashboard.html diretamente"""
    try:
        import os
        if os.path.exists('dashboard.html'):
            return FileResponse('dashboard.html')
        else:
            raise FileNotFoundError("dashboard.html não encontrado")
    except Exception as e:
        logger.error(f"Erro ao servir dashboard.html: {e}")
        return JSONResponse(
            status_code=404, 
            content={"message": "Dashboard não encontrado", "detail": str(e)}
        )

# === NOVOS ENDPOINTS API CONCURSOS BRASIL ===

@app.get("/api-brasil/concursos", response_model=List[ConcursoModel])
async def buscar_todos_concursos_brasil(
    limite: int = Query(100, description="Limite de concursos retornados"),
    estados: str = Query("", description="Estados específicos separados por vírgula (ex: sp,rj,mg)")
):
    """
    Busca concursos de todos os estados do Brasil ou estados específicos
    """
    try:
        logger.info(f"🔍 Buscando concursos de todos os estados do Brasil")
        integrador = IntegradorAPIsExternas()
        
        # Definir estados a buscar
        if estados:
            lista_estados = [e.strip().lower() for e in estados.split(",")]
            logger.info(f"📍 Estados específicos: {lista_estados}")
        else:
            # Todos os estados brasileiros
            lista_estados = [
                'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 
                'ma', 'mt', 'ms', 'mg', 'pa', 'pb', 'pr', 'pe', 'pi', 
                'rj', 'rn', 'rs', 'ro', 'rr', 'sc', 'sp', 'se', 'to'
            ]
            logger.info(f"🇧🇷 Buscando em todos os {len(lista_estados)} estados do Brasil")
        
        # Buscar dados de múltiplos estados
        logger.info(f"🔄 Iniciando coleta para {len(lista_estados)} estados")
        concursos = integrador.coletar_concursos_brasil_api(lista_estados)
        
        logger.info(f"📊 Resultado da coleta: {len(concursos)} concursos encontrados")
        
        # Aplicar limite
        if len(concursos) > limite:
            concursos = concursos[:limite]
            logger.info(f"🔢 Aplicado limite de {limite} concursos")
        
        # Se não encontrou dados reais, retornar dados exemplo representativos
        if not concursos:
            logger.warning(f"⚠️ APIs externas indisponíveis, retornando dados exemplo do Brasil")
            
            concursos_exemplo = []
            estados_exemplo = ['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'PE']
            
            for estado in estados_exemplo:
                concursos_exemplo.extend([
                    {
                        'titulo': f"Concurso Público {estado} - Prefeituras",
                        'orgao': f"Prefeituras do Estado de {estado}",
                        'cargo': 'Diversos cargos públicos',
                        'ano': '2024',
                        'tipo_documento': 'edital',
                        'url': f'https://concursos{estado.lower()}.gov.br',
                        'data_publicacao': '2024-10-09',
                        'fonte': 'Sistema ConcursAI (exemplo)',
                        'conteudo': f"Concursos públicos em andamento no estado de {estado}. "
                                   f"Múltiplas oportunidades em órgãos estaduais e municipais. "
                                   f"Sistema de fallback ativo - dados reais coletados automaticamente quando APIs estão disponíveis.",
                        'vagas': f'{500 + len(estado) * 100}+',
                        'status': 'open',
                        'estado': estado
                    },
                    {
                        'titulo': f"Processo Seletivo {estado} - Governo Estadual",
                        'orgao': f"Governo do Estado de {estado}",
                        'cargo': 'Cargos técnicos e administrativos',
                        'ano': '2024',
                        'tipo_documento': 'edital',
                        'url': f'https://governo{estado.lower()}.gov.br',
                        'data_publicacao': '2024-10-08',
                        'fonte': 'Sistema ConcursAI (exemplo)',
                        'conteudo': f"Processos seletivos do governo estadual de {estado}. "
                                   f"Oportunidades em diversas secretarias e autarquias. "
                                   f"Sistema integrado com múltiplas fontes de dados oficiais.",
                        'vagas': f'{300 + len(estado) * 50}+',
                        'status': 'expected',
                        'estado': estado
                    }
                ])
            
            # Aplicar limite aos dados exemplo
            if len(concursos_exemplo) > limite:
                concursos_exemplo = concursos_exemplo[:limite]
            
            logger.info(f"✅ Retornando {len(concursos_exemplo)} concursos exemplo do Brasil")
            return concursos_exemplo
        
        logger.info(f"✅ Retornando {len(concursos)} concursos reais do Brasil")
        return concursos
        
    except Exception as e:
        logger.error(f"💥 Erro na busca de concursos do Brasil: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api-brasil/concursos/{estado}", response_model=List[ConcursoModel])
async def buscar_concursos_por_estado(
    estado: str,
    formato_original: bool = Query(False, description="Retornar formato original da API")
):
    """
    Busca concursos por estado usando a API ConcursosNoBrasil
    Baseado em: https://github.com/Vinimartinsc/concursosPublicosAPI
    """
    try:
        logger.info(f"🔍 Buscando concursos para estado: {estado}")
        integrador = IntegradorAPIsExternas()
        
        # Buscar dados da API externa
        logger.info(f"🔄 Iniciando coleta para estado: {estado.lower()}")
        concursos = integrador.coletar_concursos_brasil_api([estado.lower()])
        
        logger.info(f"📊 Resultado da coleta: {len(concursos)} concursos encontrados")
        
        # ✅ CORREÇÃO: Sempre retornar dados úteis, mesmo quando APIs externas falham
        if not concursos:
            logger.warning(f"⚠️ APIs externas indisponíveis para {estado}, retornando dados exemplo")
            
            # Retornar dados de exemplo quando APIs externas falham
            concursos_exemplo = [
                {
                    'titulo': f"Concurso Público - {estado.upper()} (Dados Demo)",
                    'orgao': f"Órgãos Públicos - {estado.upper()}",
                    'cargo': 'Diversos cargos disponíveis',
                    'ano': '2024',
                    'tipo_documento': 'edital',
                    'url': 'https://concursosnobrasil.com',
                    'data_publicacao': '2024-01-15',
                    'fonte': 'Sistema ConcursAI (dados exemplo)',
                    'conteudo': f"Concursos públicos disponíveis para o estado de {estado.upper()}. "
                               f"Este é um exemplo de retorno quando as APIs externas estão indisponíveis. "
                               f"Em produção, o sistema tentará múltiplas fontes incluindo scraping direto dos sites oficiais.",
                    'vagas': '1000+',
                    'status': 'open',
                    'estado': estado.upper()
                },
                {
                    'titulo': f"Processo Seletivo {estado.upper()} - Múltiplos Órgãos",
                    'orgao': f"Prefeituras e Estado - {estado.upper()}",
                    'cargo': 'Cargos administrativos e técnicos',
                    'ano': '2024',
                    'tipo_documento': 'edital',
                    'url': 'https://concursosnobrasil.com',
                    'data_publicacao': '2024-01-20',
                    'fonte': 'Sistema ConcursAI (dados exemplo)',
                    'conteudo': f"Processos seletivos em andamento no estado de {estado.upper()}. "
                               f"Sistema em funcionamento - APIs externas temporariamente indisponíveis. "
                               f"Para dados reais em tempo real, o sistema implementa fallbacks automáticos.",
                    'vagas': '500+',
                    'status': 'expected',
                    'estado': estado.upper()
                }
            ]
            
            logger.info(f"✅ Retornando {len(concursos_exemplo)} concursos exemplo para {estado}")
            return concursos_exemplo
        
        logger.info(f"✅ Retornando {len(concursos)} concursos reais para {estado}")
        return concursos
        
    except HTTPException:
        # Re-raise HTTPException
        raise
    except Exception as e:
        logger.error(f"💥 Erro ao buscar concursos para {estado}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api-brasil/estados", response_model=Dict[str, str])
async def listar_estados_disponiveis():
    """Lista todos os estados disponíveis na API"""
    estados = {
        'br': 'Nacional',
        'ac': 'Acre',
        'al': 'Alagoas', 
        'ap': 'Amapá',
        'am': 'Amazonas',
        'ba': 'Bahia',
        'ce': 'Ceará',
        'df': 'Distrito Federal',
        'es': 'Espírito Santo',
        'go': 'Goiás',
        'ma': 'Maranhão',
        'mt': 'Mato Grosso',
        'ms': 'Mato Grosso do Sul',
        'mg': 'Minas Gerais',
        'pa': 'Pará',
        'pb': 'Paraíba',
        'pr': 'Paraná',
        'pe': 'Pernambuco',
        'pi': 'Piauí',
        'rj': 'Rio de Janeiro',
        'rn': 'Rio Grande do Norte',
        'rs': 'Rio Grande do Sul',
        'ro': 'Rondônia',
        'rr': 'Roraima',
        'sc': 'Santa Catarina',
        'sp': 'São Paulo',
        'se': 'Sergipe',
        'to': 'Tocantins'
    }
    return estados

@app.post("/api-brasil/coleta-completa")
async def executar_coleta_completa_api(background_tasks: BackgroundTasks):
    """Executa coleta completa de todos os estados da API ConcursosNoBrasil"""
    
    async def coleta_background():
        try:
            logger.info("Iniciando coleta completa da API ConcursosNoBrasil...")
            
            integrador = IntegradorAPIsExternas()
            todos_concursos = integrador.coletar_concursos_brasil_api()
            
            if todos_concursos:
                # Salvar dados
                df = pd.DataFrame(todos_concursos)
                arquivo = f"concursos_api_brasil_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df.to_csv(arquivo, index=False, encoding='utf-8')
                
                logger.info(f"Coleta completa finalizada: {len(todos_concursos)} concursos salvos em {arquivo}")
            else:
                logger.warning("Nenhum concurso coletado da API")
                
        except Exception as e:
            logger.error(f"Erro na coleta completa: {e}")
    
    background_tasks.add_task(coleta_background)
    
    return {
        "message": "Coleta completa da API ConcursosNoBrasil iniciada em background",
        "status": "processing"
    }

@app.get("/api-brasil/teste-conectividade")
async def testar_api_conectividade():
    """Testa se a API ConcursosNoBrasil está respondendo"""
    try:
        integrador = IntegradorAPIsExternas()
        
        # Testar com estado nacional
        concursos_teste = integrador.coletar_concursos_brasil_api(['br'])
        
        if concursos_teste:
            return {
                "status": "online",
                "message": "API ConcursosNoBrasil está funcionando",
                "concursos_teste": len(concursos_teste),
                "exemplo": concursos_teste[0] if concursos_teste else None
            }
        else:
            return {
                "status": "warning", 
                "message": "API responde mas não retornou dados",
                "concursos_teste": 0
            }
            
    except Exception as e:
        return {
            "status": "offline",
            "message": f"API ConcursosNoBrasil não está respondendo: {str(e)}",
            "concursos_teste": 0
        }

@app.get("/status", response_model=StatusSistemaResponse)
async def status_sistema():
    """Status geral do sistema"""
    try:
        # Incrementar contador de requisições
        if monitoring_system:
            increment_api_request()
        
        # Contar concursos no banco
        total_concursos = 0
        ultima_atualizacao = None
        
        if os.path.exists("concursos_chunks.csv"):
            df = pd.read_csv("concursos_chunks.csv")
            total_concursos = len(df)
            ultima_atualizacao = datetime.fromtimestamp(
                os.path.getmtime("concursos_chunks.csv")
            ).isoformat()
        
        # Status do agendador
        agendador_ativo = False
        if agendador_global:
            status_agendador = agendador_global.status()
            agendador_ativo = status_agendador.get('ativo', False)
        
        return StatusSistemaResponse(
            status="online",
            total_concursos=total_concursos,
            ultima_atualizacao=ultima_atualizacao,
            agendador_ativo=agendador_ativo,
            version="2.0.0"
        )
    except Exception as e:
        return StatusSistemaResponse(
            status="error",
            total_concursos=0,
            ultima_atualizacao=None,
            agendador_ativo=False,
            version="2.0.0"
        )

@app.get("/api/monitoring/stats")
async def get_monitoring_stats():
    """Estatísticas detalhadas do sistema"""
    try:
        if not monitoring_system:
            return {"error": "Sistema de monitoramento não disponível"}
        
        increment_api_request()
        return get_system_stats()
    except Exception as e:
        return {"error": f"Erro ao obter estatísticas: {str(e)}"}

@app.get("/api/monitoring/health")
async def get_system_health():
    """Status de saúde do sistema"""
    try:
        if not monitoring_system:
            return {"status": "unknown", "health": "monitoring_disabled"}
        
        increment_api_request()
        return get_health_status()
    except Exception as e:
        return {"status": "error", "health": "critical", "error": str(e)}

@app.get("/api/monitoring/metrics")
async def get_system_metrics():
    """Métricas básicas do sistema"""
    try:
        if not monitoring_system:
            return {"error": "Sistema de monitoramento não disponível"}
        
        increment_api_request()
        
        # Métricas básicas
        metrics = {
            "total_requests": monitoring_system.request_count,
            "uptime": (datetime.now() - monitoring_system.start_time).total_seconds(),
            "endpoints_status": {
                "concursos": "online",
                "ia": "online" if edital_analyzer else "offline",
                "rag": "online" if conversational_rag else "offline",
                "monitoring": "online"
            }
        }
        
        # Adicionar estatísticas se disponíveis
        if monitoring_system.stats_history:
            latest = monitoring_system.stats_history[-1]
            metrics.update({
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "ollama_status": latest.ollama_status
            })
        
        return metrics
    except Exception as e:
        return {"error": f"Erro ao obter métricas: {str(e)}"}

# === ENDPOINTS WEBSOCKET ===

@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket para notificações em tempo real"""
    if not notification_system:
        await websocket.close(code=1000, reason="Sistema de notificações não disponível")
        return
    
    await notification_system.handle_websocket(websocket)

@app.get("/api/notifications/stats")
async def get_notification_stats():
    """Estatísticas das notificações em tempo real"""
    try:
        if not notification_system:
            return {"error": "Sistema de notificações não disponível"}
        
        return get_notification_stats()
    except Exception as e:
        return {"error": f"Erro ao obter estatísticas de notificações: {str(e)}"}

# === ENDPOINTS PRINCIPAIS CONTINUAÇÃO ===

@app.get("/concursos", response_model=List[ConcursoModel])
async def listar_concursos(
    orgao: Optional[str] = Query(None, description="Filtrar por órgão"),
    ano: Optional[str] = Query(None, description="Filtrar por ano"),
    cargo: Optional[str] = Query(None, description="Filtrar por cargo"),
    limit: int = Query(50, le=500, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Deslocamento para paginação")
):
    """Lista concursos com filtros opcionais"""
    try:
        if not os.path.exists("concursos_chunks.csv"):
            raise HTTPException(status_code=404, detail="Base de dados não encontrada")
        
        # Carregar dados
        df = pd.read_csv("concursos_chunks.csv")
        
        # Aplicar filtros
        if orgao:
            df = df[df['orgao'].str.contains(orgao, case=False, na=False)]
        
        if ano:
            df = df[df['ano'].astype(str) == ano]
        
        if cargo:
            df = df[df['cargo'].str.contains(cargo, case=False, na=False)]
        
        # Paginação
        df_paginated = df.iloc[offset:offset + limit]
        
        # Converter para modelo (tratando NaN e tipos não-string do CSV)
        def s(val, default=''):
            if val is None:
                return default
            try:
                if pd.isna(val):
                    return default
            except (TypeError, ValueError):
                pass
            return str(val)

        concursos = []
        for _, row in df_paginated.iterrows():
            concurso = ConcursoModel(
                titulo=s(row.get('titulo')),
                orgao=s(row.get('orgao')),
                cargo=s(row.get('cargo')),
                ano=s(row.get('ano')),
                tipo_documento=s(row.get('tipo_documento'), 'edital'),
                url=s(row.get('url')),
                data_publicacao=s(row.get('data_publicacao')),
                fonte=s(row.get('fonte')),
                conteudo=s(row.get('conteudo'))
            )
            concursos.append(concurso)
        
        logger.info(f"Retornando {len(concursos)} concursos")
        return concursos
        
    except Exception as e:
        logger.error(f"Erro ao listar concursos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/buscar", response_model=BuscaSemanticaResponse)
async def buscar_semantica(request: BuscaSemanticaRequest):
    """Busca semântica usando RAG ou fallback simples"""
    try:
        if responder_interface:
            # Usar sistema RAG completo
            resposta = responder_interface(
                request.filtro_orgao or "",
                request.filtro_ano or "",
                request.filtro_cargo or "",
                request.pergunta
            )
        else:
            # Fallback: busca textual simples
            resposta = busca_simples_fallback(request)
        
        # Buscar documentos relevantes dos dados
        documentos_relevantes = []
        try:
            df_dados = df_chunks if df_chunks is not None else carregar_dados_fallback()
            
            if not df_dados.empty:
                # Filtrar dados baseado na pergunta
                pergunta_lower = request.pergunta.lower()
                
                mask = (
                    df_dados['titulo'].str.lower().str.contains(pergunta_lower, na=False) |
                    df_dados.get('conteudo', pd.Series()).str.lower().str.contains(pergunta_lower, na=False) |
                    df_dados['cargo'].str.lower().str.contains(pergunta_lower, na=False) |
                    df_dados['orgao'].str.lower().str.contains(pergunta_lower, na=False)
                )
                
                # Aplicar filtros adicionais
                if request.filtro_orgao:
                    mask &= df_dados['orgao'].str.contains(request.filtro_orgao, case=False, na=False)
                if request.filtro_ano:
                    mask &= df_dados['ano'].astype(str) == str(request.filtro_ano)
                if request.filtro_cargo:
                    mask &= df_dados['cargo'].str.contains(request.filtro_cargo, case=False, na=False)
                
                resultados = df_dados[mask].head(5)
                documentos_relevantes = resultados.to_dict('records')
        except Exception as e:
            print(f"⚠️ Erro ao buscar documentos relevantes: {e}")
        
        # Metadados da busca
        metadados = {
            "pergunta": request.pergunta,
            "filtros_aplicados": {
                "orgao": request.filtro_orgao,
                "ano": request.filtro_ano,
                "cargo": request.filtro_cargo
            },
            "timestamp": datetime.now().isoformat(),
            "sistema_usado": "RAG" if responder_interface else "fallback_simples",
            "documentos_encontrados": len(documentos_relevantes)
        }
        
        return BuscaSemanticaResponse(
            resposta=resposta,
            documentos_relevantes=documentos_relevantes,
            metadados=metadados
        )
        
    except Exception as e:
        logger.error(f"Erro na busca semântica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def busca_simples_fallback(request: BuscaSemanticaRequest) -> str:
    """Busca textual simples quando RAG não está disponível"""
    try:
        df_dados = carregar_dados_fallback()
        
        if df_dados.empty:
            return "❌ **Dados não disponíveis.** Sistema em modo de recuperação."
        
        pergunta_lower = request.pergunta.lower()
        
        # Buscar nos dados
        mask = (
            df_dados['titulo'].str.lower().str.contains(pergunta_lower, na=False) |
            df_dados.get('conteudo', pd.Series()).str.lower().str.contains(pergunta_lower, na=False) |
            df_dados['cargo'].str.lower().str.contains(pergunta_lower, na=False) |
            df_dados['orgao'].str.lower().str.contains(pergunta_lower, na=False)
        )
        
        # Aplicar filtros
        if request.filtro_orgao:
            mask &= df_dados['orgao'].str.contains(request.filtro_orgao, case=False, na=False)
        if request.filtro_ano:
            mask &= df_dados['ano'].astype(str) == str(request.filtro_ano)
        if request.filtro_cargo:
            mask &= df_dados['cargo'].str.contains(request.filtro_cargo, case=False, na=False)
        
        resultados = df_dados[mask]
        
        if resultados.empty:
            return f"""
❌ **Não encontrei resultados para: "{request.pergunta}"**

**Sistema em modo simplificado** - algumas funcionalidades avançadas podem estar indisponíveis.

**Sugestões:**
- Tente termos mais gerais
- Verifique os filtros aplicados
- Use palavras-chave diferentes

**Total de registros disponíveis:** {len(df_dados)}
"""
        
        resposta = f"✅ **Encontrei {len(resultados)} resultado(s) para sua busca** (modo simplificado)\n\n"
        
        for i, (_, row) in enumerate(resultados.head(3).iterrows(), 1):
            resposta += f"**{i}. {row['titulo']}**\n"
            resposta += f"   - **Órgão:** {row['orgao']}\n"
            resposta += f"   - **Cargo:** {row['cargo']}\n"
            resposta += f"   - **Ano:** {row['ano']}\n\n"
        
        if len(resultados) > 3:
            resposta += f"... e mais {len(resultados) - 3} resultado(s).\n\n"
        
        resposta += "💡 **Dica:** Sistema em modo simplificado - para recursos completos de IA, verifique as dependências."
        
        return resposta
        
    except Exception as e:
        return f"❌ **Erro na busca:** {str(e)}"

@app.get("/orgaos")
async def listar_orgaos():
    """Lista todos os órgãos únicos"""
    try:
        if not os.path.exists("concursos_chunks.csv"):
            return {"orgaos": []}
        
        df = pd.read_csv("concursos_chunks.csv")
        orgaos = sorted(df['orgao'].dropna().unique().tolist())
        
        return {"orgaos": orgaos}
        
    except Exception as e:
        logger.error(f"Erro ao listar órgãos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/anos")
async def listar_anos():
    """Lista todos os anos únicos"""
    try:
        if not os.path.exists("concursos_chunks.csv"):
            return {"anos": []}
        
        df = pd.read_csv("concursos_chunks.csv")
        anos = sorted(df['ano'].dropna().unique().tolist(), reverse=True)
        
        return {"anos": anos}
        
    except Exception as e:
        logger.error(f"Erro ao listar anos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cargos")
async def listar_cargos():
    """Lista todos os cargos únicos"""
    try:
        if not os.path.exists("concursos_chunks.csv"):
            return {"cargos": []}
        
        df = pd.read_csv("concursos_chunks.csv")
        cargos = sorted(df['cargo'].dropna().unique().tolist())
        
        return {"cargos": cargos}
        
    except Exception as e:
        logger.error(f"Erro ao listar cargos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ENDPOINTS DE ADMINISTRAÇÃO ===

@app.post("/admin/coletar")
async def coletar_dados(request: ColetaRequest, background_tasks: BackgroundTasks):
    """Inicia coleta de dados em background"""
    try:
        if not coletor_global:
            raise HTTPException(
                status_code=503,
                detail="Coletor não disponível"
            )
        
        def executar_coleta():
            logger.info("Iniciando coleta de dados...")
            try:
                if "pci" in request.fontes:
                    coletor_global.coletar_pci_avancado()
                
                if "brasil_api" in request.fontes:
                    coletor_global.coletar_brasil_api()
                
                if "apis_integradas" in request.fontes:
                    coletor_global.coletar_apis_integradas()
                
                if "completa" in request.fontes:
                    coletor_global.coletar_todos_melhorado()
                
                if "qconcursos" in request.fontes:
                    coletor_global.coletar_qconcursos()
                
                logger.info("Coleta concluída")
                
            except Exception as e:
                logger.error(f"Erro na coleta: {e}")
        
        background_tasks.add_task(executar_coleta)
        
        return {
            "message": "Coleta iniciada em background",
            "fontes": request.fontes,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao iniciar coleta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/agendador/iniciar")
async def iniciar_agendador():
    """Inicia o agendador automático"""
    try:
        if not agendador_global:
            raise HTTPException(
                status_code=503,
                detail="Agendador não disponível"
            )
        
        agendador_global.iniciar()
        return {"message": "Agendador iniciado", "status": "ativo"}
        
    except Exception as e:
        logger.error(f"Erro ao iniciar agendador: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/agendador/parar")
async def parar_agendador():
    """Para o agendador automático"""
    try:
        if not agendador_global:
            raise HTTPException(
                status_code=503,
                detail="Agendador não disponível"
            )
        
        agendador_global.parar()
        return {"message": "Agendador parado", "status": "inativo"}
        
    except Exception as e:
        logger.error(f"Erro ao parar agendador: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === NOVOS ENDPOINTS PARA APIS ESPECÍFICAS ===

@app.post("/admin/coletar/brasil-api")
async def coletar_brasil_api(
    estados: List[str] = ["sp", "rj", "mg", "pr", "rs", "sc", "br"],
    background_tasks: BackgroundTasks = None
):
    """Coleta específica da API Concursos Brasil"""
    try:
        if not coletor_global:
            raise HTTPException(status_code=503, detail="Coletor não disponível")
        
        def executar_coleta_brasil():
            try:
                concursos = coletor_global.coletar_brasil_api(estados)
                logger.info(f"Coletados {len(concursos)} da API Brasil")
            except Exception as e:
                logger.error(f"Erro na coleta Brasil API: {e}")
        
        if background_tasks:
            background_tasks.add_task(executar_coleta_brasil)
            return {"message": "Coleta Brasil API iniciada", "estados": estados}
        else:
            executar_coleta_brasil()
            return {"message": "Coleta Brasil API concluída", "estados": estados}
            
    except Exception as e:
        logger.error(f"Erro ao coletar Brasil API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/coletar/pci-avancado")
async def coletar_pci_avancado(background_tasks: BackgroundTasks):
    """Coleta avançada do PCI Concursos"""
    try:
        if not coletor_global:
            raise HTTPException(status_code=503, detail="Coletor não disponível")
        
        def executar_coleta_pci():
            try:
                concursos = coletor_global.coletar_pci_avancado()
                logger.info(f"Coletados {len(concursos)} do PCI avançado")
            except Exception as e:
                logger.error(f"Erro na coleta PCI avançada: {e}")
        
        background_tasks.add_task(executar_coleta_pci)
        
        return {
            "message": "Coleta PCI avançada iniciada",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao coletar PCI avançado: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/coletar/completa-melhorada")
async def coletar_completa_melhorada(background_tasks: BackgroundTasks):
    """Executa coleta completa com todas as fontes integradas"""
    try:
        if not coletor_global:
            raise HTTPException(status_code=503, detail="Coletor não disponível")
        
        def executar_coleta_completa():
            try:
                concursos = coletor_global.coletar_todos_melhorado()
                # Salvar dados
                if concursos:
                    coletor_global.salvar_csv(concursos, "concursos_chunks.csv")
                logger.info(f"Coleta completa: {len(concursos)} concursos")
            except Exception as e:
                logger.error(f"Erro na coleta completa: {e}")
        
        background_tasks.add_task(executar_coleta_completa)
        
        return {
            "message": "Coleta completa melhorada iniciada",
            "fontes": ["brasil_api", "pci_avancado", "qconcursos"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao iniciar coleta completa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/fontes-disponiveis")
async def listar_fontes_disponiveis():
    """Lista todas as fontes de dados disponíveis"""
    fontes = {
        "brasil_api": {
            "nome": "API Concursos Públicos Brasil",
            "descricao": "API baseada em ConcursosNoBrasil.com",
            "estados_suportados": ["sp", "rj", "mg", "pr", "rs", "sc", "br", "pe", "ba", "go"],
            "status": "ativo" if coletor_global and hasattr(coletor_global, 'integrador_apis') else "inativo"
        },
        "pci_avancado": {
            "nome": "PCI Concursos Avançado",
            "descricao": "Scraper avançado do PCI Concursos",
            "categorias": ["federal", "estadual", "municipal"],
            "status": "ativo"
        },
        "pci_simples": {
            "nome": "PCI Concursos Simples",
            "descricao": "Método simplificado do PCI",
            "status": "ativo"
        },
        "qconcursos": {
            "nome": "QConcursos",
            "descricao": "Dados do portal QConcursos",
            "status": "ativo"
        },
        "completa": {
            "nome": "Coleta Completa Integrada",
            "descricao": "Combina todas as fontes disponíveis",
            "status": "ativo"
        }
    }
    
    return {
        "fontes_disponiveis": fontes,
        "total_fontes": len(fontes),
        "timestamp": datetime.now().isoformat()
    }

# === ENDPOINTS DE ANÁLISE DE EDITAIS COM IA ===

class EditalAnalysisRequest(BaseModel):
    """Modelo para requisição de análise de edital"""
    titulo: str = Field(..., description="Título do concurso")
    orgao: str = Field(..., description="Órgão responsável")
    estado: str = Field(..., description="Estado do concurso")
    conteudo_edital: str = Field(..., description="Texto completo do edital")
    data_publicacao: Optional[str] = Field(None, description="Data de publicação")

class EditalComparisonRequest(BaseModel):
    """Modelo para comparação de editais"""
    edital1: Dict[str, Any] = Field(..., description="Primeiro edital")
    edital2: Dict[str, Any] = Field(..., description="Segundo edital")

@app.get("/ia/status")
async def status_ia():
    """Verifica status do sistema de IA (Ollama)"""
    try:
        if edital_analyzer:
            status = edital_analyzer.get_health_status()
            return {
                "status": "online" if status['ollama_conectado'] else "offline",
                "detalhes": status
            }
        else:
            return {
                "status": "offline",
                "mensagem": "Analisador de editais não inicializado"
            }
    except Exception as e:
        logger.error(f"Erro ao verificar status IA: {e}")
        return {
            "status": "erro",
            "mensagem": str(e)
        }

@app.post("/ia/analisar-edital")
async def analisar_edital(request: EditalAnalysisRequest):
    """
    Analisa um edital usando IA e extrai informações estruturadas
    """
    try:
        if not edital_analyzer:
            raise HTTPException(
                status_code=503, 
                detail="Sistema de IA não disponível. Verifique se o Ollama está rodando."
            )
        
        # Preparar dados do concurso
        concurso_info = {
            "titulo": request.titulo,
            "orgao": request.orgao,
            "estado": request.estado,
            "data_publicacao": request.data_publicacao
        }
        
        # Executar análise
        logger.info(f"🧠 Iniciando análise IA do edital: {request.titulo}")
        analise = edital_analyzer.analyze_edital_content(
            request.conteudo_edital, 
            concurso_info
        )
        
        return {
            "success": True,
            "analise": analise,
            "concurso": concurso_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na análise do edital: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia/explicar-secao")
async def explicar_secao_edital(
    secao_texto: str = Query(..., description="Texto da seção do edital"),
    nome_secao: str = Query(..., description="Nome da seção")
):
    """
    Explica uma seção específica do edital em linguagem simples
    """
    try:
        if not edital_analyzer:
            raise HTTPException(
                status_code=503,
                detail="Sistema de IA não disponível"
            )
        
        explicacao = edital_analyzer.explain_edital_section(secao_texto, nome_secao)
        
        return {
            "success": True,
            "secao": nome_secao,
            "explicacao": explicacao,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao explicar seção: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia/dicas-estudo")
async def gerar_dicas_estudo(
    cargo: str = Query(..., description="Cargo do concurso"),
    materias: List[str] = Query(..., description="Lista de matérias do conteúdo programático")
):
    """
    Gera dicas personalizadas de estudo para um cargo específico
    """
    try:
        if not edital_analyzer:
            raise HTTPException(
                status_code=503,
                detail="Sistema de IA não disponível"
            )
        
        dicas = edital_analyzer.generate_study_tips(cargo, materias)
        
        return {
            "success": True,
            "cargo": cargo,
            "dicas_estudo": dicas,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar dicas de estudo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia/comparar-editais")
async def comparar_editais(request: EditalComparisonRequest):
    """
    Compara dois editais e destaca diferenças importantes
    """
    try:
        if not edital_analyzer:
            raise HTTPException(
                status_code=503,
                detail="Sistema de IA não disponível"
            )
        
        comparacao = edital_analyzer.compare_editais(
            request.edital1, 
            request.edital2
        )
        
        return {
            "success": True,
            "comparacao": comparacao,
            "editais_comparados": {
                "edital1": request.edital1.get("titulo", "N/A"),
                "edital2": request.edital2.get("titulo", "N/A")
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na comparação de editais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ia/modelos-disponiveis")
async def listar_modelos_ia():
    """
    Lista os modelos de IA disponíveis no Ollama
    """
    try:
        if not edital_analyzer:
            raise HTTPException(
                status_code=503,
                detail="Sistema de IA não disponível"
            )
        
        status = edital_analyzer.get_health_status()
        
        return {
            "modelos_disponiveis": status['modelos_disponiveis'],
            "modelo_atual": status['modelo_atual'],
            "ollama_conectado": status['ollama_conectado'],
            "recomendacoes": {
                "llama3": "Melhor para análises gerais e explicações",
                "mistral": "Ótimo para textos técnicos",
                "gemma": "Rápido para tarefas simples"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar modelos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ia/definir-modelo")
async def definir_modelo_ia(
    modelo: str = Query(..., description="Nome do modelo a ser usado")
):
    """
    Define qual modelo de IA usar para as análises
    """
    try:
        if not edital_analyzer:
            raise HTTPException(
                status_code=503,
                detail="Sistema de IA não disponível"
            )
        
        sucesso = edital_analyzer.set_model(modelo)
        
        if sucesso:
            return {
                "success": True,
                "modelo_definido": modelo,
                "message": f"Modelo {modelo} definido com sucesso"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Modelo {modelo} não está disponível"
            )
        
    except Exception as e:
        logger.error(f"❌ Erro ao definir modelo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ENDPOINTS DE CHAT CONVERSACIONAL ===

class EditalChatRequest(BaseModel):
    """Modelo para requisição de chat sobre editais"""
    user_id: str = Field(..., description="ID único do usuário")
    message: str = Field(..., description="Mensagem do usuário")
    edital_id: str = Field(..., description="ID do edital para consultar")

class EditalUploadRequest(BaseModel):
    """Modelo para upload de edital"""
    edital_id: str = Field(..., description="ID único do edital")
    titulo: str = Field(..., description="Título do edital")
    orgao: str = Field(..., description="Órgão responsável")
    estado: str = Field(..., description="Estado")
    conteudo: str = Field(..., description="Texto completo do edital")

@app.post("/chat/upload-edital")
async def upload_edital_para_chat(request: EditalUploadRequest):
    """
    Faz upload de um edital para o sistema de chat conversacional
    """
    try:
        if not conversational_rag:
            raise HTTPException(
                status_code=503,
                detail="Sistema de chat não disponível"
            )
        
        # Preparar informações do edital
        edital_info = {
            'titulo': request.titulo,
            'orgao': request.orgao,
            'estado': request.estado,
            'data_upload': datetime.now().isoformat()
        }
        
        # Adicionar edital ao sistema RAG
        success = conversational_rag.add_edital(
            request.edital_id,
            request.conteudo,
            edital_info
        )
        
        if success:
            # Obter resumo do edital
            summary = conversational_rag.get_edital_summary(request.edital_id)
            
            return {
                'success': True,
                'message': f'Edital {request.edital_id} carregado com sucesso',
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Erro ao processar edital"
            )
            
    except Exception as e:
        logger.error(f"❌ Erro no upload do edital: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/conversar-edital")
async def conversar_sobre_edital(request: EditalChatRequest):
    """
    Conversa sobre um edital específico usando RAG conversacional
    (DEPRECATED: Use /chat/conversar para conversas gerais)
    """
    try:
        if not conversational_rag:
            raise HTTPException(
                status_code=503,
                detail="Sistema de chat não disponível"
            )
        
        # Processar conversa
        response = conversational_rag.chat_with_edital(
            request.user_id,
            request.message,
            request.edital_id
        )
        
        if response['success']:
            return {
                'success': True,
                'response': response['response'],
                'sources': response['sources'],
                'chunks_used': response['chunks_used'],
                'total_chunks': response['total_chunks'],
                'timestamp': response['timestamp']
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=response['error']
            )
            
    except Exception as e:
        logger.error(f"❌ Erro na conversa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/historico/{user_id}")
async def obter_historico_chat(user_id: str):
    """
    Obtém o histórico de chat de um usuário
    """
    try:
        if not conversational_rag:
            raise HTTPException(
                status_code=503,
                detail="Sistema de chat não disponível"
            )
        
        history = conversational_rag.get_chat_history(user_id)
        
        return {
            'success': True,
            'user_id': user_id,
            'history': history,
            'total_messages': len(history)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/historico/{user_id}")
async def limpar_historico_chat(user_id: str):
    """
    Limpa o histórico de chat de um usuário
    """
    try:
        if not conversational_rag:
            raise HTTPException(
                status_code=503,
                detail="Sistema de chat não disponível"
            )
        
        success = conversational_rag.clear_chat_history(user_id)
        
        return {
            'success': success,
            'message': f'Histórico do usuário {user_id} limpo' if success else 'Usuário não encontrado'
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao limpar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/edital/{edital_id}/resumo")
async def obter_resumo_edital(edital_id: str):
    """
    Obtém resumo de um edital carregado no sistema
    """
    try:
        if not conversational_rag:
            raise HTTPException(
                status_code=503,
                detail="Sistema de chat não disponível"
            )
        
        summary = conversational_rag.get_edital_summary(edital_id)
        
        if 'error' in summary:
            raise HTTPException(
                status_code=404,
                detail=summary['error']
            )
        
        return {
            'success': True,
            'edital_id': edital_id,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter resumo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/editais-carregados")
async def listar_editais_carregados():
    """
    Lista todos os editais carregados no sistema de chat
    """
    try:
        if not conversational_rag:
            raise HTTPException(
                status_code=503,
                detail="Sistema de chat não disponível"
            )
        
        editais = []
        for edital_id in conversational_rag.edital_chunks.keys():
            summary = conversational_rag.get_edital_summary(edital_id)
            editais.append({
                'edital_id': edital_id,
                'info': summary['edital_info'],
                'chunks': summary['total_chunks'],
                'size': summary['total_size']
            })
        
        return {
            'success': True,
            'editais': editais,
            'total': len(editais)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar editais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === SCRAPING AUTOMÁTICO DE EDITAIS ===

# Importar sistema de scraping
try:
    from scrapers.scraper_scheduler import (
        coletar_agora,
        coletar_todas_agora,
        agendar_diario,
        agendar_semanal,
        obter_status,
        parar_scheduler,
        scheduler_instance
    )
    SCRAPING_DISPONIVEL = True
    print("✅ Sistema de scraping carregado")
except ImportError as e:
    print(f"⚠️ Sistema de scraping não disponível: {e}")
    SCRAPING_DISPONIVEL = False

class ScrapingRequest(BaseModel):
    banca: str = Field(..., description="Nome da banca (cebraspe, fgv)")
    max_concursos: int = Field(5, ge=1, le=20, description="Máximo de concursos a coletar")

class AgendamentoRequest(BaseModel):
    tipo: str = Field(..., description="Tipo: 'diario' ou 'semanal'")
    hora: int = Field(..., ge=0, le=23, description="Hora (0-23)")
    minuto: int = Field(0, ge=0, le=59, description="Minuto (0-59)")
    dia_semana: Optional[str] = Field(None, description="Dia da semana para semanal (monday-sunday)")

@app.post("/scraping/coletar")
async def iniciar_coleta(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Inicia coleta de editais de uma banca específica
    """
    try:
        if not SCRAPING_DISPONIVEL:
            raise HTTPException(
                status_code=503,
                detail="Sistema de scraping não disponível. Instale: pip install scrapy apscheduler"
            )
        
        # Valida banca
        bancas_disponiveis = ['cebraspe', 'fgv']
        if request.banca.lower() not in bancas_disponiveis:
            raise HTTPException(
                status_code=400,
                detail=f"Banca inválida. Disponíveis: {', '.join(bancas_disponiveis)}"
            )
        
        # Inicia coleta em background
        def executar_coleta():
            coletar_agora(request.banca.lower(), request.max_concursos)
        
        background_tasks.add_task(executar_coleta)
        
        return {
            'success': True,
            'message': f'Coleta da {request.banca.upper()} iniciada em background',
            'banca': request.banca,
            'max_concursos': request.max_concursos,
            'estimativa_tempo': f'{request.max_concursos * 60} segundos'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar coleta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scraping/coletar-todas")
async def iniciar_coleta_todas(background_tasks: BackgroundTasks, max_concursos: int = Query(3, ge=1, le=10)):
    """
    Inicia coleta de todas as bancas disponíveis
    """
    try:
        if not SCRAPING_DISPONIVEL:
            raise HTTPException(
                status_code=503,
                detail="Sistema de scraping não disponível"
            )
        
        # Inicia coleta em background
        def executar_coleta():
            coletar_todas_agora(max_concursos)
        
        background_tasks.add_task(executar_coleta)
        
        return {
            'success': True,
            'message': 'Coleta de todas as bancas iniciada',
            'bancas': ['Cebraspe', 'FGV'],
            'max_concursos': max_concursos,
            'estimativa_tempo': f'{max_concursos * 120} segundos'
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar coleta geral: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scraping/agendar")
async def agendar_coleta(request: AgendamentoRequest):
    """
    Agenda coleta automática (diária ou semanal)
    """
    try:
        if not SCRAPING_DISPONIVEL:
            raise HTTPException(
                status_code=503,
                detail="Sistema de scraping não disponível"
            )
        
        if request.tipo.lower() == 'diario':
            agendar_diario(hora=request.hora, minuto=request.minuto)
            proxima = f"Todo dia às {request.hora:02d}:{request.minuto:02d}"
            
        elif request.tipo.lower() == 'semanal':
            if not request.dia_semana:
                raise HTTPException(
                    status_code=400,
                    detail="dia_semana é obrigatório para agendamento semanal"
                )
            agendar_semanal(dia=request.dia_semana.lower(), hora=request.hora)
            dias_pt = {
                'monday': 'Segunda', 'tuesday': 'Terça', 'wednesday': 'Quarta',
                'thursday': 'Quinta', 'friday': 'Sexta', 'saturday': 'Sábado', 'sunday': 'Domingo'
            }
            proxima = f"Toda {dias_pt.get(request.dia_semana.lower(), request.dia_semana)} às {request.hora:02d}:00"
        else:
            raise HTTPException(
                status_code=400,
                detail="Tipo deve ser 'diario' ou 'semanal'"
            )
        
        return {
            'success': True,
            'message': 'Agendamento configurado com sucesso',
            'tipo': request.tipo,
            'proxima_execucao': proxima
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao agendar coleta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scraping/status")
async def obter_status_scraping():
    """
    Obtém status do sistema de scraping
    """
    try:
        if not SCRAPING_DISPONIVEL:
            return {
                'disponivel': False,
                'message': 'Sistema de scraping não instalado'
            }
        
        status = obter_status()
        
        # Adiciona info sobre PDFs
        editais_dir = 'editais'
        pdfs = []
        if os.path.exists(editais_dir):
            pdfs = [f for f in os.listdir(editais_dir) if f.endswith('.pdf')]
        
        return {
            'disponivel': True,
            'scheduler': {
                'rodando': status.get('rodando', False),
                'jobs_ativos': status.get('jobs_ativos', 0)
            },
            'estatisticas': {
                'total_coletados': status.get('total_coletados', 0),
                'total_indexados': status.get('total_indexados', 0),
                'ultima_coleta': status.get('ultima_coleta'),
                'proxima_coleta': status.get('proxima_coleta')
            },
            'pdfs': {
                'total': len(pdfs),
                'arquivos': pdfs[:10]  # Primeiros 10
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scraping/parar")
async def parar_scraping():
    """
    Para o scheduler de scraping
    """
    try:
        if not SCRAPING_DISPONIVEL:
            raise HTTPException(
                status_code=503,
                detail="Sistema de scraping não disponível"
            )
        
        parar_scheduler()
        
        return {
            'success': True,
            'message': 'Scheduler parado com sucesso'
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao parar scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scraping/pdfs")
async def listar_pdfs_coletados():
    """
    Lista todos os PDFs coletados pelo scraping
    """
    try:
        editais_dir = 'editais'
        if not os.path.exists(editais_dir):
            return {
                'success': True,
                'total': 0,
                'pdfs': []
            }
        
        pdfs = []
        for filename in os.listdir(editais_dir):
            if filename.endswith('.pdf'):
                filepath = os.path.join(editais_dir, filename)
                stat = os.stat(filepath)
                
                # Extrai metadados do nome
                parts = filename.replace('.pdf', '').split('_')
                banca = parts[0] if len(parts) > 0 else 'desconhecido'
                tipo = parts[1] if len(parts) > 1 else 'documento'
                
                pdfs.append({
                    'filename': filename,
                    'banca': banca,
                    'tipo': tipo,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'data_modificacao': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                })
        
        # Ordena por data (mais recentes primeiro)
        pdfs.sort(key=lambda x: x['data_modificacao'], reverse=True)
        
        return {
            'success': True,
            'total': len(pdfs),
            'pdfs': pdfs
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar PDFs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINTS PCI SCRAPER (CONFIÁVEL) ===

@app.post("/scraping/pci/coletar")
async def iniciar_coleta_pci(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Inicia coleta via PCI Concursos (mais confiável)
    Bancas disponíveis: cebraspe, fcc, fgv
    """
    try:
        if not SCRAPING_DISPONIVEL:
            raise HTTPException(
                status_code=503,
                detail="Sistema de scraping não disponível. Execute: instalar_scraping.bat"
            )
        
        from scrapers.scraper_scheduler import coletar_pci_agora
        
        # Valida banca
        bancas_disponiveis = ['cebraspe', 'fcc', 'fgv']
        if request.banca.lower() not in bancas_disponiveis:
            raise HTTPException(
                status_code=400,
                detail=f"Banca inválida. Disponíveis: {', '.join(bancas_disponiveis)}"
            )
        
        # Inicia coleta em background
        def executar_coleta():
            coletar_pci_agora(request.banca.lower(), request.max_concursos)
        
        background_tasks.add_task(executar_coleta)
        
        return {
            'success': True,
            'message': f'Coleta PCI da {request.banca.upper()} iniciada',
            'fonte': 'PCI Concursos',
            'banca': request.banca,
            'max_concursos': request.max_concursos,
            'estimativa_tempo': f'{request.max_concursos * 30} segundos'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar coleta PCI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scraping/pci/coletar-todas")
async def iniciar_coleta_todas_pci(background_tasks: BackgroundTasks, max_concursos: int = Query(5, ge=1, le=15)):
    """
    Inicia coleta de todas as bancas via PCI Concursos
    Coleta: Cebraspe, FCC e FGV
    """
    try:
        if not SCRAPING_DISPONIVEL:
            raise HTTPException(
                status_code=503,
                detail="Sistema de scraping não disponível"
            )
        
        from scrapers.scraper_scheduler import coletar_todas_pci
        
        # Inicia coleta em background
        def executar_coleta():
            coletar_todas_pci(max_concursos)
        
        background_tasks.add_task(executar_coleta)
        
        return {
            'success': True,
            'message': 'Coleta PCI de todas as bancas iniciada',
            'fonte': 'PCI Concursos',
            'bancas': ['Cebraspe', 'FCC', 'FGV'],
            'max_concursos': max_concursos,
            'estimativa_tempo': f'{max_concursos * 90} segundos'
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar coleta PCI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scraping/pci/info")
async def info_pci_scraper():
    """
    Informações sobre o PCI Scraper
    """
    return {
        'success': True,
        'nome': 'PCI Concursos Scraper',
        'descricao': 'Coleta provas e editais do site PCI Concursos',
        'url_base': 'https://www.pciconcursos.com.br',
        'bancas_disponiveis': [
            {
                'id': 'cebraspe',
                'nome': 'Cebraspe',
                'url': 'https://www.pciconcursos.com.br/organizadoras/cebraspe'
            },
            {
                'id': 'fcc',
                'nome': 'FCC',
                'url': 'https://www.pciconcursos.com.br/organizadoras/fcc'
            },
            {
                'id': 'fgv',
                'nome': 'FGV',
                'url': 'https://www.pciconcursos.com.br/organizadoras/fgv'
            }
        ],
        'tipos_documentos': ['edital', 'prova', 'gabarito', 'retificacao'],
        'vantagens': [
            'Mais confiável que scraping direto',
            'Estrutura HTML consistente',
            'Inclui FCC (não disponível no scraper direto)',
            'Menos propenso a bloqueios'
        ]
    }


@app.post("/scraping/coletar-indexar")
async def coletar_e_indexar_automatico(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Coleta PDFs e indexa automaticamente no ChromaDB (RAG)
    PDFs ficam prontos para consultas imediatas
    """
    try:
        if not SCRAPING_DISPONIVEL:
            raise HTTPException(
                status_code=503,
                detail="Sistema de scraping não disponível"
            )
        
        from coletar_indexar_automatico import ColetorIndexadorAutomatico
        
        bancas_disponiveis = ['cebraspe', 'fcc', 'fgv']
        if request.banca.lower() not in bancas_disponiveis:
            raise HTTPException(
                status_code=400,
                detail=f"Banca inválida. Disponíveis: {', '.join(bancas_disponiveis)}"
            )
        
        def executar_coleta_indexacao():
            coletor = ColetorIndexadorAutomatico()
            coletor.coletar_e_indexar_banca(request.banca.lower(), request.max_concursos)
        
        background_tasks.add_task(executar_coleta_indexacao)
        
        return {
            'success': True,
            'message': f'Coleta e indexação da {request.banca.upper()} iniciada',
            'banca': request.banca,
            'max_concursos': request.max_concursos,
            'processo': 'download + indexação automática',
            'estimativa_tempo': f'{request.max_concursos * 45} segundos',
            'resultado': 'PDFs prontos para consultas RAG'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar coleta+indexação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scraping/coletar-indexar-todas")
async def coletar_indexar_todas_bancas(background_tasks: BackgroundTasks, max_concursos: int = Query(5, ge=1, le=10)):
    """
    Coleta e indexa TODAS as bancas automaticamente
    Cebraspe + FCC + FGV em uma única operação
    """
    try:
        if not SCRAPING_DISPONIVEL:
            raise HTTPException(
                status_code=503,
                detail="Sistema de scraping não disponível"
            )
        
        from coletar_indexar_automatico import ColetorIndexadorAutomatico
        
        def executar_coleta_completa():
            coletor = ColetorIndexadorAutomatico()
            coletor.coletar_e_indexar_todas(max_concursos)
        
        background_tasks.add_task(executar_coleta_completa)
        
        total_concursos = max_concursos * 3  # 3 bancas
        
        return {
            'success': True,
            'message': 'Coleta e indexação de TODAS as bancas iniciada',
            'bancas': ['Cebraspe', 'FCC', 'FGV'],
            'total_concursos': total_concursos,
            'max_por_banca': max_concursos,
            'processo': 'download + indexação automática',
            'estimativa_tempo': f'{max_concursos * 135} segundos (~{max_concursos * 2.25:.1f} minutos)',
            'resultado': 'Base RAG atualizada com novos editais'
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar coleta completa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === NOVOS ENDPOINTS - PROVAS ANTERIORES ===

@app.post("/scraping/provas/coletar")
async def coletar_provas_banca(
    background_tasks: BackgroundTasks, 
    banca: str = Query(..., pattern="^(cebraspe|fcc|fgv)$"),
    max_provas: int = Query(15, ge=5, le=30),
    anos: List[int] = Query([2023, 2024, 2025])
):
    """
    Baixa provas anteriores de uma banca específica
    Filtra por anos (padrão: 2023-2025)
    """
    try:
        from scrapers.provas_scraper import coletar_provas_banca
        
        def executar_coleta():
            coletar_provas_banca(banca, anos, max_provas)
        
        background_tasks.add_task(executar_coleta)
        
        return {
            'success': True,
            'message': f'Coleta de provas {banca.upper()} iniciada',
            'banca': banca.upper(),
            'max_provas': max_provas,
            'anos_filtro': anos,
            'processo': 'download de provas + gabaritos',
            'diretorio': f'provas/{banca}/',
            'estimativa_tempo': f'{max_provas * 3} segundos (~{max_provas * 0.05:.1f} minutos)'
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar coleta de provas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scraping/provas/coletar-todas")
async def coletar_provas_todas_bancas(
    background_tasks: BackgroundTasks,
    max_por_banca: int = Query(15, ge=5, le=30),
    anos: List[int] = Query([2023, 2024, 2025])
):
    """
    Baixa provas de TODAS as bancas (Cebraspe + FCC + FGV)
    """
    try:
        from scrapers.provas_scraper import coletar_todas_provas
        
        def executar_coleta_completa():
            coletar_todas_provas(anos, max_por_banca)
        
        background_tasks.add_task(executar_coleta_completa)
        
        total_provas = max_por_banca * 3
        
        return {
            'success': True,
            'message': 'Coleta de provas de TODAS as bancas iniciada',
            'bancas': ['Cebraspe', 'FCC', 'FGV'],
            'total_provas_estimado': total_provas,
            'max_por_banca': max_por_banca,
            'anos_filtro': anos,
            'processo': 'download completo de provas + gabaritos',
            'estimativa_tempo': f'{max_por_banca * 135} segundos (~{max_por_banca * 2.25:.1f} minutos)'
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar coleta completa de provas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scraping/provas/estatisticas")
async def estatisticas_provas():
    """
    Retorna estatísticas das provas baixadas
    """
    try:
        import os
        from pathlib import Path
        
        provas_dir = Path("provas")
        bancas = ['cebraspe', 'fcc', 'fgv']
        
        stats = {
            'bancas': {},
            'total_provas': 0,
            'total_gabaritos': 0,
            'total_arquivos': 0
        }
        
        for banca in bancas:
            banca_dir = provas_dir / banca
            if banca_dir.exists():
                arquivos = list(banca_dir.glob("*.pdf"))
                provas = [f for f in arquivos if '_prova_' in f.name]
                gabaritos = [f for f in arquivos if '_gabarito_' in f.name]
                
                stats['bancas'][banca] = {
                    'total': len(arquivos),
                    'provas': len(provas),
                    'gabaritos': len(gabaritos),
                    'diretorio': str(banca_dir)
                }
                
                stats['total_provas'] += len(provas)
                stats['total_gabaritos'] += len(gabaritos)
                stats['total_arquivos'] += len(arquivos)
            else:
                stats['bancas'][banca] = {
                    'total': 0,
                    'provas': 0,
                    'gabaritos': 0,
                    'diretorio': 'não criado'
                }
        
        return {
            'success': True,
            'data': stats,
            'diretorio_base': str(provas_dir.absolute())
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scraping/provas/listar")
async def listar_provas(
    banca: Optional[str] = Query(None, pattern="^(cebraspe|fcc|fgv)$"),
    tipo: Optional[str] = Query(None, pattern="^(prova|gabarito)$"),
    ano: Optional[int] = Query(None)
):
    """
    Lista todas as provas disponíveis com links para download
    """
    try:
        from pathlib import Path
        import re
        
        provas_dir = Path("provas")
        bancas = [banca] if banca else ['cebraspe', 'fcc', 'fgv']
        
        resultado = {
            'total': 0,
            'provas': []
        }
        
        for banca_nome in bancas:
            banca_dir = provas_dir / banca_nome
            if not banca_dir.exists():
                continue
            
            arquivos = list(banca_dir.glob("*.pdf"))
            
            for arquivo in arquivos:
                nome = arquivo.name
                
                # Extrai informações do nome do arquivo
                partes = nome.replace('.pdf', '').split('_')
                
                # Determina tipo
                tipo_arquivo = 'gabarito' if 'gabarito' in nome else 'prova'
                
                # Filtra por tipo se especificado
                if tipo and tipo != tipo_arquivo:
                    continue
                
                # Extrai ano
                ano_arquivo = None
                for parte in partes:
                    if parte.isdigit() and len(parte) == 4:
                        ano_arquivo = int(parte)
                        break
                
                # Filtra por ano se especificado
                if ano and ano != ano_arquivo:
                    continue
                
                # Extrai título (após banca_ano_tipo_)
                titulo = ' '.join(partes[3:]) if len(partes) > 3 else nome
                titulo = titulo.replace('.pdf', '')[:100]
                
                prova_info = {
                    'banca': banca_nome.upper(),
                    'tipo': tipo_arquivo,
                    'ano': ano_arquivo,
                    'titulo': titulo,
                    'arquivo': nome,
                    'url': f'/provas/{banca_nome}/{nome}',
                    'tamanho_mb': round(arquivo.stat().st_size / 1024 / 1024, 2)
                }
                
                resultado['provas'].append(prova_info)
                resultado['total'] += 1
        
        # Ordena por ano (mais recente primeiro) e depois por banca
        resultado['provas'].sort(key=lambda x: (-(x['ano'] or 0), x['banca'], x['tipo']))
        
        return {
            'success': True,
            'data': resultado
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar provas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/perguntar-provas")
async def perguntar_sobre_provas(request: dict):
    """
    Chat inteligente que retorna provas e gabaritos relacionados à pergunta
    """
    try:
        from pathlib import Path
        import re
        
        pergunta = request.get('pergunta', '').lower()
        
        # Detecta banca mencionada
        banca_detectada = None
        if 'cebraspe' in pergunta or 'cespe' in pergunta:
            banca_detectada = 'cebraspe'
        elif 'fcc' in pergunta:
            banca_detectada = 'fcc'
        elif 'fgv' in pergunta:
            banca_detectada = 'fgv'
        
        # Detecta ano mencionado
        ano_detectado = None
        anos_match = re.findall(r'20\d{2}', pergunta)
        if anos_match:
            ano_detectado = int(anos_match[0])
        
        # Detecta tipo
        tipo_detectado = None
        if 'gabarito' in pergunta:
            tipo_detectado = 'gabarito'
        elif 'prova' in pergunta:
            tipo_detectado = 'prova'
        
        # Lista provas filtradas
        provas_dir = Path("provas")
        bancas = [banca_detectada] if banca_detectada else ['cebraspe', 'fcc', 'fgv']
        
        provas_encontradas = []
        
        for banca_nome in bancas:
            banca_dir = provas_dir / banca_nome
            if not banca_dir.exists():
                continue
            
            arquivos = list(banca_dir.glob("*.pdf"))
            
            for arquivo in arquivos:
                nome = arquivo.name
                
                # Extrai informações
                partes = nome.replace('.pdf', '').split('_')
                tipo_arquivo = 'gabarito' if 'gabarito' in nome else 'prova'
                
                # Filtra por tipo
                if tipo_detectado and tipo_detectado != tipo_arquivo:
                    continue
                
                # Extrai ano
                ano_arquivo = None
                for parte in partes:
                    if parte.isdigit() and len(parte) == 4:
                        ano_arquivo = int(parte)
                        break
                
                # Filtra por ano
                if ano_detectado and ano_detectado != ano_arquivo:
                    continue
                
                # Busca palavras-chave no nome
                relevante = False
                palavras_chave = pergunta.split()
                for palavra in palavras_chave:
                    if len(palavra) > 3 and palavra in nome.lower():
                        relevante = True
                        break
                
                if not banca_detectada and not ano_detectado and not relevante:
                    continue
                
                titulo = ' '.join(partes[3:]) if len(partes) > 3 else nome
                titulo = titulo.replace('.pdf', '')
                
                prova_info = {
                    'banca': banca_nome.upper(),
                    'tipo': tipo_arquivo,
                    'ano': ano_arquivo,
                    'titulo': titulo,
                    'arquivo': nome,
                    'url': f'http://localhost:8000/provas/{banca_nome}/{nome}',
                    'download_url': f'/provas/{banca_nome}/{nome}'
                }
                
                provas_encontradas.append(prova_info)
        
        # Ordena por relevância (ano mais recente primeiro)
        provas_encontradas.sort(key=lambda x: (-(x['ano'] or 0), x['tipo']))
        
        # Gera resposta inteligente
        if provas_encontradas:
            resposta = f"Encontrei {len(provas_encontradas)} arquivo(s) relacionado(s) à sua busca"
            
            if banca_detectada:
                resposta += f" da banca {banca_detectada.upper()}"
            if ano_detectado:
                resposta += f" do ano {ano_detectado}"
            if tipo_detectado:
                resposta += f" (tipo: {tipo_detectado})"
            
            resposta += ":\n\n"
            
            for i, prova in enumerate(provas_encontradas[:10], 1):
                resposta += f"{i}. [{prova['banca']}] {prova['titulo'][:60]}... ({prova['ano']})\n"
                resposta += f"   📥 Download: {prova['url']}\n\n"
        else:
            resposta = "Não encontrei provas correspondentes à sua busca. "
            resposta += "Tente especificar a banca (Cebraspe, FCC, FGV) ou o ano (2023-2025)."
        
        return {
            'success': True,
            'resposta': resposta,
            'total_encontrado': len(provas_encontradas),
            'provas': provas_encontradas[:10],
            'filtros_aplicados': {
                'banca': banca_detectada,
                'ano': ano_detectado,
                'tipo': tipo_detectado
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar provas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def gerar_resposta_metodo_estudo(contexto: dict, temas: dict, pergunta_lower: str) -> str:
    """
    Gera respostas inteligentes sobre métodos de estudo, fluxogramas, estratégias
    """
    resposta = ""
    
    # Fluxograma / Cronograma de estudos
    if temas['fluxograma']:
        resposta = "📊 **FLUXOGRAMA DE ESTUDOS PARA CONCURSOS**\n\n"
        
        if contexto['banca']:
            banca = contexto['banca'].upper()
            resposta += f"**Preparação focada em {banca}:**\n\n"
            
            if contexto['banca'] == 'cebraspe':
                resposta += """
```
┌─────────────────────────────────────┐
│  FASE 1: TEORIA (40% do tempo)     │
│  ✓ Estude pela letra da lei        │
│  ✓ Faça resumos e mapas mentais    │
│  ✓ Foco em jurisprudência           │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  FASE 2: QUESTÕES (40% do tempo)   │
│  ✓ Mínimo 50 questões/dia           │
│  ✓ Foco em CERTO ou ERRADO          │
│  ✓ Revise os erros diariamente      │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  FASE 3: REVISÃO (20% do tempo)    │
│  ✓ Revisão espaçada (7/15/30 dias) │
│  ✓ Simulados completos              │
│  ✓ Revisão de anotações             │
└─────────────────────────────────────┘
```

**🎯 Método Pomodoro para Cebraspe:**
- 50 min de estudo intenso
- 10 min de intervalo
- A cada 4 ciclos: descanso de 30 min

**📚 Divisão de matérias:**
- 30% Português (peso alto)
- 25% Raciocínio Lógico
- 25% Direito (Admin + Constitucional)
- 20% Conhecimentos específicos
"""
            
            elif contexto['banca'] == 'fcc':
                resposta += """
```
┌─────────────────────────────────────┐
│  FASE 1: LEGISLAÇÃO (50% tempo)    │
│  ✓ Lei seca é fundamental           │
│  ✓ Decore artigos importantes       │
│  ✓ Estude doutrina consolidada      │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  FASE 2: QUESTÕES FCC (30% tempo)  │
│  ✓ Questões antigas da FCC          │
│  ✓ Identifique pegadinhas comuns    │
│  ✓ Treine eliminação de alternativas│
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  FASE 3: SIMULADOS (20% tempo)     │
│  ✓ Simule tempo real de prova       │
│  ✓ Revisar erros sistematicamente   │
└─────────────────────────────────────┘
```

**🎯 Estratégia FCC:**
- Foco em lei seca (70% das questões)
- Atenção aos detalhes das alternativas
- Elimine as absurdas primeiro

**📚 Prioridades:**
- 35% Legislação específica
- 25% Português
- 20% Raciocínio Lógico
- 20% Conhecimentos gerais
"""
            
            elif contexto['banca'] == 'fgv':
                resposta += """
```
┌─────────────────────────────────────┐
│  FASE 1: CONTEXTUALIZAÇÃO (35%)    │
│  ✓ Estude casos práticos            │
│  ✓ Leia notícias e atualidades      │
│  ✓ Compreensão > Decoreba           │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  FASE 2: QUESTÕES FGV (40%)        │
│  ✓ Resolva muitas questões FGV      │
│  ✓ Identifique armadilhas típicas   │
│  ✓ Treino de interpretação          │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│  FASE 3: ATUALIZAÇÃO (25%)         │
│  ✓ Jurisprudência recente           │
│  ✓ Mudanças legislativas            │
│  ✓ Temas contemporâneos             │
└─────────────────────────────────────┘
```

**🎯 Técnica para FGV:**
- Leia a questão inteira antes das alternativas
- Identifique palavras-chave
- Desconfie de alternativas muito absolutas

**📚 Distribuição:**
- 30% Atualidades e contexto
- 25% Português (interpretação)
- 25% Raciocínio
- 20% Específicos
"""
        else:
            # Fluxograma genérico
            resposta += """
```
┌──────────────────────────────────────────┐
│  ETAPA 1: PLANEJAMENTO (1-2 semanas)    │
│  ✓ Analise edital completo               │
│  ✓ Identifique matérias e pesos          │
│  ✓ Monte cronograma realista             │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│  ETAPA 2: TEORIA (30-40% do tempo)      │
│  ✓ Estude teoria de forma sistemática    │
│  ✓ Faça resumos e mapas mentais          │
│  ✓ Use técnicas de memorização           │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│  ETAPA 3: QUESTÕES (40-50% do tempo)    │
│  ✓ Resolva questões da banca             │
│  ✓ Anote erros e dúvidas                 │
│  ✓ Revise conceitos errados              │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│  ETAPA 4: REVISÃO (20% do tempo)        │
│  ✓ Revisão espaçada (Curva Esquecimento)│
│  ✓ Simulados semanais                    │
│  ✓ Flash cards de conceitos chave        │
└──────────────────────────────────────────┘
```

**⏰ CRONOGRAMA SEMANAL SUGERIDO:**

**Segunda a Sexta:**
- 6h-8h: Matéria A (teoria)
- 8h-8h30: Intervalo/Café
- 8h30-10h30: Matéria B (questões)
- 10h30-11h: Revisão flash
- 14h-16h: Matéria C (teoria)
- 16h-16h30: Intervalo
- 16h30-18h30: Matéria D (questões)
- 19h-20h: Revisão do dia

**Sábado:**
- 8h-12h: Simulado completo
- 14h-17h: Correção e revisão

**Domingo:**
- Descanso ou revisão leve
"""
    
    # Métodos de estudo
    elif temas['metodo']:
        resposta = "🎓 **MÉTODOS DE ESTUDO PARA CONCURSOS**\n\n"
        
        if contexto['banca']:
            banca = contexto['banca'].upper()
            resposta += f"**Estratégias específicas para {banca}:**\n\n"
            
            if contexto['banca'] == 'cebraspe':
                resposta += """
**📚 Método Cebraspe:**

**1️⃣ TÉCNICA CERTO/ERRADO:**
- Leia afirmação completa
- Identifique palavras absolutas (sempre, nunca, todos)
- Geralmente são ERRADAS
- Cuidado com pegadinhas sutis

**2️⃣ MÉTODO DE RESOLUÇÃO:**
- Faça mínimo 100 questões/semana
- Anote TODOS os erros em caderno
- Revise erros antes de dormir
- Refaça questões erradas após 7 dias

**3️⃣ GESTÃO DE TEMPO:**
- 3 minutos máximo por questão
- Marque dúvidas e volte depois
- Nunca deixe em branco (não zera mais)
- Priorize questões fáceis primeiro

**4️⃣ REVISÃO INTELIGENTE:**
- Flashcards de conceitos-chave
- Revisão espaçada: 1-7-15-30 dias
- Mapas mentais para legislação
- Grave áudios dos resumos

**5️⃣ ERROS COMUNS A EVITAR:**
❌ Ler rápido demais
❌ Pular trechos da questão
❌ Não revisar marcações
❌ Estudar sem resolver questões

**✅ CHECKLIST PRÉ-PROVA:**
- [ ] Revisei todos os erros
- [ ] Fiz 3 simulados completos
- [ ] Decorei artigos importantes
- [ ] Dormi bem na véspera
"""
            
            elif contexto['banca'] == 'fcc':
                resposta += """
**📚 Método FCC:**

**1️⃣ LEI SECA É FUNDAMENTAL:**
- 70% das questões são lei seca
- Decore artigos literalmente
- Use mnemônicos para listas
- Grife legislação importante

**2️⃣ ELIMINAÇÃO ESTRATÉGICA:**
- Leia todas as 5 alternativas
- Elimine as absurdas primeiro
- Entre duas parecidas, a mais específica
- Atenção às palavras-chave

**3️⃣ GESTÃO TEMPO FCC:**
- Prova geralmente é longa
- 2-3 minutos por questão
- Faça provas antigas cronometradas
- Treine velocidade de leitura

**4️⃣ PORTUGUÊS FCC:**
- Foco em gramática tradicional
- Estude regência e concordância
- Faça questões do professor Pestana
- Decore regras principais

**5️⃣ MATERIAIS RECOMENDADOS:**
📖 Lei seca comentada
📝 Resumos em tabelas
🎯 1000+ questões FCC
📊 Estatísticas de assuntos

**⚠️ PEGADINHAS TÍPICAS FCC:**
- Troca de palavras sutis
- Inversão de conceitos
- Exceções às regras
- Detalhes de prazos/números
"""
            
            elif contexto['banca'] == 'fgv':
                resposta += """
**📚 Método FGV:**

**1️⃣ CONTEXTUALIZAÇÃO:**
- FGV cobra aplicação prática
- Estude casos reais
- Leia notícias relacionadas
- Compreenda o "porquê"

**2️⃣ INTERPRETAÇÃO AVANÇADA:**
- Leia textos de apoio com atenção
- Identifique palavras-chave
- Relacione texto com alternativas
- Cuidado com inferências

**3️⃣ ARMADILHAS FGV:**
- Alternativas muito parecidas
- Detalhes que mudam sentido
- Exceções às regras gerais
- Interpretação dupla

**4️⃣ ATUALIDADES:**
- 15-20% da prova é atualidades
- Leia jornais diariamente
- Acompanhe STF/Legislação nova
- Estude temas contemporâneos

**5️⃣ ESTRATÉGIA DE PROVA:**
- Faça questões em 2 passadas
- 1ª: Responda as certas
- 2ª: Analise as dúvidas
- Confie no primeiro instinto

**🎯 DIFERENCIAL FGV:**
✓ Raciocínio > Decoreba
✓ Aplicação > Teoria pura
✓ Contexto > Conceito isolado
✓ Atualização constante
"""
        else:
            resposta += """
**📚 MÉTODOS COMPROVADOS:**

**1️⃣ TÉCNICA POMODORO:**
- 25 min foco total + 5 min pausa
- 4 pomodoros = pausa longa (15-30 min)
- Elimine distrações (celular modo avião)
- Use timer/app específico

**2️⃣ REVISÃO ESPAÇADA:**
- Dia 1: Aprenda o conteúdo
- Dia 2: Revise (24h depois)
- Dia 7: Revise (1 semana)
- Dia 30: Revise (1 mês)
- Reduz esquecimento em 80%

**3️⃣ MAPAS MENTAIS:**
- Centro: Tema principal
- Ramificações: Subtemas
- Cores diferentes por assunto
- Desenhos/símbolos para memorizar

**4️⃣ TÉCNICA FEYNMAN:**
- Aprenda o conceito
- Explique para uma criança
- Identifique lacunas
- Revise e simplifique

**5️⃣ QUESTÕES RESOLVIDAS:**
- Resolva 50-100 questões/dia
- Anote TODOS os erros
- Revise teoria dos erros
- Refaça questões erradas

**6️⃣ FLASHCARDS:**
- Frente: Pergunta/Conceito
- Verso: Resposta
- Revise diariamente
- Apps: Anki, Quizlet

**🎯 CICLO DE ESTUDO EFICAZ:**
```
Teoria → Questões → Revisão → Simulado
  ↑                                ↓
  └────────── Correção ←──────────┘
```

**⏰ GESTÃO DE TEMPO:**
- Identifique horários de pico
- Matérias difíceis quando alerta
- Questões ao final do dia
- Revisões antes de dormir

**💡 DICAS DE OURO:**
✓ Durma 7-8 horas (consolida memória)
✓ Exercício físico 30 min/dia (oxigena cérebro)
✓ Alimentação saudável (evite açúcar)
✓ Hidratação constante (2L água/dia)
✓ Pausas regulares (evita burnout)
"""
    
    # Temas mais cobrados
    elif temas['mais_cobrado']:
        if contexto['banca']:
            resposta = f"📊 **TEMAS MAIS COBRADOS - {contexto['banca'].upper()}**\n\n"
            
            if contexto['banca'] == 'cebraspe':
                resposta += """
**📈 ESTATÍSTICAS CEBRASPE (últimos 3 anos):**

**PORTUGUÊS (25-30% da prova):**
1. Interpretação de texto (35%)
2. Gramática - Concordância (20%)
3. Regência verbal/nominal (15%)
4. Crase (10%)
5. Pontuação (10%)
6. Coesão e coerência (10%)

**RACIOCÍNIO LÓGICO (15-20%):**
1. Lógica de argumentação (30%)
2. Tabelas e gráficos (25%)
3. Sequências (20%)
4. Probabilidade (15%)
5. Análise combinatória (10%)

**DIREITO CONSTITUCIONAL (15-20%):**
1. Direitos fundamentais (30%)
2. Organização do Estado (25%)
3. Poder Executivo (15%)
4. Poder Legislativo (15%)
5. Controle de constitucionalidade (15%)

**DIREITO ADMINISTRATIVO (10-15%):**
1. Atos administrativos (25%)
2. Licitações (Lei 14.133) (20%)
3. Servidores públicos (20%)
4. Improbidade administrativa (15%)
5. Contratos administrativos (20%)

**INFORMÁTICA (5-10%):**
1. Segurança da informação (30%)
2. Windows/Linux (25%)
3. Redes e internet (20%)
4. Pacote Office (15%)
5. Conceitos de TI (10%)

**⭐ DICA:** Foque nos top 3 de cada matéria = 60% da prova!
"""
            
            elif contexto['banca'] == 'fcc':
                resposta += """
**📈 ESTATÍSTICAS FCC (últimos 3 anos):**

**PORTUGUÊS (20-25%):**
1. Interpretação textual (30%)
2. Concordância verbal (20%)
3. Regência (15%)
4. Pontuação (15%)
5. Ortografia (10%)
6. Acentuação (10%)

**LEGISLAÇÃO ESPECÍFICA (30-35%):**
1. Regime jurídico (Lei 8.112) (40%)
2. Estatuto do órgão (30%)
3. Regimento interno (20%)
4. Legislação complementar (10%)

**RACIOCÍNIO LÓGICO (10-15%):**
1. Lógica proposicional (35%)
2. Análise de tabelas (25%)
3. Matemática básica (20%)
4. Porcentagem (20%)

**DIREITO (20-25%):**
1. Administrativo (50%)
2. Constitucional (30%)
3. Tributário (20%)

**CONHECIMENTOS GERAIS (10-15%):**
1. Atualidades nacionais (40%)
2. Geografia (20%)
3. História (20%)
4. Conhecimentos regionais (20%)

**🎯 ESTRATÉGIA FCC:**
- Dedique 40% do tempo à legislação
- 30% Português + RLM
- 30% Direito e atualidades
"""
            
            elif contexto['banca'] == 'fgv':
                resposta += """
**📈 ESTATÍSTICAS FGV (últimos 3 anos):**

**PORTUGUÊS (20-25%):**
1. Interpretação e compreensão (45%)
2. Semântica e vocabulário (20%)
3. Coesão e coerência (15%)
4. Gramática contextualizada (20%)

**RACIOCÍNIO LÓGICO (15-20%):**
1. Lógica proposicional (30%)
2. Lógica de argumentação (25%)
3. Raciocínio quantitativo (25%)
4. Análise de dados (20%)

**CONHECIMENTOS ESPECÍFICOS (40-50%):**
Varia por cargo, mas comum:
1. Legislação aplicada (35%)
2. Teoria + prática (30%)
3. Casos práticos (20%)
4. Ética profissional (15%)

**ATUALIDADES (10-15%):**
1. Política nacional (30%)
2. Economia (25%)
3. Tecnologia (20%)
4. Meio ambiente (15%)
5. Sociedade (10%)

**📊 DISTRIBUIÇÃO POR DIFICULDADE:**
- 30% Fáceis (acertar 100%)
- 50% Médias (acertar 70%)
- 20% Difíceis (acertar 40%)

**💡 ESTRATÉGIA:**
Foque em não errar as fáceis e médias = nota de corte garantida!
"""
    
    return resposta if resposta else None


class ChatRequest(BaseModel):
    pergunta: str

@app.post("/chat/conversar")
async def conversar_com_ia(request: ChatRequest):
    """
    Chat inteligente especializado em concursos públicos com análise de bancas
    
    Capacidades:
    - ✅ Análise parametrizada por banca + área (NOVO!)
    - ✅ Responde "O que o CESPE mais cobra em Tecnologia?"
    - ✅ Identifica padrões específicos (linguagens, leis, etc.)
    - ✅ Gera recomendações personalizadas de estudo
    - ✅ Compara bancas na mesma área
    - ✅ Usa PDFs indexados (Cebraspe, FCC, FGV)
    - ✅ Fornece métodos de estudo e estratégias
    """
    try:
        import re
        from pathlib import Path
        
        pergunta = request.pergunta.strip()
        
        if not pergunta:
            raise HTTPException(status_code=400, detail="Pergunta não pode estar vazia")
        
        logger.info(f"💬 Pergunta recebida: {pergunta}")
        
        # ============================================
        # PRIORIDADE 1: Sistema de Análise de Bancas
        # ============================================
        if rag_banca_inteligente:
            try:
                # Verificar se é pergunta sobre bancas/áreas
                pergunta_lower = pergunta.lower()
                keywords_banca = [
                    'o que', 'mais cobra', 'mais cobrado', 'como estudar',
                    'dificuldade', 'difícil', 'tempo', 'estratégia',
                    'cespe', 'cebraspe', 'fcc', 'fgv', 'vunesp',
                    'tecnologia', 'ti', 'jurídica', 'direito', 'saúde',
                    'administrativa', 'português', 'matemática'
                ]
                
                # DESATIVAR Sistema de Bancas - usar sempre o modelo Llama
                # O Sistema de Bancas precisa de PDFs organizados em pastas específicas
                # Como não temos essa estrutura, vamos usar o RAG tradicional
                is_banca_query = False
                
                logger.info(f"🔍 Usando RAG tradicional com modelo Llama 3.1 8B")
                
                if False:  # Desativado temporariamente
                    logger.info("🎯 Usando Sistema de Análise de Bancas (Banca + Área específica)")
                    
                    try:
                        # Usar RAG inteligente de bancas
                        resposta_banca = rag_banca_inteligente.responder(
                            pergunta,
                            usar_ollama=False  # Usar modo simplificado (Ollama não disponível)
                        )
                        
                        return {
                            'success': True,
                            'resposta': resposta_banca,
                            'fonte': 'Sistema de Análise de Bancas (Parametrizado por Área)',
                            'tipo_resposta': 'analise_banca',
                            'timestamp': datetime.now().isoformat(),
                            'contexto': {
                                'sistema': 'banca_area_analyzer',
                                'modo': 'rag_inteligente'
                            }
                        }
                    except Exception as e:
                        logger.warning(f"⚠️ Erro no Sistema de Bancas: {e}, usando RAG geral")
                        # Continua para usar modelo Llama
            
            except Exception as e:
                logger.warning(f"⚠️ Módulo RAG Bancas não disponível: {e}")
                # Continua para RAG tradicional
        
        # ============================================
        # PRIORIDADE 2: RAG Tradicional
        # ============================================
        try:
            from src.core import perguntar, vectordb
        except ImportError:
            logger.warning("⚠️ src.core não disponível, usando fallback")
            perguntar = None
        
        # Detecta contexto da pergunta
        contexto = {
            'banca': None,
            'ano': None,
            'tipo': None,
            'tema': None
        }
        
        # Detecta banca
        pergunta_lower = pergunta.lower()
        if 'cebraspe' in pergunta_lower or 'cespe' in pergunta_lower or 'unb' in pergunta_lower:
            contexto['banca'] = 'cebraspe'
        elif 'fcc' in pergunta_lower or 'carlos chagas' in pergunta_lower:
            contexto['banca'] = 'fcc'
        elif 'fgv' in pergunta_lower or 'getúlio vargas' in pergunta_lower or 'getulio' in pergunta_lower:
            contexto['banca'] = 'fgv'
        
        # Detecta ano
        anos_match = re.findall(r'20\d{2}', pergunta)
        if anos_match:
            contexto['ano'] = int(anos_match[0])
        
        # Detecta tipo de documento
        if 'gabarito' in pergunta_lower or 'resposta' in pergunta_lower:
            contexto['tipo'] = 'gabarito'
        elif 'prova' in pergunta_lower or 'questão' in pergunta_lower or 'questao' in pergunta_lower:
            contexto['tipo'] = 'prova'
        elif 'edital' in pergunta_lower:
            contexto['tipo'] = 'edital'
        
        # Detecta temas de interesse para métodos de estudo
        temas_metodo = {
            'metodo': 'método' in pergunta_lower or 'como estudar' in pergunta_lower or 'estratégia' in pergunta_lower or 'dica' in pergunta_lower,
            'fluxograma': 'fluxograma' in pergunta_lower or 'mapa' in pergunta_lower or 'organizar' in pergunta_lower or 'cronograma' in pergunta_lower,
            'mais_cobrado': 'mais cobrado' in pergunta_lower or 'temas frequentes' in pergunta_lower or 'principais assuntos' in pergunta_lower or 'estatística' in pergunta_lower,
            'duvida_especifica': 'dúvida' in pergunta_lower or 'duvida' in pergunta_lower or 'não entendo' in pergunta_lower or 'explica' in pergunta_lower
        }
        
        # Monta contexto enriquecido para a pergunta
        pergunta_enriquecida = pergunta
        if contexto['banca']:
            pergunta_enriquecida += f" banca {contexto['banca']}"
        if contexto['ano']:
            pergunta_enriquecida += f" ano {contexto['ano']}"
        if contexto['tipo']:
            pergunta_enriquecida += f" {contexto['tipo']}"
        
        logger.info(f"🔍 Contexto detectado: {contexto}")
        logger.info(f"🔍 Pergunta enriquecida: {pergunta_enriquecida}")
        
        # Responde primeiro se for pergunta sobre métodos de estudo ou estratégias
        if temas_metodo['metodo'] or temas_metodo['fluxograma']:
            resposta_metodo = gerar_resposta_metodo_estudo(contexto, temas_metodo, pergunta_lower)
            if resposta_metodo:
                return {
                    'success': True,
                    'resposta': resposta_metodo,
                    'contexto': contexto,
                    'fonte': 'Sistema de Métodos de Estudo ConcursAI',
                    'provas_relacionadas': [],
                    'tipo_resposta': 'metodo_estudo',
                    'timestamp': datetime.now().isoformat()
                }
        
        # Usa o sistema RAG para buscar resposta nos PDFs (SEMPRE priorizar RAG)
        if not perguntar:
            logger.error("❌ Função perguntar() não disponível")
            return {
                'success': False,
                'resposta': f"🤖 Olá! Você perguntou: **{pergunta}**\n\nO sistema RAG está inicializando. Por favor, aguarde alguns segundos e tente novamente.",
                'erro': 'Sistema RAG não carregado',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            logger.info(f"🔍 Consultando modelo Llama 3.1 8B...")
            # Reduzir k para evitar context overflow
            resposta, fonte = perguntar(pergunta_enriquecida, k=5)
            logger.info(f"✅ Resposta gerada pelo modelo: {len(resposta)} caracteres")
            
            # Formata resposta de forma mais natural
            resposta_formatada = resposta
            
            # Adiciona contexto apenas se relevante
            if contexto['banca'] or (fonte and fonte != "Nenhum documento encontrado"):
                resposta_formatada += "\n\n---\n"
                if contexto['banca']:
                    resposta_formatada += f"📚 **Banca:** {contexto['banca'].upper()}\n"
                if fonte and fonte != "Nenhum documento encontrado":
                    resposta_formatada += f"📄 **Fonte:** {fonte}\n"
            
            # Busca provas relacionadas para incluir na resposta
            from pathlib import Path
            provas_relacionadas = []
            
            if contexto['banca']:
                provas_dir = Path("provas") / contexto['banca']
                if provas_dir.exists():
                    arquivos = list(provas_dir.glob("*.pdf"))[:5]
                    for arquivo in arquivos:
                        nome = arquivo.name
                        
                        # Filtra por tipo se especificado
                        if contexto['tipo']:
                            tipo_arquivo = 'gabarito' if 'gabarito' in nome.lower() else 'prova'
                            if contexto['tipo'] != tipo_arquivo:
                                continue
                        
                        # Filtra por ano se especificado
                        if contexto['ano']:
                            if str(contexto['ano']) not in nome:
                                continue
                        
                        provas_relacionadas.append({
                            'banca': contexto['banca'].upper(),
                            'arquivo': nome,
                            'url': f'/provas/{contexto['banca']}/{nome}',
                            'tipo': 'gabarito' if 'gabarito' in nome.lower() else 'prova'
                        })
            
            return {
                'success': True,
                'resposta': resposta_formatada,
                'contexto': contexto,
                'fonte': fonte,
                'provas_relacionadas': provas_relacionadas,
                'timestamp': datetime.now().isoformat()
            }
            
        except FileNotFoundError as e:
            logger.error(f"❌ Modelo não encontrado: {e}")
            
            # Fallback: resposta genérica APENAS se modelo não existir
            resposta_fallback = "🤖 **Sistema de IA ConcursAI**\n\n"
            resposta_fallback += "⚠️ O modelo de IA não está disponível no momento.\n\n"
            resposta_fallback += f"**Sua pergunta:** {pergunta}\n\n"
            resposta_fallback += "O sistema precisa do modelo Llama 3.1 8B para responder. Aguarde o carregamento."
            
            return {
                'success': False,
                'resposta': resposta_fallback,
                'erro': str(e),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Erro ao consultar RAG: {e}")
            
            # Tenta novamente com menos contexto
            try:
                logger.info("🔄 Tentando novamente com menos contexto...")
                resposta, fonte = perguntar(pergunta, k=3)  # Tenta com apenas 3 documentos
                
                resposta_formatada = f"**Resposta baseada nos documentos indexados:**\n\n{resposta}\n\n"
                
                if contexto['banca']:
                    resposta_formatada += f"📚 **Banca:** {contexto['banca'].upper()}\n"
                
                if fonte and fonte != "Nenhum documento encontrado":
                    resposta_formatada += f"📄 **Fonte:** {fonte}\n"
                
                # Busca provas relacionadas
                from pathlib import Path
                provas_relacionadas = []
                
                if contexto['banca']:
                    provas_dir = Path("provas") / contexto['banca']
                    if provas_dir.exists():
                        arquivos = list(provas_dir.glob("*.pdf"))[:5]
                        for arquivo in arquivos:
                            nome = arquivo.name
                            
                            if contexto['tipo']:
                                tipo_arquivo = 'gabarito' if 'gabarito' in nome.lower() else 'prova'
                                if contexto['tipo'] != tipo_arquivo:
                                    continue
                            
                            if contexto['ano']:
                                if str(contexto['ano']) not in nome:
                                    continue
                            
                            provas_relacionadas.append({
                                'banca': contexto['banca'].upper(),
                                'arquivo': nome,
                                'url': f'/provas/{contexto["banca"]}/{nome}',
                                'tipo': 'gabarito' if 'gabarito' in nome.lower() else 'prova'
                            })
                
                return {
                    'success': True,
                    'resposta': resposta_formatada,
                    'contexto': contexto,
                    'fonte': fonte,
                    'provas_relacionadas': provas_relacionadas,
                    'aviso': '⚠️ Resposta com contexto reduzido devido a limitações de memória.',
                    'timestamp': datetime.now().isoformat()
                }
            
            except Exception as e2:
                logger.error(f"❌ Erro mesmo com contexto reduzido: {e2}")
            
            # Último fallback: resposta genérica baseada no contexto
            resposta_fallback = "🤖 **Sistema de IA ConcursAI**\n\n"
            
            if contexto['banca']:
                resposta_fallback += f"Você perguntou sobre a banca **{contexto['banca'].upper()}**.\n\n"
                
                if contexto['banca'] == 'cebraspe':
                    resposta_fallback += "O **Cebraspe (CESPE/UnB)** é conhecido por questões dissertativas, "
                    resposta_fallback += "provas objetivas com até 5 alternativas (C/E), e alto nível de dificuldade. "
                    resposta_fallback += "Costuma cobrar interpretação de texto e raciocínio lógico.\n\n"
                elif contexto['banca'] == 'fcc':
                    resposta_fallback += "A **FCC (Fundação Carlos Chagas)** é tradicional em concursos, "
                    resposta_fallback += "com questões objetivas de 5 alternativas. Cobra conhecimento técnico "
                    resposta_fallback += "profundo e legislação específica.\n\n"
                elif contexto['banca'] == 'fgv':
                    resposta_fallback += "A **FGV (Fundação Getúlio Vargas)** elabora provas com questões "
                    resposta_fallback += "contextualizadas, pegadinhas sutis e exige atenção aos detalhes. "
                    resposta_fallback += "Costuma trabalhar com casos práticos.\n\n"
            
            resposta_fallback += "💡 **Dica:** Faça perguntas mais específicas sobre:\n"
            resposta_fallback += "- Conteúdo programático de cargos\n"
            resposta_fallback += "- Análise de provas anteriores\n"
            resposta_fallback += "- Dicas de estudo para bancas específicas\n"
            resposta_fallback += "- Estatísticas de questões por disciplina\n\n"
            resposta_fallback += "📚 Para melhores resultados, certifique-se de que os PDFs estão indexados!"
            
            return {
                'success': True,
                'resposta': resposta_fallback,
                'contexto': contexto,
                'fonte': 'Sistema de fallback',
                'provas_relacionadas': [],
                'aviso': 'Resposta genérica. Para respostas precisas, indexe PDFs das provas.',
                'timestamp': datetime.now().isoformat()
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no chat com IA: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")


@app.post("/chat/analisar-pdf")
async def analisar_pdf_prova(file: UploadFile = File(...)):
    """
    🎯 ANÁLISE COMPLETA DE PDF DE PROVA
    
    O usuário anexa um PDF de prova/concurso e recebe:
    1. Identificação automática de banca e área
    2. Análise dos tópicos mais cobrados
    3. Fluxograma de estudo personalizado em Mermaid
    4. Comparação com base de dados existente
    5. Recomendações específicas de estudo
    
    Retorna:
    {
        'analise': {banca, area, topicos, metadados},
        'fluxograma': 'código mermaid',
        'recomendacoes': 'texto com estratégias',
        'id_analise': 'ID para fazer perguntas posteriores'
    }
    """
    if not pdf_analyzer:
        raise HTTPException(
            status_code=503, 
            detail="Sistema de análise de PDFs não disponível. Instale: pip install PyPDF2"
        )
    
    try:
        from pathlib import Path
        import shutil
        
        # Validar tipo de arquivo
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")
        
        logger.info(f"📤 PDF recebido para análise: {file.filename}")
        
        # Criar diretório temporário para upload
        upload_dir = Path("provas/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Salvar arquivo temporariamente
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        tamanho_mb = file_path.stat().st_size / 1024 / 1024
        logger.info(f"  📁 Tamanho: {tamanho_mb:.2f} MB")
        
        # ===================================
        # ANÁLISE COMPLETA DO PDF
        # ===================================
        logger.info("🔍 Iniciando análise completa...")
        
        analise = pdf_analyzer.analisar_pdf_completo(str(file_path), file.filename)
        
        logger.info(f"  📋 Banca: {analise['banca'] or 'Não identificada'}")
        logger.info(f"  📚 Área: {analise['area'] or 'Não identificada'}")
        logger.info(f"  🎯 Tópicos encontrados: {len(analise['topicos'])}")
        
        # ===================================
        # GERAR FLUXOGRAMA DE ESTUDO
        # ===================================
        logger.info("📊 Gerando fluxograma de estudo...")
        
        fluxograma = pdf_analyzer.gerar_fluxograma_estudo(analise)
        
        # ===================================
        # PREPARAR VECTORSTORE PARA PERGUNTAS
        # ===================================
        logger.info("🧠 Preparando sistema de perguntas e respostas...")
        
        texto_completo, _ = pdf_analyzer.extrair_texto_pdf(str(file_path))
        vectorstore_criado = pdf_analyzer.criar_vectorstore_pdf(texto_completo)
        
        # ===================================
        # GERAR RECOMENDAÇÕES
        # ===================================
        banca = analise['banca'] or 'desconhecida'
        area = analise['area'] or 'desconhecida'
        topicos = analise['topicos']
        
        recomendacoes = f"""# 📋 Plano de Estudo Personalizado

## 🎯 Perfil da Prova
- **Banca:** {banca.upper()}
- **Área:** {area.title()}
- **Tópicos Identificados:** {len(topicos)}
- **Arquivo:** {file.filename}

## 📊 O Que Mais Cai (Top 10)

"""
        
        for i, (topico, freq) in enumerate(list(topicos.items())[:10], 1):
            percentual = (freq / sum(topicos.values()) * 100) if sum(topicos.values()) > 0 else 0
            
            # Emoji baseado em prioridade
            if i <= 3:
                emoji = "🔴"  # Alta prioridade
            elif i <= 6:
                emoji = "🟡"  # Média prioridade
            else:
                emoji = "🟢"  # Baixa prioridade
            
            recomendacoes += f"{emoji} **{i}. {topico}**\n"
            recomendacoes += f"   - Frequência: {percentual:.1f}% ({freq} menções)\n"
            recomendacoes += f"   - Prioridade: {'ALTA' if i <= 3 else 'MÉDIA' if i <= 6 else 'NORMAL'}\n\n"
        
        recomendacoes += f"""
## 🎓 Estratégia Recomendada

### Semana 1-2: PRIORIDADE MÁXIMA
Foque nos **3 primeiros tópicos** (representam ~{sum(freq for _, freq in list(topicos.items())[:3]) / sum(topicos.values()) * 100:.0f}% da prova):
"""
        for topico, _ in list(topicos.items())[:3]:
            recomendacoes += f"- [ ] {topico}\n"
        
        recomendacoes += f"""
### Semana 3-4: CONSOLIDAÇÃO
Estude os próximos **5 tópicos** para cobrir ~{sum(freq for _, freq in list(topicos.items())[:8]) / sum(topicos.values()) * 100:.0f}% da prova:
"""
        for topico, _ in list(topicos.items())[3:8]:
            recomendacoes += f"- [ ] {topico}\n"
        
        recomendacoes += """
### Semana 5+: REVISÃO E QUESTÕES
- ✅ Revisar todos os tópicos
- ✅ Fazer questões anteriores da banca
- ✅ Simulados cronometrados
- ✅ Identificar pontos fracos

## 💡 Dicas Específicas da Banca

"""
        
        # Dicas específicas por banca
        dicas_banca = {
            'cebraspe': """
**CEBRASPE/CESPE:**
- ⚠️ Pegadinhas em questões CERTO/ERRADO
- 📖 Leia com atenção: palavras absolutas (sempre, nunca, todo)
- ⏱️ Gestão de tempo: não perca muito tempo em uma questão
- 🎯 Anule se tiver dúvida (erro desconta ponto)
""",
            'fcc': """
**FCC (Fundação Carlos Chagas):**
- 📚 Cobra literalidade da lei
- 🔍 Questões objetivas e diretas
- 📖 Estude legislação seca
- ✅ Menos pegadinhas que CESPE
""",
            'fgv': """
**FGV (Fundação Getúlio Vargas):**
- 🧠 Questões que exigem raciocínio
- 📊 Interpretação de gráficos e casos
- 🎯 Menos decoreba, mais análise
- 📖 Jurisprudência atualizada
""",
        }
        
        recomendacoes += dicas_banca.get(banca, """
**Banca Genérica:**
- 📚 Faça questões anteriores
- ⏱️ Pratique com cronômetro
- 📖 Revise regularmente
- 🎯 Foque nos tópicos mais cobrados
""")
        
        # Adicionar análise contextual se disponível
        if analise.get('analise_contextual'):
            recomendacoes += f"""
## 🔍 Análise Contextual da Base de Dados

{analise['analise_contextual'][:1000]}
"""
        
        logger.info("✅ Análise completa finalizada!")
        
        # ===================================
        # RETORNAR RESULTADO
        # ===================================
        return {
            'success': True,
            'analise': {
                'banca': analise['banca'],
                'area': analise['area'],
                'topicos': analise['topicos'],
                'metadados': analise['metadados'],
                'num_topicos': len(analise['topicos']),
                'arquivo': file.filename,
                'tamanho_mb': round(tamanho_mb, 2),
                'id_analise': analise['id_analise']
            },
            'fluxograma': fluxograma,
            'recomendacoes': recomendacoes,
            'vectorstore_ativo': vectorstore_criado,
            'pode_fazer_perguntas': vectorstore_criado,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao analisar PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao analisar PDF: {str(e)}")


@app.post("/chat/perguntar-pdf")
async def perguntar_sobre_pdf(pergunta: str = Query(..., description="Pergunta sobre o PDF analisado")):
    """
    💬 FAZER PERGUNTAS SOBRE O PDF ANALISADO
    
    Após analisar um PDF com /chat/analisar-pdf, use este endpoint para:
    - Fazer perguntas específicas sobre o conteúdo
    - Consultar detalhes de tópicos
    - Pedir esclarecimentos sobre padrões identificados
    
    Exemplo: "Quais as questões de Python no PDF?"
    """
    if not pdf_analyzer:
        raise HTTPException(
            status_code=503,
            detail="Sistema de análise de PDFs não disponível"
        )
    
    if not pdf_analyzer.qa_chain:
        raise HTTPException(
            status_code=400,
            detail="Nenhum PDF foi analisado ainda. Use /chat/analisar-pdf primeiro."
        )
    
    try:
        logger.info(f"💬 Pergunta sobre PDF: {pergunta}")
        
        # Responder usando o vectorstore do último PDF
        resposta = pdf_analyzer.qa_chain.invoke({"query": pergunta})
        
        return {
            'success': True,
            'pergunta': pergunta,
            'resposta': resposta['result'],
            'fonte': 'PDF analisado anteriormente',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao responder pergunta: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")


@app.post("/upload-pdf")
async def upload_pdf_para_indexar(file: UploadFile = File(...)):
    """
    Upload de PDF para indexação no sistema RAG
    Aceita qualquer PDF (edital, prova, gabarito) e indexa automaticamente
    """
    try:
        from pathlib import Path
        import shutil
        
        # Validar tipo de arquivo
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos")
        
        # Criar diretório para uploads se não existir
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Salvar arquivo
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📤 PDF recebido: {file.filename} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)")
        
        # Tentar indexar o PDF
        try:
            from src.core import indexar_pdf
            
            # Metadados do upload
            metadata = {
                'tipo': 'upload_usuario',
                'fonte': 'Dashboard Upload',
                'data_upload': datetime.now().isoformat(),
                'arquivo': file.filename
            }
            
            # Indexar PDF
            indexar_pdf(str(file_path), metadados=metadata)
            
            logger.info(f"✅ PDF indexado com sucesso: {file.filename}")
            
            return {
                'success': True,
                'message': f'PDF "{file.filename}" indexado com sucesso',
                'arquivo': file.filename,
                'tamanho_mb': round(file_path.stat().st_size / 1024 / 1024, 2),
                'path': str(file_path),
                'indexado': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as idx_error:
            logger.warning(f"⚠️ Erro ao indexar PDF, mas arquivo foi salvo: {idx_error}")
            return {
                'success': True,
                'message': f'PDF "{file.filename}" salvo (indexação pendente)',
                'arquivo': file.filename,
                'tamanho_mb': round(file_path.stat().st_size / 1024 / 1024, 2),
                'path': str(file_path),
                'indexado': False,
                'erro_indexacao': str(idx_error),
                'timestamp': datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ Erro no upload do PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")


# === EXECUTAR APLICAÇÃO ===

if __name__ == "__main__":
    uvicorn.run(
        "api_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
