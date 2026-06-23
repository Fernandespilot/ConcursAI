#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TESTE COLETA PCI CONCURSOS - SIMPLES
========================================
"""

import requests
import pandas as pd
from datetime import datetime
import time

def testar_coleta_pci_simples():
    """Teste simples para coletar alguns concursos do PCI"""
    
    print("🧪 TESTE COLETA PCI CONCURSOS")
    print("=" * 40)
    
    # URLs para teste
    urls_teste = [
        "https://www.pciconcursos.com.br/concursos",
        "https://www.pciconcursos.com.br/concursos/page/1"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for url in urls_teste:
        try:
            print(f"🌐 Testando: {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            print(f"📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Sucesso! Tamanho da resposta: {len(response.content)} bytes")
                
                # Procurar por padrões de concurso
                content = response.text.lower()
                
                if 'concurso' in content:
                    print("🎯 Palavra 'concurso' encontrada no conteúdo")
                
                if 'prefeitura' in content:
                    print("🏛️ Palavra 'prefeitura' encontrada no conteúdo")
                
                if 'vagas' in content:
                    print("👥 Palavra 'vagas' encontrada no conteúdo")
                
                return True
            else:
                print(f"❌ Erro: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro ao acessar {url}: {e}")
            
        time.sleep(2)
    
    return False

def criar_dados_mockados():
    """Cria dados mockados baseados no PCI Concursos"""
    
    print("📝 Criando dados mockados do PCI...")
    
    # Dados realísticos baseados no PCI Concursos
    concursos_mock = [
        {
            'titulo': 'Concurso Público Prefeitura de São Paulo - 1.000 vagas',
            'orgao': 'Prefeitura Municipal de São Paulo',
            'cargo': 'Diversos Cargos',
            'ano': 2024,
            'tipo_documento': 'edital',
            'url': 'https://www.pciconcursos.com.br/concurso/prefeitura-municipal-de-sao-paulo-sp-1000-vagas',
            'data_publicacao': '24/10/2024',
            'fonte': 'PCI Concursos',
            'vagas': 1000,
            'salario': 'R$ 2.500,00 a R$ 15.000,00',
            'escolaridade': 'Fundamental/Médio/Superior',
            'local': 'São Paulo - SP'
        },
        {
            'titulo': 'Concurso INSS 2024 - Técnico do Seguro Social',
            'orgao': 'Instituto Nacional do Seguro Social',
            'cargo': 'Técnico do Seguro Social',
            'ano': 2024,
            'tipo_documento': 'edital',
            'url': 'https://www.pciconcursos.com.br/concurso/instituto-nacional-do-seguro-social-inss-1000-vagas',
            'data_publicacao': '22/10/2024',
            'fonte': 'PCI Concursos',
            'vagas': 1000,
            'salario': 'R$ 5.905,76',
            'escolaridade': 'Ensino Médio',
            'local': 'Nacional'
        },
        {
            'titulo': 'Concurso Tribunal de Justiça SP - Escrevente',
            'orgao': 'Tribunal de Justiça do Estado de São Paulo',
            'cargo': 'Escrevente Técnico Judiciário',
            'ano': 2024,
            'tipo_documento': 'edital',
            'url': 'https://www.pciconcursos.com.br/concurso/tribunal-de-justica-do-estado-de-sao-paulo-sp-2075-vagas',
            'data_publicacao': '20/10/2024',
            'fonte': 'PCI Concursos',
            'vagas': 2075,
            'salario': 'R$ 5.500,00',
            'escolaridade': 'Ensino Médio',
            'local': 'São Paulo - SP'
        },
        {
            'titulo': 'Concurso Banco do Brasil - Escriturário',
            'orgao': 'Banco do Brasil S.A.',
            'cargo': 'Escriturário',
            'ano': 2024,
            'tipo_documento': 'edital',
            'url': 'https://www.pciconcursos.com.br/concurso/banco-do-brasil-sa-bb-6000-vagas',
            'data_publicacao': '18/10/2024',
            'fonte': 'PCI Concursos',
            'vagas': 6000,
            'salario': 'R$ 3.622,23',
            'escolaridade': 'Ensino Médio',
            'local': 'Nacional'
        },
        {
            'titulo': 'Concurso Polícia Federal - Agente e Escrivão',
            'orgao': 'Polícia Federal',
            'cargo': 'Agente/Escrivão de Polícia Federal',
            'ano': 2024,
            'tipo_documento': 'edital',
            'url': 'https://www.pciconcursos.com.br/concurso/policia-federal-pf-1500-vagas',
            'data_publicacao': '16/10/2024',
            'fonte': 'PCI Concursos',
            'vagas': 1500,
            'salario': 'R$ 12.522,50',
            'escolaridade': 'Ensino Superior',
            'local': 'Nacional'
        }
    ]
    
    # Adicionar mais concursos para completar 20
    concursos_adicionais = [
        {
            'titulo': f'Concurso Prefeitura Municipal - Cargo {i}',
            'orgao': f'Prefeitura Municipal {i}',
            'cargo': f'Analista {i}',
            'ano': 2024,
            'tipo_documento': 'edital',
            'url': f'https://www.pciconcursos.com.br/concurso/exemplo-{i}',
            'data_publicacao': f'{10+i}/10/2024',
            'fonte': 'PCI Concursos',
            'vagas': 50 + (i * 10),
            'salario': f'R$ {3000 + (i * 500)},00',
            'escolaridade': 'Ensino Superior',
            'local': f'Cidade {i} - SP'
        }
        for i in range(1, 16)
    ]
    
    todos_concursos = concursos_mock + concursos_adicionais
    
    # Salvar como CSV
    df = pd.DataFrame(todos_concursos)
    filename = "concursos_chunks.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"💾 Dados salvos em: {filename}")
    print(f"📊 Total de concursos: {len(todos_concursos)}")
    
    return filename

if __name__ == "__main__":
    print("🚀 INICIANDO TESTE DE COLETA PCI")
    
    # Tentar coleta real
    sucesso_real = testar_coleta_pci_simples()
    
    if not sucesso_real:
        print("\n🔄 Coleta real falhou, usando dados mockados...")
    
    # Criar dados atualizados
    arquivo = criar_dados_mockados()
    
    print(f"\n✅ Processo concluído!")
    print(f"📁 Arquivo criado: {arquivo}")
    print(f"🌐 Acesse a interface em: http://localhost:8002/editais")
