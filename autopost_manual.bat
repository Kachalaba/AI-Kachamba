chcp 65001
@echo off
set /p THEME="����� ���� �����: "
python autopost.py --theme "%THEME%" --tone serious --length medium
pause
