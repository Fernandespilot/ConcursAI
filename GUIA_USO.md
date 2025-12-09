# 🚀 GUIA RÁPIDO - ConcursAI com Llama-3.1

## ⚡ Início Rápido (3 Passos)

### 1️⃣ Verifique a Instalação
```bash
python test_setup.py
```
**Deve mostrar**: ✅ OK em todos os testes

### 2️⃣ Inicie o Sistema
```bash
streamlit run src/app.py
```
**Ou clique duas vezes em**: `INICIAR_CONCURSAI.bat`

### 3️⃣ Use a Interface
Abrirá automaticamente em: `http://localhost:8501`

---

## 📖 Como Usar (Passo a Passo Ilustrado)

### 🔹 Adicionar um Edital

1. **Clique na aba**: "📁 Adicionar PDF"
2. **Faça upload**: Escolha um PDF de edital
3. **Preencha os dados**:
   - **Banca**: cebraspe
   - **Cargo**: Analista TI
   - **Ano**: 2025
   - **Órgão**: TRF
4. **Clique**: "📥 Indexar PDF"
5. **Aguarde**: 20-40 segundos (aparece barra de progresso)
6. **Sucesso**: Aparece ✅ com número de chunks

**Exemplo real:**
```
PDF: edital_trf_2025.pdf (50 páginas)
Banca: cebraspe
Resultado: ✅ 87 chunks indexados
```

---

### 🔹 Fazer Perguntas

1. **Clique na aba**: "💬 Perguntas"
2. **Digite**: "Qual o salário inicial?"
3. **Clique**: "🔍 Buscar Resposta"
4. **Aguarde**: 2-5 segundos
5. **Resultado**: 
   - **📝 Resposta**: Texto extraído do edital
   - **📄 Fonte**: Nome do PDF original

**Exemplos de perguntas:**
- ❓ "Quantas vagas para TI?"
- ❓ "Quais os requisitos mínimos?"
- ❓ "Qual a carga horária?"
- ❓ "Quando são as inscrições?"
- ❓ "Qual o conteúdo de Redes?"

---

### 🔹 Gerar Análise de Banca

1. **Clique na aba**: "📊 Análise de Banca"
2. **Selecione a banca**: ex: Cebraspe
3. **Clique**: "🔬 Gerar Análise"
4. **Aguarde**: 5-10 segundos
5. **Resultado**: Relatório com:
   - Disciplinas identificadas
   - Temas mais cobrados por disciplina
   - Porcentagem estimada de cada tema

**Exemplo de saída:**
```
📊 ANÁLISE DE TEMAS - BANCA CEBRASPE

🔹 INFORMÁTICA (40%)
- Redes de Computadores (25%)
- Segurança da Informação (20%)
- Banco de Dados (15%)
- Desenvolvimento de Sistemas (15%)
- Hardware e Software (10%)

🔹 DIREITO ADMINISTRATIVO (30%)
- Atos Administrativos (35%)
- Licitações e Contratos (30%)
- Servidores Públicos (20%)
- Organização Administrativa (15%)

...
```

6. **Baixar**: Clique em "💾 Baixar Relatório (.txt)"

---

## 🎯 Fluxo de Trabalho Recomendado

```
1. Adicione 3-5 editais da mesma banca
   ↓
2. Faça perguntas específicas sobre cada edital
   ↓
3. Gere análise consolidada da banca
   ↓
4. Use o relatório para focar nos temas mais cobrados
```

---

## ⚙️ Configurações do Sistema

### Recursos Usados (i7-1255U)
- **RAM**: 8-10 GB durante uso
- **CPU**: 8 threads (80% dos núcleos)
- **Disco**: ~6 GB (modelo + banco)

### Tempos Esperados
| Ação | Tempo |
|------|-------|
| Carregar modelo (1ª vez) | 1-2 min |
| Indexar PDF (50 pág) | 20-40 seg |
| Responder pergunta | 2-5 seg |
| Gerar análise | 5-10 seg |

---

## 🐛 Resolução de Problemas

### ❌ "Modelo não encontrado"
**Causa**: Modelo não foi baixado ou está em local errado  
**Solução**:
```bash
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='bartowski/Meta-Llama-3.1-8B-Instruct-GGUF', filename='Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf', local_dir='./models')"
```

### ❌ "Out of Memory"
**Causa**: RAM insuficiente  
**Solução**:
1. Feche outros aplicativos
2. Edite `src/core.py`:
   ```python
   llm = Llama(..., n_ctx=1024, n_threads=4)  # Reduz uso
   ```

### ❌ Respostas muito lentas (>10 seg)
**Causa**: CPU sobrecarregada  
**Solução**: Reduza threads em `src/core.py`:
```python
llm = Llama(..., n_threads=4)  # Era 8
```

### ❌ "ModuleNotFoundError: No module named 'xxx'"
**Causa**: Dependência não instalada  
**Solução**:
```bash
pip install -r src/requirements.txt
```

---

## 💡 Dicas de Uso Avançado

### 🔸 Perguntas Mais Eficazes
✅ **Bom**: "Qual o salário do cargo de Analista?"  
❌ **Ruim**: "Salário?"

✅ **Bom**: "Quais disciplinas caem na prova de TI?"  
❌ **Ruim**: "O que estudar?"

### 🔸 Organize por Banca
Use sempre o mesmo nome de banca:
- ✅ "cebraspe" (sempre minúsculo)
- ❌ "Cebraspe", "CEBRASPE", "cespe"

### 🔸 Metadados Completos
Preencha todos os campos ao indexar:
- **Banca**: Obrigatório para análise
- **Cargo**: Ajuda a filtrar depois
- **Ano**: Identifica editais recentes
- **Órgão**: Contexto adicional

---

## 📊 Exemplo de Sessão Completa

```
[09:00] Indexando editais...
  📁 edital_cebraspe_trf_2025.pdf → ✅ 87 chunks
  📁 edital_cebraspe_pf_2024.pdf → ✅ 102 chunks
  📁 edital_cebraspe_tcu_2024.pdf → ✅ 94 chunks

[09:05] Fazendo perguntas...
  ❓ "Qual o salário do TRF?" → R$ 12.455,30
  ❓ "Quantas vagas para PF?" → 500 vagas
  ❓ "Conteúdo de Redes no TCU?" → [lista de tópicos]

[09:10] Gerando análise da Cebraspe...
  📊 Relatório gerado com 15 disciplinas
  💾 Baixado: analise_cebraspe_2025.txt

[09:15] Estudando com base no relatório! 📚
```

---

## 🆘 Suporte

**Erro não listado?** Execute:
```bash
python test_setup.py
```

**Ainda com problemas?** Verifique:
- [ ] Python 3.10 ou 3.11
- [ ] 16 GB RAM disponível
- [ ] ~10 GB espaço em disco livre
- [ ] Antivírus não bloqueando

---

## 🎓 Bons Estudos!

**Sistema 100% funcional e otimizado para seu i7-1255U!**

📚 **ConcursAI** - Seu assistente local de editais  
🤖 **Llama-3.1** - IA de última geração da Meta  
🚀 **Gratuito** - Sem APIs pagas, sem internet necessária
