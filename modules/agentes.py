# -*- coding: utf-8 -*-
"""
Orquestrador de Agentes Especializados — ConcursAI
===================================================

Arquitetura: Supervisor (roteador) + Skills especializadas.

Um agente SUPERVISOR classifica a intenção da pergunta do aluno e a encaminha
para o agente especializado correto. Cada agente possui uma PERSONA (system
prompt) própria e decide se usa o RAG (busca nos concursos indexados) ou se
gera a resposta de forma autônoma.

Todos os agentes compartilham o mesmo LLM (Groq / llama-3.3-70b-versatile),
reaproveitando o cliente e a busca vetorial já existentes em concurso_rag.

>>> PERSONALIZAÇÃO <<<
Os campos `system_prompt` abaixo combinam a persona base de cada agente com os
prompts do projeto (concurso_rag, conversational_rag, edital_analyzer,
rag_banca_inteligente, banca_analyzer), integrados por agente.
"""

from __future__ import annotations
import re

# Reaproveita infraestrutura já existente (cliente Groq + busca vetorial)
try:
    from modules.concurso_rag import _get_groq_client, buscar_documentos
except Exception:  # pragma: no cover - fallback para import relativo
    from .concurso_rag import _get_groq_client, buscar_documentos

MODELO_LLM = "llama-3.3-70b-versatile"

# Diretrizes comuns a todos os agentes (tom, formato, honestidade)
_BASE = (
    "Você faz parte do ConcursAI, um sistema de IA para candidatos a concursos "
    "públicos brasileiros. Responda em português do Brasil, use markdown para "
    "organizar (negrito, listas), seja didático e direto. Nunca invente dados: "
    "se a informação não estiver no contexto fornecido, diga claramente."
)

