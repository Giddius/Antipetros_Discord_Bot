@ECHO OFF
SETLOCAL ENABLEEXTENSIONS

REM ----------------------------------------------------------------------------------------------------
REM Necessary Files:
REM - pre_setup_scripts.txt
REM - required_personal_packages.txt
REM - required_misc.txt
REM - required_Qt.txt
REM - required_from_github.txt
REM - required_test.txt
REM - required_dev.txt
REM - post_setup_scripts.txt
REM ----------------------------------------------------------------------------------------------------


SET PROJECT_NAME=%~1
SET PROJECT_AUTHOR=%~2

SET TOOLS_FOLDER=%~dp0
SET WORKSPACE_FOLDER=%TOOLS_FOLDER%\..
SET OUTPRFX=++++++++++

REM ---------------------------------------------------
SET _date=%DATE:/=-%
SET _time=%TIME::=%
SET _time=%_time: =0%
REM ---------------------------------------------------
REM ---------------------------------------------------
SET _decades=%_date:~-2%
SET _years=%_date:~-4%
SET _months=%_date:~3,2%
SET _days=%_date:~0,2%
REM ---------------------------------------------------
SET _hours=%_time:~0,2%
SET _minutes=%_time:~2,2%
SET _seconds=%_time:~4,2%
REM ---------------------------------------------------
SET TIMEBLOCK=%_years%-%_months%-%_days%_%_hours%-%_minutes%-%_seconds%

ECHO ***************** Current time is *****************
ECHO                     %TIMEBLOCK%

ECHO ################# CHANGING DIRECTORY to -- %TOOLS_FOLDER% -- +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
CD %TOOLS_FOLDER%
ECHO.

ECHO -------------------------------------------- PRE-SETUP SCRIPTS --------------------------------------------
ECHO.
FOR /F "tokens=1,2 delims=," %%A in (.\venv_setup_settings\pre_setup_scripts.txt) do (
ECHO.
ECHO -------------------------- Calling %%A with %%B --------------^>
ECHO %OUTPRFX% CALL %%A %%B 1>&2
CALL %%A %%B
ECHO.
)
Echo.
ECHO -------------------------------------------- preparing venv_setup_settings --------------------------------------------
ECHO.
ECHO ################# preparing venv_setup_settings
ECHO %OUTPRFX% %TOOLS_FOLDER%prepare_venv_settings.py %TOOLS_FOLDER% 1>&2
call %TOOLS_FOLDER%prepare_venv_settings.py %TOOLS_FOLDER%
if %ERRORLEVEL% == 1 (
    ECHO.
    ECHO ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ECHO 8888888888888888888888888888888888888888888888888
    ECHO.
    Echo Created Venv settings folder, please custimize the files and restart the Scripts
    ECHO.
    ECHO 8888888888888888888888888888888888888888888888888
    ECHO ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ECHO.
    Exit 63
) else (
    Echo finished preparing venv
)


ECHO.
ECHO -------------------------------------------- Clearing Pip Cache --------------------------------------------
ECHO %OUTPRFX% call pip cache purge 1>&2
call pip cache purge
ECHO.



ECHO -------------------------------------------- BASIC VENV SETUP --------------------------------------------
ECHO.


ECHO ################# Removing old venv folder

ECHO %OUTPRFX% RD /S /Q %WORKSPACE_FOLDER%\.venv 1>&2
RD /S /Q %WORKSPACE_FOLDER%\.venv

ECHO.


ECHO ################# pycleaning workspace

ECHO %OUTPRFX% call pyclean %WORKSPACE_FOLDER% 1>&2
call pyclean %WORKSPACE_FOLDER%

echo.



ECHO ################# creating new venv folder

ECHO %OUTPRFX% mkdir %WORKSPACE_FOLDER%\.venv 1>&2
mkdir %WORKSPACE_FOLDER%\.venv

ECHO.

ECHO ################# Calling venv module to initialize new venv

ECHO %OUTPRFX% python -m venv %WORKSPACE_FOLDER%\.venv 1>&2
python -m venv %WORKSPACE_FOLDER%\.venv

ECHO.

ECHO ################# activating venv for package installation

ECHO %OUTPRFX% CALL %WORKSPACE_FOLDER%\.venv\Scripts\activate.bat 1>&2
CALL %WORKSPACE_FOLDER%\.venv\Scripts\activate.bat
ECHO.

ECHO ################# upgrading pip to get rid of stupid warning

ECHO %OUTPRFX% call curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py 1>&2
call curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

set _REPLACE_STRING=

ECHO %OUTPRFX% call fart -C %TOOLS_FOLDER%get-pip.py "import os.path" "import setuptools\nimport os.path" 1>&2
call fart -C %TOOLS_FOLDER%get-pip.py "import os.path" "import setuptools\nimport os.path"

ECHO %OUTPRFX% call get-pip.py --force-reinstall 1>&2
call get-pip.py --force-reinstall

ECHO %OUTPRFX% del /Q get-pip.py 1>&2
del /Q get-pip.py

ECHO.

ECHO.
ECHO -------------------------------------------------------------------------------------------------------------
ECHO ++++++++++++++++++++++++++++++++++++++++++++ INSTALLING PACKAGES ++++++++++++++++++++++++++++++++++++++++++++
ECHO -------------------------------------------------------------------------------------------------------------
ECHO.
ECHO.



ECHO +++++++++++++++++++++++++++++ Standard Packages +++++++++++++++++++++++++++++
ECHO.
ECHO.

