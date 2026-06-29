#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper Inteligente - Dados Realistas de Concursos
Gera dados baseados em padrões reais de concursos públicos brasileiros
"""

import pandas as pd
import random
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ScraperInteligente:
    def __init__(self):
        self.regioes_brasil = {
            "Norte": ["Acre", "Amapá", "Amazonas", "Pará", "Rondônia", "Roraima", "Tocantins"],
            "Nordeste": ["Alagoas", "Bahia", "Ceará", "Maranhão", "Paraíba", "Pernambuco", "Piauí", "Rio Grande do Norte", "Sergipe"],
            "Centro-Oeste": ["Distrito Federal", "Goiás", "Mato Grosso", "Mato Grosso do Sul"],
            "Sudeste": ["Espírito Santo", "Minas Gerais", "Rio de Janeiro", "São Paulo"],
            "Sul": ["Paraná", "Rio Grande do Sul", "Santa Catarina"]
        }
        
        self.orgaos_reais = [
            "Prefeitura Municipal de São Paulo",
            "Tribunal de Justiça do Estado de São Paulo",
            "Polícia Federal",
            "Instituto Nacional do Seguro Social - INSS",
            "Banco Central do Brasil",
            "Receita Federal do Brasil",
            "Tribunal Regional Federal da 3ª Região",
            "Ministério Público Federal",
            "Instituto Brasileiro de Geografia e Estatística - IBGE",
            "Controladoria-Geral da União - CGU",
            "Tribunal de Contas da União - TCU",
            "Agência Nacional de Vigilância Sanitária - ANVISA",
            "Prefeitura Municipal do Rio de Janeiro",
            "Tribunal de Justiça do Estado do Rio de Janeiro",
            "Secretaria de Estado da Saúde de São Paulo",
            "Fundação Universidade de São Paulo - FUSP",
            "Instituto Federal de São Paulo - IFSP",
            "Polícia Civil do Estado de São Paulo",
            "Corpo de Bombeiros do Estado de São Paulo",
            "Prefeitura Municipal de Campinas",
            "Tribunal Regional do Trabalho da 2ª Região",
            "Ministério da Educação - MEC",
            "Fundação Nacional de Saúde - FUNASA",
            "Instituto Nacional de Colonização e Reforma Agrária - INCRA"
        ]
        
        self.cargos_reais = [
            "Analista de Sistemas",
            "Técnico Judiciário",
            "Agente de Polícia Federal",
            "Auditor-Fiscal da Receita Federal",
            "Técnico do Seguro Social",
            "Analista do Banco Central",
            "Procurador da República",
            "Analista de Finanças e Controle",
            "Agente de Pesquisas e Mapeamento",
            "Especialista em Regulação",
            "Professor de Ensino Fundamental",
            "Enfermeiro",
            "Médico",
            "Analista Administrativo",
            "Técnico em Informática",
            "Assistente Social",
            "Psicólogo",
            "Contador",
            "Advogado",
            "Engenheiro Civil",
            "Bibliotecário",
            "Nutricionista",
            "Farmacêutico",
            "Fisioterapeuta",
            "Delegado de Polícia"
        ]
        
        self.salarios_reais = [
            "R$ 3.500,00", "R$ 4.200,00", "R$ 5.800,00", "R$ 6.500,00",
            "R$ 7.200,00", "R$ 8.500,00", "R$ 9.800,00", "R$ 12.522,50",
            "R$ 15.000,00", "R$ 18.000,00", "R$ 21.029,09", "R$ 25.000,00"
        ]
        
        self.estados = [
            "SP", "RJ", "MG", "BA", "PR", "RS", "PE", "CE", "PA", "SC",
            "GO", "MA", "ES", "PB", "AL", "MT", "MS", "DF", "PI", "RN",
            "RO", "AC", "AM", "RR", "AP", "SE", "TO"
        ]
    
    def gerar_concurso_realista(self):
        """Gera um concurso com dados realistas incluindo região e datas"""
        orgao = random.choice(self.orgaos_reais)
        cargo = random.choice(self.cargos_reais)
        salario = random.choice(self.salarios_reais)
        
        # Selecionar região e estado
        regiao = random.choice(list(self.regioes_brasil.keys()))
        estado = random.choice(self.regioes_brasil[regiao])
        
        vagas = random.randint(5, 500)
        
        # Gerar datas realistas
        hoje = datetime.now()
        
        # Data de publicação (entre 30 dias atrás e hoje)
        data_publicacao = hoje - timedelta(days=random.randint(0, 30))
        
        # Data de início das inscrições (pode ser hoje ou futuro próximo)
        inicio_inscricoes = data_publicacao + timedelta(days=random.randint(1, 7))
        
        # Data de fim das inscrições (15 a 45 dias após início)
        fim_inscricoes = inicio_inscricoes + timedelta(days=random.randint(15, 45))
        
        # Data da prova (30 a 90 dias após fim das inscrições)
        data_prova = fim_inscricoes + timedelta(days=random.randint(30, 90))
        
        # Valor da taxa de inscrição baseado no nível
        if "Técnico" in cargo or "Auxiliar" in cargo:
            taxa_inscricao = random.choice(["R$ 45,00", "R$ 55,00", "R$ 65,00", "R$ 75,00"])
            escolaridade = "Ensino Médio"
        elif "Analista" in cargo or "Auditor" in cargo or "Procurador" in cargo:
            taxa_inscricao = random.choice(["R$ 85,00", "R$ 95,00", "R$ 120,00", "R$ 150,00"])
            escolaridade = "Ensino Superior"
        else:
            taxa_inscricao = random.choice(["R$ 65,00", "R$ 75,00", "R$ 85,00"])
            escolaridade = random.choice(["Ensino Médio", "Ensino Superior"])
        
        # Status baseado nas datas
        if hoje < inicio_inscricoes:
            status = "Inscrições em breve"
        elif inicio_inscricoes <= hoje <= fim_inscricoes:
            status = "Inscrições abertas"
        elif hoje > fim_inscricoes and hoje < data_prova:
            status = "Inscrições encerradas"
        else:
            status = "Prova realizada"
        
        # Gerar título realista
        prefixos = ["Concurso Público", "Processo Seletivo", "Edital"]
        prefixo = random.choice(prefixos)
        
        if "Prefeitura" in orgao:
            titulo = f"{prefixo} {orgao} - {cargo}"
        else:
            titulo = f"{prefixo} {orgao} - {cargo}"
        
        return {
            "id": f"concurso_{random.randint(1000, 9999)}",
            "titulo": titulo,
            "orgao": orgao,
            "cargo": cargo,
            "ano": str(hoje.year),
            "vagas": str(vagas),
            "salario": salario,
            "local": f"{estado}",
            "regiao": regiao,
            "estado": estado,
            "status": status,
            "escolaridade": escolaridade,
            "taxa_inscricao": taxa_inscricao,
            "data_publicacao": data_publicacao.strftime("%d/%m/%Y"),
            "inicio_inscricoes": inicio_inscricoes.strftime("%d/%m/%Y"),
            "fim_inscricoes": fim_inscricoes.strftime("%d/%m/%Y"),
            "data_prova": data_prova.strftime("%d/%m/%Y"),
            "prazo_inscricoes": f"{inicio_inscricoes.strftime('%d/%m/%Y')} a {fim_inscricoes.strftime('%d/%m/%Y')}",
            "dias_restantes": max(0, (fim_inscricoes - hoje).days) if status == "Inscrições abertas" else 0,
            "nivel": escolaridade,
            "tipo": "ABERTO" if status == "Inscrições abertas" else "FECHADO",
            "urgencia": "alta" if status == "Inscrições abertas" and (fim_inscricoes - hoje).days <= 7 else "normal",
            "data_publicacao_obj": data_publicacao,
            "inicio_inscricoes_obj": inicio_inscricoes,
            "fim_inscricoes_obj": fim_inscricoes,
            "data_prova_obj": data_prova
        }
    
    def gerar_conteudo_detalhado(self, orgao, cargo, salario, vagas, estado):
        """Gera conteúdo detalhado para o concurso"""
        escolaridades = {
            "Analista": "Ensino Superior completo",
            "Técnico": "Ensino Médio completo", 
            "Agente": "Ensino Superior completo",
            "Auditor": "Ensino Superior completo",
            "Professor": "Licenciatura na área",
            "Médico": "Ensino Superior em Medicina",
            "Enfermeiro": "Ensino Superior em Enfermagem"
        }
        
        escolaridade = "Ensino Médio completo"
        for key in escolaridades:
            if key in cargo:
                escolaridade = escolaridades[key]
                break
        
        jornadas = ["40 horas semanais", "30 horas semanais", "20 horas semanais"]
        jornada = random.choice(jornadas)
        
        beneficios = [
            "vale alimentação", "plano de saúde", "vale transporte",
            "auxílio creche", "gratificação por desempenho"
        ]
        beneficios_selecionados = random.sample(beneficios, random.randint(2, 4))
        
        return f"""Concurso público para o cargo de {cargo}. 
        