# ───────────────────────────────────────────────────────────────────
# DEFINIÇÃO DOS AGENTES ESPECIALIZADOS
# ───────────────────────────────────────────────────────────────────
AGENTES = {
    "busca": {
        "nome": "Agente de Busca de Concursos",
        "emoji": "🔍",
        "descricao": "Encontra concursos e responde sobre vagas, salários, requisitos e prazos.",
        "usa_rag": True,
        "keywords": [
            "concurso", "vaga", "vagas", "salário", "salario", "remuneração",
            "remuneracao", "edital aberto", "inscrição", "inscricao", "prazo",
            "abertos", "aberto", "quando", "onde", "qual concurso", "requisito",
            "lotação", "lotacao", "cargo", "órgão", "orgao",
        ],
        "system_prompt": (
            f"{_BASE}\n\n"
            "Você é o AGENTE DE BUSCA DE CONCURSOS. Sua função é localizar e "
            "resumir concursos públicos a partir do contexto fornecido (dados "
            "coletados pelo sistema). Destaque: órgão, cargo, vagas, salário, "
            "datas de inscrição e link. Se houver vários, liste de forma "
            "organizada. Use APENAS o contexto fornecido.\n"
            # Prompt do usuário (modules/concurso_rag.py — SYSTEM_PROMPT):
            "\nResponsabilidades: responder sobre editais, vagas, salários, "
            "requisitos e cronogramas; citar dados específicos (datas, valores, "
            "requisitos); quando não houver informação suficiente, dizer "
            "claramente que não encontrou. Use markdown, destaque datas, "
            "salários e números, e não invente nada fora do contexto. Você "
            "representa uma ferramenta confiável: precisão e clareza são essenciais."
        ),
    },
    "edital": {
        "nome": "Agente de Edital",
        "emoji": "📄",
        "descricao": "Analisa editais: requisitos, etapas, conteúdo programático e cronograma.",
        "usa_rag": True,
        "keywords": [
            "edital", "conteúdo programático", "conteudo programatico", "etapas",
            "fases", "cronograma", "anexo", "retificação", "retificacao",
            "documento", "matéria do edital", "programa", "disciplinas exigidas",
        ],
        "system_prompt": (
            f"{_BASE}\n\n"
            "Você é o AGENTE DE EDITAL. Especialista em interpretar editais de "
            "concurso. Extraia e explique de forma estruturada: cargo e "
            "requisitos, número de vagas, remuneração, etapas/fases da seleção, "
            "conteúdo programático e datas-chave. Cite os trechos do edital. "
            "Se algo não constar no contexto, avise.\n"
            # Prompt do usuário (modules/conversational_rag.py + edital_analyzer.py):
            "\nResponda baseando-se EXCLUSIVAMENTE nos trechos do edital "
            "fornecidos. Se a informação não estiver nos trechos, diga 'Esta "
            "informação não está nos trechos analisados'. Cite qual trecho usou "
            "(ex: 'Segundo o TRECHO 1...'). Seja claro, objetivo e didático, em "
            "linguagem acessível ao candidato, e dê dicas práticas quando "
            "relevante. Quando fizer um panorama do edital, organize em: resumo "
            "executivo, cargos/vagas/salários, requisitos, etapas do concurso, "
            "cronograma (datas-chave), conteúdo programático, destaques "
            "importantes e recomendações estratégicas."
        ),
    },
    "banca": {
        "nome": "Agente de Banca",
        "emoji": "🏛️",
        "descricao": "Explica o estilo, as tendências e a forma de cobrança de cada banca.",
        "usa_rag": True,
        "keywords": [
            "banca", "cespe", "cebraspe", "fcc", "fgv", "vunesp", "ibfc",
            "quadrix", "aocp", "estilo", "tendência", "tendencia", "pegadinha",
            "certo e errado", "múltipla escolha", "multipla escolha", "como cobra",
        ],
        "system_prompt": (
            f"{_BASE}\n\n"
            "Você é o AGENTE DE BANCA. Especialista no perfil das bancas "
            "examinadoras (CESPE/CEBRASPE, FCC, FGV, VUNESP, IBFC, etc.). "
            "Explique o estilo de cobrança, formato das questões, pegadinhas "
            "típicas e estratégias para a banca em questão. Use o contexto "
            "quando houver provas/dados; caso contrário, use conhecimento "
            "consolidado sobre a banca, deixando claro quando for genérico.\n"
            # Prompt do usuário (modules/rag_banca_inteligente.py):
            "\nResponda de forma clara e objetiva, usando as informações do "
            "contexto fornecido. Se não houver informação suficiente, seja "
            "honesto e diga isso, complementando com o perfil consolidado da "
            "banca (deixando claro o que é estimativa)."
        ),
    },
    "plano": {
        "nome": "Agente de Plano de Estudos",
        "emoji": "📅",
        "descricao": "Monta cronogramas de estudo personalizados por tempo e cargo.",
        "usa_rag": False,
        "keywords": [
            "plano de estudo", "cronograma de estudo", "organizar estudo",
            "quanto estudar", "rotina", "horas por dia", "semanas", "meses",
            "por onde começar", "por onde comecar", "montar um plano", "agenda",
        ],
        "system_prompt": (
            f"{_BASE}\n\n"
            "Você é o AGENTE DE PLANO DE ESTUDOS. Monte cronogramas realistas e "
            "personalizados conforme o cargo-alvo, o tempo disponível "
            "(semanas/horas por dia) e o nível do aluno. Distribua as "
            "disciplinas por prioridade, inclua revisões espaçadas e simulados, "
            "e apresente em formato de tabela/semana. Seja prático e motivador.\n"
            # Prompt do usuário (didático — base conversational_rag.py):
            "\nUse linguagem acessível ao candidato e dê dicas práticas. "
            "Seja honesto sobre o que depende do edital específico."
        ),
    },
    "questoes": {
        "nome": "Agente de Questões",
        "emoji": "📝",
        "descricao": "Gera questões e simulados no estilo da banca, com gabarito comentado.",
        "usa_rag": False,
        "keywords": [
            "questão", "questao", "questões", "questoes", "simulado", "exercício",
            "exercicio", "me teste", "gabarito", "prova de", "crie questões",
            "gere questões", "faça questões", "faca questoes",
        ],
        "system_prompt": (
            f"{_BASE}\n\n"
            "Você é o AGENTE DE QUESTÕES. Gere questões de simulado no estilo da "
            "banca pedida (CESPE certo/errado, múltipla escolha ou dissertativa) "
            "sobre o tema solicitado. Para cada questão forneça o GABARITO e um "
            "comentário explicando o porquê. Numere as questões e mantenha o "
            "nível de dificuldade pedido.\n"
            # Prompt do usuário (estilo provas — base banca_analyzer.py):
            "\nQuando possível, baseie as questões no estilo real de cobrança da "
            "banca. Use linguagem clara e indique o nível de dificuldade."
        ),
    },
    "tutor": {
        "nome": "Agente Tutor",
        "emoji": "👨‍🏫",
        "descricao": "Explica matérias e conceitos de forma didática para o aluno.",
        "usa_rag": False,
        "keywords": [
            "explique", "explica", "o que é", "o que e", "como funciona",
            "diferença entre", "diferenca entre", "conceito", "resuma", "resumo",
            "me ensina", "não entendi", "nao entendi", "significa", "exemplo de",
        ],
        "system_prompt": (
            f"{_BASE}\n\n"
            "Você é o AGENTE TUTOR. Explique matérias e conceitos cobrados em "
            "concursos de forma clara e didática, do simples ao complexo. Use "
            "analogias, exemplos e, ao final, um resumo em tópicos do que foi "
            "explicado. Adapte a profundidade ao nível do aluno.\n"
            # Prompt do usuário (didático — base conversational_rag.py):
            "\nUse linguagem acessível para candidatos, seja claro, objetivo e "
            "didático, e dê dicas práticas. Ao final, traga um resumo em tópicos."
        ),
    },
}

AGENTE_PADRAO = "busca"


