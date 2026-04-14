@echo off
echo ============================================
echo  INICIANDO PAINEL TRADER TROCA DE ACOES
echo ============================================
echo.
echo Acesse no browser: http://localhost:8501
echo Para acessar de fora da VPS: http://SEU-IP-VPS:8501
echo.
echo Pressione CTRL+C para parar.
echo.

streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
pause
