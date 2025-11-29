@echo off
chcp 65001 >nul
echo ====================================
echo   Запуск Telegram бота
echo ====================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python с https://www.python.org/
    pause
    exit /b 1
)

REM Проверка наличия .env файла
if not exist .env (
    echo [ВНИМАНИЕ] Файл .env не найден!
    echo.
    echo Создайте файл .env со следующим содержимым:
    echo.
    echo BOT_TOKEN=ваш_токен_бота
    echo DATABASE_PATH=database.db
    echo ADMIN_IDS=ваш_telegram_id
    echo.
    pause
    exit /b 1
)

REM Проверка установки зависимостей
echo Проверка зависимостей...
python -c "import aiogram" >nul 2>&1
if errorlevel 1 (
    echo Установка зависимостей...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить зависимости
        pause
        exit /b 1
    )
)

echo.
echo Запуск бота...
echo Для остановки нажмите Ctrl+C
echo.
python main.py

pause

