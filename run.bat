@echo off
title MailSentry Microservices Launcher
echo ===================================================
echo   Starting MailSentry Microservices Application
echo ===================================================

echo [1/3] Starting Backend API (Port 8000)...
start "MailSentry Backend API (:8000)" cmd /k "cd backend && python main.py"

echo [2/3] Starting ML Inference Service (Port 9000)...
start "MailSentry ML Service (:9000)" cmd /k "cd ml-service && python main.py"

echo [3/3] Starting React Frontend...
start "MailSentry Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo MailSentry microservices stack launched!