@echo off
echo Building Echo Gateway Docker image...
docker build -t echo-gateway .
echo Running Echo Gateway container...
docker run -p 3000:3000 echo-gateway
echo.
echo Echo Gateway is now running!
echo Open http://localhost:3000 in your web browser.
echo Press Ctrl+C to stop the server.
pause
