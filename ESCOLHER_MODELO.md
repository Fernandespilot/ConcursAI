# 🎛️ GUIA: Escolher entre Groq e Modelo Local

## 📋 RESUMO

Agora você pode **controlar qual modelo usar** através do arquivo `.env`!

---

## 🔧 CONFIGURAÇÕES DISPONÍVEIS

Edite o arquivo `.env` e mude a linha `USE_MODEL`:

### 1️⃣ Modo AUTO (Recomendado) ✅
```env
USE_MODEL=auto
```

**Comportamento:**
- ✅ Tenta usar Groq primeiro (se configurado)
- ✅ Se Groq falhar, usa modelo local automaticamente
- ✅ Nunca fica offline!
- ✅ Melhor dos dois mundos

**Quando usar:** Sempre! É a configuração padrão.

---

### 2️⃣ Modo GROQ APENAS ⚡
```env
USE_MODEL=groq
```

**Comportamento:**
- ⚡ Usa APENAS Groq (ultra rápido)
- ❌ Se Groq não estiver configurado, API não inicia
- ❌ Se Groq falhar, retorna erro (sem fallback)

**Quando usar:** 
- Você tem API key configurada
- Quer garantir respostas rápidas sempre
- Prefere erro a respostas lentas

---

### 3️⃣ Modo LOCAL APENAS 🤖
```env
USE_MODEL=local
```

**Comportamento:**
- 🤖 Usa APENAS modelo local (Llama 8B)
- 🔒 Ignora Groq mesmo se configurado
- 💻 Usa sua CPU/RAM
- 🐌 Respostas em 15-30 segundos

**Quando usar:**
- Sem internet
- Testes offline
- Privacidade total (tudo local)
- Economizar cota do Groq

---

## 📊 COMPARAÇÃO

| Modo | Groq | Local | Fallback | Velocidade | Recomendado |
|------|------|-------|----------|------------|-------------|
| **auto** | ✅ Sim | ✅ Sim | ✅ Sim | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ |
| **groq** | ✅ Sim | ❌ Não | ❌ Não | ⚡⚡⚡ | ⭐⭐⭐ |
| **local** | ❌ Não | ✅ Sim | N/A | 🐌 | ⭐⭐ |

---

## 🎯 EXEMPLOS DE USO

### Exemplo 1: Desenvolvimento Normal
```env
USE_MODEL=auto
GROQ_API_KEY=gsk_sua_chave_aqui
```
**Resultado:** Groq rápido, fallback local se necessário ✅

---

### Exemplo 2: Máxima Performance
```env
USE_MODEL=groq
GROQ_API_KEY=gsk_sua_chave_aqui
```
**Resultado:** Sempre ultra rápido, erro se Groq falhar ⚡

---

### Exemplo 3: Offline/Privacidade
```env
USE_MODEL=local
# GROQ_API_KEY não necessário
```
**Resultado:** Tudo local, lento mas privado 🔒

---

### Exemplo 4: Economizar Cota Groq
```env
USE_MODEL=local
GROQ_API_KEY=gsk_sua_chave_aqui  # Mantém configurado mas não usa
```
**Resultado:** Força local, reserva Groq para depois 💰

---

## 🔍 COMO SABER QUAL ESTÁ USANDO?

### No console ao iniciar API:

**Modo AUTO (Groq disponível):**
```
[IA] ⚡ Groq API configurada! (Llama-3.1-70B na nuvem)
[IA] 🔄 Modo AUTO: Groq ativo, fallback local disponível
```

**Modo AUTO (Groq indisponível):**
```
[IA] ⚠️ GROQ_API_KEY não configurada, usando modelo local
[IA] 🤖 Carregando Llama-3.1 8B (GGUF) na CPU...
```

**Modo GROQ:**
```
[IA] ⚡ Groq API configurada! (Llama-3.1-70B na nuvem)
```

**Modo LOCAL:**
```
[IA] 🤖 Configuração: Usando APENAS modelo local (Llama 8B)
[IA] 🤖 Carregando Llama-3.1 8B (GGUF) na CPU...
```

---

## ⚙️ MUDANDO CONFIGURAÇÃO

### Passo a passo:

1. **Edite `.env`:**
   ```env
   USE_MODEL=auto  # ou groq ou local
   ```

2. **Salve o arquivo**

3. **Reinicie a API:**
   ```cmd
   START_API_RAPIDO.bat
   ```

4. **Veja no console qual modo está ativo**

---

## 🎮 TESTANDO OS MODOS

### Teste 1: Modo AUTO
```env
USE_MODEL=auto
GROQ_API_KEY=gsk_...
```
Faça pergunta no Dashboard → Resposta rápida (Groq)

---

### Teste 2: Modo LOCAL
```env
USE_MODEL=local
```
Faça pergunta no Dashboard → Resposta lenta (Local)

---

### Teste 3: Comparar Velocidade
1. Configure `USE_MODEL=groq`
2. Pergunte: "O que é IA?"
3. Anote tempo (1-2s)
4. Configure `USE_MODEL=local`
5. Reinicie API
6. Mesma pergunta
7. Anote tempo (15-30s)

**Diferença: 15-20x mais rápido!** 🚀

---

## 🛡️ SEGURANÇA

### ✅ Modo AUTO (Recomendado)
- Groq: Dados enviados para nuvem
- Fallback local: Tudo na sua máquina
- Balanceamento automático

### ⚡ Modo GROQ
- Todos os dados vão para nuvem Groq
- Mais rápido mas menos privado

### 🔒 Modo LOCAL
- **100% privado**
- Nenhum dado sai da sua máquina
- Ideal para dados sensíveis

---

## 💡 DICAS

### Dica 1: Economizar Cota
Se está perto do limite diário (14.400 req):
```env
USE_MODEL=local  # Temporário
```

### Dica 2: Desenvolvimento
Para testes rápidos:
```env
USE_MODEL=groq  # Rápido
```

### Dica 3: Produção
Para máxima confiabilidade:
```env
USE_MODEL=auto  # Fallback garantido
```

### Dica 4: Demos Offline
Para apresentações sem internet:
```env
USE_MODEL=local  # Sempre funciona
```

---

## 🆘 PROBLEMAS

### "ValueError: GROQ_API_KEY não configurada"
- Você está em modo `USE_MODEL=groq`
- Mas não tem GROQ_API_KEY
- **Solução:** Configure key ou mude para `auto`

### "API não inicia"
- Erro no init_llm
- **Solução:** Mude para `USE_MODEL=local` temporariamente

### "Respostas muito lentas"
- Provavelmente em modo `local`
- **Solução:** Configure Groq e use `USE_MODEL=auto`

---

## 📌 CONFIGURAÇÃO RECOMENDADA

```env
# .env
USE_MODEL=auto
GROQ_API_KEY=gsk_sua_chave_aqui
```

**Por quê?**
- ⚡ Rápido quando possível
- 🛡️ Funciona sempre (fallback)
- 🎯 Melhor experiência

---

## 🏁 RESUMO

✅ **USE_MODEL=auto** → Inteligente, sempre funciona  
⚡ **USE_MODEL=groq** → Máxima velocidade, sem fallback  
🤖 **USE_MODEL=local** → 100% local, lento mas privado

**Configure no `.env` e reinicie a API!** 🚀
