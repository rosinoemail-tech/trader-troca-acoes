@echo off
title Trader Troca de Acoes
cd /d "%~dp0"

echo.
echo  ========================================
echo   TRADER TROCA DE ACOES - Iniciando...
echo  ========================================
echo.
echo  Aguarde 5 segundos e o browser vai abrir.
echo  Para fechar o painel, feche esta janela.
echo.

:: Abre o browser automaticamente apos 5 segundos
start "" timeout /t 5 /nobreak >nul & start "" "http://localhost:8501"

:: Inicia o Streamlit
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
