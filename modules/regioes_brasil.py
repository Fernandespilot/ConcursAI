"""
Módulo de Mapeamento de Regiões do Brasil
==========================================
Fornece mapeamento de estados para regiões e funções auxiliares
para organização geográfica de concursos
"""

from typing import Dict, List, Optional

# Mapeamento completo de estados para regiões
REGIOES_BRASIL: Dict[str, List[str]] = {
    'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
    'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
    'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
    'Sul': ['PR', 'RS', 'SC']
}

# Mapeamento inverso: Estado -> Região
ESTADO_PARA_REGIAO: Dict[str, str] = {}
for regiao, estados in REGIOES_BRASIL.items():
    for estado in estados:
        ESTADO_PARA_REGIAO[estado] = regiao

# Nomes completos dos estados
ESTADOS_COMPLETOS: Dict[str, str] = {
    'AC': 'Acre',
    'AL': 'Alagoas',
    'AP': 'Amapá',
    'AM': 'Amazonas',
    'BA': 'Bahia',
    'CE': 'Ceará',
    'DF': 'Distrito Federal',
    'ES': 'Espírito Santo',
    'GO': 'Goiás',
    'MA': 'Maranhão',
    'MT': 'Mato Grosso',
    'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais',
    'PA': 'Pará',
    'PB': 'Paraíba',
    'PR': 'Paraná',
    'PE': 'Pernambuco',
    'PI': 'Piauí',
    'RJ': 'Rio de Janeiro',
    'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul',
    'RO': 'Rondônia',
    'RR': 'Roraima',
    'SC': 'Santa Catarina',
    'SP': 'São Paulo',
    'SE': 'Sergipe',
    'TO': 'Tocantins'
}

# Capitais dos estados
CAPITAIS: Dict[str, str] = {
    'AC': 'Rio Branco',
    'AL': 'Maceió',
    'AP': 'Macapá',
    'AM': 'Manaus',
    'BA': 'Salvador',
    'CE': 'Fortaleza',
    'DF': 'Brasília',
    'ES': 'Vitória',
    'GO': 'Goiânia',
    'MA': 'São Luís',
    'MT': 'Cuiabá',
    'MS': 'Campo Grande',
    'MG': 'Belo Horizonte',
    'PA': 'Belém',
    'PB': 'João Pessoa',
    'PR': 'Curitiba',
    'PE': 'Recife',
    'PI': 'Teresina',
    'RJ': 'Rio de Janeiro',
    'RN': 'Natal',
    'RS': 'Porto Alegre',
    'RO': 'Porto Velho',
    'RR': 'Boa Vista',
    'SC': 'Florianópolis',
    'SP': 'São Paulo',
    'SE': 'Aracaju',
    'TO': 'Palmas'
}


def obter_regiao_por_estado(sigla_estado: str) -> Optional[str]:
    """
    Retorna a região de um estado pela sigla
    
    Args:
        sigla_estado: Sigla do estado (ex: 'SP', 'RJ')
        
    Returns:
        Nome da região ou None se estado inválido
    """
    return ESTADO_PARA_REGIAO.get(sigla_estado.upper())


def obter_estados_por_regiao(nome_regiao: str) -> List[str]:
    """
    Retorna lista de estados de uma região
    
    Args:
        nome_regiao: Nome da região (ex: 'Sudeste', 'Norte')
        
    Returns:
        Lista de siglas dos estados ou lista vazia
    """
    return REGIOES_BRASIL.get(nome_regiao, [])


def validar_estado(sigla_estado: str) -> bool:
    """
    Valida se a sigla é de um estado válido
    
    Args:
        sigla_estado: Sigla do estado
        
    Returns:
        True se válido, False caso contrário
    """
    return sigla_estado.upper() in ESTADO_PARA_REGIAO


def extrair_estado_de_texto(texto: str) -> Optional[str]:
    """
    Tenta extrair sigla de estado de um texto
    Procura por siglas de 2 letras maiúsculas ou nomes completos
    
    Args:
        texto: Texto contendo possível estado
        
    Returns:
        Sigla do estado encontrado ou None
    """
    import re
    
    if not texto:
        return None
    
    texto_upper = texto.upper()
    
    # Procurar por siglas diretas (ex: "SP", "RJ")
    for sigla in ESTADO_PARA_REGIAO.keys():
        # Procurar sigla com word boundaries
        if re.search(rf'\b{sigla}\b', texto_upper):
            return sigla
    
    # Procurar por nomes completos
    for sigla, nome_completo in ESTADOS_COMPLETOS.items():
        if nome_completo.upper() in texto_upper:
            return sigla
    
    # Procurar por capitais
    for sigla, capital in CAPITAIS.items():
        if capital.upper() in texto_upper:
            return sigla
    
    return None


def obter_nome_completo_estado(sigla_estado: str) -> Optional[str]:
    """
    Retorna o nome completo do estado
    
    Args:
        sigla_estado: Sigla do estado
        
    Returns:
        Nome completo ou None
    """
    return ESTADOS_COMPLETOS.get(sigla_estado.upper())


