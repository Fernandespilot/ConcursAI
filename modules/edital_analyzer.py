"""
🧠 ANALISADOR DE EDITAIS COM IA - ConcursAI
Módulo para análise inteligente de editais usando LLMs via Ollama
"""

import requests
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
import aiohttp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EditalAnalyzer:
    """Analisador de editais usando LLMs via Ollama"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """
        Inicializa o analisador
        
        Args:
            ollama_url: URL do servidor Ollama
        """
        self.ollama_url = ollama_url
        self.available_models = []
        self.current_model = "llama3"
        self._check_ollama_connection()
    
    def _check_ollama_connection(self) -> bool:
        """Verifica se o Ollama está disponível"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = [model['name'] for model in models_data.get('models', [])]
                logger.info(f"✅ Ollama conectado! Modelos disponíveis: {self.available_models}")
                return True
            else:
                logger.warning(f"⚠️ Erro na conexão com Ollama: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Ollama não disponível: {e}")
            logger.info("🔄 Sistema funcionará em modo simplificado sem IA")
            return False
    
    def set_model(self, model_name: str) -> bool:
        """Define o modelo LLM a ser usado"""
        if model_name in self.available_models:
            self.current_model = model_name
            logger.info(f"✅ Modelo definido: {model_name}")
            return True
        else:
            logger.error(f"❌ Modelo {model_name} não disponível. Modelos: {self.available_models}")
            return False
    
    def _generate_response(self, prompt: str, model: str = None) -> Optional[str]:
        """Gera resposta usando Ollama ou fallback sem IA"""
        try:
            # Se Ollama não está disponível, usar fallback
            if not self.available_models:
                return self._fallback_response(prompt)
            
            model_to_use = model or self.current_model
            
            data = {
                "model": model_to_use,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Mais determinístico para análises
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=data,
                timeout=60  # Timeout de 60 segundos
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.warning(f"⚠️ Erro na geração: {response.status_code}, usando fallback")
                return self._fallback_response(prompt)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao gerar resposta: {e}, usando fallback")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Resposta de fallback quando Ollama não está disponível"""
        logger.info("🔄 Usando modo simplificado (sem IA)")
        
        # Análise baseada em palavras-chave
        prompt_lower = prompt.lower()
        
        if "analisar edital" in prompt_lower or "análise" in prompt_lower:
            return """**Análise do Edital (Modo Simplificado)**

⚠️ **Sistema funcionando em modo simplificado** - IA não disponível

**Informações extraídas por análise textual:**

📋 **Estrutura padrão de editais:**
- Disposições preliminares
- Dos cargos e vagas
- Dos requisitos e atribuições
- Das inscrições
- Das provas
- Da classificação
- Dos recursos
- Da nomeação e posse

💡 **Para análise completa com IA:**
1. Instale o Ollama: https://ollama.ai
2. Execute: `ollama pull llama3`
3. Reinicie o sistema

📊 **Funcionalidades disponíveis:**
- Busca textual nos editais
- Filtros por órgão, cargo e ano
- Listagem de concursos
- Consulta de dados básicos"""

        elif "explicar" in prompt_lower or "seção" in prompt_lower:
            return """**Explicação da Seção (Modo Simplificado)**

⚠️ Sistema em modo simplificado - análise básica disponível

📖 **Dicas para leitura de editais:**

1. **Leia sempre as disposições preliminares**
2. **Verifique requisitos específicos do cargo**
3. **Atente-se aos prazos de inscrição**
4. **Consulte o conteúdo programático**
5. **Confirme as etapas do processo seletivo**

🔍 **Para explicações detalhadas com IA, instale o Ollama**"""

        elif "dicas" in prompt_lower or "estudo" in prompt_lower:
            return """**Dicas de Estudo (Modo Simplificado)**

📚 **Estratégia geral de estudos:**

1. **Organize seu tempo:**
   - Defina cronograma de estudos
   - Priorize disciplinas com maior peso
   - Reserve tempo para revisões

2. **Estude o edital:**
   - Leia completamente o edital
   - Destaque pontos importantes
   - Entenda a banca organizadora

3. **Material de estudo:**
   - Use livros atualizados
   - Faça questões de provas anteriores
   - Participe de grupos de estudo

4. **Disciplinas comuns:**
   - Português: gramática e interpretação
   - Matemática: básica e raciocínio lógico
   - Conhecimentos gerais: atualidades
   - Específicas: conforme o cargo

💡 **Para dicas personalizadas com IA, instale o Ollama**"""

        elif "comparar" in prompt_lower:
            return """**Comparação de Editais (Modo Simplificado)**

📊 **Para comparar editais manualmente:**

1. **Compare requisitos:**
   - Escolaridade exigida
   - Experiência necessária
   - Idade mínima/máxima

2. **Analise remuneração:**
   - Salário inicial
   - Benefícios oferecidos
   - Progressão na carreira

3. **Verifique processo seletivo:**
   - Tipos de prova
   - Número de fases
   - Critérios de aprovação

4. **Considere localização:**
   - Local de trabalho
   - Possibilidade de remoção
   - Custo de vida da região

🔍 **Para comparação automatizada com IA, instale o Ollama**"""

        else:
            return """**ConcursAI - Modo Simplificado**

⚠️ Sistema funcionando sem IA (Ollama não disponível)

**Funcionalidades ativas:**
✅ Consulta de concursos
✅ Busca textual
✅ Filtros por órgão/cargo/ano
✅ Listagem de dados

**Para funcionalidades avançadas com IA:**
1. Instale Ollama: https://ollama.ai
2. Execute: `ollama pull llama3`
3. Reinicie o sistema

📞 **Suporte:** Sistema funcionando em modo básico"""
    
    def analyze_edital_content(self, edital_text: str, concurso_info: Dict) -> Dict:
        """
        Analisa o conteúdo de um edital e extrai informações relevantes
        
        Args:
            edital_text: Texto completo do edital
            concurso_info: Informações básicas do concurso
            
        Returns:
            Dict com análise completa do edital
        """
        logger.info(f"🧠 Analisando edital: {concurso_info.get('titulo', 'N/A')}")
        
        # Se Ollama não está disponível, usar análise simplificada
        if not self.available_models:
            return self._analyze_edital_fallback(edital_text, concurso_info)
        
        # Prompt estruturado para análise de edital
        prompt = f"""
ANÁLISE ESPECIALIZADA DE EDITAL DE CONCURSO PÚBLICO

DADOS DO CONCURSO:
- Título: {concurso_info.get('titulo', 'N/A')}
- Órgão: {concurso_info.get('orgao', 'N/A')}
- Estado: {concurso_info.get('estado', 'N/A')}
- Data: {concurso_info.get('data_publicacao', 'N/A')}

TEXTO DO EDITAL:
{edital_text[:4000]}  # Limita para não exceder tokens

INSTRUÇÕES:
Analise este edital de concurso público e forneça um relatório estruturado em JSON com as seguintes informações:

1. RESUMO_EXECUTIVO: Resumo em 2-3 frases do que é o concurso
2. CARGOS_DISPONIVEIS: Lista dos cargos com vagas e salários
3. REQUISITOS_GERAIS: Escolaridade, idade, outros requisitos
4. ETAPAS_CONCURSO: Fases do concurso (provas, títulos, etc.)
5. CRONOGRAMA_IMPORTANTE: Datas-chave (inscrições, provas, resultados)
6. CONTEUDO_PROGRAMATICO: Principais matérias por cargo
7. DESTAQUES_IMPORTANTES: Informações cruciais que o candidato deve saber
8. NIVEL_DIFICULDADE: Estimativa de dificuldade (Baixo/Médio/Alto)
9. COMPETITIVIDADE: Análise da concorrência esperada
10. RECOMENDACOES: Dicas estratégicas para os candidatos

Responda APENAS com um JSON válido, sem texto adicional.
"""
        
        try:
            response = self._generate_response(prompt)
            if response:
                # Tenta extrair JSON da resposta
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    analysis['timestamp_analise'] = datetime.now().isoformat()
                    analysis['modelo_usado'] = self.current_model
                    analysis['status'] = 'sucesso'
                    return analysis
                else:
                    # Fallback: resposta em texto livre
                    return {
                        'status': 'texto_livre',
                        'analise_textual': response,
                        'timestamp_analise': datetime.now().isoformat(),
                        'modelo_usado': self.current_model
                    }
            else:
                return self._analyze_edital_fallback(edital_text, concurso_info)
                
        except json.JSONDecodeError:
            logger.warning("⚠️ Erro ao decodificar JSON, usando fallback")
            return self._analyze_edital_fallback(edital_text, concurso_info)
        except Exception as e:
            logger.warning(f"⚠️ Erro na análise: {e}, usando fallback")
            return self._analyze_edital_fallback(edital_text, concurso_info)
    
    def _analyze_edital_fallback(self, edital_text: str, concurso_info: Dict) -> Dict:
        """Análise simplificada sem IA"""
        logger.info("🔄 Usando análise simplificada (sem IA)")
        
        # Análise baseada em palavras-chave e padrões
        texto_lower = edital_text.lower()
        
        # Extrair informações básicas por palavras-chave
        analysis = {
            'status': 'modo_simplificado',
            'resumo_executivo': f"Concurso público do(a) {concurso_info.get('orgao', 'N/A')} para o cargo de {concurso_info.get('titulo', 'N/A')}.",
            'modo': 'fallback_sem_ia',
            'timestamp_analise': datetime.now().isoformat(),
            'informacoes_basicas': {
                'titulo': concurso_info.get('titulo', 'N/A'),
                'orgao': concurso_info.get('orgao', 'N/A'),
                'estado': concurso_info.get('estado', 'N/A'),
                'data_publicacao': concurso_info.get('data_publicacao', 'N/A')
            }
        }
        
        # Detectar palavras-chave importantes
        keywords_found = []
        if 'salário' in texto_lower or 'remuneração' in texto_lower:
            keywords_found.append('remuneração')
        if 'inscrição' in texto_lower or 'inscrições' in texto_lower:
            keywords_found.append('inscrições')
        if 'prova' in texto_lower or 'provas' in texto_lower:
            keywords_found.append('provas')
        if 'requisito' in texto_lower or 'requisitos' in texto_lower:
            keywords_found.append('requisitos')
        if 'cronograma' in texto_lower or 'prazo' in texto_lower:
            keywords_found.append('cronograma')
        
        analysis['palavras_chave_detectadas'] = keywords_found
        
        analysis['recomendacoes'] = [
            "Para análise completa com IA, instale o Ollama",
            "Leia o edital completo com atenção",
            "Verifique os requisitos específicos do cargo",
            "Atente-se aos prazos de inscrição",
            "Consulte o conteúdo programático das provas"
        ]
        
        analysis['aviso'] = "Análise básica - Para análise detalhada com IA, instale o Ollama (https://ollama.ai)"
        
        return analysis
    
    def explain_edital_section(self, section_text: str, section_name: str) -> str:
        """
        Explica uma seção específica do edital em linguagem simples
        
        Args:
            section_text: Texto da seção
            section_name: Nome da seção
            
        Returns:
            Explicação simplificada
        """
        # Se Ollama não está disponível, usar explicação simplificada
        if not self.available_models:
            return self._explain_section_fallback(section_text, section_name)
        
        prompt = f"""
Você é um especialista em concursos públicos. Explique a seguinte seção de edital de forma simples e clara:

SEÇÃO: {section_name}
TEXTO: {section_text[:2000]}

INSTRUÇÕES:
- Use linguagem simples e acessível
- Destaque os pontos mais importantes
- Explique termos técnicos se houver
- Seja objetivo e prático
- Forneça dicas úteis para o candidato

Responda de forma direta, sem preâmbulos.
"""
        
        response = self._generate_response(prompt)
        return response or self._explain_section_fallback(section_text, section_name)
    
    def _explain_section_fallback(self, section_text: str, section_name: str) -> str:
        """Explicação simplificada sem IA"""
        return f"""**Explicação da Seção: {section_name}** (Modo Simplificado)

📄 **Texto da seção:** 
{section_text[:500]}{'...' if len(section_text) > 500 else ''}

📝 **Dicas gerais para leitura de editais:**

• **Leia com atenção:** Cada palavra tem importância legal
• **Destaque pontos-chave:** Use marca-texto para informações importantes
• **Anote dúvidas:** Liste pontos que precisam de esclarecimento
• **Verifique prazos:** Atenção especial a datas e cronogramas
• **Consulte legislação:** Se houver referências a leis específicas

⚠️ **Para explicações detalhadas com IA, instale o Ollama**
🔗 https://ollama.ai"""
    
    def generate_study_tips(self, cargo: str, conteudo_programatico: List[str]) -> Dict:
        """
        Gera dicas de estudo personalizadas para um cargo
        
        Args:
            cargo: Nome do cargo
            conteudo_programatico: Lista de matérias
            
        Returns:
            Dicas de estudo estruturadas
        """
        # Se Ollama não está disponível, usar dicas gerais
        if not self.available_models:
            return self._generate_study_tips_fallback(cargo, conteudo_programatico)
        
        materias_texto = "\n".join([f"- {materia}" for materia in conteudo_programatico])
        
        prompt = f"""
CARGO: {cargo}
CONTEÚDO PROGRAMÁTICO:
{materias_texto}

Como especialista em concursos públicos, crie um plano de estudos estratégico.

Forneça um JSON com:
1. PRIORIDADES: Ordem das matérias por importância
2. TEMPO_ESTUDO: Sugestão de distribuição de tempo
3. MATERIAIS_RECOMENDADOS: Tipos de material por matéria
4. ESTRATEGIA_REVISAO: Como revisar cada matéria
5. DICAS_ESPECIFICAS: Dicas específicas para este cargo
6. CRONOGRAMA_SUGERIDO: Cronograma de estudos em semanas

Responda apenas com JSON válido.
"""
        
        try:
            response = self._generate_response(prompt)
            if response:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
            return self._generate_study_tips_fallback(cargo, conteudo_programatico)
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao gerar dicas: {e}, usando fallback")
            return self._generate_study_tips_fallback(cargo, conteudo_programatico)
    
    def _generate_study_tips_fallback(self, cargo: str, conteudo_programatico: List[str]) -> Dict:
        """Dicas de estudo simplificadas sem IA"""
        
        # Dicas baseadas em padrões comuns
        materias_basicas = ['português', 'matemática', 'conhecimentos gerais', 'informática']
        materias_juridicas = ['direito', 'lei', 'código', 'constituição']
        materias_tecnicas = ['técnico', 'específico', 'engenharia', 'contabilidade']
        
        materias_lower = [m.lower() for m in conteudo_programatico]
        
        # Classificar tipo de concurso
        tipo_concurso = "geral"
        if any(mat in ' '.join(materias_lower) for mat in materias_juridicas):
            tipo_concurso = "jurídico"
        elif any(mat in ' '.join(materias_lower) for mat in materias_tecnicas):
            tipo_concurso = "técnico"
        
        dicas = {
            "status": "modo_simplificado",
            "cargo": cargo,
            "tipo_concurso": tipo_concurso,
            "materias_identificadas": len(conteudo_programatico),
            "prioridades": {
                "alta_prioridade": [],
                "media_prioridade": [],
                "baixa_prioridade": []
            },
            "tempo_estudo": {
                "sugestao_diaria": "4-6 horas",
                "distribuicao": "60% específicas, 40% básicas"
            },
            "dicas_gerais": [
                "Foque nas matérias de maior peso",
                "Faça questões de provas anteriores",
                "Crie cronograma realista",
                "Reserve tempo para revisões",
                "Mantenha constância nos estudos"
            ],
            "materiais_recomendados": {
                "livros": "Material atualizado da área",
                "questoes": "Questões de bancas similares",
                "videos": "Videoaulas para fixação",
                "mapas": "Mapas mentais para revisão"
            },
            "cronograma_sugerido": {
                "fase1": "Teoria básica (4-6 semanas)",
                "fase2": "Aprofundamento (6-8 semanas)",
                "fase3": "Questões intensivas (4 semanas)",
                "fase4": "Revisão final (2 semanas)"
            },
            "aviso": "Dicas gerais - Para plano personalizado com IA, instale o Ollama"
        }
        
        # Classificar matérias por prioridade baseado em padrões
        for materia in conteudo_programatico:
            materia_lower = materia.lower()
            if any(basica in materia_lower for basica in materias_basicas):
                dicas["prioridades"]["alta_prioridade"].append(materia)
            elif tipo_concurso == "jurídico" and any(jur in materia_lower for jur in materias_juridicas):
                dicas["prioridades"]["alta_prioridade"].append(materia)
            elif "específic" in materia_lower or cargo.lower() in materia_lower:
                dicas["prioridades"]["alta_prioridade"].append(materia)
            else:
                dicas["prioridades"]["media_prioridade"].append(materia)
        
        return dicas
    
    def compare_editais(self, edital1: Dict, edital2: Dict) -> Dict:
        """
        Compara dois editais e destaca diferenças importantes
        
        Args:
            edital1: Primeiro edital
            edital2: Segundo edital
            
        Returns:
            Comparação estruturada
        """
        prompt = f"""
Compare estes dois editais de concurso público:

EDITAL 1:
- Título: {edital1.get('titulo', 'N/A')}
- Órgão: {edital1.get('orgao', 'N/A')}
- Vagas: {edital1.get('vagas', 'N/A')}
- Salário: {edital1.get('salario', 'N/A')}

EDITAL 2:
- Título: {edital2.get('titulo', 'N/A')}
- Órgão: {edital2.get('orgao', 'N/A')}
- Vagas: {edital2.get('vagas', 'N/A')}
- Salário: {edital2.get('salario', 'N/A')}

Forneça uma comparação estruturada em JSON:
1. VANTAGENS_EDITAL1: Pontos favoráveis do primeiro
2. VANTAGENS_EDITAL2: Pontos favoráveis do segundo
3. DIFERENCAS_PRINCIPAIS: Principais diferenças
4. RECOMENDACAO: Qual é mais vantajoso e por quê
5. FATORES_DECISAO: O que considerar na escolha

Responda apenas com JSON válido.
"""
        
        try:
            response = self._generate_response(prompt)
            if response:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
            return {"erro": "Não foi possível comparar os editais"}
            
        except Exception as e:
            logger.error(f"❌ Erro na comparação: {e}")
            return {"erro": str(e)}
    
    async def analyze_multiple_editais(self, editais_list: List[Dict]) -> List[Dict]:
        """
        Analisa múltiplos editais de forma assíncrona
        
        Args:
            editais_list: Lista de editais para analisar
            
        Returns:
            Lista com análises dos editais
        """
        logger.info(f"🔄 Analisando {len(editais_list)} editais...")
        
        async def analyze_single(edital):
            return self.analyze_edital_content(
                edital.get('conteudo', ''),
                edital
            )
        
        # Analisa até 5 editais simultaneamente para não sobrecarregar
        semaphore = asyncio.Semaphore(5)
        
        async def analyze_with_limit(edital):
            async with semaphore:
                return await analyze_single(edital)
        
        tasks = [analyze_with_limit(edital) for edital in editais_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtra resultados válidos
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Erro no edital {i}: {result}")
                valid_results.append({
                    'status': 'erro',
                    'mensagem': str(result),
                    'edital_index': i
                })
            else:
                valid_results.append(result)
        
        return valid_results
    
    def get_health_status(self) -> Dict:
        """Retorna status do analisador"""
        return {
            'ollama_conectado': bool(self.available_models),
            'modelos_disponiveis': self.available_models,
            'modelo_atual': self.current_model,
            'url_ollama': self.ollama_url,
            'timestamp': datetime.now().isoformat()
        }

# Instância global para uso em outros módulos
edital_analyzer = EditalAnalyzer()

if __name__ == "__main__":
    # Teste básico
    analyzer = EditalAnalyzer()
    print("🔍 Status do Analisador:")
    print(json.dumps(analyzer.get_health_status(), indent=2, ensure_ascii=False))