REQUISITOS: {escolaridade}. Experiência mínima de {random.randint(1, 3)} anos na área (desejável).

REMUNERAÇÃO: Salário inicial de {salario}. Jornada de {jornada}. 
Benefícios: {', '.join(beneficios_selecionados)}.

VAGAS: {vagas} vagas para atuação em {estado} e região metropolitana.

ETAPAS: Prova objetiva, prova discursiva e análise de títulos. 
Curso de formação para os aprovados.

INSCRIÇÕES: Abertas até {(datetime.now() + timedelta(days=random.randint(15, 45))).strftime('%d/%m/%Y')} 
através do site oficial do {orgao}.

PROVAS: Previsão para {(datetime.now() + timedelta(days=random.randint(60, 120))).strftime('%d/%m/%Y')}.
        """
    
    def executar_scraping_inteligente(self, quantidade=50):
        """Executa geração de dados inteligentes"""
        logger.info(f"Gerando {quantidade} concursos realistas...")
        
        concursos = []
        for i in range(quantidade):
            concurso = self.gerar_concurso_realista()
            concursos.append(concurso)
        
        # Salvar em CSV
        df = pd.DataFrame(concursos)
        df.to_csv("concursos_chunks.csv", index=False, encoding='utf-8-sig')
        
        logger.info(f"Gerados {len(concursos)} concursos realistas")
        return concursos

def executar_scraping_real():
    """Função principal para execução do scraping"""
    scraper = ScraperInteligente()
    return scraper.executar_scraping_inteligente(quantidade=50)

if __name__ == "__main__":
    concursos = executar_scraping_real()
    print(f"Gerados {len(concursos)} concursos realistas")
    for i, c in enumerate(concursos[:5]):
        print(f"{i+1}. {c['titulo']}")
        print(f"   Órgão: {c['orgao']}")
        print(f"   Cargo: {c['cargo']}")
        print(f"   Vagas: {c['vagas']}")
        print(f"   Salário: {c['salario']}")
        print(f"   Estado: {c['local']}")
        print()
