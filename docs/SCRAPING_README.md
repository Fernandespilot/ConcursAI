# 🕷️ SCRAPING AUTOMÁTICO - CONCURSAI

## 📋 VISÃO GERAL

Sistema de coleta automática de editais de concursos públicos integrado ao ConcursAI. Coleta PDFs de sites oficiais, indexa no ChromaDB e atualiza a IA em tempo real.

---

## 🎯 FUNCIONALIDADES

### ✅ O que o Sistema Faz

1. **Coleta Automática**: Navega em sites de bancas e baixa editais
2. **Download Inteligente**: Identifica e baixa apenas PDFs relevantes
3. **Indexação Automática**: Adiciona ao RAG sem intervenção manual
4. **Agendamento**: Coleta diária ou semanal configurável
5. **Metadados Automáticos**: Extrai banca, tipo, data automaticamente

### 🏛️ Bancas Suportadas

| Banca | Status | URL Base |
|-------|--------|----------|
| **Cebraspe** | ✅ Ativo | cebraspe.org.br |
| **FGV** | ✅ Ativo | conhecimento.fgv.br |
| **FCC** | 🔜 Próximo | concursosfcc.com.br |
| **Vunesp** | 🔜 Próximo | vunesp.com.br |

---

## 🚀 COMO USAR

### Método 1: Interface Web (Recomendado)

1. **Inicie o ConcursAI**:
   ```bash
   streamlit run src/app.py
   ```

2. **Acesse a aba "🕷️ Scraping Auto"**

3. **Coleta Imediata**:
   - Escolha a banca (Cebraspe ou FGV)
   - Defina máximo de concursos
   - Clique em **"🕷️ Coletar [BANCA]"**
   - Aguarde ~2-5 minutos
   - PDFs são baixados e indexados automaticamente!

4. **Agendar Coleta**:
   - Escolha **Diária** ou **Semanal**
   - Selecione horário/dia
   - Clique em **"📅 Agendar"**
   - Sistema coleta automaticamente sem precisar abrir a interface!

### Método 2: Script Python

```python
from scrapers.scraper_scheduler import (
    coletar_agora,
    coletar_todas_agora,
    agendar_diario,
    obter_status
)

# Coleta imediata de uma banca
coletar_agora('cebraspe', max_concursos=5)

# Coleta de todas as bancas
coletar_todas_agora(max_concursos=3)

# Agendar coleta diária às 6h
agendar_diario(hora=6, minuto=0)

# Verificar status
status = obter_status()
print(status)
```

### Método 3: Terminal

```bash
# Coleta única (teste)
python -c "from scrapers.scraper_scheduler import coletar_agora; coletar_agora('cebraspe', 2)"

# Iniciar scheduler em background
python scrapers/scraper_scheduler.py

# Ou use o script batch (Windows)
INICIAR_SCRAPING.bat
```

---

## 📂 ESTRUTURA DE ARQUIVOS

```
ConcursAI/
├── scrapers/
│   ├── __init__.py
│   ├── cebraspe_scraper.py        ← Scraper Cebraspe
│   ├── fgv_scraper.py             ← Scraper FGV
│   └── scraper_scheduler.py       ← Sistema de agendamento
│
├── editais/                       ← PDFs baixados (criado automaticamente)
│   ├── cebraspe_edital_trf_*.pdf
│   ├── fgv_prova_senado_*.pdf
│   └── ...
│
├── scraper.log                    ← Log de operações
└── INICIAR_SCRAPING.bat           ← Launcher Windows
```

---

## ⚙️ CONFIGURAÇÃO AVANÇADA

### Alterar Frequência de Coleta

Edite `scrapers/scraper_scheduler.py`:

```python
# Coleta a cada 6 horas
scheduler.add_job(
    func=coletar_todas_bancas,
    trigger='interval',
    hours=6,
    id='coleta_periodica'
)
```

