"""
Database e Sistema de Análise de Bancas de Concursos
=====================================================
Gerencia informações sobre bancas organizadoras de concursos
e fornece análises de padrões
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# Database de bancas conhecidas
BANCAS_DATABASE = {
    "CESPE/CEBRASPE": {
        "nome_completo": "Centro de Seleção e de Promoção de Eventos",
        "sigla": "CESPE/CEBRASPE",
        "tipo": "Pública",
        "vinculo": "Universidade de Brasília (UnB)",
        "site": "https://www.cebraspe.org.br",
        "caracteristicas": {
            "estilo_questoes": "Assertivas Certo/Errado, questões longas e contextualizadas",
            "dificuldade": "Alta",
            "peculiaridades": [
                "Desconta pontos por erros em algumas provas",
                "Questões com múltiplas assertivas",
                "Textos longos e interpretação complexa",
                "Multidisciplinaridade frequente"
            ],
            "disciplinas_fortes": [
                "Direito Constitucional",
                "Direito Administrativo",
                "Raciocínio Lógico",
                "Informática",
                "Administração Pública"
            ]
        },
        "estrategias_preparacao": [
            "Praticar muito questões C/E",
            "Atenção aos detalhes dos enunciados",
            "Estudar jurisprudência atualizada",
            "Treinar interpretação de texto",
            "Gerenciar tempo (questões longas)"
        ],
        "estatisticas": {
            "concursos_realizados": 450,
            "areas_principais": ["Federal", "Justiça", "Polícias"],
            "taxa_aprovacao_media": 0.02,
            "candidatos_por_vaga": 150
        }
    },
    
    "FCC": {
        "nome_completo": "Fundação Carlos Chagas",
        "sigla": "FCC",
        "tipo": "Privada",
        "vinculo": "Fundação",
        "site": "https://www.concursosfcc.com.br",
        "caracteristicas": {
            "estilo_questoes": "Múltipla escolha, objetivas, foco em lei seca",
            "dificuldade": "Média-Alta",
            "peculiaridades": [
                "Questões diretas sobre legislação",
                "Pouca contextualização",
                "Foco em memorização de artigos",
                "Português cobrado de forma clássica"
            ],
            "disciplinas_fortes": [
                "Direito (lei seca)",
                "Português",
                "Raciocínio Lógico-Matemático",
                "Contabilidade",
                "Conhecimentos Bancários"
            ]
        },
        "estrategias_preparacao": [
            "Decorar artigos de lei importantes",
            "Fazer questões antigas da FCC",
            "Estudar português pela gramática tradicional",
            "Praticar RLM (questões estruturadas)",
            "Conhecer súmulas e jurisprudência"
        ],
        "estatisticas": {
            "concursos_realizados": 380,
            "areas_principais": ["Tribunais", "Bancas", "Prefeituras SP"],
            "taxa_aprovacao_media": 0.025,
            "candidatos_por_vaga": 120
        }
    },
    
    "FGV": {
        "nome_completo": "Fundação Getúlio Vargas",
        "sigla": "FGV",
        "tipo": "Privada",
        "vinculo": "FGV",
        "site": "https://conhecimento.fgv.br/concursos",
        "caracteristicas": {
            "estilo_questoes": "Interpretativas, contextualizadas, raciocínio complexo",
            "dificuldade": "Alta",
            "peculiaridades": [
                "Questões que exigem interpretação profunda",
                "Contextualização com atualidades",
                "Pouca decoreba, mais raciocínio",
                "Interdisciplinaridade"
            ],
            "disciplinas_fortes": [
                "Direito (interpretação)",
                "Administração",
                "Economia",
                "Português (interpretação)",
                "Atualidades"
            ]
        },
        "estrategias_preparacao": [
            "Desenvolver pensamento crítico",
            "Estudar contexto, não apenas lei seca",
            "Acompanhar notícias e atualidades",
            "Praticar interpretação de texto",
            "Resolver questões anteriores da FGV"
        ],
        "estatisticas": {
            "concursos_realizados": 320,
            "areas_principais": ["Federal", "Estadual", "Diversos"],
            "taxa_aprovacao_media": 0.018,
            "candidatos_por_vaga": 180
        }
    },
    
    "VUNESP": {
        "nome_completo": "Fundação para o Vestibular da Unesp",
        "sigla": "VUNESP",
        "tipo": "Pública",
        "vinculo": "UNESP",
        "site": "https://www.vunesp.com.br",
        "caracteristicas": {
            "estilo_questoes": "Objetivas diretas, ênfase em conhecimentos específicos",
            "dificuldade": "Média",
            "peculiaridades": [
                "Predominância no estado de SP",
                "Questões técnicas bem elaboradas",
                "Foco em conhecimentos específicos",
                "Português intermediário"
            ],
            "disciplinas_fortes": [
                "Conhecimentos Específicos",
                "Português",
                "Raciocínio Lógico",
                "Legislação Estadual (SP)",
                "Informática"
            ]
        },
        "estrategias_preparacao": [
            "Foco nos conhecimentos específicos do cargo",
            "Estudar legislação paulista",
            "Português pela norma culta",
            "Resolver simulados VUNESP",
            "Atenção a detalhes técnicos"
        ],
        "estatisticas": {
            "concursos_realizados": 280,
            "areas_principais": ["SP (principalmente)", "Prefeituras", "Polícias"],
            "taxa_aprovacao_media": 0.03,
            "candidatos_por_vaga": 100
        }
    },
    
    "IDECAN": {
        "nome_completo": "Instituto de Desenvolvimento Educacional, Cultural e Assistencial Nacional",
        "sigla": "IDECAN",
        "tipo": "Privada",
        "vinculo": "Fundação",
        "site": "https://www.idecan.org.br",
        "caracteristicas": {
            "estilo_questoes": "Objetivas, variadas, alguns concursos regionais",
            "dificuldade": "Média",
            "peculiaridades": [
                "Presente em diversos estados",
                "Questões bem elaboradas",
                "Nível médio de dificuldade",
                "Boa para iniciantes"
            ],
            "disciplinas_fortes": [
                "Português",
                "Raciocínio Lógico",
                "Conhecimentos Gerais",
                "Informática Básica",
                "Legislação Municipal"
            ]
        },
        "estrategias_preparacao": [
            "Base sólida em disciplinas básicas",
            "Conhecimentos gerais e atualidades",
            "Praticar questões variadas",
            "Legislação do órgão/município"
        ],
        "estatisticas": {
            "concursos_realizados": 200,
            "areas_principais": ["Municipal", "Estadual", "Federal"],
            "taxa_aprovacao_media": 0.035,
            "candidatos_por_vaga": 80
        }
    },
    
    "IBFC": {
        "nome_completo": "Instituto Brasileiro de Formação e Capacitação",
        "sigla": "IBFC",
        "tipo": "Privada",
        "vinculo": "Fundação",
        "site": "https://www.ibfc.org.br",
        "caracteristicas": {
            "estilo_questoes": "Objetivas, crescente no mercado",
            "dificuldade": "Média",
            "peculiaridades": [
                "Banca em crescimento",
                "Questões bem estruturadas",
                "Diversos estados"
            ],
            "disciplinas_fortes": [
                "Português",
                "Raciocínio Lógico",
                "Direito",
                "Conhecimentos Específicos"
            ]
        },
        "estrategias_preparacao": [
            "Estudar provas anteriores IBFC",
            "Foco em disciplinas básicas",
            "Conhecimentos específicos detalhados"
        ],
        "estatisticas": {
            "concursos_realizados": 180,
            "areas_principais": ["Tribunais", "Prefeituras", "Autarquias"],
            "taxa_aprovacao_media": 0.032,
            "candidatos_por_vaga": 90
        }
    },
    
    "INSTITUTO AOCP": {
        "nome_completo": "Instituto AOCP",
        "sigla": "AOCP",
        "tipo": "Privada",
        "vinculo": "Fundação",
        "site": "https://www.institutoaocp.org.br",
        "caracteristicas": {
            "estilo_questoes": "Objetivas, questões acessíveis",
            "dificuldade": "Média-Baixa",
            "peculiaridades": [
                "Questões diretas",
                "Boa para iniciantes",
                "Regional e nacional"
            ],
            "disciplinas_fortes": [
                "Português",
                "Matemática/RLM",
                "Conhecimentos Gerais",
                "Informática"
            ]
        },
        "estrategias_preparacao": [
            "Base sólida em disciplinas fundamentais",
            "Questões objetivas e diretas",
            "Conhecimentos específicos básicos"
        ],
        "estatisticas": {
            "concursos_realizados": 150,
            "areas_principais": ["Municipal", "Estadual", "Autarquias"],
            "taxa_aprovacao_media": 0.04,
            "candidatos_por_vaga": 70
        }
    },
    
    "QUADRIX": {
        "nome_completo": "Quadrix Consultoria e Avaliação",
        "sigla": "QUADRIX",
        "tipo": "Privada",
        "vinculo": "Empresa",
        "site": "https://www.quadrix.org.br",
        "caracteristicas": {
            "estilo_questoes": "Objetivas, em crescimento no DF",
            "dificuldade": "Média",
            "peculiaridades": [
                "Forte presença no DF e região",
                "Questões bem elaboradas",
                "Crescente nacionalmente"
            ],
            "disciplinas_fortes": [
                "Português",
                "Raciocínio Lógico",
                "Direito",
                "Administração"
            ]
        },
        "estrategias_preparacao": [
            "Estudar provas anteriores",
            "Foco em disciplinas básicas",
            "Legislação do órgão"
        ],
        "estatisticas": {
            "concursos_realizados": 120,
            "areas_principais": ["DF", "Federal", "Autarquias"],
            "taxa_aprovacao_media": 0.028,
            "candidatos_por_vaga": 95
        }
    }
}


class SistemaBancas:
    """Sistema de análise e gerenciamento de bancas de concursos"""
    
    def __init__(self):
        self.bancas = BANCAS_DATABASE
        logger.info(f"✅ Sistema de Bancas inicializado com {len(self.bancas)} bancas")
    
    def listar_bancas(self) -> List[str]:
        """Retorna lista de todas as bancas"""
        return list(self.bancas.keys())
    
    def obter_info_banca(self, nome_banca: str) -> Optional[Dict]:
        """
        Obtém informações completas de uma banca
        
        Args:
            nome_banca: Nome ou sigla da banca
            
        Returns:
            Dicionário com informações ou None
        """
        # Buscar exata
        if nome_banca in self.bancas:
            return self.bancas[nome_banca]
        
        # Buscar parcial (case insensitive)
        nome_upper = nome_banca.upper()
        for banca_key, banca_info in self.bancas.items():
            if nome_upper in banca_key.upper():
                return banca_info
        
        return None
    
    def identificar_banca_em_texto(self, texto: str) -> Optional[str]:
        """
        Identifica banca a partir de um texto (título de concurso, etc)
        
        Args:
            texto: Texto contendo possível nome de banca
            
        Returns:
            Nome da banca identificada ou None
        """
        texto_upper = texto.upper()
        
        # Procurar por cada banca
        for banca_nome in self.bancas.keys():
            # Procurar pela sigla principal
            sigla = banca_nome.split('/')[0].strip()
            if sigla in texto_upper:
                return banca_nome
        
        # Aliases comuns
        aliases = {
            'CEBRASPE': 'CESPE/CEBRASPE',
            'CESPE': 'CESPE/CEBRASPE',
            'FUNDAÇÃO CARLOS CHAGAS': 'FCC',
            'GETÚLIO VARGAS': 'FGV',
            'UNESP': 'VUNESP'
        }
        
        for alias, banca_real in aliases.items():
            if alias in texto_upper:
                return banca_real
        
        return None
    
    def comparar_bancas(self, banca1: str, banca2: str) -> Dict:
        """
        Compara duas bancas
        
        Args:
            banca1: Nome da primeira banca
            banca2: Nome da segunda banca
            
        Returns:
            Dicionário com comparação
        """
        info1 = self.obter_info_banca(banca1)
        info2 = self.obter_info_banca(banca2)
        
        if not info1 or not info2:
            return {'erro': 'Uma ou ambas as bancas não foram encontradas'}
        
        return {
            'banca1': {
                'nome': banca1,
                'dificuldade': info1['caracteristicas']['dificuldade'],
                'estilo': info1['caracteristicas']['estilo_questoes'],
                'concursos': info1['estatisticas']['concursos_realizados']
            },
            'banca2': {
                'nome': banca2,
                'dificuldade': info2['caracteristicas']['dificuldade'],
                'estilo': info2['caracteristicas']['estilo_questoes'],
                'concursos': info2['estatisticas']['concursos_realizados']
            },
            'recomendacao': self._gerar_recomendacao_comparacao(info1, info2)
        }
    
    def _gerar_recomendacao_comparacao(self, info1: Dict, info2: Dict) -> str:
        """Gera recomendação baseada na comparação"""
        dif1 = info1['caracteristicas']['dificuldade']
        dif2 = info2['caracteristicas']['dificuldade']
        
        if dif1 == dif2:
            return f"Ambas têm dificuldade {dif1}. Estilos diferentes exigem adaptação."
        elif 'Alta' in dif1 and 'Média' in dif2:
            return f"{info1.get('sigla', 'Primeira')} é mais difícil. Comece pela {info2.get('sigla', 'segunda')}."
        else:
            return "Cada banca tem seu estilo. Pratique questões específicas de cada uma."
    
    def recomendar_materiais(self, banca: str) -> List[str]:
        """
        Recomenda materiais de estudo para uma banca
        
        Args:
            banca: Nome da banca
            
        Returns:
            Lista de recomendações
        """
        info = self.obter_info_banca(banca)
        if not info:
            return []
        
        materiais = [
            f"📚 Resolva questões anteriores da {banca}",
            f"📖 Estude: {', '.join(info['caracteristicas']['disciplinas_fortes'][:3])}",
        ]
        
        # Adicionar estratégias
        materiais.extend([f"✅ {est}" for est in info['estrategias_preparacao'][:3]])
        
        return materiais
    
    def estatisticas_gerais(self) -> Dict:
        """Retorna estatísticas gerais sobre bancas"""
        total_concursos = sum(
            b['estatisticas']['concursos_realizados'] 
            for b in self.bancas.values()
        )
        
        bancas_por_dificuldade = {
            'Alta': [],
            'Média-Alta': [],
            'Média': [],
            'Média-Baixa': []
        }
        
        for nome, info in self.bancas.items():
            dif = info['caracteristicas']['dificuldade']
            bancas_por_dificuldade[dif].append(nome)
        
        return {
            'total_bancas': len(self.bancas),
            'total_concursos_historico': total_concursos,
            'por_dificuldade': bancas_por_dificuldade,
            'top_3_mais_concursos': sorted(
                self.bancas.items(),
                key=lambda x: x[1]['estatisticas']['concursos_realizados'],
                reverse=True
            )[:3]
        }
    
    def adicionar_banca_em_concursos(self, concursos: List[Dict]) -> List[Dict]:
        """
        Adiciona informação de banca aos concursos
        
        Args:
            concursos: Lista de concursos
            
        Returns:
            Lista com campo 'banca' adicionado
        """
        for concurso in concursos:
            # Procurar banca no título ou órgão
            texto_busca = f"{concurso.get('titulo', '')} {concurso.get('orgao', '')}"
            
            banca = self.identificar_banca_em_texto(texto_busca)
            
            if banca:
                info_banca = self.obter_info_banca(banca)
                concurso['banca'] = banca
                concurso['banca_dificuldade'] = info_banca['caracteristicas']['dificuldade']
                concurso['banca_site'] = info_banca['site']
            else:
                concurso['banca'] = 'Não identificada'
                concurso['banca_dificuldade'] = 'N/A'
        
        return concursos


# Exemplo de uso
if __name__ == "__main__":
    print("🏛️ Sistema de Análise de Bancas\n")
    
    sistema = SistemaBancas()
    
    # Listar bancas
    print("📋 Bancas disponíveis:")
    for banca in sistema.listar_bancas():
        print(f"  - {banca}")
    
    # Info de uma banca
    print("\n🔍 Informações CESPE/CEBRASPE:")
    info = sistema.obter_info_banca("CESPE")
    if info:
        print(f"  Dificuldade: {info['caracteristicas']['dificuldade']}")
        print(f"  Estilo: {info['caracteristicas']['estilo_questoes']}")
        print(f"  Concursos realizados: {info['estatisticas']['concursos_realizados']}")
    
    # Comparar bancas
    print("\n⚖️ Comparação FCC vs CESPE:")
    comp = sistema.comparar_bancas("FCC", "CESPE")
    print(f"  Recomendação: {comp.get('recomendacao', 'N/A')}")
    
    # Estatísticas
    print("\n📊 Estatísticas Gerais:")
    stats = sistema.estatisticas_gerais()
    print(f"  Total de bancas: {stats['total_bancas']}")
    print(f"  Concursos históricos: {stats['total_concursos_historico']}")
