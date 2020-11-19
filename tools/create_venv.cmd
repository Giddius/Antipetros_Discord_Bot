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

@ECHO OFF
SETLOCAL ENABLEEXTENSIONS




SET PROJECT_NAME=antipetros_discordbot

SET OLDHOME_FOLDER=%~dp0

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

ECHO ################# changing directory to %OLDHOME_FOLDER%
CD %OLDHOME_FOLDER%
ECHO.

ECHO -------------------------------------------- PRE-SETUP SCRIPTS --------------------------------------------
ECHO.
FOR /F "tokens=1,2 delims=," %%A in (.\venv_setup_settings\pre_setup_scripts.txt) do (
ECHO.
ECHO -------------------------- Calling %%A with %%B --------------^>
CALL %%A %%B
ECHO.
)



ECHO -------------------------------------------- BASIC VENV SETUP --------------------------------------------
ECHO.

ECHO ################# suspending Dropbox
CALL pskill64 Dropbox
ECHO.

ECHO ################# Removing old venv folder
RD /S /Q ..\.venv
ECHO.

ECHO ################# creating new venv folder
mkdir ..\.venv
ECHO.

ECHO ################# Calling venv module to initialize new venv
python -m venv ..\.venv
ECHO.

ECHO ################# changing directory to ..\.venv
CD ..\.venv
ECHO.

ECHO ################# activating venv for package installation
CALL .\Scripts\activate.bat
ECHO.

ECHO ################# upgrading pip to get rid of stupid warning
CALL %OLDHOME_FOLDER%get-pip.py
ECHO.

ECHO.
ECHO -------------------------------------------------------------------------------------------------------------
ECHO ++++++++++++++++++++++++++++++++++++++++++++ INSTALLING PACKAGES ++++++++++++++++++++++++++++++++++++++++++++
ECHO -------------------------------------------------------------------------------------------------------------
ECHO.
ECHO.

CD %OLDHOME_FOLDER%

ECHO +++++++++++++++++++++++++++++ Standard Packages +++++++++++++++++++++++++++++
ECHO.
ECHO.

ECHO ################# Installing Setuptools
CALL pip install --upgrade --pre setuptools
ECHO.

ECHO ################# Installing wheel
CALL pip install --upgrade --pre wheel
ECHO.

ECHO ################# Installing python-dotenv
CALL pip install --upgrade --pre python-dotenv
ECHO.



ECHO ################# Installing flit
CALL pip install --force-reinstall --no-cache-dir --upgrade --pre flit
ECHO.

ECHO.
ECHO.

ECHO +++++++++++++++++++++++++++++ Gid Packages +++++++++++++++++++++++++++++
ECHO.
ECHO.

FOR /F "tokens=1,2 delims=," %%A in (.\venv_setup_settings\required_personal_packages.txt) do (
ECHO.
ECHO -------------------------- Installing %%B --------------^>
ECHO.
PUSHD %%A
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
CALL pip install --upgrade %%A
ECHO.
)

ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Qt Packages +++++++++++++++++++++++++++++
ECHO.
FOR /F "tokens=1 delims=," %%A in (.\venv_setup_settings\required_Qt.txt) do (
ECHO.
ECHO -------------------------- Installing %%A --------------^>
ECHO.
CALL pip install --upgrade %%A
ECHO.
)

ECHO.
ECHO.

Echo +++++++++++++++++++++++++++++ Packages From Github +++++++++++++++++++++++++++++
ECHO.
FOR /F "tokens=1 delims=," %%A in (.\venv_setup_settings\required_from_github.txt) do (
ECHO.
ECHO -------------------------- Installing %%A --------------^>
ECHO.
CALL call pip install --upgrade git+%%A
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
CALL pip install --upgrade %%A
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
CALL pip install --no-cache-dir --upgrade --pre %%A
ECHO.
)

ECHO.
ECHO.


ECHO -------------------------------------------- INSTALL THE PROJECT ITSELF AS -DEV PACKAGE --------------------------------------------
cd ..\
rem call pip install -e .
call flit install -s
ECHO.

ECHO.
ECHO.

CD %OLDHOME_FOLDER%

ECHO -------------------------------------------- POST-SETUP SCRIPTS --------------------------------------------
ECHO.
FOR /F "tokens=1,2 delims=," %%A in (.\venv_setup_settings\post_setup_scripts.txt) do (
ECHO.
ECHO -------------------------- Calling %%A with %%B --------------^>
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
ECHO ++++++++++++++++++++++++++++++++++++++++++++++++++ FINISHED +++++++++++++++++++++++++++++++++++++++++++++++++
ECHO.
ECHO #############################################################################################################
ECHO -------------------------------------------------------------------------------------------------------------
ECHO #############################################################################################################
ECHO.