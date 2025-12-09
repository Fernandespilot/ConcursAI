"""
🤖 CHAT CONVERSACIONAL COM IA - ConcursAI
Sistema de RAG conversacional para análise de editais com chunking inteligente
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
import requests
from dataclasses import dataclass

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Representa uma mensagem no chat"""
    user_id: str
    message: str
    response: str
    timestamp: datetime
    context_used: List[str]
    model_used: str

class EditalChunker:
    """Divide editais em chunks inteligentes"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_edital(self, edital_text: str, edital_info: Dict) -> List[Dict]:
        """
        Divide o edital em chunks semânticos inteligentes
        
        Args:
            edital_text: Texto completo do edital
            edital_info: Informações sobre o edital
            
        Returns:
            Lista de chunks com metadados
        """
        # Padrões para identificar seções importantes
        section_patterns = [
            r"(?i)(cap[íi]tulo|se[çc][ãa]o|artigo|item)\s*\d+",
            r"(?i)(dos?\s+requisitos?|da\s+inscri[çc][ãa]o|das?\s+provas?)",
            r"(?i)(do\s+concurso|dos?\s+cargos?|das?\s+vagas?)",
            r"(?i)(cronograma|calend[áa]rio|datas?)",
            r"(?i)(conte[úu]do\s+program[áa]tico|programa|mat[ée]rias?)",
            r"(?i)(sal[áa]rios?|remunera[çc][ãa]o|vencimentos?)"
        ]
        
        chunks = []
        
        # Dividir por seções primeiro
        sections = self._split_by_sections(edital_text, section_patterns)
        
        for section_idx, section in enumerate(sections):
            section_chunks = self._split_section(section, edital_info, section_idx)
            chunks.extend(section_chunks)
        
        return chunks
    
    def _split_by_sections(self, text: str, patterns: List[str]) -> List[str]:
        """Divide o texto por seções usando padrões regex"""
        # Combinar todos os padrões
        combined_pattern = "|".join(patterns)
        
        # Encontrar todas as posições de seções
        matches = list(re.finditer(combined_pattern, text, re.IGNORECASE))
        
        if not matches:
            # Se não encontrar seções, dividir por parágrafos
            return self._split_by_paragraphs(text)
        
        sections = []
        start = 0
        
        for match in matches:
            if match.start() > start:
                sections.append(text[start:match.start()].strip())
            start = match.start()
        
        # Adicionar última seção
        if start < len(text):
            sections.append(text[start:].strip())
        
        return [s for s in sections if s.strip()]
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Divide o texto por parágrafos quando não há seções claras"""
        paragraphs = text.split('\n\n')
        sections = []
        current_section = ""
        
        for para in paragraphs:
            if len(current_section + para) > self.chunk_size:
                if current_section:
                    sections.append(current_section.strip())
                current_section = para
            else:
                current_section += "\n\n" + para if current_section else para
        
        if current_section:
            sections.append(current_section.strip())
        
        return sections
    
    def _split_section(self, section_text: str, edital_info: Dict, section_idx: int) -> List[Dict]:
        """Divide uma seção em chunks menores se necessário"""
        chunks = []
        
        if len(section_text) <= self.chunk_size:
            # Seção pequena, usar como um chunk
            chunks.append({
                'text': section_text,
                'chunk_id': f"{edital_info.get('id', 'unknown')}_{section_idx}_0",
                'section_index': section_idx,
                'edital_info': edital_info,
                'chunk_type': 'single_section',
                'size': len(section_text)
            })
        else:
            # Seção grande, dividir em chunks menores
            words = section_text.split()
            current_chunk = []
            current_size = 0
            chunk_counter = 0
            
            for word in words:
                word_size = len(word) + 1  # +1 para espaço
                
                if current_size + word_size > self.chunk_size and current_chunk:
                    # Salvar chunk atual
                    chunk_text = ' '.join(current_chunk)
                    chunks.append({
                        'text': chunk_text,
                        'chunk_id': f"{edital_info.get('id', 'unknown')}_{section_idx}_{chunk_counter}",
                        'section_index': section_idx,
                        'sub_chunk_index': chunk_counter,
                        'edital_info': edital_info,
                        'chunk_type': 'section_part',
                        'size': len(chunk_text)
                    })
                    
                    # Começar novo chunk com overlap
                    overlap_words = current_chunk[-self.overlap//10:] if len(current_chunk) > self.overlap//10 else []
                    current_chunk = overlap_words + [word]
                    current_size = sum(len(w) + 1 for w in current_chunk)
                    chunk_counter += 1
                else:
                    current_chunk.append(word)
                    current_size += word_size
            
            # Adicionar último chunk se houver conteúdo
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'chunk_id': f"{edital_info.get('id', 'unknown')}_{section_idx}_{chunk_counter}",
                    'section_index': section_idx,
                    'sub_chunk_index': chunk_counter,
                    'edital_info': edital_info,
                    'chunk_type': 'section_part',
                    'size': len(chunk_text)
                })
        
        return chunks

