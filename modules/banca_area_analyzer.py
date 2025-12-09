"""
🎯 ANALISADOR DE BANCAS POR ÁREA - ConcursAI
=============================================
Sistema parametrizado que analisa PDFs separados por banca
e identifica padrões específicos por área de conhecimento
(Tecnologia, Jurídica, Saúde, Administrativa, etc.)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict, Counter
from pathlib import Path
import re

from modules.banca_analyzer import get_banca_analyzer
from modules.smart_pdf_chunker import get_smart_chunker

logger = logging.getLogger(__name__)


# ============================================
# 📊 ÁREAS DE CONHECIMENTO E SUAS DISCIPLINAS
# ============================================
AREAS_CONHECIMENTO = {
    "Tecnologia": {
        "disciplinas": [
            "Banco de Dados", "Engenharia de Software", "Redes de Computadores",
            "Segurança da Informação", "Programação", "Sistemas Operacionais",
            "Estrutura de Dados", "Arquitetura de Computadores", "DevOps",
            "Cloud Computing", "Big Data", "Inteligência Artificial"
        ],
        "palavras_chave": [
            "sql", "python", "java", "algoritmo", "rede", "servidor", "banco",
            "software", "sistema", "programação", "desenvolvimento", "código",
            "linux", "windows", "tcp/ip", "firewall", "nuvem", "aws", "docker"
        ],
        "nivel_tecnico": "alto",
        "tipo_prova_comum": "multipla_escolha_tecnica"
    },
    
    "Jurídica": {
        "disciplinas": [
            "Direito Constitucional", "Direito Administrativo", 
            "Direito Penal", "Direito Civil", "Direito Processual",
            "Direito Tributário", "Direito do Trabalho", "Direito Previdenciário"
        ],
        "palavras_chave": [
            "lei", "jurisprudência", "stf", "stj", "constituição", "código",
            "processo", "sentença", "recurso", "tribunal", "juiz", "advogado",
            "súmula", "legal", "ilegal", "crime", "pena", "contrato"
        ],
        "nivel_tecnico": "alto",
        "tipo_prova_comum": "certo_errado_legislacao"
    },
    
    "Saúde": {
        "disciplinas": [
            "Enfermagem", "Medicina", "Odontologia", "Farmácia",
            "Nutrição", "Fisioterapia", "Saúde Pública", "Psicologia"
        ],
        "palavras_chave": [
            "paciente", "tratamento", "diagnóstico", "doença", "sus", "saúde",
            "medicamento", "clínica", "hospital", "exame", "sintoma", "cirurgia"
        ],
        "nivel_tecnico": "alto",
        "tipo_prova_comum": "multipla_escolha_clinica"
    },
    
    "Administrativa": {
        "disciplinas": [
            "Administração Geral", "Administração Pública",
            "Gestão de Pessoas", "Orçamento Público", "Contabilidade Pública",
            "Licitações e Contratos"
        ],
        "palavras_chave": [
            "gestão", "planejamento", "controle", "orçamento", "licitação",
            "pregão", "contrato", "administração", "servidor", "público"
        ],
        "nivel_tecnico": "medio",
        "tipo_prova_comum": "multipla_escolha"
    },
    
    "Língua Portuguesa": {
        "disciplinas": ["Português", "Redação", "Interpretação de Texto"],
        "palavras_chave": [
            "gramática", "ortografia", "sintaxe", "texto", "interpretação",
            "redação", "pontuação", "concordância", "regência"
        ],
        "nivel_tecnico": "basico",
        "tipo_prova_comum": "multipla_escolha"
    },
    
    "Conhecimentos Gerais": {
        "disciplinas": [
            "Raciocínio Lógico", "Matemática", "Estatística",
            "Atualidades", "História", "Geografia", "Conhecimentos Gerais"
        ],
        "palavras_chave": [
            "lógica", "matemática", "estatística", "probabilidade",
            "atualidade", "notícia", "brasil", "mundo"
        ],
        "nivel_tecnico": "medio",
        "tipo_prova_comum": "multipla_escolha"
    }
}


# ============================================
# 📂 ESTRUTURA DE DIRETÓRIOS ESPERADA
# ============================================
"""
Estrutura esperada:
provas/
├── cebraspe/
│   ├── tecnologia/
│   │   ├── prova_analista_ti_2024.pdf
│   │   └── gabarito_analista_ti_2024.pdf
│   ├── juridica/
│   │   ├── prova_advogado_2024.pdf
│   │   └── gabarito_advogado_2024.pdf
│   └── administrativa/
│       └── ...
├── fcc/
│   ├── tecnologia/
│   └── ...
├── fgv/
└── vunesp/
"""


class BancaAreaAnalyzer:
    """Analisador parametrizado de bancas por área de conhecimento"""
    
    def __init__(self, base_path: str = "provas"):
        """
        Inicializa o analisador
        
        Args:
            base_path: Caminho base onde estão as pastas de bancas
        """
        self.base_path = Path(base_path)
        self.banca_analyzer = get_banca_analyzer()
        self.pdf_chunker = get_smart_chunker()
        
        # Armazenar perfis por banca + área
        self.perfis = {}  # {banca: {area: perfil}}
        
        # Cache de chunks processados
        self.chunks_cache = defaultdict(list)
        
        logger.info(f"✅ BancaAreaAnalyzer inicializado - Base: {self.base_path}")
    
    
    def detectar_area_automatica(self, chunks: List[Dict]) -> str:
        """
        Detecta automaticamente a área de conhecimento baseado nos chunks
        
        Args:
            chunks: Lista de chunks processados
            
        Returns:
            Nome da área detectada
        """
        # Contar disciplinas por área
        area_scores = defaultdict(int)
        
        for chunk in chunks:
            disciplina = chunk.get("categoria", {}).get("disciplina", "")
            
            # Verificar em qual área a disciplina se encaixa
            for area, config in AREAS_CONHECIMENTO.items():
                if disciplina in config["disciplinas"]:
                    area_scores[area] += 1
        
        if not area_scores:
            return "Conhecimentos Gerais"
        
        # Retornar área com mais ocorrências
        return max(area_scores.items(), key=lambda x: x[1])[0]
    
    
    def organizar_pdfs_existentes(self):
        """
        Organiza PDFs já baixados criando estrutura por área
        Analisa o conteúdo para detectar automaticamente a área
        """
        logger.info("🔄 Organizando PDFs existentes por área...")
        
        bancas = ["cebraspe", "fcc", "fgv", "vunesp"]
        reorganizados = 0
        
        for banca in bancas:
            banca_path = self.base_path / banca
            
            if not banca_path.exists():
                logger.warning(f"⚠️ Pasta não encontrada: {banca_path}")
                continue
            
            # Listar PDFs diretamente na pasta da banca
            pdfs = list(banca_path.glob("*.pdf"))
            
            for pdf in pdfs:
                try:
                    # Processar PDF temporariamente para detectar área
                    resultado = self.pdf_chunker.process_pdf(
                        str(pdf),
                        tipo_doc="prova",
                        banca=banca.upper()
                    )
                    
                    if resultado["success"]:
                        chunks = resultado["chunks"]
                        area = self.detectar_area_automatica(chunks)
                        
                        # Criar pasta da área se não existir
                        area_path = banca_path / area.lower().replace(" ", "_")
                        area_path.mkdir(exist_ok=True)
                        
                        # Mover PDF para pasta da área
                        novo_caminho = area_path / pdf.name
                        if not novo_caminho.exists():
                            pdf.rename(novo_caminho)
                            logger.info(f"📁 {pdf.name} → {area}")
                            reorganizados += 1
                
                except Exception as e:
                    logger.error(f"❌ Erro ao processar {pdf.name}: {e}")
                    continue
        
        logger.info(f"✅ {reorganizados} PDFs reorganizados por área")
        return reorganizados
    
    
    def processar_banca_area(
        self,
        banca: str,
        area: str,
        forcar_reprocessamento: bool = False
    ) -> Dict[str, Any]:
        """
        Processa todos os PDFs de uma banca em uma área específica
        
        Args:
            banca: Nome da banca (cebraspe, fcc, fgv, vunesp)
            area: Área de conhecimento
            forcar_reprocessamento: Se True, reprocessa mesmo que já exista
            
        Returns:
            Perfil completo da banca naquela área
        """
        banca_lower = banca.lower()
        area_normalized = area.lower().replace(" ", "_")
        
        # Verificar se já foi processado
        chave = f"{banca_lower}_{area_normalized}"
        if chave in self.perfis and not forcar_reprocessamento:
            logger.info(f"✅ Usando perfil em cache: {banca} - {area}")
            return self.perfis[chave]
        
        # Caminho da pasta
        pasta_area = self.base_path / banca_lower / area_normalized
        
        if not pasta_area.exists():
            logger.warning(f"⚠️ Pasta não encontrada: {pasta_area}")
            return {"erro": f"Pasta não encontrada: {pasta_area}"}
        
        # Listar PDFs
        pdfs = list(pasta_area.glob("*.pdf"))
        
        if not pdfs:
            logger.warning(f"⚠️ Nenhum PDF encontrado em: {pasta_area}")
            return {"erro": f"Nenhum PDF encontrado"}
        
        logger.info(f"🔄 Processando {len(pdfs)} PDFs - {banca} - {area}")
        
        # Processar cada PDF
        todos_chunks = []
        provas_processadas = []
        gabaritos_processados = []
        
        for pdf in pdfs:
            try:
                # Detectar tipo (prova ou gabarito)
                nome_arquivo = pdf.name.lower()
                tipo_doc = "gabarito" if "gabarito" in nome_arquivo else "prova"
                
                # Processar
                resultado = self.pdf_chunker.process_pdf(
                    str(pdf),
                    tipo_doc=tipo_doc,
                    banca=banca.upper(),
                    metadata={
                        "area": area,
                        "banca": banca,
                        "arquivo": pdf.name
                    }
                )
                
                if resultado["success"]:
                    chunks = resultado["chunks"]
                    todos_chunks.extend(chunks)
                    
                    if tipo_doc == "prova":
                        provas_processadas.append({
                            "arquivo": pdf.name,
                            "questoes": len(chunks),
                            "chunks": chunks
                        })
                    else:
                        gabaritos_processados.append({
                            "arquivo": pdf.name,
                            "respostas": len(chunks)
                        })
                    
                    # Cache
                    self.chunks_cache[chave].extend(chunks)
                    
                    logger.info(f"✅ {pdf.name} - {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"❌ Erro em {pdf.name}: {e}")
                continue
        
        # Gerar perfil da banca nesta área
        perfil = self._gerar_perfil_banca_area(
            banca=banca,
            area=area,
            chunks=todos_chunks,
            provas=provas_processadas,
            gabaritos=gabaritos_processados
        )
        
        # Armazenar
        if banca_lower not in self.perfis:
            self.perfis[banca_lower] = {}
        
        self.perfis[banca_lower][area] = perfil
        self.perfis[chave] = perfil
        
        logger.info(f"✅ Perfil gerado: {banca} - {area}")
        
        return perfil
    
    
    def _gerar_perfil_banca_area(
        self,
        banca: str,
        area: str,
        chunks: List[Dict],
        provas: List[Dict],
        gabaritos: List[Dict]
    ) -> Dict[str, Any]:
        """
        Gera perfil completo de uma banca em uma área específica
        
        Returns:
            Perfil detalhado com estatísticas e análises
        """
        if not chunks:
            return {"erro": "Nenhum chunk processado"}
        
        # Configuração da área
        config_area = AREAS_CONHECIMENTO.get(area, {})
        
        # Estatísticas básicas
        total_questoes = len([c for c in chunks if c.get("tipo") == "questao"])
        
        # Distribuição de disciplinas
        disciplinas = Counter()
        for chunk in chunks:
            disc = chunk.get("categoria", {}).get("disciplina", "Não classificado")
            disciplinas[disc] += 1
        
        # Distribuição de dificuldade
        dificuldades = Counter()
        for chunk in chunks:
            dif = chunk.get("categoria", {}).get("dificuldade", "Não classificado")
            dificuldades[dif] += 1
        
        # Tipos de questão
        tipos = Counter()
        for chunk in chunks:
            tipo = chunk.get("categoria", {}).get("tipo_questao", "Não classificado")
            tipos[tipo] += 1
        
        # Temas mais cobrados
        todos_temas = []
        for chunk in chunks:
            temas = chunk.get("categoria", {}).get("temas", [])
            todos_temas.extend(temas)
        
        temas_frequentes = Counter(todos_temas).most_common(15)
        
        # Análise de padrões específicos da área
        padroes_area = self._analisar_padroes_especificos_area(
            chunks=chunks,
            area=area,
            config_area=config_area
        )
        
        # Gerar recomendações
        recomendacoes = self._gerar_recomendacoes_area(
            banca=banca,
            area=area,
            disciplinas=disciplinas,
            dificuldades=dificuldades,
            temas_frequentes=temas_frequentes,
            padroes_area=padroes_area
        )
        
        # Perfil completo
        perfil = {
            "banca": banca,
            "area": area,
            "data_analise": datetime.now().isoformat(),
            
            # Dados brutos
            "total_provas_analisadas": len(provas),
            "total_gabaritos": len(gabaritos),
            "total_questoes": total_questoes,
            
            # Distribuições
            "distribuicao_disciplinas": {
                disc: {
                    "count": count,
                    "percentual": (count / total_questoes * 100) if total_questoes > 0 else 0
                }
                for disc, count in disciplinas.most_common()
            },
            
            "distribuicao_dificuldade": {
                dif: {
                    "count": count,
                    "percentual": (count / total_questoes * 100) if total_questoes > 0 else 0
                }
                for dif, count in dificuldades.items()
            },
            
            "distribuicao_tipos": {
                tipo: {
                    "count": count,
                    "percentual": (count / total_questoes * 100) if total_questoes > 0 else 0
                }
                for tipo, count in tipos.items()
            },
            
            # Temas
            "temas_mais_cobrados": [
                {"tema": tema, "frequencia": freq}
                for tema, freq in temas_frequentes
            ],
            
            # Padrões específicos da área
            "padroes_especificos": padroes_area,
            
            # Configuração da área
            "config_area": config_area,
            
            # Recomendações
            "recomendacoes": recomendacoes,
            
            # Arquivos processados
            "arquivos": {
                "provas": [p["arquivo"] for p in provas],
                "gabaritos": [g["arquivo"] for g in gabaritos]
            }
        }
        
        return perfil
    
    
    def _analisar_padroes_especificos_area(
        self,
        chunks: List[Dict],
        area: str,
        config_area: Dict
    ) -> Dict[str, Any]:
        """
        Analisa padrões específicos de uma área de conhecimento
        
        Por exemplo:
        - Tecnologia: questões sobre linguagens, frameworks, ferramentas
        - Jurídica: menções a leis, jurisprudência, súmulas
        - Saúde: protocolos, diagnósticos, tratamentos
        """
        padroes = {
            "palavras_chave_detectadas": Counter(),
            "caracteristicas_predominantes": {},
            "nivel_detalhamento": "médio",
            "exemplos": []
        }
        
        palavras_chave_area = config_area.get("palavras_chave", [])
        
        # Contar palavras-chave
        for chunk in chunks:
            conteudo = chunk.get("conteudo", "").lower()
            
            for palavra in palavras_chave_area:
                if palavra in conteudo:
                    padroes["palavras_chave_detectadas"][palavra] += 1
        
        # Top 10 palavras-chave
        padroes["palavras_chave_detectadas"] = dict(
            padroes["palavras_chave_detectadas"].most_common(10)
        )
        
        # Características específicas por área
        if area == "Tecnologia":
            padroes["caracteristicas_predominantes"] = self._analisar_tecnologia(chunks)
        elif area == "Jurídica":
            padroes["caracteristicas_predominantes"] = self._analisar_juridica(chunks)
        elif area == "Saúde":
            padroes["caracteristicas_predominantes"] = self._analisar_saude(chunks)
        
        # Pegar exemplos de questões
        padroes["exemplos"] = [
            {
                "numero": c.get("numero_questao"),
                "disciplina": c.get("categoria", {}).get("disciplina"),
                "conteudo_preview": c.get("conteudo", "")[:150] + "..."
            }
            for c in chunks[:3] if c.get("tipo") == "questao"
        ]
        
        return padroes
    
    
    def _analisar_tecnologia(self, chunks: List[Dict]) -> Dict:
        """Análise específica para área de Tecnologia"""
        linguagens = Counter()
        frameworks = Counter()
        ferramentas = Counter()
        
        keywords_linguagens = ["python", "java", "javascript", "c++", "php", "sql"]
        keywords_frameworks = ["spring", "django", "react", "angular", "vue"]
        keywords_ferramentas = ["git", "docker", "kubernetes", "jenkins", "aws"]
        
        for chunk in chunks:
            conteudo = chunk.get("conteudo", "").lower()
            
            for ling in keywords_linguagens:
                if ling in conteudo:
                    linguagens[ling] += 1
            
            for fw in keywords_frameworks:
                if fw in conteudo:
                    frameworks[fw] += 1
            
            for tool in keywords_ferramentas:
                if tool in conteudo:
                    ferramentas[tool] += 1
        
        return {
            "linguagens_mais_cobradas": dict(linguagens.most_common(5)),
            "frameworks_mencionados": dict(frameworks.most_common(5)),
            "ferramentas_citadas": dict(ferramentas.most_common(5)),
            "foco": "prático" if sum(linguagens.values()) > len(chunks) * 0.3 else "teórico"
        }
    
    
    def _analisar_juridica(self, chunks: List[Dict]) -> Dict:
        """Análise específica para área Jurídica"""
        mencoes_lei = 0
        mencoes_jurisprudencia = 0
        mencoes_sumula = 0
        mencoes_stf = 0
        mencoes_stj = 0
        
        for chunk in chunks:
            conteudo = chunk.get("conteudo", "").lower()
            
            if re.search(r"lei\s+n[º°]?\s*\d+", conteudo):
                mencoes_lei += 1
            if "jurisprudência" in conteudo or "jurisprudencia" in conteudo:
                mencoes_jurisprudencia += 1
            if "súmula" in conteudo or "sumula" in conteudo:
                mencoes_sumula += 1
            if "stf" in conteudo:
                mencoes_stf += 1
            if "stj" in conteudo:
                mencoes_stj += 1
        
        total = len(chunks)
        
        return {
            "percentual_lei_seca": (mencoes_lei / total * 100) if total > 0 else 0,
            "percentual_jurisprudencia": (mencoes_jurisprudencia / total * 100) if total > 0 else 0,
            "percentual_sumula": (mencoes_sumula / total * 100) if total > 0 else 0,
            "tribunal_stf": mencoes_stf,
            "tribunal_stj": mencoes_stj,
            "foco": "lei seca" if mencoes_lei > mencoes_jurisprudencia else "jurisprudência"
        }
    
    
    def _analisar_saude(self, chunks: List[Dict]) -> Dict:
        """Análise específica para área de Saúde"""
        mencoes_diagnostico = 0
        mencoes_tratamento = 0
        mencoes_prevencao = 0
        mencoes_sus = 0
        
        for chunk in chunks:
            conteudo = chunk.get("conteudo", "").lower()
            
            if "diagnóstico" in conteudo or "diagnostico" in conteudo:
                mencoes_diagnostico += 1
            if "tratamento" in conteudo:
                mencoes_tratamento += 1
            if "prevenção" in conteudo or "prevencao" in conteudo:
                mencoes_prevencao += 1
            if "sus" in conteudo:
                mencoes_sus += 1
        
        total = len(chunks)
        
        return {
            "percentual_diagnostico": (mencoes_diagnostico / total * 100) if total > 0 else 0,
            "percentual_tratamento": (mencoes_tratamento / total * 100) if total > 0 else 0,
            "percentual_prevencao": (mencoes_prevencao / total * 100) if total > 0 else 0,
            "mencoes_sus": mencoes_sus,
            "foco": "clínico" if (mencoes_diagnostico + mencoes_tratamento) > mencoes_prevencao else "saúde pública"
        }
    
    
    def _gerar_recomendacoes_area(
        self,
        banca: str,
        area: str,
        disciplinas: Counter,
        dificuldades: Counter,
        temas_frequentes: List[Tuple],
        padroes_area: Dict
    ) -> Dict[str, Any]:
        """Gera recomendações personalizadas para estudar aquela banca + área"""
        
        # Top 3 disciplinas
        top_disciplinas = [disc for disc, _ in disciplinas.most_common(3)]
        
        # Dificuldade predominante
        dif_predominante = max(dificuldades.items(), key=lambda x: x[1])[0] if dificuldades else "Médio"
        
        # Top 5 temas
        top_temas = [tema for tema, _ in temas_frequentes[:5]]
        
        recomendacoes = {
            "foco_disciplinas": top_disciplinas,
            "dificuldade_esperada": dif_predominante,
            "temas_prioritarios": top_temas,
            
            "estrategia_estudo": self._gerar_estrategia_estudo(
                banca, area, top_disciplinas, dif_predominante, padroes_area
            ),
            
            "tempo_sugerido": self._calcular_tempo_estudo(
                area, len(disciplinas), dif_predominante
            ),
            
            "materiais_recomendados": self._recomendar_materiais(
                area, top_disciplinas, padroes_area
            )
        }
        
        return recomendacoes
    
    
    def _gerar_estrategia_estudo(
        self,
        banca: str,
        area: str,
        disciplinas: List[str],
        dificuldade: str,
        padroes: Dict
    ) -> List[str]:
        """Gera estratégias específicas de estudo"""
        
        estrategias = []
        
        # Estratégia geral da banca
        if "CEBRASPE" in banca.upper() or "CESPE" in banca.upper():
            estrategias.append("⚠️ CESPE: Atenção a questões com NEGAÇÃO (incorreto, exceto)")
            estrategias.append("📚 Estude lei seca e jurisprudência recente")
        elif "FCC" in banca.upper():
            estrategias.append("📖 FCC: Foco em lei seca e literalidade")
            estrategias.append("✅ Questões objetivas - evite interpretações extensivas")
        elif "FGV" in banca.upper():
            estrategias.append("🧠 FGV: Interpretação e raciocínio - não decora tudo")
            estrategias.append("🎯 Contextualize os conceitos com exemplos práticos")
        
        # Estratégia por área
        if area == "Tecnologia":
            estrategias.append("💻 Pratique código e comandos práticos")
            estrategias.append("🛠️ Conheça ferramentas e tecnologias atuais")
            
            padroes_tec = padroes.get("caracteristicas_predominantes", {})
            if padroes_tec.get("foco") == "prático":
                estrategias.append("⚙️ Foco PRÁTICO - monte laboratório para testar")
        
        elif area == "Jurídica":
            padroes_jur = padroes.get("caracteristicas_predominantes", {})
            
            if padroes_jur.get("foco") == "lei seca":
                estrategias.append("📜 Foco em LEI SECA - leia e releia os artigos")
            else:
                estrategias.append("⚖️ Foco em JURISPRUDÊNCIA - estude decisões recentes")
            
            estrategias.append("🔍 Monte esquemas e mapas mentais de cada matéria")
        
        elif area == "Saúde":
            padroes_saude = padroes.get("caracteristicas_predominantes", {})
            
            if padroes_saude.get("foco") == "clínico":
                estrategias.append("🏥 Foco CLÍNICO - estude protocolos e diagnósticos")
            else:
                estrategias.append("🏛️ Foco SAÚDE PÚBLICA - políticas e SUS")
        
        # Por dificuldade
        if dificuldade == "Avançado":
            estrategias.append("🎯 Nível AVANÇADO - aprofunde em casos complexos")
            estrategias.append("📈 Resolva questões de bancas anteriores TODOS OS DIAS")
        
        return estrategias
    
    
    def _calcular_tempo_estudo(
        self,
        area: str,
        num_disciplinas: int,
        dificuldade: str
    ) -> Dict[str, Any]:
        """Calcula tempo sugerido de estudo"""
        
        # Base: 2h por disciplina/semana
        horas_base = num_disciplinas * 2
        
        # Ajuste por dificuldade
        if dificuldade == "Avançado":
            horas_base *= 1.5
        elif dificuldade == "Básico":
            horas_base *= 0.8
        
        # Ajuste por área
        if area in ["Tecnologia", "Jurídica", "Saúde"]:
            horas_base *= 1.2  # Áreas técnicas precisam mais tempo
        
        return {
            "horas_semanais": round(horas_base),
            "meses_preparo_sugerido": 3 if dificuldade == "Avançado" else 2,
            "distribuicao": f"{round(horas_base * 0.6)}h teoria + {round(horas_base * 0.4)}h exercícios"
        }
    
    
    def _recomendar_materiais(
        self,
        area: str,
        disciplinas: List[str],
        padroes: Dict
    ) -> List[str]:
        """Recomenda materiais de estudo"""
        
        materiais = []
        
        if area == "Tecnologia":
            materiais.append("📚 Livros técnicos de cada linguagem/ferramenta")
            materiais.append("🎥 Cursos práticos (Udemy, Coursera, Alura)")
            materiais.append("💻 Plataformas de código (GitHub, LeetCode)")
            materiais.append("📖 Documentação oficial das tecnologias")
        
        elif area == "Jurídica":
            materiais.append("📕 Vade Mecum atualizado")
            materiais.append("⚖️ Site do STF/STJ para jurisprudência")
            materiais.append("📚 Livros doutrinários dos autores clássicos")
            materiais.append("🎥 Videoaulas de professores especializados")
        
        elif area == "Saúde":
            materiais.append("📘 Protocolos clínicos atualizados")
            materiais.append("🏥 Manuais do Ministério da Saúde")
            materiais.append("📚 Livros específicos de cada especialidade")
            materiais.append("🎥 Aulas de casos clínicos")
        
        else:
            materiais.append("📚 Livros específicos de cada disciplina")
            materiais.append("🎥 Videoaulas de cursinho preparatório")
            materiais.append("📝 Questões comentadas de bancas anteriores")
        
        return materiais
    
    
    def consultar_perfil(
        self,
        banca: str,
        area: str,
        pergunta: Optional[str] = None
    ) -> str:
        """
        Consulta o perfil de uma banca em uma área
        Opcionalmente responde uma pergunta específica
        
        Args:
            banca: Nome da banca
            area: Área de conhecimento
            pergunta: Pergunta específica (opcional)
            
        Returns:
            Resposta formatada em texto
        """
        banca_lower = banca.lower()
        
        # Verificar se perfil existe
        if banca_lower not in self.perfis or area not in self.perfis[banca_lower]:
            # Tentar processar
            self.processar_banca_area(banca, area)
        
        perfil = self.perfis.get(banca_lower, {}).get(area)
        
        if not perfil or "erro" in perfil:
            return f"❌ Não há dados suficientes para {banca} na área de {area}"
        
        # Se não houver pergunta específica, retorna resumo
        if not pergunta:
            return self._formatar_resumo_perfil(perfil)
        
        # Responder pergunta específica
        return self._responder_pergunta_perfil(perfil, pergunta)
    
    
    def _formatar_resumo_perfil(self, perfil: Dict) -> str:
        """Formata resumo do perfil para exibição"""
        
        banca = perfil.get("banca", "")
        area = perfil.get("area", "")
        
        resumo = f"""
