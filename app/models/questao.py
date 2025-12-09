"""
Modelo de Questão de Concurso
Sprint 1 - Task #204: Criação do esquema inicial (bancas, questoes)
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, JSON, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

try:
    from app.database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class TipoQuestao(str, enum.Enum):
    """Tipos de questões"""
    MULTIPLA_ESCOLHA = "multipla_escolha"
    CERTO_ERRADO = "certo_errado"
    DISSERTATIVA = "dissertativa"
    DISCURSIVA = "discursiva"
    PRATICA = "pratica"
    ORAL = "oral"
    REDACAO = "redacao"


class Dificuldade(str, enum.Enum):
    """Níveis de dificuldade"""
    MUITO_FACIL = "muito_facil"
    FACIL = "facil"
    MEDIA = "media"
    DIFICIL = "dificil"
    MUITO_DIFICIL = "muito_dificil"


class Questao(Base):
    """
    Modelo de Questão de Concurso
    
    Armazena questões completas com análises NLP, classificações
    e features para Machine Learning.
    """
    __tablename__ = "questoes"
    
    # Identificação
    id = Column(Integer, primary_key=True, index=True)
    codigo_questao = Column(String(100), unique=True, index=True)
    
    # Relacionamentos
    banca_id = Column(Integer, ForeignKey("bancas.id"), index=True)
    concurso_id = Column(Integer, index=True)  # ForeignKey a ser adicionado
    
    # Conteúdo da Questão
    enunciado = Column(Text, nullable=False)
    enunciado_html = Column(Text)  # Versão formatada
    
    # Alternativas (JSON para flexibilidade)
    alternativas = Column(JSON)
    # Estrutura: [
    #     {"letra": "A", "texto": "...", "correta": false},
    #     {"letra": "B", "texto": "...", "correta": true},
    #     ...
    # ]
    
    gabarito = Column(String(10))  # "A", "B", "C", "Certo", "Errado", etc.
    gabarito_oficial = Column(String(10))  # Pode ser diferente após recursos
    teve_alteracao_gabarito = Column(Boolean, default=False)
    
    # Tipo de Questão
    tipo_questao = Column(String(50), index=True)
    # "multipla_escolha", "certo_errado", "dissertativa"
    
    # Classificação por Disciplina/Assunto
    disciplina = Column(String(100), index=True)
    # Ex: "Direito Constitucional", "Informática", "Português"
    
    assunto = Column(String(200), index=True)
    # Ex: "Direitos Fundamentais", "Redes de Computadores"
    
    subassunto = Column(String(200))
    # Ex: "Direitos Sociais", "Protocolo TCP/IP"
    
    # Taxonomia Completa (JSON para estrutura hierárquica)
    taxonomia = Column(JSON, default={})
    # {
    #     "area": "Direito",
    #     "disciplina": "Constitucional",
    #     "assunto": "Direitos Fundamentais",
    #     "topico": "Direitos Sociais",
    #     "subtopico": "Saúde"
    # }
    
    # Metadados do Concurso
    ano = Column(Integer, index=True)
    ano_prova = Column(Integer)  # Pode ser diferente do ano do concurso
    cargo = Column(String(200), index=True)
    orgao = Column(String(200), index=True)
    estado = Column(String(2))
    municipio = Column(String(100))
    
    # Nível e Escolaridade
    nivel_cargo = Column(String(50))  # "fundamental", "medio", "superior"
    area_cargo = Column(String(100))  # "administrativa", "tecnica", "juridica"
    
    # Dificuldade e Estatísticas
    dificuldade = Column(String(20))  # "facil", "media", "dificil"
    dificuldade_score = Column(Float)  # 1-10
    
    # Estatísticas de Desempenho
    taxa_acerto = Column(Float)  # % de candidatos que acertaram
    numero_respondentes = Column(Integer, default=0)
    tempo_medio_resposta = Column(Float)  # segundos
    
    # Análise NLP (JSON)
    analise_nlp = Column(JSON, default={})
    # {
    #     "num_palavras": 45,
    #     "num_caracteres": 320,
    #     "complexidade_lexical": 7.5,
    #     "nivel_leitura": "superior",
    #     "sentimento": "neutro",
    #     "entidades_mencionadas": ["STF", "CF/88"],
    #     "conceitos_juridicos": ["devido processo legal"]
    # }
    
    # Keywords e Temas (extraídos automaticamente)
    keywords = Column(JSON, default=[])
    # ["constituição", "direitos fundamentais", "STF"]
    
    temas = Column(JSON, default=[])
    # ["direitos_humanos", "jurisprudencia", "legislacao"]
    
    # Complexidade Textual
    complexidade_textual = Column(Float)  # 1-10
    indice_legibilidade = Column(Float)  # Flesch Reading Ease adaptado
    
    # Características Específicas
    tem_grafico = Column(Boolean, default=False)
    tem_tabela = Column(Boolean, default=False)
    tem_imagem = Column(Boolean, default=False)
    tem_codigo = Column(Boolean, default=False)  # código de programação
    tem_formula = Column(Boolean, default=False)  # fórmulas matemáticas
    
    requer_calculo = Column(Boolean, default=False)
    requer_interpretacao = Column(Boolean, default=False)
    requer_memoria = Column(Boolean, default=False)
    
    # Pegadinhas e Armadilhas
    tem_pegadinha = Column(Boolean, default=False)
    tipo_pegadinha = Column(JSON, default=[])
    # ["negacao_dupla", "excecao_nao_mencionada", "detalhe_sutil"]
    
    # Features para Machine Learning (JSON)
    features_linguisticas = Column(JSON, default={})
    # {
    #     "tfidf_vector": [...],
    #     "pos_tags": {...},
    #     "dependency_tree": {...}
    # }
    
    features_conteudo = Column(JSON, default={})
    # {
    #     "menciona_lei": true,
    #     "menciona_jurisprudencia": true,
    #     "menciona_doutrina": false,
    #     "usa_exemplo_pratico": true
    # }
    
    features_formato = Column(JSON, default={})
    # {
    #     "tamanho_enunciado": "longo",
    #     "numero_alternativas": 5,
    #     "balanceamento_alternativas": "equilibrado"
    # }
    
    embedding_vector = Column(JSON)  # Embedding da questão completa
    
    # Recursos e Anulações
    teve_recurso = Column(Boolean, default=False)
    foi_anulada = Column(Boolean, default=False)
    motivo_anulacao = Column(Text)
    
    # Referências e Fontes
    legislacao_base = Column(JSON, default=[])
    # ["CF/88 Art. 5º", "Lei 8.112/90 Art. 20"]
    
    jurisprudencia_citada = Column(JSON, default=[])
    doutrina_referenciada = Column(JSON, default=[])
    
    # Links e Arquivos
    url_questao = Column(String(500))
    url_resolucao = Column(String(500))
    arquivo_pdf = Column(String(500))
    
    # Resolução e Comentários
    resolucao_oficial = Column(Text)
    comentario_professor = Column(Text)
    dica_resolucao = Column(Text)
    
    # Tags e Categorização
    tags = Column(JSON, default=[])
    # ["importante", "cai_muito", "atualidades", "jurisprudencia_recente"]
    
    # Importância e Relevância
    importancia_score = Column(Float)  # 1-10
    # Baseado em: frequência do tema, relevância para cargo, etc.
    
    probabilidade_cair_novamente = Column(Float)  # 0-1
    # Calculado por modelo preditivo
    
    # Status e Metadados
    verificado = Column(Boolean, default=False)
    revisado = Column(Boolean, default=False)
    publicado = Column(Boolean, default=True)
    
    # Contadores de Uso
    visualizacoes = Column(Integer, default=0)
    tentativas_resposta = Column(Integer, default=0)
    adicionado_favoritos = Column(Integer, default=0)
    
    # Observações
    observacoes = Column(Text)
    fonte_dados = Column(String(100))  # "PCI", "QConcursos", "site_oficial"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_aplicacao_prova = Column(DateTime)
    
    # Relacionamentos
    # banca = relationship("Banca", back_populates="questoes")
    # concurso = relationship("Concurso", back_populates="questoes")
    
    def __repr__(self):
        return f"<Questao(id={self.id}, codigo='{self.codigo_questao}', disciplina='{self.disciplina}')>"
    
    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            'id': self.id,
            'codigo_questao': self.codigo_questao,
            'banca_id': self.banca_id,
            'enunciado': self.enunciado,
            'alternativas': self.alternativas,
            'gabarito': self.gabarito,
            'tipo_questao': self.tipo_questao,
            'disciplina': self.disciplina,
            'assunto': self.assunto,
            'ano': self.ano,
            'cargo': self.cargo,
            'orgao': self.orgao,
            'dificuldade': self.dificuldade,
            'dificuldade_score': self.dificuldade_score,
            'taxa_acerto': self.taxa_acerto,
            'keywords': self.keywords,
            'temas': self.temas,
            'complexidade_textual': self.complexidade_textual,
            'foi_anulada': self.foi_anulada,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_dict_completo(self):
        """Converte objeto para dicionário completo (com todas as análises)"""
        base_dict = self.to_dict()
        base_dict.update({
            'analise_nlp': self.analise_nlp,
            'features_linguisticas': self.features_linguisticas,
            'features_conteudo': self.features_conteudo,
            'features_formato': self.features_formato,
            'legislacao_base': self.legislacao_base,
            'jurisprudencia_citada': self.jurisprudencia_citada,
            'resolucao_oficial': self.resolucao_oficial,
            'tags': self.tags,
            'importancia_score': self.importancia_score,
            'probabilidade_cair_novamente': self.probabilidade_cair_novamente
        })
        return base_dict