class ConversationalRAG:
    """Sistema de RAG conversacional para editais"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.chunker = EditalChunker()
        self.chat_history: Dict[str, List[ChatMessage]] = {}
        self.edital_chunks: Dict[str, List[Dict]] = {}
        self.current_model = "llama3"
        
    def add_edital(self, edital_id: str, edital_text: str, edital_info: Dict) -> bool:
        """
        Adiciona um edital ao sistema de RAG
        
        Args:
            edital_id: ID único do edital
            edital_text: Texto completo do edital
            edital_info: Metadados do edital
            
        Returns:
            True se adicionado com sucesso
        """
        try:
            # Adicionar ID aos metadados
            edital_info['id'] = edital_id
            
            # Chunking inteligente
            chunks = self.chunker.chunk_edital(edital_text, edital_info)
            self.edital_chunks[edital_id] = chunks
            
            logger.info(f"✅ Edital {edital_id} dividido em {len(chunks)} chunks")
            
            # Log dos tamanhos dos chunks
            for i, chunk in enumerate(chunks):
                logger.debug(f"Chunk {i}: {chunk['size']} caracteres")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar edital {edital_id}: {e}")
            return False
    
    def chat_with_edital(self, user_id: str, message: str, edital_id: str) -> Dict:
        """
        Conversa sobre um edital específico
        
        Args:
            user_id: ID do usuário
            message: Pergunta do usuário
            edital_id: ID do edital para consultar
            
        Returns:
            Resposta estruturada
        """
        try:
            # Verificar se o edital existe
            if edital_id not in self.edital_chunks:
                return {
                    'success': False,
                    'error': f'Edital {edital_id} não encontrado. Carregue o edital primeiro.'
                }
            
            # Buscar chunks relevantes
            relevant_chunks = self._find_relevant_chunks(message, edital_id)
            
            # Gerar resposta contextual
            response = self._generate_contextual_response(user_id, message, relevant_chunks, edital_id)
            
            return {
                'success': True,
                'response': response['answer'],
                'sources': response['sources'],
                'chunks_used': len(relevant_chunks),
                'total_chunks': len(self.edital_chunks[edital_id]),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no chat: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_relevant_chunks(self, query: str, edital_id: str, max_chunks: int = 3) -> List[Dict]:
        """
        Encontra chunks relevantes usando busca semântica simples
        """
        chunks = self.edital_chunks[edital_id]
        query_lower = query.lower()
        
        # Palavras-chave da consulta
        query_words = set(re.findall(r'\w+', query_lower))
        
        # Calcular relevância para cada chunk
        chunk_scores = []
        
        for chunk in chunks:
            text_lower = chunk['text'].lower()
            text_words = set(re.findall(r'\w+', text_lower))
            
            # Score baseado em palavras em comum
            common_words = query_words.intersection(text_words)
            word_score = len(common_words) / len(query_words) if query_words else 0
            
            # Bonus para matches exatos de frases
            phrase_score = 0
            for word in query_words:
                if word in text_lower:
                    phrase_score += text_lower.count(word)
            
            total_score = word_score + (phrase_score * 0.1)
            
            chunk_scores.append({
                'chunk': chunk,
                'score': total_score
            })
        
        # Ordenar por relevância e retornar os melhores
        chunk_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return [item['chunk'] for item in chunk_scores[:max_chunks] if item['score'] > 0]
    
    def _generate_contextual_response(self, user_id: str, question: str, chunks: List[Dict], edital_id: str) -> Dict:
        """
        Gera resposta contextual usando os chunks relevantes
        """
        # Preparar contexto
        context_text = "\n\n".join([f"TRECHO {i+1}:\n{chunk['text']}" for i, chunk in enumerate(chunks)])
        
        # Histórico do usuário (últimas 3 mensagens)
        user_history = self.chat_history.get(user_id, [])[-3:]
        history_text = ""
        
        if user_history:
            history_text = "\n".join([
                f"USER: {msg.message}\nASSISTANT: {msg.response}" 
                for msg in user_history
            ])
        
        # Informações do edital
        edital_info = chunks[0]['edital_info'] if chunks else {}
        
        # Prompt otimizado para RAG conversacional
        prompt = f"""
