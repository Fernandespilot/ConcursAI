# 🤖 MODELOS DE MACHINE LEARNING - ConcursAI

## 📋 Visão Geral

Sistema completo de Machine Learning com dois modelos principais:

### 1. **Classificador de Bancas** (#205)
Ensemble de modelos para classificar automaticamente questões por banca examinadora.

### 2. **Preditor de Temas** (#206)
Sistema de análise temporal para prever tendências e frequências de temas.

---

## 🎯 Classificador de Bancas

### Arquitetura

**Ensemble Voting com 3 modelos:**
- **Random Forest** (peso 2) - 200 árvores, profundidade 20
- **MLP Neural Network** (peso 1) - Camadas: 100→50 neurônios
- **SVM RBF** (peso 1) - Kernel radial, C=1.0

**Features:**
- **TF-IDF** (5.000 features, n-grams 1-3)
- **Features textuais:** comprimento, complexidade, estrutura
- **Features estilísticas:** padrões CEBRASPE, FCC, FGV

### Como Usar

#### Treinamento:
```cmd
TREINAR_MODELOS_ML.bat
```

Ou via Python:
```python
from modules.ml_models import get_banca_classifier

classifier = get_banca_classifier()

# Preparar dados
textos, bancas = classifier.preparar_dados("concursos_chunks.csv")

# Treinar
metricas = classifier.treinar(textos, bancas)

# Salvar modelo
classifier.salvar_modelo("models/banca_classifier.pkl")
```

#### Previsão:
```python
classifier = get_banca_classifier()
classifier.carregar_modelo("models/banca_classifier.pkl")

texto = "Julgue o item a seguir sobre administração pública..."
resultado = classifier.prever(texto)

print(f"Banca: {resultado['banca_prevista']}")
print(f"Confiança: {resultado['confianca']:.2%}")
print(f"Top 3: {resultado['top_3']}")
```

### Métricas Esperadas

| Modelo | Acurácia Típica |
|--------|-----------------|
| Random Forest | 85-92% |
| MLP | 80-88% |
| SVM | 82-90% |
| **Ensemble** | **88-95%** |

---

## 📈 Preditor de Temas

### Funcionalidades

1. **Análise Temporal:** Identifica evolução de temas ao longo dos anos
2. **Previsão de Frequência:** Prevê quantas vezes tema aparecerá
3. **Temas Emergentes:** Detecta temas em crescimento acelerado
4. **Tendências:** Classifica como crescente/decrescente/estável

### Como Usar

#### Análise Completa:
```python
from modules.ml_models import get_theme_predictor

predictor = get_theme_predictor()

# Gerar relatório
relatorio = predictor.gerar_relatorio_tendencias(
    banca='CEBRASPE',
    output_path='relatorio_cebraspe.json'
)
```

#### Prever Tema Específico:
```python
previsao = predictor.prever_frequencia(
    tema='principios_adm',
    banca='CEBRASPE',
    anos_futuros=2
)

print(f"Média histórica: {previsao['historico']['media_historica']}")
print(f"Tendência: {previsao['tendencia']['tipo']}")
print(f"Recomendação: {previsao['recomendacao']}")
```

#### Identificar Emergentes:
```python
emergentes = predictor.identificar_temas_emergentes(
    banca='FGV',
    threshold=0.5  # 50% de crescimento
)

for tema in emergentes:
    print(f"{tema['tema']}: +{tema['taxa_crescimento']:.1%}")
```

### Temas Reconhecidos

**Direito Administrativo:**
- `principios_adm` - Princípios da Administração
- `atos_administrativos` - Atos Administrativos
- `licitacao` - Licitações e Contratos
- `servidores` - Servidores Públicos
- `responsabilidade` - Responsabilidade Civil

**Direito Constitucional:**
- `direitos_fundamentais` - Direitos Fundamentais
- `organizacao_estado` - Organização do Estado
- `poder_executivo` - Poder Executivo
- `poder_legislativo` - Poder Legislativo

**Língua Portuguesa:**
- `concordancia` - Concordância Verbal/Nominal
- `regencia` - Regência Verbal/Nominal
- `crase` - Uso da Crase
- `interpretacao` - Interpretação de Textos

**Raciocínio Lógico:**
- `logica_proposicional` - Lógica Proposicional
- `logica_argumentacao` - Lógica de Argumentação
- `matematica_basica` - Matemática Básica

**Informática:**
- `hardware` - Hardware e Componentes
- `redes` - Redes e Internet
- `seguranca` - Segurança da Informação

---

## 🚀 Comandos Rápidos

### Instalação de Dependências
```cmd
CORRIGIR_DEPENDENCIAS.bat
```

