@echo off
setlocal

:: Manual builds are disabled by default as they have lead to installers based
:: on irreproducible sourcecode and environment.
:: Running the installer creation script through a github action is the
:: preferred and official way of releasing your project.
:: If you are absolutely sure you need a manual build, follow these steps:
:: 1) issue the command `set LOCAL_BUILD=1` first
:: 2) run `make_pkg.bat release version`, where version is an integer
if "" == "%GITHUB_ACTIONS%" if "" == "%LOCAL_BUILD%" (
    echo You cannot build this project manually.
    echo Please check in your changes and have the installer build from an ^
automated build system^.
    exit /B 1
)

REM call env_deactivate.bat
call env_activate.bat env.ini

echo Cleaning up previous installation...
if exist %~dp0\dist RMDIR /Q /S %~dp0..\dist

call %~dp0\_dirsetup.cmd
if ERRORLEVEL 1 GOTO ERROR

set RELEASE_VERSION=%~2
echo Creating installer...
python prototype_installer_config.py spec
if ERRORLEVEL 1 GOTO ERROR

echo Packing installer directory...
python prototype_installer_config.py makeinst
set SEVENZIP_OK=%ERRORLEVEL%
if NOT "0" == "%SEVENZIP_OK%" GOTO ERROR

echo Exporting %~dp0\environment yml
call conda env export > %~dp0\dist\export_environment.yml
if ERRORLEVEL 1 GOTO ERROR

call env_deactivate.bat

echo Finished.
goto :eof

:ERROR
echo.
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ERROR !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo "!! An error occurred during execution.                            !!"
echo "!! The produced setup file may not be valid.                      !!"
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ERROR !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo.
echo.
exit /B %SEVENZIP_OK%
