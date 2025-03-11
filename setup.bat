@echo off
setlocal EnableDelayedExpansion

set /a total_steps=6
set /a current_step=0
set "ESC="
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do set "ESC=%%b"

:: Initialize display
echo %ESC%[2J%ESC%[0;0H[  0%%] Setup Progress
echo %ESC%[1;0HInitializing setup components...

:: Check Python installation
call :update_status "Checking Python installation..."
python --version >nul 2>&1
if %errorlevel% neq 0 (
    call :update_status "Installing Python 3.12..."
    winget install -h --accept-package-agreements --accept-source-agreements Python.Python.3.12 >nul
    call :update_status "Python 3.12 installed"
) else (
    for /f "tokens=2" %%i in ('python --version 2^>nul') do set "pyversion=%%i"
    for /f "tokens=1,2 delims=." %%a in ("!pyversion!") do (
        if %%a lss 3 (
            call :update_status "Upgrading Python !pyversion!..."
            winget install -h --accept-package-agreements Python.Python.3.12 >nul
            call :update_status "Python 3.12 installed"
        ) else if %%a equ 3 if %%b lss 10 (
            call :update_status "Upgrading Python !pyversion!..."
            winget install -h --accept-package-agreements Python.Python.3.12 >nul
            call :update_status "Python 3.12 installed"
        ) else (
            call :update_status "Python !pyversion! detected"
        )
    )
)
set /a current_step+=1
call :update_progress

:: Check Ollama installation
set "ollama_new=0"
call :update_status "Checking Ollama installation..."
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    call :update_status "Downloading Ollama..."
    powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'OllamaSetup.exe'" >nul
    call :update_status "Installing Ollama..."
    start /wait "" OllamaSetup.exe /S
    del OllamaSetup.exe >nul
    set "ollama_new=1"
    call :update_status "Ollama installed"
) else (
    call :update_status "Ollama detected"
)
set /a current_step+=1
call :update_progress

:: Install Python requirements
call :update_status "Installing dependencies..."
pip install -r requirements.txt >nul
call :update_status "Dependencies installed"
set /a current_step+=1
call :update_progress

:: Run NLTK download
call :update_status "Setting up NLTK..."
python download_nltk.py >nul
call :update_status "NLTK configured"
set /a current_step+=1
call :update_progress

:: Handle Ollama model
if %ollama_new% equ 1 (
    call :update_status "Downloading AI model..."
    ollama pull todorov/bggpt:latest >nul
    call :update_status "Model downloaded"
) else (
    call :update_status "Checking AI model..."
    ollama list | findstr /C:"todorov/bggpt:latest" >nul || (
        ollama pull todorov/bggpt:latest >nul
        call :update_status "Model downloaded"
    )
    if errorlevel 0 call :update_status "Model exists"
)
set /a current_step+=1
call :update_progress

:: Create launcher and shortcut
call :update_status "Creating application shortcut..."
(
    echo @echo off
    echo python "%%~dp0stanibogat.py"
    echo pause
) > "СтанИИ Богат v.10.bat"

set "script_path=%~dp0СтанИИ Богат v.10.bat"
set "shortcut_path=%USERPROFILE%\Desktop\СтанИИ Богат v.10.lnk"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%shortcut_path%'); $sc.TargetPath = '%script_path%'; $sc.WorkingDirectory = '%~dp0'; $sc.Save()" >nul

call :update_status "Desktop shortcut created"
set /a current_step+=1
call :update_progress

:: Final display
echo %ESC%[2J%ESC%[0;0H[100%%] Setup Complete
echo %ESC%[1;0HApplication ready - Shortcut created on desktop
timeout /t 3 >nul
exit /b

:update_progress
set /a percent=(current_step * 100) / total_steps
echo %ESC%[0;0H%ESC%[2K[%percent%^^%%] Setup Progress
exit /b

:update_status
echo %ESC%[1;0H%ESC%[2K%~1
exit /b