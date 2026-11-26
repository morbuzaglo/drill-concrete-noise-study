@echo off
rem double precision, BEM enabled. The direct SSD needs the SMP solver (not MPP).
if "%LSDYNA_EXE%"=="" set "LSDYNA_EXE=C:\Program Files\ANSYS Inc\v252\ansys\bin\winx64\lsdyna_dp.exe"
"%LSDYNA_EXE%" i=main.k ncpu=4 memory=2000m bem=1 > solver.log 2>&1
