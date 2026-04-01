@echo off
REM Step 1: Extract translatable strings
pybabel extract -F babel.cfg -o locales/messages.pot .

REM Step 2: Update existing .po catalogs
pybabel update -i locales/messages.pot -d locales -l en
pybabel update -i locales/messages.pot -d locales -l id

REM Step 3: Compile .po to .mo
pybabel compile -d locales -l en
pybabel compile -d locales -l id

echo Done!
