@echo off
cd /d D:\DriftDetection
call venv\Scripts\activate.bat
python -m src.drift_report >> logs\drift_job.log 2>&1
echo ---- Run finished %date% %time% ---- >> logs\drift_job.log 