def obter_capital(sigla_estado: str) -> Optional[str]:
    """
    Retorna a capital do estado
    
    Args:
        sigla_estado: Sigla do estado
        
    Returns:
        Nome da capital ou None
    """
    return CAPITAIS.get(sigla_estado.upper())


def listar_todas_regioes() -> List[str]:
    """
    Retorna lista com nomes de todas as regiões
    
    Returns:
        Lista de regiões
    """
    return list(REGIOES_BRASIL.keys())


def listar_todos_estados() -> List[str]:
    """
    Retorna lista com siglas de todos os estados
    
    Returns:
        Lista de siglas
    """
    return list(ESTADO_PARA_REGIAO.keys())


def estatisticas_regionais(concursos: List[Dict]) -> Dict:
    """
    Gera estatísticas de concursos por região
    
    Args:
        concursos: Lista de concursos com campo 'estado'
        
    Returns:
        Dicionário com estatísticas por região
    """
    stats = {
        'por_regiao': {regiao: 0 for regiao in REGIOES_BRASIL.keys()},
        'por_estado': {estado: 0 for estado in ESTADO_PARA_REGIAO.keys()},
        'sem_localizacao': 0,
        'total': len(concursos)
    }
    
    for concurso in concursos:
        estado = concurso.get('estado', '').upper()
        
        if not estado or not validar_estado(estado):
            # Tentar extrair do campo localização
            localizacao = concurso.get('localizacao', '')
            estado = extrair_estado_de_texto(localizacao)
        
        if estado and validar_estado(estado):
            stats['por_estado'][estado] += 1
            regiao = obter_regiao_por_estado(estado)
            if regiao:
                stats['por_regiao'][regiao] += 1
        else:
            stats['sem_localizacao'] += 1
    
    return stats


def adicionar_regiao_aos_concursos(concursos: List[Dict]) -> List[Dict]:
    """
    Adiciona campo 'regiao' aos concursos baseado no estado
    
    Args:
        concursos: Lista de concursos
        
    Returns:
        Lista de concursos com campo 'regiao' adicionado
    """
    for concurso in concursos:
        estado = concurso.get('estado', '').upper()
        
        # Se não tem estado, tentar extrair
        if not estado or not validar_estado(estado):
            localizacao = concurso.get('localizacao', '')
            estado = extrair_estado_de_texto(localizacao)
        
        # Adicionar região
        if estado and validar_estado(estado):
            concurso['estado'] = estado
            concurso['regiao'] = obter_regiao_por_estado(estado)
            concurso['estado_nome'] = obter_nome_completo_estado(estado)
        else:
            concurso['regiao'] = 'Nacional/Não identificado'
            concurso['estado_nome'] = 'Não identificado'
    
    return concursos


def filtrar_por_regiao(concursos: List[Dict], regiao: str) -> List[Dict]:
    """
    Filtra concursos por região
    
    Args:
        concursos: Lista de concursos
        regiao: Nome da região
        
    Returns:
        Lista de concursos filtrados
    """
    if regiao not in REGIOES_BRASIL:
        return []
    
    estados_regiao = REGIOES_BRASIL[regiao]
    return [c for c in concursos if c.get('estado', '').upper() in estados_regiao]


def filtrar_por_estado(concursos: List[Dict], estado: str) -> List[Dict]:
    """
    Filtra concursos por estado
    
    Args:
        concursos: Lista de concursos
        estado: Sigla do estado
        
    Returns:
        Lista de concursos filtrados
    """
    estado_upper = estado.upper()
    if not validar_estado(estado_upper):
        return []
    
    return [c for c in concursos if c.get('estado', '').upper() == estado_upper]


# Exemplo de uso
if __name__ == "__main__":
    print("🗺️ Sistema de Regiões do Brasil\n")
    
    # Teste 1: Obter região por estado
    print("1. Região de SP:", obter_regiao_por_estado('SP'))
    print("   Região de BA:", obter_regiao_por_estado('BA'))
    
    # Teste 2: Estados por região
    print("\n2. Estados do Sudeste:", obter_estados_por_regiao('Sudeste'))
    
    # Teste 3: Extrair estado de texto
    print("\n3. Extrair estados de textos:")
    print("   'Concurso em São Paulo':", extrair_estado_de_texto('Concurso em São Paulo'))
    print("   'Edital RJ 2024':", extrair_estado_de_texto('Edital RJ 2024'))
    print("   'Fortaleza - CE':", extrair_estado_de_texto('Fortaleza - CE'))
    
    # Teste 4: Estatísticas
    concursos_teste = [
        {'titulo': 'TRT', 'estado': 'SP'},
        {'titulo': 'Prefeitura', 'localizacao': 'Rio de Janeiro - RJ'},
        {'titulo': 'INSS', 'estado': 'DF'},
        {'titulo': 'PF', 'estado': 'BA'},
    ]
    
    print("\n4. Estatísticas:")
    concursos_teste = adicionar_regiao_aos_concursos(concursos_teste)
    stats = estatisticas_regionais(concursos_teste)
    print(f"   Por região: {stats['por_regiao']}")
    print(f"   Sem localização: {stats['sem_localizacao']}")
