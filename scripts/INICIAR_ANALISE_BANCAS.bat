@echo off
chcp 65001 >nul
title Sistema de Análise de Bancas - ConcursAI

echo.
echo ===============================================================
echo  🎯 SISTEMA DE ANÁLISE DE BANCAS POR ÁREA - ConcursAI
echo ===============================================================
echo.
echo  Este sistema analisa PDFs de provas separados por banca e área
echo  identificando padrões específicos de cada concurso.
echo.
echo ===============================================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo    Instale Python 3.8+ de: https://www.python.org/
    pause
    exit /b 1
)

echo ✅ Python detectado
echo.

REM Verificar se módulos necessários existem
if not exist "modules\banca_area_analyzer.py" (
    echo ❌ Módulo banca_area_analyzer.py não encontrado!
    echo    Execute este script na pasta raiz do projeto.
    pause
    exit /b 1
)

echo ✅ Módulos encontrados
echo.

REM Menu de opções
:MENU
cls
echo.
echo ===============================================================
echo  🎯 SISTEMA DE ANÁLISE DE BANCAS - MENU PRINCIPAL
echo ===============================================================
echo.
echo  Escolha uma opção:
echo.
echo  1. 🧪 Executar Testes Interativos
echo  2. 📁 Organizar PDFs por Área (Automático)
echo  3. 🔄 Processar uma Banca + Área Específica
echo  4. 💬 Modo Chat (Faça perguntas sobre bancas)
echo  5. 📊 Processar TODAS as Bancas (demorado)
echo  6. 📖 Ver Guia de Uso
echo  7. 🏛️  Listar Bancas e Áreas Suportadas
echo.
echo  0. ❌ Sair
echo.
echo ===============================================================
echo.

set /p opcao="➡️  Digite o número da opção: "

if "%opcao%"=="1" goto TESTES
if "%opcao%"=="2" goto ORGANIZAR
if "%opcao%"=="3" goto PROCESSAR
if "%opcao%"=="4" goto CHAT
if "%opcao%"=="5" goto PROCESSAR_TODAS
if "%opcao%"=="6" goto GUIA
if "%opcao%"=="7" goto LISTAR
if "%opcao%"=="0" goto FIM

echo.
echo ❌ Opção inválida!
timeout /t 2 >nul
goto MENU

REM ===============================================================
REM OPÇÃO 1: Testes Interativos
REM ===============================================================
:TESTES
cls
echo.
echo ===============================================================
echo  🧪 EXECUTANDO TESTES INTERATIVOS
echo ===============================================================
echo.
python teste_sistema_bancas.py
echo.
pause
goto MENU

REM ===============================================================
REM OPÇÃO 2: Organizar PDFs
REM ===============================================================
:ORGANIZAR
cls
echo.
echo ===============================================================
echo  📁 ORGANIZANDO PDFs POR ÁREA
echo ===============================================================
echo.
echo  Este processo vai:
echo  1. Analisar o conteúdo de cada PDF
echo  2. Detectar automaticamente a área (Tecnologia, Jurídica, etc.)
echo  3. Mover para a pasta correta
echo.
echo  Estrutura criada:
echo  provas/
echo    ├── cebraspe/
echo    │   ├── tecnologia/
echo    │   ├── juridica/
echo    │   └── ...
echo    ├── fcc/
echo    └── fgv/
echo.
set /p confirma="  Tem certeza? (S/N): "
if /i not "%confirma%"=="S" goto MENU

echo.
echo 🔄 Processando...
echo.

python -c "from modules.banca_area_analyzer import get_banca_area_analyzer; analyzer = get_banca_area_analyzer(); print(f'\n✅ {analyzer.organizar_pdfs_existentes()} PDFs organizados!')"

echo.
pause
goto MENU

REM ===============================================================
REM OPÇÃO 3: Processar Banca + Área
REM ===============================================================
:PROCESSAR
cls
echo.
echo ===============================================================
echo  🔄 PROCESSAR BANCA + ÁREA ESPECÍFICA
echo ===============================================================
echo.
echo  Bancas disponíveis: cebraspe, fcc, fgv, vunesp
echo  Áreas: Tecnologia, Jurídica, Saúde, Administrativa, etc.
echo.

set /p banca="  Digite a banca (ex: cebraspe): "
set /p area="  Digite a área (ex: Tecnologia): "

if "%banca%"=="" goto PROCESSAR
if "%area%"=="" goto PROCESSAR

echo.
echo 🔄 Processando %banca% - %area%...
echo.

