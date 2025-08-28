@echo off
REM Script para iniciar o sistema completo

echo.
echo ========================================
echo    SISTEMA EMPENHOS + CHAT MSN
echo ========================================
echo.

REM Verificar se MySQL está rodando
echo [1/4] Verificando MySQL...
python test_mysql_connection.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ MySQL nao esta configurado!
    echo.
    echo Solucoes:
    echo 1. Instale XAMPP
    echo 2. Inicie Apache e MySQL no painel
    echo 3. Execute novamente
    echo.
    pause
    exit /b 1
)

echo.
echo [2/4] Iniciando Sistema Principal (Porta 5001)...
start "Sistema Principal" cmd /k "python app_mysql_principal.py"

echo [3/4] Aguardando 3 segundos...
timeout /t 3 /nobreak >nul

echo [4/4] Iniciando Chat MSN (Porta 5002)...
start "Chat MSN" cmd /k "python app_mysql_chat.py"

echo.
echo ✅ Sistemas iniciados com sucesso!
echo.
echo 📊 Dashboard: http://localhost:5001/dashboard
echo 💬 Chat MSN:  http://localhost:5002/chat
echo 🔐 Login:     admin / admin123
echo.
echo Pressione qualquer tecla para abrir os navegadores...
pause >nul

start http://localhost:5001/login
start http://localhost:5002/login

echo.
echo 🎉 Tudo pronto! Os sistemas estao rodando.
echo.
echo Para parar os sistemas:
echo - Feche as janelas do terminal
echo - Ou pressione Ctrl+C em cada uma
echo.
pause