Você é um assistente especializado em concursos públicos e editais. Responda à pergunta do usuário baseando-se EXCLUSIVAMENTE nos trechos do edital fornecidos.

INFORMAÇÕES DO EDITAL:
- Título: {edital_info.get('titulo', 'N/A')}
- Órgão: {edital_info.get('orgao', 'N/A')}
- Estado: {edital_info.get('estado', 'N/A')}

HISTÓRICO DA CONVERSA:
{history_text}

TRECHOS RELEVANTES DO EDITAL:
{context_text}

PERGUNTA DO USUÁRIO: {question}

INSTRUÇÕES:
1. Responda APENAS com base nos trechos fornecidos
2. Se a informação não estiver nos trechos, diga "Esta informação não está nos trechos analisados"
3. Cite qual trecho usou (ex: "Segundo o TRECHO 1...")
4. Seja claro, objetivo e didático
5. Use linguagem acessível para candidatos
6. Se relevante, dê dicas práticas

RESPOSTA:
"""
        
        # Gerar resposta via Ollama
        try:
            response = self._call_ollama(prompt)
            
            # Salvar no histórico
            chat_msg = ChatMessage(
                user_id=user_id,
                message=question,
                response=response,
                timestamp=datetime.now(),
                context_used=[chunk['chunk_id'] for chunk in chunks],
                model_used=self.current_model
            )
            
            if user_id not in self.chat_history:
                self.chat_history[user_id] = []
            
            self.chat_history[user_id].append(chat_msg)
            
            return {
                'answer': response,
                'sources': [chunk['chunk_id'] for chunk in chunks]
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta: {e}")
            return {
                'answer': "Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente.",
                'sources': []
            }
    
    def _call_ollama(self, prompt: str) -> str:
        """Chama a API do Ollama"""
        try:
            data = {
                "model": self.current_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f"❌ Erro na API Ollama: {response.status_code}")
                return "Erro na comunicação com a IA."
                
        except requests.exceptions.ConnectionError:
            return "IA não disponível. Verifique se o Ollama está rodando."
        except Exception as e:
            logger.error(f"❌ Erro na chamada Ollama: {e}")
            return "Erro interno na IA."
    
    def get_chat_history(self, user_id: str) -> List[Dict]:
        """Retorna histórico do chat do usuário"""
        history = self.chat_history.get(user_id, [])
        return [
            {
                'message': msg.message,
                'response': msg.response,
                'timestamp': msg.timestamp.isoformat(),
                'sources': msg.context_used
            }
            for msg in history
        ]
    
    def clear_chat_history(self, user_id: str) -> bool:
        """Limpa histórico do chat do usuário"""
        if user_id in self.chat_history:
            del self.chat_history[user_id]
            return True
        return False
    
    def get_edital_summary(self, edital_id: str) -> Dict:
        """Retorna resumo do edital"""
        if edital_id not in self.edital_chunks:
            return {'error': 'Edital não encontrado'}
        
        chunks = self.edital_chunks[edital_id]
        edital_info = chunks[0]['edital_info'] if chunks else {}
        
        return {
            'edital_info': edital_info,
            'total_chunks': len(chunks),
            'total_size': sum(chunk['size'] for chunk in chunks),
            'chunk_types': list(set(chunk['chunk_type'] for chunk in chunks))
        }

# Instância global
conversational_rag = ConversationalRAG()

if __name__ == "__main__":
    # Teste básico
    rag = ConversationalRAG()
    print("🤖 Sistema de RAG Conversacional iniciado!")
