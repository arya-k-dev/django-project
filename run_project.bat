@echo off
cd /d "%~dp0"

set "DJANGO_DEBUG=True"
set "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver"
set "PYTHONUTF8=1"

set "PYTHON_CMD="

rem Prefer the Python bundled with this project copy.
rem Copied venv folders can contain absolute paths to older SkillSphere projects.
if exist "%~dp0.python\Python312\python.exe" (
    "%~dp0.python\Python312\python.exe" --version >nul 2>nul && set "PYTHON_CMD="%~dp0.python\Python312\python.exe""
)
if not defined PYTHON_CMD if exist "%~dp0.venv\Scripts\python.exe" (
    findstr /i /c:"%~dp0" "%~dp0.venv\pyvenv.cfg" >nul 2>nul && "%~dp0.venv\Scripts\python.exe" --version >nul 2>nul && set "PYTHON_CMD="%~dp0.venv\Scripts\python.exe""
)
if not defined PYTHON_CMD if exist "%~dp0venv\Scripts\python.exe" (
    findstr /i /c:"%~dp0" "%~dp0venv\pyvenv.cfg" >nul 2>nul && "%~dp0venv\Scripts\python.exe" --version >nul 2>nul && set "PYTHON_CMD="%~dp0venv\Scripts\python.exe""
)
if not defined PYTHON_CMD where py >nul 2>nul (
    py -3 --version >nul 2>nul && set "PYTHON_CMD=py -3"
)
if not defined PYTHON_CMD where python >nul 2>nul (
    python --version >nul 2>nul && set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo Python was not found.
    echo.
    echo Install Python 3.12, then run:
    echo python -m pip install -r requirements.txt
    echo python manage.py runserver
    exit /b 1
)

echo.
echo Starting SkillSphere from:
echo %CD%
echo.
echo Using Python:
%PYTHON_CMD% -c "import sys; print(sys.executable)"
echo.

%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

%PYTHON_CMD% manage.py check
if errorlevel 1 exit /b 1

%PYTHON_CMD% manage.py migrate
if errorlevel 1 exit /b 1

%PYTHON_CMD% manage.py seed_skills
if errorlevel 1 exit /b 1

%PYTHON_CMD% manage.py runserver 127.0.0.1:8000 --noreload