ECHO ################# Installing Setuptools

ECHO %OUTPRFX% CALL pip install --upgrade setuptools 1>&2
CALL pip install --upgrade setuptools

ECHO.

ECHO ################# Installing wheel

ECHO %OUTPRFX% CALL pip install --upgrade wheel 1>&2
CALL pip install --upgrade wheel

ECHO.

ECHO ################# Installing PEP517

ECHO %OUTPRFX% CALL pip install --upgrade PEP517 1>&2
CALL pip install --upgrade PEP517

ECHO.

ECHO ################# Installing python-dotenv

ECHO %OUTPRFX% CALL pip install --upgrade python-dotenv 1>&2
CALL pip install --upgrade python-dotenv

ECHO.



ECHO ################# Installing flit

ECHO %OUTPRFX% CALL pip install --upgrade flit 1>&2
CALL pip install --upgrade flit

ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Qt Packages +++++++++++++++++++++++++++++
ECHO.
rem CALL pip install --upgrade --no-cache-dir PyQt5>=5.15.3
FOR /F "tokens=1 delims=," %%A in (.\venv_setup_settings\required_Qt.txt) do (
ECHO.

ECHO.
ECHO.

ECHO -------------------------- Installing %%A --------------^>
ECHO.
ECHO %OUTPRFX% CALL pip install %%A 1>&2
CALL pip install %%A
ECHO.
)
ECHO +++++++++++++++++++++++++++++ Gid Packages +++++++++++++++++++++++++++++
ECHO.
ECHO.

FOR /F "tokens=1,2 delims=," %%A in (.\venv_setup_settings\required_personal_packages.txt) do (
ECHO.
ECHO -------------------------- Installing %%B --------------^>
ECHO.
ECHO %OUTPRFX% PUSHD %%A 1>&2
PUSHD %%A
ECHO %OUTPRFX% CALL flit install -s  1>&2
CALL flit install -s
POPD
ECHO.
)

ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Misc Packages +++++++++++++++++++++++++++++
ECHO.
FOR /F "tokens=1 delims=," %%A in (.\venv_setup_settings\required_misc.txt) do (
ECHO.
ECHO -------------------------- Installing %%A --------------^>
ECHO.
ECHO %OUTPRFX% CALL pip install %%A 1>&2
CALL pip install %%A
ECHO.
)

ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Experimental Packages +++++++++++++++++++++++++++++
ECHO.
FOR /F "tokens=1 delims=," %%A in (.\venv_setup_settings\required_experimental.txt) do (
ECHO.
ECHO -------------------------- Installing %%A --------------^>
ECHO.
ECHO %OUTPRFX% CALL pip install %%A 1>&2
CALL pip install %%A
ECHO.
)

ECHO.
ECHO.



ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Packages From Github +++++++++++++++++++++++++++++
ECHO.
FOR /F "tokens=1 delims=," %%A in (.\venv_setup_settings\required_from_github.txt) do (
ECHO.
ECHO -------------------------- Installing %%A --------------^>
ECHO.
ECHO %OUTPRFX% CALL pip install --upgrade --no-cache-dir git+%%A %OUTPRFX% 1>&2
CALL pip install --upgrade --no-cache-dir git+%%A
ECHO.
)

ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Test Packages +++++++++++++++++++++++++++++
ECHO.
FOR /F "tokens=1 delims=," %%A in (.\venv_setup_settings\required_test.txt) do (
ECHO.
ECHO -------------------------- Installing %%A --------------^>
ECHO.
ECHO %OUTPRFX% CALL pip install %%A 1>&2
CALL pip install %%A
ECHO.
)

ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Dev Packages +++++++++++++++++++++++++++++
ECHO.
FOR /F "tokens=1 delims=," %%A in (.\venv_setup_settings\required_dev.txt) do (
ECHO.
ECHO -------------------------- Installing %%A --------------^>
ECHO.
ECHO %OUTPRFX% CALL pip install %%A 1>&2
CALL pip install %%A
ECHO.
)

ECHO.
ECHO.


ECHO -------------------------------------------- INSTALL THE PROJECT ITSELF AS -DEV PACKAGE --------------------------------------------
echo.
ECHO %OUTPRFX% PUSHD %WORKSPACE_FOLDER% 1>&2
PUSHD %WORKSPACE_FOLDER%
rem call pip install -e .
ECHO %OUTPRFX% call flit install -s 1>&2
call flit install -s
echo.
POPD
ECHO.

ECHO.
ECHO.

ECHO -------------------------------------------- POST-SETUP SCRIPTS --------------------------------------------
ECHO.
FOR /F "tokens=1,2 delims=," %%A in (.\venv_setup_settings\post_setup_scripts.txt) do (
ECHO.
ECHO -------------------------- Calling %%A with %%B --------------^>
ECHO %OUTPRFX% CALL %%A %%B 1>&2
CALL %%A %%B
ECHO.
)

ECHO.
ECHO.

ECHO.
ECHO #############################################################################################################
ECHO -------------------------------------------------------------------------------------------------------------
ECHO #############################################################################################################
ECHO.
ECHO.
ECHO ++++++++++++++++++++++++++++++++++++++++++++++++++ FINISHED +++++++++++++++++++++++++++++++++++++++++++++++++
ECHO.
echo ************************** ErrorLevel at end of create_venv script is %ERRORLEVEL% ************************** 1>&2
ECHO.
ECHO #############################################################################################################
ECHO -------------------------------------------------------------------------------------------------------------
ECHO #############################################################################################################
ECHO.