### Adicionar Nova Banca

1. **Crie arquivo** `scrapers/nova_banca_scraper.py`:

```python
from scrapers.cebraspe_scraper import CebraspeScraper

class NovaBancaScraper(CebraspeScraper):
    def __init__(self, output_dir="editais"):
        super().__init__(output_dir)
        self.base_url = "https://www.novabanca.com.br"
        self.concursos_url = f"{self.base_url}/concursos"
```

2. **Registre** em `scraper_scheduler.py`:

```python
self.scrapers = {
    'cebraspe': CebraspeScraper(output_dir),
    'fgv': FGVScraper(output_dir),
    'nova_banca': NovaBancaScraper(output_dir)  # ← Adicione aqui
}
```

### Filtrar Tipos de Documento

Edite `*_scraper.py`, método `get_pdfs_from_page`:

```python
# Ignora retificações
if 'retific' in titulo.lower():
    continue  # Pula este PDF

# Só editais e provas
if tipo not in ['edital', 'prova']:
    continue
```

---

## 📊 DESEMPENHO

### Tempos Esperados (i7-1255U)

| Operação | Tempo Médio | RAM Usada |
|----------|-------------|-----------|
| Coletar 1 concurso (Cebraspe) | 10-20 seg | +200 MB |
| Baixar 1 PDF (5 MB) | 5-10 seg | +10 MB |
| Indexar 1 PDF (50 pág) | 20-30 seg | +500 MB |
| Coleta completa (5 concursos) | 3-5 min | +2 GB |

### Otimizações

```python
# scrapers/cebraspe_scraper.py

# Reduza max_concursos para coletas mais rápidas
scraper.coletar_tudo(max_concursos=3)  # Padrão: 5

# Ajuste delays entre requisições
time.sleep(0.5)  # Mais rápido (cuidado com bloqueios)
time.sleep(3)    # Mais seguro
```

---

## 🐛 TROUBLESHOOTING

### ❌ "Nenhum concurso encontrado"

**Causa**: Site mudou estrutura HTML ou está offline

**Solução**:
1. Teste manualmente:
   ```python
   from scrapers.cebraspe_scraper import CebraspeScraper
   scraper = CebraspeScraper()
   concursos = scraper.get_concursos_ativos()
   print(concursos)
   ```

2. Se retornar vazio, atualize seletores CSS em `*_scraper.py`

### ❌ "Erro ao baixar PDF"

**Causa**: URL inválida, timeout ou bloqueio de IP

**Solução**:
- Aumente timeout: `response = self.session.get(url, timeout=60)`
- Adicione delays: `time.sleep(3)` entre downloads
- Use VPN se IP estiver bloqueado

### ❌ "Import Error: apscheduler"

**Causa**: APScheduler não instalado

**Solução**:
```bash
pip install apscheduler
```

### ❌ PDFs baixados mas não indexados

**Causa**: Core do ConcursAI não inicializado

**Solução**:
1. Verifique se Llama-3.1 está carregado:
   ```python
   from src.core import init_llm, init_db
   init_llm()
   init_db()
   ```

2. Ou indexe manualmente depois:
   ```python
   from src.core import indexar_pdf
   import os
   
   for filename in os.listdir('editais'):
       if filename.endswith('.pdf'):
           filepath = os.path.join('editais', filename)
           indexar_pdf(filepath, {'banca': 'cebraspe'})
   ```

### ❌ Scheduler não inicia

**Causa**: Porta/processo já em uso

**Solução**:
```python
from scrapers.scraper_scheduler import scheduler_instance

# Para scheduler existente
scheduler_instance.parar()

# Reinicia
scheduler_instance.iniciar()
```

---

## 📈 MONITORAMENTO

### Ver Logs em Tempo Real

```bash
# Windows
type scraper.log

# PowerShell
Get-Content scraper.log -Wait

# Ou abra com Notepad++/VS Code
```

