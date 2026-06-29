# 🚀 GUIA RÁPIDO: Configurar Groq API

## ⚡ O QUE É?
Groq é uma API cloud que roda Llama-3.1-70B **ULTRA RÁPIDO**!
- Respostas em **1-2 segundos** (vs 15-30s no modelo local)
- Modelo **70B** (vs 8B local) = respostas muito melhores
- **14.400 requisições GRÁTIS por dia**
- Sem usar sua RAM/CPU

---

## 📝 PASSO A PASSO (2 minutos!)

### 1. Obter API Key (GRÁTIS!)
1. Acesse: https://console.groq.com/keys
2. Clique em **"Sign in"** (pode usar Google/GitHub)
3. Clique em **"Create API Key"**
4. Copie a chave (começa com `gsk_...`)

### 2. Configurar no ConcursAI
1. Abra o arquivo `.env` na raiz do projeto
2. Encontre a linha: `GROQ_API_KEY=SUA_CHAVE_AQUI`
3. Substitua por: `GROQ_API_KEY=gsk_sua_chave_aqui`
4. **Salve o arquivo**

### 3. Reiniciar API
```cmd
INICIAR_FAPEMAT.bat
```
Ou:
```cmd
START_API_RAPIDO.bat
```

---

## ✅ COMO TESTAR

### No Dashboard (http://localhost:8000/dashboard.html):
```
Pergunta: O que é inteligência artificial?
```

**Com Groq:** Resposta em 1-2 segundos ⚡
**Sem Groq:** Resposta em 15-30 segundos 🐌

---

## 🔍 VERIFICAR SE ESTÁ FUNCIONANDO

### No console da API, você verá:
```
[IA] ✓ Groq API configurada! (Llama-3.1-70B na nuvem)
```

### Se vir isso, está usando modelo local:
```
[IA] 🤖 Modelo Llama 3.1 8B carregado localmente
```

---

## 🔒 SEGURANÇA

⚠️ **NUNCA compartilhe sua API key!**
- O arquivo `.env` está no `.gitignore`
- Não compartilhe prints da tela com a key visível
- Não commit o `.env` no git

Se expôs acidentalmente:
1. Acesse https://console.groq.com/keys
2. Delete a key antiga
3. Crie uma nova

---

## 🆘 PROBLEMAS?

### Erro: "Groq API não configurada"
- Verifique se copiou a key corretamente no `.env`
- Certifique-se que não tem espaços extras
- A key deve começar com `gsk_`

### Erro: "Invalid API key"
- Key expirada ou incorreta
- Gere uma nova em https://console.groq.com/keys

### Erro: "Rate limit exceeded"
- Limite de 14.400 req/dia atingido
- Aguarde reset (meia-noite UTC)
- Sistema volta automaticamente para modelo local

---

## 🎯 LIMITES GRATUITOS

| Modelo | Requisições/Dia | Tokens/Minuto |
|--------|----------------|---------------|
| Llama-3.1-70B | 14.400 | 30.000 |
| Llama-3.1-8B | 30.000 | 60.000 |

Para mais: https://console.groq.com/docs/rate-limits

---

## 🔄 FALLBACK AUTOMÁTICO

O sistema detecta automaticamente:
- ✅ **Groq disponível:** Usa Groq (rápido)
- ❌ **Groq indisponível:** Usa modelo local (lento mas funciona)

Nunca fica offline! 🎉

---

## 📊 COMPARAÇÃO

| Recurso | Groq API ⚡ | Local 🐌 |
|---------|------------|----------|
| Velocidade | 1-2s | 15-30s |
| Modelo | 70B | 8B |
| Qualidade | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| RAM/CPU | 0% | 4.6GB RAM |
| Custo | Grátis | Grátis |

---

**💡 DICA:** Configure hoje e tenha respostas instantâneas! 🚀
