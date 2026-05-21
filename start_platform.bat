@echo off

docker compose up -d

timeout /t 20

datahub docker quickstart

echo Platform Started
pause