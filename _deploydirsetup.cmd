@echo off
set DEPENDENCIES_PATH=%~dp0.\dependencies
set MFW_BUILD_PATH=%DEPENDENCIES_PATH%\build_utils
set DIST_DIR=%~dp0.\dist

set PYTHONPATH=%DEPENDENCIES_PATH%;%~dp0
