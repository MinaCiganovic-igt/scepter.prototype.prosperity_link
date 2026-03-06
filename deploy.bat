@echo off

setlocal

set MYDIR=%~dp0.
call %MYDIR%\_deploydirsetup.cmd

set RELEASE_TYPE=%~1
set RELEASE_VERSION=%~2
shift
if "" == "%RELEASE_TYPE%" set RELEASE_TYPE=release

call env_push
set deploy_exe=%MFW_BUILD_PATH%\bin\deploy.exe
set PYTHONPATH=%SOURCE_DIR%;.
python prototype_deployment\configure_deployment_data.py --version %RELEASE_VERSION% --template prototype_deployment\deployment_data.json.in --output "%DIST_DIR%\deployment_data.json"
if ERRORLEVEL 1 GOTO ERROR

if "release" == "%RELEASE_TYPE%" (
    python prototype_deployment\_deploy_installer.py
    if ERRORLEVEL 1 GOTO ERROR
)

call env_pop
exit /B 0

:ERROR
call env_pop
echo.
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ERROR !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo "!! An error occurred during execution.                            !!"
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ERROR !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo.
exit /B 1

