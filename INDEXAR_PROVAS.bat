@echo off
chcp 65001 >nul
title Indexar Provas no Modelo RAG

echo.
echo ========================================================================
echo    INDEXAR PROVAS NO MODELO RAG (ChromaDB)
echo ========================================================================
echo.

python indexar_provas.py

pause