### Treinar Modelos
```cmd
TREINAR_MODELOS_ML.bat
```

### Testar Modelos
```cmd
TESTAR_MODELOS_ML.bat
```

### Via Python
```bash
# Instalar dependências
pip install scikit-learn joblib

# Treinar
python treinar_modelos_ml.py

# Testar
python testar_modelos_ml.py
```

---

## 📊 Estrutura de Arquivos

```
ConcursAI/
├── modules/
│   └── ml_models/
│       ├── __init__.py
│       ├── banca_classifier.py      # Classificador
│       └── theme_predictor.py       # Preditor
├── models/
│   └── banca_classifier.pkl         # Modelo treinado
├── relatorios/
│   ├── tendencias_cebraspe.json
│   ├── tendencias_fgv.json
│   └── tendencias_fcc.json
├── treinar_modelos_ml.py            # Script treinamento
├── testar_modelos_ml.py             # Script teste
├── TREINAR_MODELOS_ML.bat
└── TESTAR_MODELOS_ML.bat
```

---

## 🔧 Requisitos

### Dependências Python:
```
scikit-learn>=1.3.0
joblib>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
```

### Dados Necessários:
- `concursos_chunks.csv` OU
- `concursos_questoes_respostas.csv`

**Formato esperado:**
```csv
conteudo,banca,ano,area,orgao
"Texto da questão...",CEBRASPE,2023,Juridica,TCU
```

---

## 📈 Pipeline Completo

### 1. Preparar Dados
```cmd
PROCESSAR_QUESTOES_GABARITOS.bat
```

### 2. Corrigir Dependências
```cmd
CORRIGIR_DEPENDENCIAS.bat
```

### 3. Treinar Modelos
```cmd
TREINAR_MODELOS_ML.bat
```

### 4. Testar Modelos
```cmd
TESTAR_MODELOS_ML.bat
```

### 5. Integrar com API
Os modelos são automaticamente disponibilizados via API FastAPI:

**Endpoints:**
- `POST /api/ml/classificar` - Classificar questão
- `GET /api/ml/tendencias/{banca}` - Relatório de tendências
- `GET /api/ml/prever/{banca}/{tema}` - Prever tema específico
- `GET /api/ml/emergentes/{banca}` - Temas emergentes

---

## 🎯 Casos de Uso

### 1. Sistema de Recomendação
Classifica automaticamente novas questões por banca para sistema de recomendação.

### 2. Análise de Tendências
Identifica quais temas estão "em alta" para priorizar estudos.

### 3. Planejamento de Estudos
Gera plano personalizado baseado em previsões de frequência.

### 4. Detecção de Padrões
Identifica mudanças nos padrões de cobrança das bancas.

---

## 🐛 Troubleshooting

### Erro: "Modelo não encontrado"
**Solução:** Execute `TREINAR_MODELOS_ML.bat`

### Erro: "Arquivo de dados não encontrado"
**Solução:** Execute `PROCESSAR_QUESTOES_GABARITOS.bat` primeiro

### Erro: "sklearn não instalado"
**Solução:** Execute `CORRIGIR_DEPENDENCIAS.bat`

### Acurácia baixa (<80%)
**Possíveis causas:**
- Poucos dados de treinamento (< 500 questões)
- Desbalanceamento entre bancas
- Dados de baixa qualidade

**Solução:** Coletar mais questões com `BAIXAR_PROVAS_PCI.bat`

---

## 📚 Referências

**Modelos Utilizados:**
- Random Forest: Breiman, L. (2001)
- MLP: Rumelhart et al. (1986)
- SVM: Cortes & Vapnik (1995)
- TF-IDF: Salton & Buckley (1988)

**Bibliotecas:**
- Scikit-learn: Pedregosa et al. (2011)
- Pandas: McKinney (2010)

---

## 🎓 Resultados Esperados

### Após Treinamento:

**Classificador:**
- ✅ Acurácia ≥ 88%
- ✅ Modelo salvo em `models/banca_classifier.pkl`
- ✅ Feature importance calculada

**Preditor:**
- ✅ 3 relatórios de tendências gerados
- ✅ Temas emergentes identificados
- ✅ Previsões para próximos 2 anos

---

## 🚀 Próximos Passos

1. **Expandir Temas:** Adicionar mais categorias temáticas
2. **Deep Learning:** Testar BERT para classificação
3. **Time Series:** Modelos ARIMA/LSTM para predição
4. **Ensemble Stacking:** Combinar predições de múltiplos modelos
5. **AutoML:** Otimização automática de hiperparâmetros

---

**✅ Sprint 4 - Tarefas #205 e #206 CONCLUÍDAS!**
