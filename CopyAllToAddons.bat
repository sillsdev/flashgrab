ECHO OFF
REM Developer (build): run this when you edit the SyncFromXML files or want to 'reinstall' them into Anki's
REM addons folder. Then restart Anki. 
REM Don't make edits over there in addons directly, as VCS won't see them, and an Anki or addon upgrade
REM might destroy them.
ECHO ON

xcopy /D /E /Y /exclude:excludedfileslist.txt xml\*.* %USERPROFILE%\documents\Anki\addons\xml\
xcopy /D /E /Y /exclude:excludedfileslist.txt xpath\*.* %USERPROFILE%\documents\Anki\addons\xpath\
xcopy /D /E /Y /exclude:excludedfileslist.txt distutils\*.* %USERPROFILE%\documents\Anki\addons\distutils\

xcopy /D /Y syncx.py %USERPROFILE%\documents\Anki\addons\
xcopy /D /E /Y /exclude:excludedfileslist.txt syncxml\*.* %USERPROFILE%\documents\Anki\addons\syncxml\

PAUSE
