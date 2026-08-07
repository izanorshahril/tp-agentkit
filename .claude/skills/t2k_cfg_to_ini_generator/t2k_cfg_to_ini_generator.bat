@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM USAGE GUIDE
REM ============================================================================
REM 1. Interactive: Auto-detects cfg, previews, and prompts for confirmation.
REM    - Mode is auto-detected: OTPL if cfg contains stplFile, else RDK.
REM 2. Silent Mode:
REM    - "%~nx0" "path\to\config.cfg" [RDK|OTPL]
REM    - If mode is omitted, mode is auto-detected from cfg content.
REM    - If mode is provided, it overrides auto-detection.
REM ============================================================================

REM =========================================================
REM CONFIGURATION
REM =========================================================
set "defaultCfg=tplConfigFile.cfg"
set "excludeFolders= /Cfg/ /CommonLib/ /OfflineCfg/ /Scripts/ /Patterns/ /TestFunctions/ "
set "TAB=       "

REM =========================================================
REM MODE SELECTION
REM =========================================================
set "mode=RDK"
set "autoMode=1"

REM --- SILENT MODE ---
if not "%~1"=="" (
    set "cfgFile=%~1"
    set "isInteractive=0"
    if not "%~2"=="" (
        set "mode=%~2"
        set "autoMode=0"
    )
    goto :NormalizeMode
)
set "isInteractive=1"

goto :StartSearch

:NormalizeMode
set "mode=%mode: =%"
set "mode=%mode:"=%"
if /i "%mode%"=="OTPL" goto :DispatchMode
set "mode=RDK"

:DispatchMode
if "%isInteractive%"=="0" goto :SilentStart
goto :StartSearch

:StartSearch
cls
echo ========================================================
echo           T2K %mode% .ini generator for STCC
echo ========================================================
echo.

REM =========================================================
REM SCOPE DETECTION
REM =========================================================
set "searchPath=."
set "pathPrefix=."
set "searchRootDesc=Current Folder"

REM Analyze Parent Folder
for %%I in ("..") do set "pName=%%~nxI"
REM Check for "_" and prefix length >= 4
echo "!pName!" | findstr "_" >nul
if !errorlevel! EQU 0 (
    for /f "delims=_" %%A in ("!pName!") do set "pPrefix=%%A"
    if not "!pPrefix:~3,1!"=="" (
        set "searchPath=.."
        set "pathPrefix=.."
        set "searchRootDesc=Parent (!pName!)"
    )
)

REM Get Absolute Path of Search Root for string replacement
pushd "!searchPath!"
set "absSearchRoot=!CD!"
popd
set "outputRoot=!absSearchRoot!"

echo [Scope] Scanning !searchRootDesc!...

REM =========================================================
REM SCANNING
REM =========================================================
set "count=0"

REM Recursive search based on determined scope
for /r "%searchPath%" %%F in (*.cfg) do (
    set "skip=0"
    set "fullPath=%%~dpF"

    REM Exclusions
    for %%X in (%excludeFolders%) do (
        echo "!fullPath!" | findstr /i /c:"%%~X" >nul
        if !errorlevel! EQU 0 set "skip=1"
    )

    if "!skip!"=="0" (
        set /a count+=1
        set "file[!count!]=%%F"

        REM --- RELATIVE PATH CALCULATION ---
        set "absPath=%%~dpF"
        REM Remove the Search Root from the file path
        call :GetRelativePath "!absPath!" "!absSearchRoot!" "!pathPrefix!"
        set "displayPath=!relResult!%%~nxF"
        set "display[!count!]=!displayPath!"
    )
)

REM =========================================================
REM SELECTION LOGIC
REM =========================================================
if !count! EQU 0 (
    echo [!] No suitable .cfg files found.
    goto :ManualPathInput
)

REM --- SMART TRIGGER: IF ONLY 1 FILE, SKIP MENU ---
if !count! EQU 1 (
    set "cfgFile=!file[1]!"
    goto :PrepareProposal
)

REM --- MULTIPLE FILES MENU ---
echo.
echo [ Select Configuration File ]
echo --------------------------------------------------------
for /L %%i in (1,1,!count!) do (
    echo  %%i. !display[%%i]!
)
echo  A. Generate .ini for ALL .cfg
echo  M. Manual Path Input
echo  E. Exit
echo --------------------------------------------------------
set "fileChoice="
set /p "fileChoice=Select Option [1-!count!, A, M, E]: "

if /i "!fileChoice!"=="E" goto :EOF
if /i "!fileChoice!"=="M" goto :ManualPathInput
if /i "!fileChoice!"=="A" goto :GenerateAll
if !fileChoice! GTR !count! goto :StartSearch
if !fileChoice! LSS 1 goto :StartSearch

set "cfgFile=!file[%fileChoice%]!"
goto :PrepareProposal

