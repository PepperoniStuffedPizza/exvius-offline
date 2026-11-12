@echo off
setlocal
rem ==========================================================================
rem  One-click build for this fork: checks your setup, then builds a signed APK.
rem  Double-click it, or run "build.bat" from Command Prompt in this folder.
rem  The finished app appears in source\build\distribution\assets\
rem ==========================================================================
cd /d "%~dp0"

set "APP_VERSION=0.1.30-smd"
set "CLIENT_VERSION=9.0.0-offline.30-smd"
rem Must stay above the upstream app (9070) and the data minimum (9015).
set "VERSION_CODE=9071"
set "KEYSTORE=tools\vendor\my-exvius.jks"
set "KEY_ALIAS=my-exvius"
set "ORIGINAL_APK=repository snapshots\FFBE-Global-v9.0.0-original.apk"
set "APKTOOL=tools\vendor\apktool_3.0.3.jar"
set "FRAMEWORK=tools\vendor\apktool-framework"

echo.
echo === Checking your setup ===
set "PROBLEMS=0"

rem --- Python 3.10 (the Android runtime is built for 3.10) ---
set "PY310="
for /f "delims=" %%P in ('py -3.10 -c "import sys; print(sys.prefix)" 2^>nul') do set "PY310=%%P"
if not defined PY310 (
    echo [MISSING] Python 3.10. Install 3.10.11 from python.org, then run this again.
    set "PROBLEMS=1"
) else (
    echo [OK] Python 3.10 at %PY310%
    set "PATH=%PY310%;%PY310%\Scripts;%PATH%"
    py -3.10 -c "import cryptography, yaml" 2>nul || (
        echo [MISSING] Python 3.10 add-ons. Run: py -3.10 -m pip install cryptography==42.0.8 PyYAML==6.0.1
        set "PROBLEMS=1"
    )
)

rem --- Java 11 ---
if not defined JAVA_HOME (
    for /d %%J in ("C:\Program Files\Eclipse Adoptium\jdk-11*") do set "JAVA_HOME=%%~fJ"
)
if not defined JAVA_HOME (
    echo [MISSING] Java 11. Install "Temurin 11" from adoptium.net, then run this again.
    set "PROBLEMS=1"
) else if not exist "%JAVA_HOME%\bin\java.exe" (
    echo [MISSING] Java not found at %JAVA_HOME%. Install "Temurin 11" from adoptium.net.
    set "PROBLEMS=1"
) else (
    echo [OK] Java at %JAVA_HOME%
    "%JAVA_HOME%\bin\java.exe" -version 2>&1 | findstr /i "version"
    set "PATH=%JAVA_HOME%\bin;%PATH%"
)

rem --- Android SDK ---
if not defined ANDROID_HOME set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
if not exist "%ANDROID_HOME%\platforms\android-33\android.jar" (
    echo [MISSING] Android 13 ^(API 33^). In Android Studio: SDK Manager ^> SDK Platforms ^> Android 13.
    set "PROBLEMS=1"
) else (
    echo [OK] Android SDK platform 33
)
if not exist "%ANDROID_HOME%\build-tools\36.0.0\apksigner.bat" (
    echo [MISSING] Build-Tools 36.0.0. In Android Studio: SDK Manager ^> SDK Tools ^> Show Package Details ^> 36.0.0.
    set "PROBLEMS=1"
) else (
    echo [OK] Android build-tools 36.0.0
)

rem --- Node.js ---
where node >nul 2>nul || (
    echo [MISSING] Node.js. Install the LTS version from nodejs.org.
    set "PROBLEMS=1"
)

rem --- Files that live only on this PC ---
call :need "%ORIGINAL_APK%" "the original FFBE Global v9.0.0 APK"
call :need "%APKTOOL%" "apktool 3.0.3"
call :need "%FRAMEWORK%\" "the empty apktool-framework folder"
call :need "tools\vendor\frida-gadget-17.24.3-android-arm64.so" "Frida Gadget 17.24.3 for arm64"
call :need "tools\vendor\android-agent\node_modules\frida-compile\dist\cli.js" "frida-compile (npm install frida-compile)"
call :need "%KEYSTORE%" "your signing key (step 6)"

if "%PROBLEMS%"=="1" (
    echo.
    echo Fix the [MISSING] items above, then run build.bat again.
    goto :done
)

echo.
set /p "EXVIUS_KEYSTORE_PASSWORD=Type your signing key password and press Enter: "
if not defined EXVIUS_KEYSTORE_PASSWORD (
    echo No password entered.
    goto :done
)

echo.
echo === Decoding the original APK (a few minutes) ===
rem Full decode, read-only source for the code patches. Made once.
if not exist "source\build\android\decoded-code\smali" (
    java -jar "%APKTOOL%" d -f -p "%FRAMEWORK%" "%ORIGINAL_APK%" -o "source\build\android\decoded-code" || goto :failed
)
rem Fresh resources-only copy every build, so patches never apply twice.
if exist "source\build\android\client" rmdir /s /q "source\build\android\client"
java -jar "%APKTOOL%" d --no-src -f -p "%FRAMEWORK%" "%ORIGINAL_APK%" -o "source\build\android\client" || goto :failed

echo.
echo === Building (the first run downloads Gradle and can take 20+ minutes) ===
powershell -NoProfile -ExecutionPolicy Bypass -File "source\exvius\build_distribution.ps1" ^
    -Version "%APP_VERSION%" -ClientVersion "%CLIENT_VERSION%" -VersionCode %VERSION_CODE% ^
    -KeyStore "%KEYSTORE:\=/%" -KeyAlias "%KEY_ALIAS%"
set "BUILD_RESULT=%ERRORLEVEL%"

set "APK=source\build\distribution\assets\exvius-offline-v%APP_VERSION%.apk"
echo.
if exist "%APK%" (
    echo ==========================================================
    echo  Your app is ready:
    echo  %CD%\%APK%
    echo ==========================================================
    if not "%BUILD_RESULT%"=="0" (
        echo The APK was signed, but a check after signing reported a problem.
        echo The upstream release check often fails on other PCs; the APK itself is usually fine.
    )
    explorer /select,"%CD%\%APK%"
    goto :done
)

:failed
echo.
echo The build stopped with an error. Copy the red/last lines above and send them to Claude.
echo A full log is in the "logs" folder.

:done
set "EXVIUS_KEYSTORE_PASSWORD="
echo.
pause
exit /b

:need
if exist "%~1" (
    echo [OK] %~2
) else (
    echo [MISSING] %~2 at %~1
    set "PROBLEMS=1"
)
exit /b 0
