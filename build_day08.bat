@echo off
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot
set Path=%JAVA_HOME%\bin;%Path%
cd /d D:\YueQian\shopping-frontend\day08
echo Using Java:
"%JAVA_HOME%\bin\java" -version
echo.
echo Building...
D:\apache-maven-3.8.6\bin\mvn.cmd clean install -DskipTests 2>&1
echo BUILD EXIT CODE: %ERRORLEVEL%
