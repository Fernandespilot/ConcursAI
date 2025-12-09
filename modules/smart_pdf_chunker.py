"""
📄 SMART PDF CHUNKER - ConcursAI
=================================
Sistema inteligente de chunking de PDFs de provas e gabaritos
com categorização automática por assunto, disciplina e dificuldade
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict

# PDF processing
import fitz  # PyMuPDF
import pypdf

# NLP e ML
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class SmartPDFChunker:
    """Chunker inteligente de PDFs de provas e gabaritos"""
    
    # Padrões para identificar diferentes tipos de conteúdo
    PATTERNS = {
        "questao_numero": [
            r"^(\d+)[\.\)]\s",  # "1. " ou "1) "
            r"QUESTÃO\s+(\d+)",
            r"Questão\s+(\d+)"
        ],
        "gabarito": [
            r"GABARITO",
            r"Gabarito",
            r"RESPOSTA",
            r"Chave de Respostas"
        ],
        "disciplinas": {
            "Português": r"(Português|Língua Portuguesa|LP|Gramática|Interpretação de Texto)",
            "Matemática": r"(Matemática|Mat\.|Cálculo|Álgebra)",
            "Raciocínio Lógico": r"(Raciocínio Lógico|R\.? ?L\.?|Lógica|RLM)",
            "Direito Constitucional": r"(Direito Constitucional|Dir\.? Const\.|Constitucional|CF/?88)",
            "Direito Administrativo": r"(Direito Administrativo|Dir\.? Adm\.|Administrativo)",
            "Direito Penal": r"(Direito Penal|Dir\.? Penal|Penal|CP)",
            "Direito Civil": r"(Direito Civil|Dir\.? Civil|Civil|CC)",
            "Informática": r"(Informática|Tecnologia da Informação|TI|Computação)",
            "Conhecimentos Gerais": r"(Conhecimentos Gerais|CG|Atualidades)",
            "Conhecimentos Específicos": r"(Conhecimentos Específicos|CE|Específicos)"
        },
        "tipo_questao": {
            "Múltipla Escolha": r"[ABCDE]\)",
            "Certo/Errado": r"(CERTO|ERRADO|C|E)\s*$",
            "Dissertativa": r"(dissertativa|redação|texto)"
        }
    }
    
    def __init__(self, use_embeddings: bool = True):
        """
        Inicializa o chunker
        
        Args:
            use_embeddings: Se deve usar embeddings para categorização semântica
        """
        self.use_embeddings = use_embeddings
        self.embedder = None
        
        if use_embeddings:
            try:
                self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("✅ Embeddings carregados para chunking semântico")
            except Exception as e:
                logger.warning(f"⚠️ Embeddings não disponíveis: {e}")
                self.use_embeddings = False
        
        # Cache de chunks processados
        self.chunks_cache = {}
    
    def process_pdf(
        self,
        pdf_path: str,
        tipo_doc: str = "prova",  # "prova" ou "gabarito"
        banca: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Processa PDF e gera chunks inteligentes
        
        Args:
            pdf_path: Caminho para o PDF
            tipo_doc: Tipo de documento ("prova" ou "gabarito")
            banca: Nome da banca organizadora
            metadata: Metadados adicionais
            
        Returns:
            Dicionário com chunks categorizados
        """
        try:
            logger.info(f"🔄 Processando PDF: {os.path.basename(pdf_path)}")
            
            # 1. Extrair texto do PDF
            texto_completo, paginas = self._extrair_texto_com_paginas(pdf_path)
            
            # 2. Identificar tipo de documento se não fornecido
            if not tipo_doc or tipo_doc == "auto":
                tipo_doc = self._identificar_tipo_documento(texto_completo)
            
            # 3. Processar baseado no tipo
            if tipo_doc == "prova":
                chunks = self._processar_prova(texto_completo, paginas, banca)
            elif tipo_doc == "gabarito":
                chunks = self._processar_gabarito(texto_completo, paginas)
            else:
                # Fallback: chunking genérico
                chunks = self._chunking_generico(texto_completo, paginas)
            
            # 4. Adicionar metadata
            for chunk in chunks:
                chunk["metadata"].update({
                    "arquivo_origem": os.path.basename(pdf_path),
                    "tipo_documento": tipo_doc,
                    "banca": banca,
                    "processado_em": datetime.now().isoformat(),
                    **(metadata or {})
                })
            
            # 5. Gerar embeddings se habilitado
            if self.use_embeddings and self.embedder:
                chunks = self._adicionar_embeddings(chunks)
            
            resultado = {
                "success": True,
                "arquivo": os.path.basename(pdf_path),
                "tipo_documento": tipo_doc,
                "total_chunks": len(chunks),
                "chunks": chunks,
                "estatisticas": self._gerar_estatisticas(chunks),
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache do resultado
            self.chunks_cache[pdf_path] = resultado
            
            logger.info(f"✅ PDF processado: {len(chunks)} chunks gerados")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar PDF: {e}")
            return {
                "success": False,
                "erro": str(e),
                "arquivo": os.path.basename(pdf_path)
            }
    
    def _extrair_texto_com_paginas(self, pdf_path: str) -> Tuple[str, List[Dict]]:
        """Extrai texto do PDF mantendo informação de páginas"""
        try:
            doc = fitz.open(pdf_path)
            texto_completo = ""
            paginas = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                
                paginas.append({
                    "numero": page_num + 1,
                    "texto": page_text,
                    "caracteres": len(page_text)
                })
                
                texto_completo += f"\n--- PÁGINA {page_num + 1} ---\n{page_text}"
            
            doc.close()
            return texto_completo, paginas
            
        except Exception as e:
            logger.error(f"Erro na extração do PDF: {e}")
            raise
    
    def _identificar_tipo_documento(self, texto: str) -> str:
        """Identifica se é prova ou gabarito"""
        texto_amostra = texto[:2000].upper()
        
        # Procurar por palavras-chave de gabarito
        for padrao in self.PATTERNS["gabarito"]:
            if re.search(padrao, texto_amostra, re.I):
                return "gabarito"
        
        # Se tem muitas questões numeradas, é prova
        questoes = re.findall(r"^(\d+)[\.\)]", texto[:5000], re.MULTILINE)
        if len(questoes) > 5:
            return "prova"
        
        return "desconhecido"
    
    def _processar_prova(
        self,
        texto: str,
        paginas: List[Dict],
        banca: Optional[str]
    ) -> List[Dict]:
        """
        Processa prova, separando por questões e categorizando
        
        Returns:
            Lista de chunks (questões) categorizados
        """
        chunks = []
        
        # 1. Identificar questões
        questoes_raw = self._extrair_questoes(texto)
        
        # 2. Para cada questão, criar chunk categorizado
        for questao_data in questoes_raw:
            chunk = {
                "id": f"questao_{questao_data['numero']}",
                "tipo": "questao",
                "numero_questao": questao_data["numero"],
                "conteudo": questao_data["texto"],
                "metadata": {
                    "pagina_inicio": questao_data.get("pagina", 0),
                    "tamanho_palavras": len(questao_data["texto"].split()),
                    "tamanho_caracteres": len(questao_data["texto"])
                },
                "categoria": {},
                "tags": []
            }
            
            # Categorizar questão
            chunk = self._categorizar_questao(chunk, banca)
            
            chunks.append(chunk)
        
        return chunks
    
    def _extrair_questoes(self, texto: str) -> List[Dict]:
        """Extrai questões individuais do texto"""
        questoes = []
        
        # Padrão para encontrar início de questões
        # Busca por "1.", "2.", etc. no início de linha
        padrao_questao = r"^\s*(\d+)[\.\)]\s*(.*?)(?=^\s*\d+[\.\)]|\Z)"
        
        matches = re.finditer(padrao_questao, texto, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            numero = int(match.group(1))
            texto_questao = match.group(2).strip()
            
            # Identificar página aproximada
            pos = match.start()
            pagina = texto[:pos].count("--- PÁGINA") + 1
            
            questoes.append({
                "numero": numero,
                "texto": texto_questao,
                "pagina": pagina,
                "posicao": pos
            })
        
        # Fallback: se não encontrou questões numeradas, dividir por parágrafos
        if not questoes:
            paragrafos = texto.split('\n\n')
            for i, para in enumerate(paragrafos, 1):
                if len(para.strip()) > 50:  # Apenas parágrafos significativos
                    questoes.append({
                        "numero": i,
                        "texto": para.strip(),
                        "pagina": 0,
                        "posicao": 0
                    })
        
        return questoes
    
    def _categorizar_questao(self, chunk: Dict, banca: Optional[str]) -> Dict:
        """
        Categoriza uma questão por disciplina, tipo, dificuldade
        
        Args:
            chunk: Chunk da questão
            banca: Nome da banca (opcional)
            
        Returns:
            Chunk atualizado com categorização
        """
        texto = chunk["conteudo"]
        
        # 1. Identificar disciplina
        disciplina = self._identificar_disciplina(texto)
        chunk["categoria"]["disciplina"] = disciplina
        chunk["tags"].append(disciplina)
        
        # 2. Identificar tipo de questão
        tipo_questao = self._identificar_tipo_questao(texto)
        chunk["categoria"]["tipo_questao"] = tipo_questao
        chunk["tags"].append(tipo_questao)
        
        # 3. Estimar dificuldade
        dificuldade = self._estimar_dificuldade(texto, banca)
        chunk["categoria"]["dificuldade"] = dificuldade
        chunk["tags"].append(f"dificuldade_{dificuldade}")
        
        # 4. Identificar temas específicos
        temas = self._extrair_temas(texto, disciplina)
        chunk["categoria"]["temas"] = temas
        chunk["tags"].extend(temas)
        
        # 5. Características da questão
        caracteristicas = self._analisar_caracteristicas(texto)
        chunk["categoria"]["caracteristicas"] = caracteristicas
        
        return chunk
    
    def _identificar_disciplina(self, texto: str) -> str:
        """Identifica a disciplina da questão"""
        texto_upper = texto.upper()
        
        scores = {}
        for disciplina, padrao in self.PATTERNS["disciplinas"].items():
            if re.search(padrao, texto, re.I):
                scores[disciplina] = 1.0
            else:
                # Score baseado em palavras-chave específicas
                scores[disciplina] = self._calcular_score_disciplina(texto_upper, disciplina)
        
        if scores:
            melhor_disciplina = max(scores.items(), key=lambda x: x[1])
            if melhor_disciplina[1] > 0.2:  # Threshold mínimo
                return melhor_disciplina[0]
        
        return "Conhecimentos Específicos"
    
    def _calcular_score_disciplina(self, texto: str, disciplina: str) -> float:
        """Calcula score de relevância para uma disciplina"""
        # Palavras-chave por disciplina
        keywords = {
            "Português": ["verbo", "oração", "sujeito", "predicado", "concordância", "regência", "ortografia", "acentuação"],
            "Matemática": ["equação", "função", "porcentagem", "fração", "probabilidade", "estatística", "geometria"],
            "Raciocínio Lógico": ["lógica", "premissa", "conclusão", "silogismo", "proposição", "argumento"],
            "Direito Constitucional": ["constituição", "fundamental", "artigo 5", "CF/88", "constitucional"],
            "Direito Administrativo": ["servidor", "licitação", "contrato", "administrativo", "ato administrativo"],
            "Direito Penal": ["crime", "pena", "dolo", "culpa", "código penal", "delito"],
            "Direito Civil": ["contrato", "propriedade", "posse", "família", "sucessão", "código civil"],
            "Informática": ["computador", "software", "hardware", "internet", "sistema", "rede", "algoritmo"],
            "Conhecimentos Gerais": ["história", "geografia", "política", "economia", "atualidades", "brasil"]
        }
        
        palavras = keywords.get(disciplina, [])
        if not palavras:
            return 0.0
        
        texto_lower = texto.lower()
        encontradas = sum(1 for palavra in palavras if palavra in texto_lower)
        
        return encontradas / len(palavras)
    
    def _identificar_tipo_questao(self, texto: str) -> str:
        """Identifica o tipo de questão"""
        # Verificar múltipla escolha
        if re.search(r"[ABCDE]\)", texto) or re.search(r"alternativa", texto, re.I):
            return "Múltipla Escolha"
        
        # Verificar certo/errado
        if re.search(r"(CERTO|ERRADO)", texto):
            return "Certo/Errado"
        
        # Verificar dissertativa
        if re.search(r"(dissertativa|redação|texto|escreva)", texto, re.I):
            return "Dissertativa"
        
        return "Objetiva"
    
    def _estimar_dificuldade(self, texto: str, banca: Optional[str]) -> str:
        """
        Estima dificuldade da questão
        
        Returns:
            "Básico", "Intermediário" ou "Avançado"
        """
        score_dificuldade = 0
        
        # Tamanho do texto (questões mais longas tendem a ser mais difíceis)
        palavras = len(texto.split())
        if palavras > 150:
            score_dificuldade += 3
        elif palavras > 80:
            score_dificuldade += 2
        else:
            score_dificuldade += 1
        
        # Complexidade vocabular
        palavras_complexas = [p for p in texto.split() if len(p) > 12]
        if len(palavras_complexas) > 10:
            score_dificuldade += 3
        elif len(palavras_complexas) > 5:
            score_dificuldade += 2
        
        # Indicadores de complexidade
        indicadores_avancado = [
            r"jurisprudência",
            r"súmula",
            r"doutrina",
            r"STF|STJ",
            r"exceto",
            r"incorreto",
            r"à exceção"
        ]
        
        for indicador in indicadores_avancado:
            if re.search(indicador, texto, re.I):
                score_dificuldade += 1
        
        # Classificar
        if score_dificuldade >= 7:
            return "Avançado"
        elif score_dificuldade >= 4:
            return "Intermediário"
        else:
            return "Básico"
    
    def _extrair_temas(self, texto: str, disciplina: str) -> List[str]:
        """Extrai temas específicos da questão"""
        temas = []
        
        # Temas por disciplina
        temas_disciplina = {
            "Direito Constitucional": [
                "direitos fundamentais", "organização do Estado", "organização dos poderes",
                "controle de constitucionalidade", "remédios constitucionais"
            ],
            "Direito Administrativo": [
                "atos administrativos", "licitações", "contratos", "servidores públicos",
                "responsabilidade civil", "improbidade administrativa"
            ],
            "Português": [
                "interpretação de texto", "gramática", "ortografia", "concordância",
                "regência", "crase", "pontuação"
            ],
            "Matemática": [
                "álgebra", "geometria", "probabilidade", "estatística",
                "porcentagem", "regra de três", "equações"
            ]
        }
        
        temas_possiveis = temas_disciplina.get(disciplina, [])
        texto_lower = texto.lower()
        
        for tema in temas_possiveis:
            if tema.lower() in texto_lower:
                temas.append(tema)
        
        return temas[:5]  # Limitar a 5 temas mais relevantes
    
    def _analisar_caracteristicas(self, texto: str) -> Dict[str, bool]:
        """Analisa características específicas da questão"""
        return {
            "tem_negacao": bool(re.search(r"(não|nunca|jamais)", texto, re.I)),
            "tem_excecao": bool(re.search(r"(exceto|à exceção|salvo)", texto, re.I)),
            "tem_jurisprudencia": bool(re.search(r"(jurisprudência|súmula|STF|STJ)", texto, re.I)),
            "tem_legislacao": bool(re.search(r"(lei|artigo|CF|CP|CC)", texto, re.I)),
            "questao_longa": len(texto.split()) > 100,
            "tem_contexto": bool(re.search(r"(considerando|situação|contexto)", texto, re.I))
        }
    
    def _processar_gabarito(self, texto: str, paginas: List[Dict]) -> List[Dict]:
        """
        Processa gabarito, extraindo respostas
        
        Returns:
            Lista de chunks com respostas
        """
        chunks = []
        
        # Padrões comuns de gabarito
        # Ex: "1. A", "2 - C", "3: E", etc.
        padrao_gabarito = r"(\d+)[\.\-\:\)]\s*([A-E]|CERTO|ERRADO|C|E)\b"
        
        matches = re.finditer(padrao_gabarito, texto, re.I)
        
        for match in matches:
            numero = int(match.group(1))
            resposta = match.group(2).upper()
            
            chunk = {
                "id": f"gabarito_{numero}",
                "tipo": "gabarito",
                "numero_questao": numero,
                "resposta": resposta,
                "conteudo": f"Questão {numero}: {resposta}",
                "metadata": {
                    "tipo_documento": "gabarito"
                },
                "categoria": {
                    "tipo_resposta": "Múltipla Escolha" if resposta in "ABCDE" else "Certo/Errado"
                },
                "tags": ["gabarito"]
            }
            
            chunks.append(chunk)
        
        return chunks
    
    def _chunking_generico(self, texto: str, paginas: List[Dict]) -> List[Dict]:
        """Chunking genérico para documentos não identificados"""
        chunks = []
        
        # Dividir por parágrafos ou seções
        secoes = re.split(r"\n\n+", texto)
        
        for i, secao in enumerate(secoes, 1):
            if len(secao.strip()) > 50:  # Apenas seções significativas
                chunk = {
                    "id": f"chunk_{i}",
                    "tipo": "secao",
                    "conteudo": secao.strip(),
                    "metadata": {
                        "numero_secao": i,
                        "tamanho_palavras": len(secao.split()),
                        "tamanho_caracteres": len(secao)
                    },
                    "categoria": {},
                    "tags": ["generico"]
                }
                
                chunks.append(chunk)
        
        return chunks
    
    def _adicionar_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Adiciona embeddings aos chunks"""
        try:
            textos = [chunk["conteudo"] for chunk in chunks]
            embeddings = self.embedder.encode(textos, show_progress_bar=False)
            
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = embeddings[i].tolist()
            
            logger.info(f"✅ Embeddings adicionados a {len(chunks)} chunks")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao adicionar embeddings: {e}")
        
        return chunks
    
    def _gerar_estatisticas(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Gera estatísticas sobre os chunks processados"""
        if not chunks:
            return {}
        
        stats = {
            "total_chunks": len(chunks),
            "tipos_chunks": {},
            "disciplinas": {},
            "niveis_dificuldade": {},
            "tipos_questao": {},
            "tamanho_medio_palavras": 0,
            "total_palavras": 0
        }
        
        # Contadores
        tipos = defaultdict(int)
        disciplinas = defaultdict(int)
        dificuldades = defaultdict(int)
        tipos_questao = defaultdict(int)
        
        total_palavras = 0
        
        for chunk in chunks:
            # Tipo de chunk
            tipos[chunk.get("tipo", "desconhecido")] += 1
            
            # Categoria
            cat = chunk.get("categoria", {})
            if "disciplina" in cat:
                disciplinas[cat["disciplina"]] += 1
            if "dificuldade" in cat:
                dificuldades[cat["dificuldade"]] += 1
            if "tipo_questao" in cat:
                tipos_questao[cat["tipo_questao"]] += 1
            
            # Tamanho
            palavras = chunk["metadata"].get("tamanho_palavras", 0)
            total_palavras += palavras
        
        stats["tipos_chunks"] = dict(tipos)
        stats["disciplinas"] = dict(sorted(disciplinas.items(), key=lambda x: x[1], reverse=True))
        stats["niveis_dificuldade"] = dict(dificuldades)
        stats["tipos_questao"] = dict(tipos_questao)
        stats["total_palavras"] = total_palavras
        stats["tamanho_medio_palavras"] = total_palavras / len(chunks) if chunks else 0
        
        return stats
    
    def buscar_chunks(
        self,
        pdf_path: str,
        filtros: Optional[Dict] = None,
        query: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Busca chunks processados com filtros e busca semântica
        
        Args:
            pdf_path: Caminho do PDF processado
            filtros: Filtros (disciplina, dificuldade, tipo, etc.)
            query: Query para busca semântica
            top_k: Número de resultados
            
        Returns:
            Lista de chunks filtrados/rankeados
        """
        # Verificar se PDF já foi processado
        if pdf_path not in self.chunks_cache:
            return []
        
        chunks = self.chunks_cache[pdf_path]["chunks"]
        
        # Aplicar filtros
        if filtros:
            chunks = self._aplicar_filtros(chunks, filtros)
        
        # Busca semântica se query fornecida
        if query and self.use_embeddings and self.embedder:
            chunks = self._busca_semantica(chunks, query, top_k)
        
        return chunks[:top_k]
    
    def _aplicar_filtros(self, chunks: List[Dict], filtros: Dict) -> List[Dict]:
        """Aplica filtros aos chunks"""
        filtrados = chunks
        
        for key, value in filtros.items():
            if key == "disciplina":
                filtrados = [c for c in filtrados if c.get("categoria", {}).get("disciplina") == value]
            elif key == "dificuldade":
                filtrados = [c for c in filtrados if c.get("categoria", {}).get("dificuldade") == value]
            elif key == "tipo":
                filtrados = [c for c in filtrados if c.get("tipo") == value]
            elif key == "tipo_questao":
                filtrados = [c for c in filtrados if c.get("categoria", {}).get("tipo_questao") == value]
        
        return filtrados
    
    def _busca_semantica(self, chunks: List[Dict], query: str, top_k: int) -> List[Dict]:
        """Busca semântica usando embeddings"""
        try:
            # Gerar embedding da query
            query_embedding = self.embedder.encode([query], show_progress_bar=False)[0]
            
            # Calcular similaridade
            scores = []
            for chunk in chunks:
                if "embedding" in chunk:
                    chunk_embedding = np.array(chunk["embedding"])
                    similarity = np.dot(query_embedding, chunk_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                    )
                    scores.append((chunk, similarity))
            
            # Ordenar por similaridade
            scores.sort(key=lambda x: x[1], reverse=True)
            
            return [chunk for chunk, _ in scores[:top_k]]
            
        except Exception as e:
            logger.error(f"Erro na busca semântica: {e}")
            return chunks[:top_k]


# Instância global
smart_chunker = None

def get_smart_chunker() -> SmartPDFChunker:
    """Obtém instância global do chunker"""
    global smart_chunker
    if smart_chunker is None:
        smart_chunker = SmartPDFChunker()
    return smart_chunker


# Teste
if __name__ == "__main__":
    print("📄 TESTE DO SMART PDF CHUNKER\n")
    
    chunker = get_smart_chunker()
    print(f"✅ Chunker inicializado (embeddings: {chunker.use_embeddings})")
    
    # Exemplo de uso (requer PDF real)
    # resultado = chunker.process_pdf("prova_exemplo.pdf", tipo_doc="prova", banca="CESPE/CEBRASPE")
    # print(f"\nChunks gerados: {resultado['total_chunks']}")
    # print(f"Estatísticas: {resultado['estatisticas']}")
