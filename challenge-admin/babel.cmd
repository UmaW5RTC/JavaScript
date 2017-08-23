@ECHO OFF

if "%1" == "init" (
    pybabel init -i messages.pot -d translations -l %2
)

if "%1" == "extract" (
    pybabel extract -F babel.cfg -o messages.pot .
)

if "%1" == "update" (
    pybabel update -i messages.pot -d translations
)

if "%1" == "compile" (
    pybabel compile -d translations
)


