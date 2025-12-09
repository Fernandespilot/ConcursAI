"""
Configurações dos Scrapers
==========================
Configurações centralizadas para os scrapers de concursos
"""

# === CONFIGURAÇÕES GERAIS ===
SCRAPERS_CONFIG = {
    "delay_range": (2, 5),  # Delay entre requests (min, max) em segundos
    "max_workers": 2,       # Número máximo de scrapers simultâneos
    "timeout": 30,          # Timeout para requests em segundos
    "max_retries": 3,       # Número máximo de tentativas por request
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# === CONFIGURAÇÕES POR SITE ===
SITES_CONFIG = {
    "pci_concurso": {
        "base_url": "https://www.pciconcursos.com.br",
        "enabled": True,
        "delay_range": (2, 4),
        "search_path": "/concursos/",
        "selectors": {
            "concurso_items": ["tr.cw", "tr.ca", "div.concurso-item"],
            "title": ["a.ca", "h3", "a.titulo"],
            "orgao": ["span.orgao", "div.instituicao"],
            "local": ["span.local", "div.localizacao"],
            "vagas": ["span.vagas", "div.vagas"],
            "salario": ["span.salario", "div.remuneracao"],
            "status": ["span.situacao", "div.status"]
        }
    },
    "concursos_brasil": {
        "base_url": "https://www.concursosnobrasil.com.br",
        "enabled": True,
        "delay_range": (2, 4),
        "search_path": "/concursos",
        "selectors": {
            "concurso_items": [
                "div.concurso-item", 
                "div.card-concurso", 
                "article.concurso",
                "li.concurso-lista",
                "tr.concurso-row"
            ],
            "title": ["h3", "h2", "a.titulo"],
            "orgao": ["span.orgao", "div.instituicao"],
            "local": ["span.local", "div.localizacao"],
            "vagas": ["span.vagas", "div.vagas"],
            "salario": ["span.salario", "div.remuneracao"],
            "status": ["span.status", "div.situacao"]
        }
    }
}

# === CATEGORIAS DE BUSCA ===
CATEGORIAS_BUSCA = {
    "tecnologia": [
        "programador", "desenvolvedor", "analista de sistemas", 
        "técnico em informática", "TI", "software", "web",
        "banco de dados", "rede", "segurança da informação"
    ],
    "saude": [
        "médico", "enfermeiro", "técnico em enfermagem",
        "farmacêutico", "fisioterapeuta", "psicólogo",
        "dentista", "auxiliar de saúde"
    ],
    "educacao": [
        "professor", "pedagogo", "coordenador pedagógico",
        "diretor escolar", "supervisor escolar", "orientador educacional"
    ],
    "administrativo": [
        "auxiliar administrativo", "assistente administrativo",
        "secretário", "recepcionista", "arquivista",
        "contador", "auxiliar contábil"
    ],
    "juridico": [
        "advogado", "procurador", "defensor público",
        "promotor", "juiz", "escrivão", "oficial de justiça"
    ],
    "seguranca": [
        "policial", "bombeiro", "guarda municipal",
        "agente penitenciário", "inspetor", "investigador"
    ],
    "engenharia": [
        "engenheiro civil", "engenheiro elétrico", "engenheiro mecânico",
        "arquiteto", "técnico em edificações", "topógrafo"
    ]
}

# === CONFIGURAÇÕES DE SAÍDA ===
OUTPUT_CONFIG = {
    "csv_encoding": "utf-8-sig",
    "include_timestamp": True,
    "deduplicate": True,
    "save_individual": True,
    "save_unified": True,
    "save_summary": True,
    "output_directory": "./scraped_data/"
}

# === FILTROS PADRÃO ===
DEFAULT_FILTERS = {
    "min_salary": 0,        # Salário mínimo (0 = sem filtro)
    "max_pages": 10,        # Máximo de páginas por busca
    "estados": [],          # Lista de estados (vazio = todos)
    "escolaridades": [],    # Lista de escolaridades (vazio = todas)
    "status": ["aberto", "ativo", "previsto"]  # Status aceitos
}

# === PALAVRAS-CHAVE PARA LIMPEZA ===
CLEANUP_KEYWORDS = {
    "salary_patterns": [
        r"R\$\s*[\d.,]+",
        r"até\s*R\$\s*[\d.,]+",
        r"(\d+)mil",
        r"salário\s*:\s*([^,\n]+)"
    ],
    "salary_replacements": {
        "mil": ".000,00",
        "R$": "R$ ",
        "até": "até R$"
    },
    "status_mapping": {
        "inscrições abertas": "aberto",
        "em andamento": "ativo",
        "previsto": "previsto",
        "encerrado": "fechado"
    }
}

# === HEADERS HTTP ===
HTTP_HEADERS = {
    "User-Agent": SCRAPERS_CONFIG["user_agent"],
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0"
}

# === CONFIGURAÇÕES DE LOG ===
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "scrapers.log",
    "max_size": "10MB",
    "backup_count": 5
}

# === FUNÇÃO PARA OBTER CONFIGURAÇÃO ===
def get_config(site_name: str = None):
    """
    Retorna configuração para um site específico ou geral
    
    Args:
        site_name: Nome do site ('pci_concurso' ou 'concursos_brasil')
        
    Returns:
        Dicionário com configurações
    """
    if site_name:
        if site_name in SITES_CONFIG:
            config = SITES_CONFIG[site_name].copy()
            config.update(SCRAPERS_CONFIG)
            return config
        else:
            raise ValueError(f"Site '{site_name}' não encontrado na configuração")
    
    return SCRAPERS_CONFIG.copy()

def get_search_terms(categoria: str = None):
    """
    Retorna termos de busca para uma categoria
    
    Args:
        categoria: Nome da categoria
        
    Returns:
        Lista de termos de busca
    """
    if categoria and categoria in CATEGORIAS_BUSCA:
        return CATEGORIAS_BUSCA[categoria]
    
    # Retornar todos os termos se categoria não especificada
    all_terms = []
    for terms in CATEGORIAS_BUSCA.values():
        all_terms.extend(terms)
    
    return list(set(all_terms))  # Remover duplicatas

def get_output_filename(site_name: str, query: str = "", timestamp: str = None):
    """
    Gera nome de arquivo padronizado
    
    Args:
        site_name: Nome do site
        query: Termo de busca
        timestamp: Timestamp (opcional)
        
    Returns:
        Nome do arquivo
    """
    if not timestamp:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    query_clean = query.replace(" ", "_").replace("/", "_") if query else "geral"
    
    return f"concursos_{site_name}_{query_clean}_{timestamp}.csv"

# === VALIDAÇÃO DE CONFIGURAÇÃO ===
def validate_config():
    """Valida se todas as configurações estão corretas"""
    errors = []
    
    # Verificar configurações obrigatórias
    required_keys = ["delay_range", "max_workers", "timeout", "max_retries"]
    for key in required_keys:
        if key not in SCRAPERS_CONFIG:
            errors.append(f"Configuração obrigatória ausente: {key}")
    
    # Verificar configurações de sites
    for site_name, config in SITES_CONFIG.items():
        if "base_url" not in config:
            errors.append(f"base_url ausente para {site_name}")
        
        if "selectors" not in config:
            errors.append(f"selectors ausentes para {site_name}")
    
    if errors:
        raise ValueError("Erros na configuração:\n" + "\n".join(errors))
    
    return True

# Validar configuração ao importar
validate_config()
