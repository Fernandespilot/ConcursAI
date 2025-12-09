"""
Modelo de Banca Organizadora de Concursos
Sprint 1 - Task #204: Criação do esquema inicial (bancas, questoes)
"""

from sqlalchemy import Column, Integer, String, Float, JSON, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from app.database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class Banca(Base):
    """
    Modelo de Banca Organizadora de Concursos
    
    Armazena informações sobre bancas organizadoras, seus padrões,
    características e estatísticas.
    """
    __tablename__ = "bancas"
    
    # Identificação
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, index=True, nullable=False)
    nome_completo = Column(String(255))
    sigla = Column(String(20), index=True)
    
    # Informações Básicas
    site_oficial = Column(String(255))
    email_contato = Column(String(255))
    telefone = Column(String(50))
    
    # Localização
    cidade = Column(String(100))
    estado = Column(String(2))
    pais = Column(String(50), default="Brasil")
    
    # Características da Banca (JSON)
    caracteristicas = Column(JSON, default={})
    # Estrutura esperada:
    # {
    #     "estilo_questoes": "objetiva|dissertativa|mista",
    #     "dificuldade_media": 7.5,  # 1-10
    #     "areas_foco": ["direito", "administracao", "informatica"],
    #     "tipo_questoes": ["multipla_escolha", "cespe_certo_errado", "dissertativa"],
    #     "tempo_medio_prova": 240,  # minutos
    #     "numero_medio_questoes": 60,
    #     "permite_recurso": true,
    #     "formato_recurso": "online|presencial"
    # }
    
    # Padrões Identificados (JSON)
    padroes = Column(JSON, default={})
    # Estrutura esperada:
    # {
    #     "temas_frequentes": [
    #         {"tema": "constituicao", "frequencia": 0.85},
    #         {"tema": "administrativo", "frequencia": 0.75}
    #     ],
    #     "formato_preferido": "cespe_style",
    #     "pegadinhas_comuns": [
    #         "uso de negação dupla",
    #         "exceções não mencionadas"
    #     ],
    #     "palavras_chave": ["exceto", "incorreto", "assinale"],
    #     "complexidade_textual_media": 6.8,
    #     "usa_jurisprudencia": true,
    #     "cita_legislacao": true
    # }
    
    # Estatísticas Gerais
    total_concursos = Column(Integer, default=0)
    total_questoes = Column(Integer, default=0)
    total_candidatos = Column(Integer, default=0)
    
    # Taxas e Médias
    taxa_aprovacao_media = Column(Float)  # %
    nota_corte_media = Column(Float)
    salario_medio_oferecido = Column(Float)
    
    # Análise de Dificuldade
    dificuldade_geral = Column(Float)  # 1-10
    dificuldade_por_area = Column(JSON, default={})
    # Exemplo: {"direito": 8.5, "informatica": 7.2}
    
    # Histórico e Tendências (JSON)
    historico_temas = Column(JSON, default=[])
    # Lista de objetos: [{"ano": 2024, "tema": "constituicao", "peso": 30%}]
    
    tendencias_recentes = Column(JSON, default={})
    # {
    #     "temas_crescentes": ["direito_digital", "lgpd"],
    #     "temas_decrescentes": ["datilografia"],
    #     "novos_formatos": ["video_entrevista"]
    # }
    
    # Reputação e Avaliação
    reputacao_score = Column(Float)  # 1-10
    avaliacao_candidatos = Column(Float)  # 1-5 (estilo rating)
    total_avaliacoes = Column(Integer, default=0)
    
    comentarios_comuns = Column(JSON, default=[])
    # ["Banca muito exigente", "Questões bem elaboradas", ...]
    
    # Features para Machine Learning (JSON)
    ml_features = Column(JSON, default={})
    # {
    #     "features_linguisticas": {...},
    #     "features_estatisticas": {...},
    #     "embedding_signature": [...]  # Embedding característico da banca
    # }
    
    # Status e Metadados
    ativo = Column(Boolean, default=True)
    verificado = Column(Boolean, default=False)  # Dados verificados manualmente
    ultima_atualizacao_dados = Column(DateTime)
    
    # Observações e Notas
    observacoes = Column(Text)
    tags = Column(JSON, default=[])  # ["federal", "estadual", "municipal", "militar"]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    # concursos = relationship("Concurso", back_populates="banca")
    # questoes = relationship("Questao", back_populates="banca")
    
    def __repr__(self):
        return f"<Banca(nome='{self.nome}', total_concursos={self.total_concursos})>"
    
    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'nome_completo': self.nome_completo,
            'sigla': self.sigla,
            'site_oficial': self.site_oficial,
            'caracteristicas': self.caracteristicas,
            'padroes': self.padroes,
            'total_concursos': self.total_concursos,
            'total_questoes': self.total_questoes,
            'taxa_aprovacao_media': self.taxa_aprovacao_media,
            'dificuldade_geral': self.dificuldade_geral,
            'reputacao_score': self.reputacao_score,
            'ativo': self.ativo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def bancas_principais(cls):
        """Lista das bancas mais importantes do Brasil"""
        return [
            "CESPE/CEBRASPE",
            "FCC",
            "FGV",
            "VUNESP",
            "IBFC",
            "IDECAN",
            "IADES",
            "AOCP",
            "CONSULPLAN",
            "FUNDATEC",
            "QUADRIX",
            "IBADE",
            "INSTITUTO AOCP",
            "CETRO",
            "COPS/UEL"
        ]
