chcp 65001
@echo off
set /p THEME="¬веди тему поста: "
python autopost.py --theme "%THEME%" --tone serious --length medium
pause
