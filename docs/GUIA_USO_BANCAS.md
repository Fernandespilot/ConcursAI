# 🎯 GUIA RÁPIDO - Sistema de Análise de Bancas por Área

## 📌 O Problema que Resolvemos

**ANTES:** Você tinha PDFs de provas jogados em uma pasta, sem organização, e o modelo não conseguia identificar padrões específicos de cada banca por área.

**AGORA:** Sistema parametrizado que:
- ✅ Organiza PDFs por **banca + área** automaticamente
- ✅ Analisa padrões específicos de cada **banca em cada área**
- ✅ Responde perguntas tipo: "O que a FCC mais cobra em TI?"
- ✅ Identifica temas mais cobrados por cargo/área
- ✅ Gera recomendações personalizadas de estudo

---

## 🚀 Como Usar

### 1️⃣ Organização dos PDFs

O sistema espera esta estrutura:

```
provas/
├── cebraspe/
│   ├── tecnologia/
│   │   ├── prova_analista_ti_pf_2024.pdf
│   │   └── gabarito_analista_ti_pf_2024.pdf
│   ├── juridica/
│   │   ├── prova_advogado_2024.pdf
│   │   └── gabarito_advogado_2024.pdf
│   ├── saude/
│   ├── administrativa/
│   └── ...
├── fcc/
│   ├── tecnologia/
│   └── ...
├── fgv/
│   └── ...
└── vunesp/
    └── ...
```

**💡 Não tem essa estrutura?** Rode o organizador automático:

```python
from modules.banca_area_analyzer import get_banca_area_analyzer

analyzer = get_banca_area_analyzer()
analyzer.organizar_pdfs_existentes()  # Analisa e organiza automaticamente!
```

---

### 2️⃣ Processar uma Banca + Área

```python
from modules.banca_area_analyzer import get_banca_area_analyzer

analyzer = get_banca_area_analyzer()

# Processar CESPE - Tecnologia
perfil = analyzer.processar_banca_area("cebraspe", "Tecnologia")

print(f"Total de questões: {perfil['total_questoes']}")
print(f"Disciplina #1: {list(perfil['distribuicao_disciplinas'].keys())[0]}")
```

**O que acontece:**
1. ✅ Lê todos os PDFs da pasta `provas/cebraspe/tecnologia/`
2. ✅ Extrai questões com PyMuPDF
3. ✅ Categoriza por disciplina, dificuldade, tipo, temas
4. ✅ Analisa padrões específicos (linguagens, frameworks, leis, etc.)
5. ✅ Gera perfil completo com estatísticas
6. ✅ Cria recomendações personalizadas

---

### 3️⃣ Fazer Perguntas Inteligentes

```python
from modules.rag_banca_inteligente import get_rag_inteligente

rag = get_rag_inteligente()

# Perguntas específicas
resposta = rag.responder("O que o CESPE mais cobra em Tecnologia?")
print(resposta)

# Outros exemplos:
# "Como estudar para FCC em Jurídica?"
# "Qual a dificuldade da FGV em Saúde?"
# "Quanto tempo preciso estudar para VUNESP em Administrativa?"
```

**O sistema identifica automaticamente:**
- 🏛️ Banca mencionada (CESPE, FCC, FGV, VUNESP)
- 📚 Área mencionada (Tecnologia, Jurídica, Saúde, etc.)
- 🎯 Tipo de pergunta (o que mais cai, como estudar, dificuldade, tempo)

---

### 4️⃣ Consultar Perfil Completo

```python
# Consulta formatada
resposta = analyzer.consultar_perfil("cebraspe", "Tecnologia")
print(resposta)

# Saída:
# 📊 PERFIL: CEBRASPE - Tecnologia
# ============================================================
# 
# 📈 Estatísticas Gerais:
#   • Total de provas analisadas: 5
#   • Total de questões: 150
# 
# 📚 Top 3 Disciplinas Mais Cobradas:
#   1. Banco de Dados: 32.5% (49 questões)
#   2. Programação: 28.0% (42 questões)
#   3. Redes de Computadores: 18.5% (28 questões)
# ...
```

---

### 5️⃣ Comparar Bancas

```python
# Processar múltiplas bancas
analyzer.processar_banca_area("cebraspe", "Tecnologia")
analyzer.processar_banca_area("fcc", "Tecnologia")
analyzer.processar_banca_area("fgv", "Tecnologia")

# Comparar
perfil_cespe = analyzer.perfis["cebraspe"]["Tecnologia"]
perfil_fcc = analyzer.perfis["fcc"]["Tecnologia"]

print("CESPE:", perfil_cespe["distribuicao_tipos"])
print("FCC:", perfil_fcc["distribuicao_tipos"])
```

---

## 📊 Áreas de Conhecimento Suportadas