python -c "from modules.banca_area_analyzer import get_banca_area_analyzer; analyzer = get_banca_area_analyzer(); perfil = analyzer.processar_banca_area('%banca%', '%area%'); print('\n✅ Concluído!'); print(f'Questões processadas: {perfil.get(\"total_questoes\", 0)}'); print(f'Provas analisadas: {perfil.get(\"total_provas_analisadas\", 0)}')"

echo.
pause
goto MENU

REM ===============================================================
REM OPÇÃO 4: Modo Chat
REM ===============================================================
:CHAT
cls
echo.
echo ===============================================================
echo  💬 MODO CHAT - Faça perguntas sobre bancas
echo ===============================================================
echo.
echo  Exemplos de perguntas:
echo    • O que o CESPE mais cobra em Tecnologia?
echo    • Como estudar para FCC em Jurídica?
echo    • Qual a dificuldade da FGV em Saúde?
echo.
echo ===============================================================
echo.

set /p pergunta="❓ Sua pergunta: "

if "%pergunta%"=="" goto CHAT

echo.
echo 💭 Processando sua pergunta...
echo.

python -c "from modules.rag_banca_inteligente import get_rag_inteligente; rag = get_rag_inteligente(); print(rag.responder('%pergunta%', usar_ollama=False))"

echo.
echo.
set /p continuar="Fazer outra pergunta? (S/N): "
if /i "%continuar%"=="S" goto CHAT

goto MENU

REM ===============================================================
REM OPÇÃO 5: Processar Todas
REM ===============================================================
:PROCESSAR_TODAS
cls
echo.
echo ===============================================================
echo  🚀 PROCESSAR TODAS AS BANCAS E ÁREAS
echo ===============================================================
echo.
echo  ⚠️  ATENÇÃO: Este processo pode demorar vários minutos
echo             dependendo da quantidade de PDFs.
echo.
set /p confirma="  Tem certeza? (S/N): "
if /i not "%confirma%"=="S" goto MENU

echo.
echo 🔄 Processando...
echo    (Pode demorar bastante, aguarde...)
echo.

python -c "from modules.banca_area_analyzer import get_banca_area_analyzer; analyzer = get_banca_area_analyzer(); resultado = analyzer.processar_todas_bancas_areas(); print(f'\n✅ Concluído!'); print(f'Total de perfis gerados: {resultado[\"total_perfis\"]}')"

echo.
pause
goto MENU

REM ===============================================================
REM OPÇÃO 6: Guia de Uso
REM ===============================================================
:GUIA
cls
echo.
echo ===============================================================
echo  📖 ABRINDO GUIA DE USO
echo ===============================================================
echo.

if exist "GUIA_USO_BANCAS.md" (
    start GUIA_USO_BANCAS.md
    echo ✅ Guia aberto!
) else (
    echo ❌ Arquivo GUIA_USO_BANCAS.md não encontrado!
)

echo.
pause
goto MENU

REM ===============================================================
REM OPÇÃO 7: Listar Bancas e Áreas
REM ===============================================================
:LISTAR
cls
echo.
echo ===============================================================
echo  🏛️  BANCAS E ÁREAS SUPORTADAS
echo ===============================================================
echo.
echo  📂 BANCAS:
echo    • CESPE/CEBRASPE
echo    • FCC
echo    • FGV
echo    • VUNESP
echo.
echo  📚 ÁREAS DE CONHECIMENTO:
echo.
echo  1️⃣  Tecnologia
echo     Disciplinas: Banco de Dados, Programação, Redes,
echo                  Segurança da Informação, DevOps, etc.
echo.
echo  2️⃣  Jurídica
echo     Disciplinas: Dir. Constitucional, Administrativo,
echo                  Penal, Civil, Processual, etc.
echo.
echo  3️⃣  Saúde
echo     Disciplinas: Enfermagem, Medicina, Odontologia,
echo                  Farmácia, Nutrição, etc.
echo.
echo  4️⃣  Administrativa
echo     Disciplinas: Administração Pública, Gestão de Pessoas,
echo                  Orçamento, Licitações, etc.
echo.
echo  5️⃣  Língua Portuguesa
echo     Disciplinas: Gramática, Interpretação, Redação
echo.
echo  6️⃣  Conhecimentos Gerais
echo     Disciplinas: Raciocínio Lógico, Matemática,
echo                  Estatística, Atualidades
echo.
echo ===============================================================
echo.
pause
goto MENU

REM ===============================================================
REM Finalizar
REM ===============================================================
:FIM
cls
echo.
echo ===============================================================
echo  👋 ATÉ LOGO!
echo ===============================================================
echo.
echo  Sistema de Análise de Bancas - ConcursAI
echo  Desenvolvido com ❤️  para ajudar você a passar!
echo.
echo ===============================================================
echo.
timeout /t 3 >nul
exit /b 0