# ───────────────────────────────────────────────────────────────────
# SUPERVISOR — classifica a intenção e escolhe o agente
# ───────────────────────────────────────────────────────────────────
def classificar(pergunta: str) -> dict:
    """Roteador heurístico: pontua a pergunta contra as keywords de cada agente.

    Retorna {'agente': id, 'confianca': float, 'placar': {...}}.
    Determinístico, gratuito e rápido — ideal para demonstração de TCC.
    """
    texto = (pergunta or "").lower()
    placar = {aid: 0 for aid in AGENTES}

    for aid, ag in AGENTES.items():
        for kw in ag["keywords"]:
            if kw in texto:
                # keywords mais longas/específicas valem mais
                placar[aid] += 2 if len(kw) > 8 else 1

    melhor = max(placar, key=placar.get)
    total = sum(placar.values())
    if placar[melhor] == 0:
        # nenhuma keyword bateu → cai no agente padrão (busca/RAG)
        return {"agente": AGENTE_PADRAO, "confianca": 0.0, "placar": placar}

    confianca = round(placar[melhor] / total, 2) if total else 0.0
    return {"agente": melhor, "confianca": confianca, "placar": placar}


# ───────────────────────────────────────────────────────────────────
# DISPATCH — executa o agente escolhido
# ───────────────────────────────────────────────────────────────────
def _chamar_llm(system_prompt: str, mensagem_usuario: str, temperatura: float = 0.4):
    """Chama o Groq com a persona do agente. Retorna texto ou None."""
    cliente = _get_groq_client()
    if not cliente:
        return None
    try:
        resp = cliente.chat.completions.create(
            model=MODELO_LLM,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensagem_usuario},
            ],
            temperature=temperatura,
            max_tokens=1200,
        )
        return resp.choices[0].message.content
    except Exception as e:  # pragma: no cover
        print(f"⚠️ Erro no agente (Groq): {e}")
        return None


def gerar(system_prompt: str, mensagem: str, temperatura: float = 0.5):
    """Geração genérica com persona custom — reutilizada pelas ferramentas."""
    return _chamar_llm(system_prompt, mensagem, temperatura)


def responder(pergunta, agente_id=None, orgao="Todos", ano="Todos",
              cargo="Todos", contexto_extra=""):
    """Ponto de entrada do orquestrador.

    Se `agente_id` for None, o supervisor escolhe o agente automaticamente.
    Retorna dict com a resposta e metadados do roteamento.
    """
    if not pergunta or not pergunta.strip():
        return {
            "resposta": "❓ Por favor, escreva sua dúvida sobre concursos públicos.",
            "agente": None, "agente_nome": None, "confianca": 0.0, "automatico": False,
        }

    automatico = agente_id is None
    if automatico:
        rota = classificar(pergunta)
        agente_id = rota["agente"]
        confianca = rota["confianca"]
    else:
        confianca = 1.0

    ag = AGENTES.get(agente_id) or AGENTES[AGENTE_PADRAO]

    # Monta o contexto: agentes com usa_rag puxam documentos do ChromaDB
    contexto_docs = ""
    fontes = 0
    if ag["usa_rag"]:
        try:
            docs = buscar_documentos(pergunta, orgao, ano, cargo, limite=5)
            fontes = len(docs)
            if docs:
                contexto_docs = "\n\n---\n\n".join(docs)
        except Exception as e:
            print(f"⚠️ Falha ao buscar contexto RAG: {e}")

    historico = f"HISTÓRICO DA CONVERSA:\n{contexto_extra}\n\n" if contexto_extra else ""
    if contexto_docs:
        mensagem = (
            f"CONTEXTO (dados de concursos/editais):\n{contexto_docs}\n\n"
            f"{historico}PERGUNTA DO ALUNO: {pergunta}"
        )
    else:
        mensagem = f"{historico}PERGUNTA DO ALUNO: {pergunta}"

    resposta = _chamar_llm(ag["system_prompt"], mensagem)

    if not resposta:
        # Sem LLM: agentes com RAG ainda mostram os documentos encontrados
        if ag["usa_rag"] and contexto_docs:
            trechos = contexto_docs.split("\n\n---\n\n")[:3]
            corpo = "\n\n".join(
                f"**{i}.** {re.sub(r'\\s+', ' ', t).strip()[:300]}..."
                for i, t in enumerate(trechos, 1)
            )
            resposta = (
                f"{ag['emoji']} **{ag['nome']}** — resultados encontrados "
                f"(modo sem IA):\n\n{corpo}\n\n---\n"
                "⚠️ *Configure uma GROQ_API_KEY válida no .env para respostas "
                "elaboradas pela IA.*"
            )
        else:
            resposta = (
                f"{ag['emoji']} **{ag['nome']}** precisa do modelo de IA para "
                "esta tarefa.\n\n⚠️ *Configure uma GROQ_API_KEY válida no arquivo "
                ".env (chave gratuita em groq.com) e reinicie o servidor.*"
            )

    return {
        "resposta": resposta,
        "agente": agente_id,
        "agente_nome": ag["nome"],
        "agente_emoji": ag["emoji"],
        "confianca": confianca,
        "automatico": automatico,
        "fontes_rag": fontes,
    }


def listar_agentes():
    """Retorna a lista de agentes para a interface (sem os prompts internos)."""
    return [
        {"id": aid, "nome": ag["nome"], "emoji": ag["emoji"],
         "descricao": ag["descricao"], "usa_rag": ag["usa_rag"]}
        for aid, ag in AGENTES.items()
    ]