| Área | Disciplinas | Análises Específicas |
|------|-------------|---------------------|
| **Tecnologia** | Banco de Dados, Programação, Redes, Segurança, etc. | Linguagens, frameworks, ferramentas |
| **Jurídica** | Dir. Constitucional, Administrativo, Penal, Civil, etc. | Lei seca %, jurisprudência %, súmulas |
| **Saúde** | Enfermagem, Medicina, Farmácia, Nutrição, etc. | Diagnóstico %, tratamento %, SUS |
| **Administrativa** | Gestão, Orçamento, Licitações, etc. | - |
| **Língua Portuguesa** | Gramática, Interpretação, Redação | - |
| **Conhecimentos Gerais** | Lógica, Matemática, Atualidades, etc. | - |

---

## 🎯 Tipos de Perguntas que o Sistema Responde

### 1. **O que mais cai?**
```python
resposta = rag.responder("O que o CESPE mais cobra em Tecnologia?")
```
**Retorna:**
- Top 5 disciplinas com percentuais
- Top 10 temas mais cobrados
- Padrões específicos da área (linguagens, leis, etc.)

### 2. **Como estudar?**
```python
resposta = rag.responder("Como estudar para FCC em Jurídica?")
```
**Retorna:**
- Estratégias específicas da banca
- Cronograma sugerido (horas/semana, meses)
- Materiais recomendados
- Disciplinas prioritárias

### 3. **Dificuldade**
```python
resposta = rag.responder("Qual a dificuldade da FGV em Saúde?")
```
**Retorna:**
- Distribuição: Básico, Intermediário, Avançado
- Nível predominante
- Preparação esperada

### 4. **Tempo de estudo**
```python
resposta = rag.responder("Quanto tempo estudar para VUNESP?")
```
**Retorna:**
- Horas semanais sugeridas
- Meses de preparação
- Distribuição teoria/prática

### 5. **Tipo de questão**
```python
resposta = rag.responder("Que tipo de questão o CESPE usa?")
```
**Retorna:**
- Tipos (Certo/Errado, Múltipla Escolha, etc.)
- Percentual de cada tipo
- Dicas específicas

---

## 🧪 Script de Teste

Execute o script interativo:

```bash
python teste_sistema_bancas.py
```

**Menu:**
1. Organizar PDFs por área (automático)
2. Processar CESPE - Tecnologia
3. Consultar perfil gerado
4. RAG Inteligente - Perguntas e Respostas
5. Comparar bancas na mesma área
6. Processar TODAS as bancas
7. Modo Interativo (faça suas perguntas)

---

## 📝 Exemplos Práticos

### Exemplo 1: Análise Completa do CESPE em TI

```python
from modules.banca_area_analyzer import get_banca_area_analyzer

analyzer = get_banca_area_analyzer()

# 1. Organizar PDFs
analyzer.organizar_pdfs_existentes()

# 2. Processar
perfil = analyzer.processar_banca_area("cebraspe", "Tecnologia")

# 3. Ver o que mais cai
print("Top 5 Disciplinas:")
for disc, dados in list(perfil["distribuicao_disciplinas"].items())[:5]:
    print(f"  {disc}: {dados['percentual']:.1f}%")

# 4. Ver temas mais cobrados
print("\nTop 10 Temas:")
for tema_data in perfil["temas_mais_cobrados"][:10]:
    print(f"  {tema_data['tema']} ({tema_data['frequencia']}x)")

# 5. Padrões de Tecnologia
padroes = perfil["padroes_especificos"]["caracteristicas_predominantes"]
print("\nLinguagens mais cobradas:")
print(padroes["linguagens_mais_cobradas"])
```

### Exemplo 2: Preparação para Concurso Específico

```python
from modules.rag_banca_inteligente import get_rag_inteligente

rag = get_rag_inteligente()

# Descobrir o que estudar
print(rag.responder("O que o CESPE mais cobra em Tecnologia?"))

# Como estudar
print(rag.responder("Como estudar para CESPE em Tecnologia?"))

# Tempo necessário
print(rag.responder("Quanto tempo preciso estudar?"))
```

### Exemplo 3: Comparação para Escolher Concurso

```python
analyzer = get_banca_area_analyzer()

# Processar 3 bancas
bancas = ["cebraspe", "fcc", "fgv"]
for banca in bancas:
    analyzer.processar_banca_area(banca, "Tecnologia")

# Comparar dificuldade
for banca in bancas:
    perfil = analyzer.perfis[banca]["Tecnologia"]
    dificuldades = perfil["distribuicao_dificuldade"]
    
    # Calcular score de dificuldade (avançado = 3, intermediário = 2, básico = 1)
    score = (
        dificuldades.get("Avançado", {}).get("percentual", 0) * 3 +
        dificuldades.get("Intermediário", {}).get("percentual", 0) * 2 +
        dificuldades.get("Básico", {}).get("percentual", 0) * 1
    ) / 100
    
    print(f"{banca.upper()}: Dificuldade = {score:.2f}/3")
```