REM =========================================================
REM BATCH GENERATION (ALL CFG)
REM =========================================================
:GenerateAll
cls
echo ========================================================
echo           T2K %mode% .ini generator for STCC
echo ========================================================
echo.
echo [Batch] Generating .ini for all detected .cfg files...
echo.

echo [ Batch Mode ]
echo  1. Auto-generate all (no prompts)
echo  2. Review each file (preview + rename option)
echo --------------------------------------------------------
set "bOpt=1"
set /p "bOpt=Select Option [1-2]: "
if not "!bOpt!"=="2" set "bOpt=1"

set "success=0"
set "fail=0"
set "origInteractive=!isInteractive!"
set "isInteractive=0"

for /L %%i in (1,1,!count!) do (
    set "cfgFile=!file[%%i]!"
    if "!bOpt!"=="2" (
        call :PrepareProposal
        if "!genError!"=="1" (
            set /a fail+=1
            echo [Skip] !cfgFile!
        ) else (
            set /a success+=1
            echo [ OK ] !cfgFile!
        )
    ) else (
        call :GenerateIniSilent
        if "!genError!"=="1" (
            set /a fail+=1
            echo [Fail] !cfgFile!
        ) else (
            set /a success+=1
            echo [Success] Generated: !iniFullPath!
        )
    )
)

set "isInteractive=!origInteractive!"
echo.
echo [Done] Success: !success!  Fail: !fail!
call :PromptReturn
exit /b 0

:ManualPathInput
echo.
set /p "cfgFile=Enter full path to .cfg: "
set "cfgFile=!cfgFile:"=!"
if not exist "!cfgFile!" goto :ManualPathInput
goto :PrepareProposal

REM =========================================================
REM PROPOSAL & PREVIEW
REM =========================================================
:PrepareProposal
REM 1. Parse Content IMMEDIATELY
call :ParseContent
if "!parseError!"=="1" goto :StartSearch

REM 2. Determine Naming Options
for %%I in ("!cfgFile!") do set "cfgDir=%%~dpI"
set "tempDir=!cfgDir:~0,-1!"
for %%I in ("!tempDir!") do set "rootFolderName=%%~nxI"

REM Option A: Folder Name (Before Underscore)
for /f "delims=_" %%A in ("!rootFolderName!") do set "optFolder=%%A"
REM Option B: Config Filename
for %%F in ("!cfgFile!") do set "optFile=%%~nF"

REM By default, prefer config filename unless it is tplConfigFile
set "finalName=!optFile!"
set "allowConfigName=1"
if /i "!optFile!"=="tplConfigFile" (
    set "finalName=!optFolder!"
    set "allowConfigName=0"
)

REM Determine whether there is a real alternative name to offer
set "hasAlt=0"
set "altCount=0"
set "alt1Name="
set "alt2Name="
if "!allowConfigName!"=="1" if /i not "!optFolder!"=="!optFile!" (
    set "hasAlt=1"
    REM Whichever is NOT the current finalName becomes the alternative
    if /i "!finalName!"=="!optFile!" (
        set /a altCount+=1
        set "alt1Name=!optFolder!"
    ) else (
        set /a altCount+=1
        set "alt1Name=!optFile!"
    )
)

REM Add free rename as another option in interactive mode
if "!isInteractive!"=="1" set /a altCount+=1

set "iniFileName=!finalName!.ini"
set "iniFullPath=!cfgDir!!iniFileName!"

if "!isInteractive!"=="0" goto :GenerateIniSilent

cls
echo ========================================================
echo           T2K %mode% .ini generator for STCC
echo ========================================================
echo.
echo [Config]
echo  CFG : !cfgFile!
echo  Mode: !mode! ^(!autoMode!^)
echo.
echo [Proposed Output]
echo  INI : !iniFullPath!
echo.
echo [Parsed Values]
echo  TestProgramFile : !tplFile!
if /i "!mode!"=="OTPL" echo  SubTestPlanList: !stplFile!
echo  SocketFile      : !socFile!
echo  EnvFile         : !envFile!
echo.
echo [Options]
echo  1. Generate with proposed name
set "optIndex=2"
if "!hasAlt!"=="1" (
    echo  !optIndex!. Use alternate name: !alt1Name!.ini
    set /a optIndex+=1
)
echo  !optIndex!. Enter custom output name
set /a exitIndex=optIndex+1
echo  !exitIndex!. Cancel
echo --------------------------------------------------------
set "choice="
set /p "choice=Select Option [1-!exitIndex!]: "

if "!choice!"=="1" goto :GenerateIni
if "!hasAlt!"=="1" if "!choice!"=="2" (
    set "iniFileName=!alt1Name!.ini"
    set "iniFullPath=!cfgDir!!iniFileName!"
    goto :GenerateIni
)

