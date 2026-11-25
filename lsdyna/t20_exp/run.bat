@echo off
rem usage: run.bat   (set LSDYNA_EXE to your solver, e.g. lsdyna_dp.exe of your installation)
if "%LSDYNA_EXE%"=="" (echo set LSDYNA_EXE first & exit /b 1)
"%LSDYNA_EXE%" i=main.k ncpu=4 memory=400m > solver.log 2>&1
