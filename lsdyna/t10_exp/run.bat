@echo off
rem double precision is required (implicit/SSD is not supported in single precision); bem=1 enables the acoustic BEM solver
if "%LSDYNA_EXE%"=="" set "LSDYNA_EXE=C:\Program Files\ANSYS Inc\v252\ansys\bin\winx64\lsdyna_dp.exe"
"%LSDYNA_EXE%" i=main.k ncpu=4 memory=400m bem=1 > solver.log 2>&1