### Verificar Status

Na interface web (aba Scraping) ou via Python:

```python
from scrapers.scraper_scheduler import obter_status

status = obter_status()
print(f"Rodando: {status['rodando']}")
print(f"PDFs coletados: {status['total_coletados']}")
print(f"Última coleta: {status['ultima_coleta']}")
```

### Listar PDFs Baixados

```bash
dir editais\*.pdf
```

Ou na interface, clique **"📁 Abrir Pasta"**.

---

## 🔒 SEGURANÇA E ÉTICA

### ✅ Boas Práticas

1. **Respeite robots.txt**: Configurado em `ROBOTSTXT_OBEY = True`
2. **Use delays**: `time.sleep(2)` entre requisições
3. **Limite max_concursos**: Não colete tudo de uma vez
4. **User-Agent adequado**: Identifica-se como navegador legítimo
5. **Horário inteligente**: Agende para madrugada (menos carga nos servidores)

### ❌ Não Faça

- ❌ Scraping excessivo (DDoS involuntário)
- ❌ Ignorar bloqueios de IP
- ❌ Redistribuir PDFs protegidos por direitos autorais
- ❌ Modificar PDFs originais

### 📜 Termos de Uso

Este scraper:
- ✅ Acessa apenas conteúdo público
- ✅ Não contorna autenticação
- ✅ Respeita robots.txt
- ✅ Usa para fins educacionais/estudo

**PDFs coletados são de propriedade das bancas organizadoras.**

---

## 🎯 CASOS DE USO

### 1. Estudante de Concurso

```python
# Agendar coleta semanal (domingo às 20h)
from scrapers.scraper_scheduler import agendar_semanal
agendar_semanal(dia='sunday', hora=20)

# Segunda de manhã: editais frescos indexados!
```

### 2. Curso Preparatório

```python
# Coleta diária de todas as bancas
from scrapers.scraper_scheduler import agendar_diario
agendar_diario(hora=5, minuto=0)  # 5h da manhã

# Alunos sempre com material atualizado
```

### 3. Pesquisador Acadêmico

```python
# Coleta em massa para análise estatística
from scrapers.scraper_scheduler import coletar_todas_agora
coletar_todas_agora(max_concursos=50)  # Cuidado: leva ~30 min

# Analisa padrões em centenas de editais
```

---

## 📚 PRÓXIMAS MELHORIAS

### Em Desenvolvimento

- [ ] Scraper FCC (estrutura pronta)
- [ ] Scraper Vunesp
- [ ] Detecção de editais duplicados
- [ ] Notificação por e-mail quando novo edital chegar
- [ ] Dashboard de estatísticas de coleta
- [ ] Suporte a proxy rotativo (evitar bloqueios)
- [ ] Coleta de questões de provas anteriores
- [ ] Exportação de metadados para CSV

### Contribuições

Quer adicionar uma nova banca? Abra PR em `scrapers/nova_banca_scraper.py`!

---

## 📞 SUPORTE

### Dúvidas?

1. Leia este README
2. Consulte `GUIA_USO.md` (tutorial geral)
3. Verifique logs: `scraper.log`
4. Execute teste: `python test_setup.py`

### Reportar Bug

Abra issue com:
- Banca que falhou
- Mensagem de erro completa
- Conteúdo de `scraper.log`

---

## ✅ CHECKLIST RÁPIDO

Antes de usar o scraping:

- [x] Dependências instaladas (`scrapy`, `apscheduler`)
- [x] Modelo Llama-3.1 carregado
- [x] ChromaDB inicializado
- [x] Pasta `editais/` existe
- [x] Testou coleta manual: `coletar_agora('cebraspe', 1)`

---

**🕷️ Sistema de Scraping Integrado ao ConcursAI - Sempre atualizado, sempre pronto! 📚**

---

*Última atualização: 27/11/2025*  
*Versão: 1.0.0*
