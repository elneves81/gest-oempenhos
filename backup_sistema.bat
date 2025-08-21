@echo off
REM Script de Backup do Sistema de Empenhos
REM Prefeitura de Guarapuava
echo.
echo ==========================================
echo    SISTEMA DE BACKUP - EMPENHOS
echo ==========================================
echo.

REM Definir diretórios
set SCRIPT_DIR=%~dp0
set BACKUP_DIR=%SCRIPT_DIR%backups
set DB_FILE=%SCRIPT_DIR%empenhos.db

REM Criar diretório de backup se não existir
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    echo ✅ Diretório de backup criado: %BACKUP_DIR%
)

REM Verificar se o banco existe
if not exist "%DB_FILE%" (
    echo ❌ ERRO: Banco de dados não encontrado: %DB_FILE%
    pause
    exit /b 1
)

REM Gerar nome do backup com timestamp
for /f "tokens=1-4 delims=/ " %%a in ("%date%") do set TODAY=%%d%%b%%a
for /f "tokens=1-3 delims=: " %%a in ("%time%") do set HOUR=%%a%%b%%c
set HOUR=%HOUR: =0%
set TIMESTAMP=%TODAY%_%HOUR%
set BACKUP_NAME=backup_empenhos_%TIMESTAMP%.zip

echo 📊 Informações do backup:
echo    - Data/Hora: %date% %time%
echo    - Banco: %DB_FILE%
echo    - Destino: %BACKUP_DIR%\%BACKUP_NAME%
echo.

REM Executar backup Python
echo 🔄 Executando backup...
python backup_manager.py > backup_log_%TIMESTAMP%.txt 2>&1

if %ERRORLEVEL% EQU 0 (
    echo ✅ Backup executado com sucesso!
    echo 📁 Log salvo em: backup_log_%TIMESTAMP%.txt
) else (
    echo ❌ Erro durante o backup. Verifique o log: backup_log_%TIMESTAMP%.txt
)

echo.
echo ==========================================
echo    BACKUP CONCLUÍDO
echo ==========================================
echo.

REM Listar backups disponíveis
echo 📋 Backups disponíveis:
dir /b "%BACKUP_DIR%\backup_empenhos_*.zip" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo    Nenhum backup encontrado
)

echo.
pause