---

## 🔧 Integração com API FastAPI

```python
# Em api_fastapi.py

from fastapi import APIRouter
from modules.rag_banca_inteligente import get_rag_inteligente

router = APIRouter()
rag = get_rag_inteligente()

@router.post("/api/chat/banca")
async def chat_banca(pergunta: str):
    """
    Endpoint para perguntas sobre bancas
    
    Exemplos:
    - "O que o CESPE mais cobra em Tecnologia?"
    - "Como estudar para FCC?"
    """
    resposta = rag.responder(pergunta, usar_ollama=True)
    
    return {
        "pergunta": pergunta,
        "resposta": resposta,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/api/banca/{banca}/area/{area}")
async def obter_perfil(banca: str, area: str):
    """Obtém perfil completo de uma banca em uma área"""
    analyzer = get_banca_area_analyzer()
    
    resposta = analyzer.consultar_perfil(banca, area)
    
    return {"perfil": resposta}
```

---

## 💡 Dicas de Uso

### ✅ Boas Práticas

1. **Nomeie os PDFs claramente:**
   - ✅ `prova_analista_ti_pf_2024.pdf`
   - ✅ `gabarito_analista_ti_pf_2024.pdf`
   - ❌ `arquivo123.pdf`

2. **Separe provas e gabaritos:**
   - O sistema detecta automaticamente pelo nome
   - Use "gabarito" no nome do arquivo

3. **Organize por área:**
   - PDFs de TI → `tecnologia/`
   - PDFs de Direito → `juridica/`
   - PDFs de Enfermagem → `saude/`

4. **Reprocesse quando adicionar novos PDFs:**
   ```python
   analyzer.processar_banca_area("cebraspe", "Tecnologia", forcar_reprocessamento=True)
   ```

### ⚠️ Troubleshooting

**Problema:** "Nenhum PDF encontrado"
- **Solução:** Verifique se os PDFs estão na pasta correta

**Problema:** "Erro ao processar PDF"
- **Solução:** PDF pode estar corrompido ou protegido. Teste manualmente.

**Problema:** "Área não detectada"
- **Solução:** Use o organizador automático ou especifique manualmente

**Problema:** Resposta genérica
- **Solução:** Seja mais específico: mencione banca + área na pergunta

---

## 📊 Estrutura de Dados

### Perfil de Banca + Área

```python
{
    "banca": "CESPE/CEBRASPE",
    "area": "Tecnologia",
    "data_analise": "2025-12-03T...",
    
    "total_provas_analisadas": 5,
    "total_gabaritos": 5,
    "total_questoes": 150,
    
    "distribuicao_disciplinas": {
        "Banco de Dados": {
            "count": 49,
            "percentual": 32.67
        },
        ...
    },
    
    "distribuicao_dificuldade": {
        "Avançado": {"count": 60, "percentual": 40.0},
        "Intermediário": {"count": 70, "percentual": 46.67},
        "Básico": {"count": 20, "percentual": 13.33}
    },
    
    "temas_mais_cobrados": [
        {"tema": "normalização de banco de dados", "frequencia": 15},
        {"tema": "sql e consultas", "frequencia": 12},
        ...
    ],
    
    "padroes_especificos": {
        "palavras_chave_detectadas": {...},
        "caracteristicas_predominantes": {
            "linguagens_mais_cobradas": {"sql": 45, "python": 23},
            "frameworks_mencionados": {...},
            "foco": "prático"
        }
    },
    
    "recomendacoes": {
        "foco_disciplinas": ["Banco de Dados", "Programação"],
        "estrategia_estudo": [...],
        "tempo_sugerido": {
            "horas_semanais": 20,
            "meses_preparo_sugerido": 3
        }
    }
}
```

---

## 🚀 Próximos Passos

1. ✅ **Adicionar mais PDFs** nas pastas de bancas
2. ✅ **Processar todas as áreas** que você tem interesse
3. ✅ **Fazer perguntas específicas** para seu concurso
4. ✅ **Comparar bancas** para escolher qual prestar
5. ✅ **Integrar na API** para acesso via interface web

---

## 📞 Suporte

Dúvidas ou problemas? 

- 📧 Abra uma issue no GitHub
- 💬 Execute `python teste_sistema_bancas.py` e escolha modo interativo
- 📖 Leia `SISTEMA_ESTUDO_BANCAS.md` para documentação completa

---

**Desenvolvido com ❤️ pela equipe ConcursAI**
