@echo off
pip install django jdatetime
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
pause