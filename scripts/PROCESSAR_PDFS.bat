@echo off
REM ========================================
REM PROCESSAR PDFs E GERAR CHUNKS
REM ========================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║           🔄 PROCESSAR PDFs PARA RAG                      ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

python processar_pdfs_chunks.py

echo.
echo ✅ Processamento concluído!
echo.
echo Próximos passos:
echo   1. Executar indexação: python -m modules.concurso_embeddings
echo   2. Testar sistema: BENCHMARK_RAPIDO.bat
echo.
pause
