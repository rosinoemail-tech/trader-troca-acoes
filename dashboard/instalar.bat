@echo off
echo ============================================
echo  INSTALANDO DEPENDENCIAS DO PAINEL
echo ============================================
echo.

pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ============================================
echo  INSTALACAO CONCLUIDA!
echo  Agora execute: rodar.bat
echo ============================================
pause
