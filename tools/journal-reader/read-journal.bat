@echo off
rem ---------------------------------------------------------------------------
rem  Magic Quest Log - read the quest journal and write Progress.lua
rem
rem  A double-click is enough, provided LOTRO is running and the character is
rem  logged in. Reads only the running client's quest journal (read-only) and
rem  writes the plugin's progress file from it.
rem ---------------------------------------------------------------------------
setlocal EnableExtensions EnableDelayedExpansion

rem --- Settings: only change these when detection fails ----------------------
rem  Empty = search automatically.
set "COMPANION_DIR="
set "LOTRO_DIR="
rem  Empty = whichever character is logged in right now.
set "CHARACTER="
rem ---------------------------------------------------------------------------

set "HERE=%~dp0"
set "OUTPUT=%USERPROFILE%\Documents\The Lord of the Rings Online\Plugins\MagicQuestLog\Data\Progress.lua"

if not defined CHARACTER set "CHARACTER=-"

echo Magic Quest Log - reading the quest journal
echo.

rem --- 1. Companion, which supplies the memory library ----------------------
if not defined COMPANION_DIR (
	for %%D in (
		"%ProgramFiles%\LOTRO Companion"
		"%ProgramFiles(x86)%\LOTRO Companion"
		"%ProgramFiles%\LotRO Companion"
		"%ProgramFiles(x86)%\LotRO Companion"
		"%LOCALAPPDATA%\LOTRO Companion"
	) do (
		if not defined COMPANION_DIR if exist "%%~D\app\lib\delta-lotro-memory*.jar" set "COMPANION_DIR=%%~D"
	)
)
if not defined COMPANION_DIR (
	echo ERROR: LOTRO Companion was not found.
	echo.
	echo Its memory library is required to read the client. Install LOTRO Companion
	echo from https://sourceforge.net/projects/lotrocompanion/ , or set COMPANION_DIR
	echo at the top of this script to its installation folder.
	goto :end
)
set "LIBS=%COMPANION_DIR%\app\lib"
echo Companion: %COMPANION_DIR%

rem --- 2. Java: the Windows runtime that ships with Companion --------------
set "JAVA=%COMPANION_DIR%\runtime\bin\java.exe"
if not exist "%JAVA%" set "JAVA=%COMPANION_DIR%\app\runtime\bin\java.exe"
if not exist "%JAVA%" (
	if defined JAVA_HOME if exist "%JAVA_HOME%\bin\java.exe" set "JAVA=%JAVA_HOME%\bin\java.exe"
)
if not exist "%JAVA%" (
	echo ERROR: no Java found. Companion ships one under runtime\bin.
	goto :end
)
echo Java:      %JAVA%

rem --- 3. The LOTRO client folder, which supplies the game database --------
if not defined LOTRO_DIR (
	for %%D in (
		"%ProgramFiles(x86)%\StandingStoneGames\The Lord of the Rings Online"
		"%ProgramFiles%\StandingStoneGames\The Lord of the Rings Online"
		"%ProgramFiles(x86)%\Standing Stone Games\The Lord of the Rings Online"
		"%ProgramFiles%\Standing Stone Games\The Lord of the Rings Online"
	) do (
		if not defined LOTRO_DIR if exist "%%~D\client_gamelogic.dat" set "LOTRO_DIR=%%~D"
	)
)
if not defined LOTRO_DIR (
	echo ERROR: the LOTRO client folder was not found.
	echo Set LOTRO_DIR at the top of this script to the folder with client_gamelogic.dat.
	goto :end
)
echo Client:    %LOTRO_DIR%
echo.

rem --- 4. Compile once ------------------------------------------------------
set "CLASSES=%HERE%classes\JournalExport.class"
if not exist "%CLASSES%" (
	echo Compiling the tool once...
	set "JAVAC=%COMPANION_DIR%\runtime\bin\javac.exe"
	if not exist "!JAVAC!" set "JAVAC=%COMPANION_DIR%\app\runtime\bin\javac.exe"
	if not exist "!JAVAC!" (
		echo ERROR: no javac found. Install a JDK, or ship classes\ with the tool.
		goto :end
	)
	if not exist "%HERE%classes" mkdir "%HERE%classes"
	"!JAVAC!" -cp "%LIBS%\*" -d "%HERE%classes" "%HERE%JournalExport.java"
	if errorlevel 1 (
		echo ERROR: compilation failed.
		goto :end
	)
	echo.
)

rem --- 5. Read and write ----------------------------------------------------
"%JAVA%" -Djava.awt.headless=true -cp "%HERE%classes;%LIBS%\*" JournalExport "%LOTRO_DIR%" "%OUTPUT%" "%CHARACTER%"
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (
	echo Done. Reload the plugin in game:
	echo     /plugins unload MagicQuestLog
	echo     /plugins load MagicQuestLog
	echo.
	echo Note: a running plugin session may overwrite the file when it unloads.
	echo Running this tool again rewrites it.
) else (
	echo Nothing was written ^(code %RESULT%^).
	echo Usual causes: the game is not running, the character is not in the world,
	echo or a different character is logged in.
)

:end
echo.
pause
endlocal