if "!hasAlt!"=="1" (
    if "!choice!"=="3" goto :CustomName
    if "!choice!"=="4" goto :StartSearch
    goto :PrepareProposal
) else (
    if "!choice!"=="2" goto :CustomName
    if "!choice!"=="3" goto :StartSearch
    goto :PrepareProposal
)

:CustomName
set "customName="
set /p "customName=Enter output base name (without .ini): "
if "!customName!"=="" goto :PrepareProposal
set "iniFileName=!customName!.ini"
set "iniFullPath=!cfgDir!!iniFileName!"
goto :GenerateIni

:SilentStart
if not exist "!cfgFile!" exit /b 1
for %%I in ("!cfgFile!") do set "cfgDir=%%~dpI"
set "tempDir=!cfgDir:~0,-1!"
for %%I in ("!tempDir!") do set "rootFolderName=%%~nxI"
for %%F in ("!cfgFile!") do set "optFile=%%~nF"
for /f "delims=_" %%A in ("!rootFolderName!") do set "optFolder=%%A"
set "finalName=!optFile!"
if /i "!optFile!"=="tplConfigFile" set "finalName=!optFolder!"
set "iniFileName=!finalName!.ini"
set "iniFullPath=!cfgDir!!iniFileName!"
call :ParseContent
if "!parseError!"=="1" exit /b 1
goto :GenerateIniSilent

:GenerateIniSilent
set "genError=0"
call :WriteIni
exit /b %errorlevel%

:GenerateIni
set "genError=0"
call :WriteIni
if "!genError!"=="1" goto :PrepareProposal
echo.
echo [Success] Generated: !iniFullPath!
call :PromptReturn
goto :StartSearch

:ParseContent
set "parseError=0"
set "tplFile="
set "stplFile="
set "envFile="
set "socFile="

if not exist "!cfgFile!" (
    echo [Error] cfg file not found: !cfgFile!
    set "parseError=1"
    exit /b 1
)

set "modeDetected=RDK"
for /f "usebackq delims=" %%L in ("!cfgFile!") do (
    set "line=%%L"
    call :ParseLine
)

call :CleanVar tplFile
call :CleanVar envFile
call :CleanVar socFile
call :CleanVar stplFile

if defined stplFile set "modeDetected=OTPL"

if "!autoMode!"=="1" set "mode=!modeDetected!"

if not defined tplFile set "parseError=1"
if not defined envFile set "parseError=1"
if not defined socFile set "parseError=1"
if /i "!mode!"=="OTPL" if not defined stplFile set "parseError=1"

if "!parseError!"=="1" (
    echo [Error] Missing required keys in cfg.
    exit /b 1
)

exit /b 0

:WriteIni
> "!iniFullPath!" (
    echo [TESTPROGRAMDEFINITION]
    echo TestProgramFile=!tplFile!
    if /i "!mode!"=="OTPL" echo SubTestPlanList=!stplFile!
    echo SocketFile=!socFile!
    echo EnvFile=!envFile!
    echo KeepPattern=false
)

if errorlevel 1 (
    echo [Error] Failed to write: !iniFullPath!
    set "genError=1"
    exit /b 1
)

exit /b 0

:ParseLine
set "rawLine=!line!"
if not defined rawLine exit /b
set "rawLine=!rawLine:%TAB%=!"
for /f "tokens=* delims= " %%a in ("!rawLine!") do set "rawLine=%%a"
if not defined rawLine exit /b
if "!rawLine:~0,1!"=="#" exit /b

for /f "tokens=1,* delims==" %%a in ("!rawLine!") do (
    set "key=%%a"
    set "val=%%b"
)
if not defined val exit /b

set "key=!key: =!"
set "key=!key:%TAB%=!"

if /i "!key!"=="tplFile" set "tplFile=!val!"
if /i "!key!"=="envFile" set "envFile=!val!"
if /i "!key!"=="socFile" set "socFile=!val!"
if /i "!key!"=="stplFile" set "stplFile=!val!"
exit /b

:CleanVar
if not defined %1 exit /b
set "val=!%1!"
for /f "tokens=* delims= " %%a in ("!val!") do set "val=%%a"
:TrimLoop
if "!val:~-1!"==" " (
    set "val=!val:~0,-1!"
    goto TrimLoop
)
set "val=!val:/=\!"
set "%1=!val!"
exit /b

:GetRelativePath
set "relAbs=%~1"
set "relRoot=%~2"
set "relPrefix=%~3"
set "relResult=%relAbs:%relRoot%=!"
if defined relResult (
    if not "%relPrefix%"=="." set "relResult=%relPrefix%%relResult%"
) else (
    set "relResult=%relPrefix%\"
)
exit /b 0

:PromptReturn
if "!isInteractive!"=="1" pause
exit /b 0