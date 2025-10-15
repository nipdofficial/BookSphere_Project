@echo off
echo Starting Book Sphere Frontend...
echo.

cd /d "%~dp0frontend"

echo Installing frontend dependencies...
call npm install

echo.
echo Starting frontend development server...
echo Frontend will be available at: http://localhost:3000
echo.

call npm start

pause
