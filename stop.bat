@echo off
chcp 65001 >nul
title 停止任务管理服务

echo 正在查找并终止 Python 进程...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq 任务管理系统*" 2>nul

echo.
echo 服务已停止！
pause