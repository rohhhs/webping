@echo off
setlocal

:: Prompt user for input path
set /p inputPath="Enter Input Path: "

:: Prompt user for output path
set /p outputPath="Enter Output Path: "

:: Run the Python script with the provided paths
python .\init.py --input "%inputPath%" --output "%outputPath%"

endlocal
