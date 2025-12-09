@echo off
REM ConcursAI - Script de Inicialização (Windows)
echo ========================================
echo  ConcursAI - Assistente de Editais
echo  Powered by Llama-3.1 8B (Local)
echo ========================================
echo.

REM Verifica se o modelo existe
if not exist "models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" (
    echo [ERRO] Modelo Llama-3.1 nao encontrado!
    echo.
    echo Baixe o modelo com:
    echo python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='bartowski/Meta-Llama-3.1-8B-Instruct-GGUF', filename='Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf', local_dir='./models')"
    echo.
    pause
    exit /b 1
)

echo [OK] Modelo encontrado!
echo [INFO] Iniciando ConcursAI...
echo.
echo Aguarde 1-2 minutos para o modelo carregar...
echo A interface abrira automaticamente no navegador.
echo.

REM Inicia Streamlit
streamlit run src\app.py

pause
