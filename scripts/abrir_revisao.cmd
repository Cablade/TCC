@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Ambiente do projeto nao encontrado em .venv.
  echo Execute primeiro o preparo do ambiente descrito em docs\guia_treinamento.md.
  pause
  exit /b 1
)
echo Iniciando a revisao das candidatas...
echo Quando aparecer a mensagem abaixo, abra no navegador:
echo http://127.0.0.1:8765/
echo.
".venv\Scripts\python.exe" scripts\review_annotations.py --batch data\annotations\negative_preselection_v1 --port 8765
pause
