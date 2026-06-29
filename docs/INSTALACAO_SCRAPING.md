# 🔧 Instalação do Sistema de Scraping

## ⚠️ Problema Identificado

O erro **"Sistema de scraping não disponível"** ocorre porque falta a biblioteca `apscheduler` e possivelmente outras dependências.

## ✅ Solução Rápida

### Opção 1: Script Automático (RECOMENDADO)

Execute o arquivo batch criado:

```cmd
cd C:\Users\FabLab Maker\Downloads\FAB\ConcursAI
instalar_scraping.bat
```

Este script irá:
1. ✅ Instalar todas as 6 dependências necessárias
2. ✅ Testar se foram instaladas corretamente
3. ✅ Exibir um relatório completo

### Opção 2: Instalação Manual

Execute cada comando individualmente:

```cmd
pip install scrapy
pip install beautifulsoup4
pip install requests
pip install APScheduler
pip install lxml
pip install html5lib
```

## 📦 Dependências Instaladas

| Pacote | Versão | Descrição |
|--------|--------|-----------|
| **scrapy** | 2.11+ | Framework de web scraping |
| **beautifulsoup4** | 4.12+ | Parser HTML/XML |
| **requests** | 2.31+ | Cliente HTTP |
| **APScheduler** | 3.10+ | Agendador de tarefas |
| **lxml** | 5.0+ | Parser XML rápido |
| **html5lib** | 1.1+ | Parser HTML5 |

## 🧪 Verificação

Teste se tudo foi instalado corretamente:

```cmd
cd C:\Users\FabLab Maker\Downloads\FAB\ConcursAI
python test_scraping_deps.py
```

Saída esperada:
```
✅ Scrapy instalado
✅ BeautifulSoup4 instalado
✅ Requests instalado
✅ APScheduler instalado
✅ lxml instalado
✅ CebraspeScraper carregado
✅ FGVScraper carregado
✅ ScraperScheduler carregado
```

## 🚀 Reiniciar a API

Após instalar as dependências, reinicie a API:

```cmd
# Pare a API atual (Ctrl+C no terminal)
# Depois inicie novamente:
cd C:\Users\FabLab Maker\Downloads\FAB\ConcursAI
python api_fastapi.py
```

Agora você verá:
```
✅ Sistema de scraping disponível!
✅ Scrapers carregados: Cebraspe, FGV
```

## 🌐 Testar no Navegador

1. Abra: `http://localhost:8000/scraping/status`
2. Deve retornar JSON com:
```json
{
  "disponivel": true,
  "scheduler": {
    "rodando": true,
    "jobs_ativos": 0
  },
  "estatisticas": {
    "total_coletados": 0,
    "total_indexados": 0
  }
}
```

3. Ou abra a interface visual:
   - **Scraping:** `file:///C:/Users/FabLab%20Maker/Downloads/FAB/ConcursAI/scraping.html`
   - **Index:** `file:///C:/Users/FabLab%20Maker/Downloads/FAB/ConcursAI/index.html`

## 📊 Arquivos Criados

- `instalar_scraping.bat` - Script de instalação automática
- `test_scraping_deps.py` - Script de teste das dependências
- `scrapers/__init__.py` - Atualizado com importações

## 🎯 Próximos Passos

Após instalar e reiniciar a API:

1. ✅ Acesse `scraping.html`
2. ✅ Click em "Atualizar Status" - deve mostrar sistema online 🟢
3. ✅ Teste uma coleta: Selecione Cebraspe, 2 concursos, "Iniciar Coleta"
4. ✅ Aguarde 2-5 minutos (scraping é lento para respeitar sites)
5. ✅ Verifique PDFs em: `C:\Users\FabLab Maker\Downloads\FAB\ConcursAI\editais\`

## 🆘 Problemas Comuns

### Erro: "No module named 'apscheduler'"
**Solução:** Execute `instalar_scraping.bat`

### Erro: "Permission denied"
**Solução:** Execute o CMD como Administrador

### API não reinicia
**Solução:** 
```cmd
taskkill /F /IM python.exe
cd C:\Users\FabLab Maker\Downloads\FAB\ConcursAI
python api_fastapi.py
```

### Status continua 🔴 (offline)
**Solução:** Verifique se a API está rodando em `http://localhost:8000`

---

**Data:** 27/11/2025  
**Status:** Sistema pronto para uso após instalação das dependências
