@echo off

for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"

echo %ESC%[33mDEBUG MODE ACTIVATED DFB %ESC%[0m
echo THIS IS ONLY FOR TESTING
pause
cd C:\Users\auray\Desktop\DarkFoxbrowser
python DFBrowser.py
pause