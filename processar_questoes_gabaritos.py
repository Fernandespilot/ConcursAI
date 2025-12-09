#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎓 PROCESSADOR DE PROVAS E GABARITOS
====================================
Processa provas e gabaritos juntos, associando questões com respostas
"""

import os
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import fitz  # PyMuPDF
from collections import defaultdict

class ProcessadorProvasGabaritos:
    def __init__(self, provas_dir="provas"):
        self.provas_dir = Path(provas_dir)
        self.provas_gabaritos = defaultdict(dict)
        self.chunks_qa = []
        
    def organizar_arquivos(self):
        """Organiza provas e seus respectivos gabaritos"""
        
        print("\n📂 ORGANIZANDO PROVAS E GABARITOS")
        print("=" * 60)
        
        for banca_dir in self.provas_dir.iterdir():
            if not banca_dir.is_dir():
                continue
            
            banca = banca_dir.name
            print(f"\n🎯 Banca: {banca.upper()}")
            
            provas = []
            gabaritos = []
            
            for arquivo in banca_dir.glob("*.pdf"):
                nome = arquivo.stem.lower()
                
                if 'gabarito' in nome:
                    gabaritos.append(arquivo)
                elif 'prova' in nome or 'caderno' in nome or 'questoes' in nome:
                    provas.append(arquivo)
            
            print(f"   Provas: {len(provas)}")
            print(f"   Gabaritos: {len(gabaritos)}")
            
            # Tentar associar provas com gabaritos
            for prova in provas:
                gabarito_associado = self._encontrar_gabarito(prova, gabaritos)
                
                concurso_id = self._extrair_id_concurso(prova)
                
                self.provas_gabaritos[concurso_id] = {
                    'prova': prova,
                    'gabarito': gabarito_associado,
                    'banca': banca
                }
        
        print(f"\n✅ Total de provas organizadas: {len(self.provas_gabaritos)}")
        print(f"   Com gabarito: {sum(1 for v in self.provas_gabaritos.values() if v['gabarito'])}")
        
        return self.provas_gabaritos
    
    def _encontrar_gabarito(self, prova: Path, gabaritos: List[Path]) -> Path:
        """Encontra o gabarito correspondente à prova"""
        
        # Extrair partes do nome da prova
        prova_nome = prova.stem.lower()
        prova_partes = set(prova_nome.split('_'))
        
        melhor_match = None
        melhor_score = 0
        
        for gabarito in gabaritos:
            gabarito_nome = gabarito.stem.lower()
            gabarito_partes = set(gabarito_nome.split('_'))
            
            # Calcular similaridade
            comum = prova_partes & gabarito_partes
            score = len(comum)
            
            if score > melhor_score:
                melhor_score = score
                melhor_match = gabarito
        
        return melhor_match if melhor_score >= 2 else None
    
    def _extrair_id_concurso(self, arquivo: Path) -> str:
        """Extrai um ID único do concurso"""
        nome = arquivo.stem
        # Remove sufixos como _prova_, _gabarito_, números
        nome_limpo = re.sub(r'_(prova|gabarito|caderno|questoes)_.*', '', nome)
        return nome_limpo
    
    def processar_todos(self):
        """Processa todas as provas e gabaritos"""
        
        print("\n\n🔄 PROCESSANDO PROVAS E GABARITOS")
        print("=" * 60)
        
        self.organizar_arquivos()
        
        for concurso_id, dados in self.provas_gabaritos.items():
            print(f"\n📝 Processando: {concurso_id}")
            
            try:
                # Extrair texto da prova
                questoes = self._extrair_questoes_prova(dados['prova'])
                print(f"   ✅ {len(questoes)} questões extraídas")
                
                # Extrair gabarito
                respostas = {}
                if dados['gabarito']:
                    respostas = self._extrair_gabarito(dados['gabarito'])
                    print(f"   ✅ {len(respostas)} respostas no gabarito")
                
                # Criar chunks Q&A
                chunks = self._criar_chunks_qa(
                    questoes, 
                    respostas, 
                    dados['banca'],
                    concurso_id
                )
                
                self.chunks_qa.extend(chunks)
                print(f"   ✅ {len(chunks)} chunks Q&A criados")
                
            except Exception as e:
                print(f"   ❌ Erro ao processar: {e}")
                continue
        
        print(f"\n\n✅ PROCESSAMENTO CONCLUÍDO")
        print(f"   Total de chunks Q&A: {len(self.chunks_qa)}")
        
        return self._salvar_chunks()
    
    def _extrair_questoes_prova(self, pdf_path: Path) -> List[Dict]:
        """Extrai questões da prova"""
        
        questoes = []
        
        try:
            doc = fitz.open(pdf_path)
            texto_completo = ""
            
            for pagina in doc:
                texto_completo += pagina.get_text()
            
            doc.close()
            
            # Padrão para identificar questões
            # Formatos comuns: "1)", "01.", "QUESTÃO 1", etc
            padroes_questao = [
                r'(?:QUESTÃO|Questão)\s+(\d+)',
                r'^(\d{1,3})[.)]\s+',
                r'\n(\d{1,3})[.)]\s+'
            ]
            
            for padrao in padroes_questao:
                matches = list(re.finditer(padrao, texto_completo, re.MULTILINE))
                
                if len(matches) > 5:  # Encontrou várias questões
                    for i, match in enumerate(matches):
                        numero_questao = int(match.group(1))
                        inicio = match.start()
                        
                        # Fim da questão = início da próxima ou fim do texto
                        if i < len(matches) - 1:
                            fim = matches[i + 1].start()
                        else:
                            fim = len(texto_completo)
                        
                        texto_questao = texto_completo[inicio:fim].strip()
                        
                        # Limpar texto
                        texto_questao = self._limpar_texto(texto_questao)
                        
                        questoes.append({
                            'numero': numero_questao,
                            'texto': texto_questao,
                            'arquivo': pdf_path.name
                        })
                    
                    break  # Encontrou com este padrão
        
        except Exception as e:
            print(f"      ⚠️ Erro ao extrair questões: {e}")
        
        return questoes
    
    def _extrair_gabarito(self, pdf_path: Path) -> Dict[int, str]:
        """Extrai respostas do gabarito"""
        
        respostas = {}
        
        try:
            doc = fitz.open(pdf_path)
            texto_completo = ""
            
            for pagina in doc:
                texto_completo += pagina.get_text()
            
            doc.close()
            
            # Padrões comuns de gabarito
            # Formato: "01 C", "1) B", "QUESTÃO 1 - LETRA D", etc
            padroes_gabarito = [
                r'(\d{1,3})\s*[:-]?\s*([A-E])',
                r'(\d{1,3})[.)]\s*([A-E])',
                r'QUESTÃO\s+(\d+)\s*[:-]?\s*(?:LETRA\s+)?([A-E])',
            ]
            
            for padrao in padroes_gabarito:
                matches = re.findall(padrao, texto_completo, re.IGNORECASE)
                
                if len(matches) > 5:  # Encontrou várias respostas
                    for numero, letra in matches:
                        respostas[int(numero)] = letra.upper()
                    break
        
        except Exception as e:
            print(f"      ⚠️ Erro ao extrair gabarito: {e}")
        
        return respostas
    
    def _criar_chunks_qa(self, questoes: List[Dict], respostas: Dict[int, str], 
                         banca: str, concurso_id: str) -> List[Dict]:
        """Cria chunks no formato Q&A"""
        
        chunks = []
        
        for questao in questoes:
            numero = questao['numero']
            texto_questao = questao['texto']
            
            # Construir chunk
            chunk = {
                'tipo': 'questao',
                'numero_questao': numero,
                'conteudo_questao': texto_questao,
                'resposta_correta': respostas.get(numero, ''),
                'tem_gabarito': numero in respostas,
                'banca': banca.upper(),
                'concurso_id': concurso_id,
                'arquivo_prova': questao['arquivo']
            }
            
            # Criar texto combinado para embedding (questão + resposta)
            if chunk['tem_gabarito']:
                chunk['conteudo'] = f"QUESTÃO {numero}:\n{texto_questao}\n\nRESPOSTA CORRETA: {chunk['resposta_correta']}"
            else:
                chunk['conteudo'] = f"QUESTÃO {numero}:\n{texto_questao}"
            
            # Extrair metadados
            chunk.update(self._extrair_metadados_questao(texto_questao, concurso_id))
            
            chunks.append(chunk)
        
        return chunks
    
    def _extrair_metadados_questao(self, texto: str, concurso_id: str) -> Dict:
        """Extrai metadados da questão"""
        
        metadados = {
            'area': 'Conhecimentos Gerais',
            'disciplina': '',
            'cargo': '',
            'ano': 2024,
            'orgao': ''
        }
        
        texto_lower = texto.lower()
        
        # Identificar área/disciplina
        areas_disciplinas = {
            'portugues': ('Língua Portuguesa', 'Português'),
            'raciocinio|logica': ('Raciocínio Lógico', 'Raciocínio Lógico'),
            'informatica|tecnologia': ('Informática', 'Tecnologia da Informação'),
            'direito': ('Jurídica', 'Direito'),
            'constitucional': ('Jurídica', 'Direito Constitucional'),
            'administrativo': ('Jurídica', 'Direito Administrativo'),
            'matematica': ('Exatas', 'Matemática'),
        }
        
        for padrao, (area, disciplina) in areas_disciplinas.items():
            if re.search(padrao, texto_lower):
                metadados['area'] = area
                metadados['disciplina'] = disciplina
                break
        
        # Extrair do nome do concurso
        partes = concurso_id.split('_')
        for parte in partes:
            # Ano
            if re.match(r'202\d', parte):
                metadados['ano'] = int(parte)
            # Cargo/Órgão
            elif len(parte) > 3:
                if not metadados['cargo']:
                    metadados['cargo'] = parte.replace('_', ' ').title()
        
        return metadados
    
    def _limpar_texto(self, texto: str) -> str:
        """Limpa e normaliza texto"""
        
        # Remover espaços múltiplos
        texto = re.sub(r'\s+', ' ', texto)
        
        # Remover caracteres especiais mantendo pontuação
        texto = re.sub(r'[^\w\s.,;:?!()\-áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]', '', texto)
        
        return texto.strip()
    
    def _salvar_chunks(self) -> pd.DataFrame:
        """Salva chunks em CSV"""
        
        df = pd.DataFrame(self.chunks_qa)
        
        # Reordenar colunas
        colunas_ordem = [
            'conteudo', 'tipo', 'numero_questao', 'conteudo_questao',
            'resposta_correta', 'tem_gabarito', 'banca', 'area', 'disciplina',
            'cargo', 'ano', 'orgao', 'concurso_id', 'arquivo_prova'
        ]
        
        # Adicionar colunas faltantes
        for col in colunas_ordem:
            if col not in df.columns:
                df[col] = ''
        
        df = df[colunas_ordem]
        
        # Salvar
        output_file = 'concursos_questoes_respostas.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n💾 Arquivo salvo: {output_file}")
        print(f"   Total de linhas: {len(df)}")
        
        # Estatísticas
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   Com gabarito: {df['tem_gabarito'].sum()}")
        print(f"   Sem gabarito: {(~df['tem_gabarito']).sum()}")
        print(f"\n   Por banca:")
        print(df['banca'].value_counts().to_string())
        print(f"\n   Por área:")
        print(df['area'].value_counts().to_string())
        
        return df


def main():
    """Função principal"""
    
    print("=" * 60)
    print("🎓 PROCESSADOR DE PROVAS E GABARITOS")
    print("=" * 60)
    
    processador = ProcessadorProvasGabaritos()
    
    # Processar todos os arquivos
    df = processador.processar_todos()
    
    if len(df) > 0:
        print("\n\n" + "=" * 60)
        resposta = input("\n🤔 Deseja indexar no ChromaDB agora? (s/n): ")
        
        if resposta.lower() in ['s', 'sim', 'y', 'yes']:
            print("\n🔄 Indexando questões e respostas no ChromaDB...")
            
            # Atualizar o CSV principal com as novas questões
            try:
                import pandas as pd
                
                # Carregar CSV existente
                try:
                    df_existente = pd.read_csv('concursos_chunks.csv')
                    print(f"   Chunks existentes: {len(df_existente)}")
                except FileNotFoundError:
                    df_existente = pd.DataFrame()
                
                # Combinar
                if not df_existente.empty:
                    df_final = pd.concat([df_existente, df], ignore_index=True)
                else:
                    df_final = df
                
                # Salvar
                df_final.to_csv('concursos_chunks.csv', index=False, encoding='utf-8-sig')
                print(f"   ✅ Total de chunks: {len(df_final)}")
                
                # Indexar
                os.system("python -m modules.concurso_embeddings")
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
    
    print("\n\n✅ PROCESSO CONCLUÍDO!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