📊 **PERFIL: {banca.upper()} - {area}**
{'='*60}

📈 **Estatísticas Gerais:**
  • Total de provas analisadas: {perfil.get('total_provas_analisadas', 0)}
  • Total de questões: {perfil.get('total_questoes', 0)}

📚 **Top 3 Disciplinas Mais Cobradas:**
"""
        
        # Top disciplinas
        disciplinas = perfil.get("distribuicao_disciplinas", {})
        for i, (disc, dados) in enumerate(list(disciplinas.items())[:3], 1):
            resumo += f"  {i}. {disc}: {dados['percentual']:.1f}% ({dados['count']} questões)\n"
        
        # Dificuldade
        resumo += f"\n📊 **Distribuição de Dificuldade:**\n"
        dificuldades = perfil.get("distribuicao_dificuldade", {})
        for dif, dados in dificuldades.items():
            resumo += f"  • {dif}: {dados['percentual']:.1f}%\n"
        
        # Top temas
        resumo += f"\n🎯 **Top 5 Temas Mais Cobrados:**\n"
        temas = perfil.get("temas_mais_cobrados", [])[:5]
        for i, tema_data in enumerate(temas, 1):
            resumo += f"  {i}. {tema_data['tema']} ({tema_data['frequencia']}x)\n"
        
        # Padrões específicos
        padroes = perfil.get("padroes_especificos", {})
        if padroes:
            carac = padroes.get("caracteristicas_predominantes", {})
            
            if area == "Tecnologia" and carac:
                resumo += f"\n💻 **Padrões de Tecnologia:**\n"
                if "linguagens_mais_cobradas" in carac:
                    resumo += f"  • Linguagens: {', '.join(carac['linguagens_mais_cobradas'].keys())}\n"
                resumo += f"  • Foco: {carac.get('foco', 'N/A')}\n"
            
            elif area == "Jurídica" and carac:
                resumo += f"\n⚖️ **Padrões Jurídicos:**\n"
                resumo += f"  • Lei seca: {carac.get('percentual_lei_seca', 0):.1f}%\n"
                resumo += f"  • Jurisprudência: {carac.get('percentual_jurisprudencia', 0):.1f}%\n"
                resumo += f"  • Foco: {carac.get('foco', 'N/A')}\n"
        
        # Recomendações
        rec = perfil.get("recomendacoes", {})
        if rec:
            resumo += f"\n💡 **Recomendações de Estudo:**\n"
            
            estrategias = rec.get("estrategia_estudo", [])
            for estrategia in estrategias[:3]:
                resumo += f"  {estrategia}\n"
            
            tempo = rec.get("tempo_sugerido", {})
            if tempo:
                resumo += f"\n⏱️ **Tempo Sugerido:**\n"
                resumo += f"  • {tempo.get('horas_semanais', 0)}h por semana\n"
                resumo += f"  • {tempo.get('meses_preparo_sugerido', 0)} meses de preparo\n"
        
        return resumo
    
    
    def _responder_pergunta_perfil(self, perfil: Dict, pergunta: str) -> str:
        """Responde pergunta específica sobre o perfil"""
        
        pergunta_lower = pergunta.lower()
        
        # O que mais cai?
        if "mais cai" in pergunta_lower or "mais cobrado" in pergunta_lower:
            disciplinas = perfil.get("distribuicao_disciplinas", {})
            top_disc = list(disciplinas.items())[0] if disciplinas else ("N/A", {"percentual": 0})
            
            temas = perfil.get("temas_mais_cobrados", [])[:5]
            
            resposta = f"🎯 **O que MAIS CAI em {perfil['banca']} - {perfil['area']}:**\n\n"
            resposta += f"📚 **Disciplina #1:** {top_disc[0]} ({top_disc[1]['percentual']:.1f}%)\n\n"
            resposta += f"🔑 **Temas principais:**\n"
            for tema_data in temas:
                resposta += f"  • {tema_data['tema']}\n"
            
            return resposta
        
        # Dificuldade
        elif "dificuldade" in pergunta_lower or "difícil" in pergunta_lower:
            dificuldades = perfil.get("distribuicao_dificuldade", {})
            
            resposta = f"📊 **Nível de Dificuldade - {perfil['banca']} - {perfil['area']}:**\n\n"
            for dif, dados in dificuldades.items():
                resposta += f"  • {dif}: {dados['percentual']:.1f}%\n"
            
            return resposta
        
        # Como estudar
        elif "como estudar" in pergunta_lower or "estratégia" in pergunta_lower:
            rec = perfil.get("recomendacoes", {})
            estrategias = rec.get("estrategia_estudo", [])
            
            resposta = f"📖 **Como Estudar para {perfil['banca']} - {perfil['area']}:**\n\n"
            for est in estrategias:
                resposta += f"{est}\n"
            
            return resposta
        
        # Tempo necessário
        elif "tempo" in pergunta_lower or "quanto estudar" in pergunta_lower:
            tempo = perfil.get("recomendacoes", {}).get("tempo_sugerido", {})
            
            resposta = f"⏱️ **Tempo de Estudo Recomendado:**\n\n"
            resposta += f"  • {tempo.get('horas_semanais', 0)}h por semana\n"
            resposta += f"  • {tempo.get('meses_preparo_sugerido', 0)} meses de preparação\n"
            resposta += f"  • {tempo.get('distribuicao', 'N/A')}\n"
            
            return resposta
        
        # Resposta genérica
        else:
            return self._formatar_resumo_perfil(perfil)
    
    
    def processar_todas_bancas_areas(self) -> Dict[str, Any]:
        """
        Processa TODAS as bancas e áreas disponíveis
        Gera perfil completo do sistema
        """
        logger.info("🚀 Iniciando processamento completo de todas bancas e áreas...")
        
        bancas = ["cebraspe", "fcc", "fgv", "vunesp"]
        resultados = {}
        
        for banca in bancas:
            banca_path = self.base_path / banca
            
            if not banca_path.exists():
                continue
            
            resultados[banca] = {}
            
            # Listar pastas de áreas
            areas = [d for d in banca_path.iterdir() if d.is_dir()]
            
            for area_path in areas:
                area_nome = area_path.name.replace("_", " ").title()
                
                try:
                    perfil = self.processar_banca_area(banca, area_nome)
                    resultados[banca][area_nome] = {
                        "status": "sucesso",
                        "questoes": perfil.get("total_questoes", 0)
                    }
                except Exception as e:
                    logger.error(f"❌ Erro em {banca}/{area_nome}: {e}")
                    resultados[banca][area_nome] = {
                        "status": "erro",
                        "mensagem": str(e)
                    }
        
        logger.info("✅ Processamento completo finalizado!")
        
        return {
            "status": "concluído",
            "timestamp": datetime.now().isoformat(),
            "resultados": resultados,
            "total_perfis": sum(
                1 for b in resultados.values() 
                for a in b.values() 
                if a.get("status") == "sucesso"
            )
        }


# ============================================
# 🔧 FUNÇÕES AUXILIARES
# ============================================

def get_banca_area_analyzer(base_path: str = "provas") -> BancaAreaAnalyzer:
    """Retorna instância única do analisador"""
    return BancaAreaAnalyzer(base_path=base_path)


if __name__ == "__main__":
    # Teste
    logging.basicConfig(level=logging.INFO)
    
    analyzer = get_banca_area_analyzer()
    
    print("🎯 Sistema de Análise de Bancas por Área")
    print("="*60)
    
    # Organizar PDFs
    print("\n📁 Organizando PDFs existentes...")
    analyzer.organizar_pdfs_existentes()
    
    # Processar CESPE - Tecnologia
    print("\n🔄 Processando CESPE - Tecnologia...")
    perfil = analyzer.processar_banca_area("cebraspe", "Tecnologia")
    
    # Consultar
    print("\n" + "="*60)
    resposta = analyzer.consultar_perfil("cebraspe", "Tecnologia")
    print(resposta)
