@echo off
chcp 65001 > nul
echo ============================================================
echo  🎓 TREINAMENTO DE MODELOS ML
echo ============================================================
echo.
echo Este script irá treinar:
echo   1. Classificador de Bancas (Random Forest + MLP + SVM)
echo   2. Preditor de Temas (Análise Temporal)
echo.
echo Isso pode levar alguns minutos...
echo ============================================================
echo.

cd /d "%~dp0"

REM Instalar dependências ML
echo 🔄 Instalando dependências de Machine Learning...
"C:/Users/FabLab Maker/Downloads/FAB/.venv/Scripts/python.exe" -m pip install scikit-learn joblib -q

echo.
echo 🎓 Iniciando treinamento...
echo.

"C:/Users/FabLab Maker/Downloads/FAB/.venv/Scripts/python.exe" treinar_modelos_ml.py

echo.
echo ============================================================
echo  ✅ TREINAMENTO CONCLUÍDO!
echo ============================================================
echo.
echo Os modelos foram salvos em:
echo   • models/banca_classifier.pkl
echo   • relatorios/tendencias_*.json
echo.
echo Para usar os modelos, consulte a API ou dashboard.
echo ============================================================
pause
