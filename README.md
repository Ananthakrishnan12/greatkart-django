Install Django ---> pip install django==3.1
pip freeze --> to find the list of installed packages by Django in the virtual Environment.

create Django project --> django-admin startproject greatkart .

To run Django project --> python manage.py runserver 

create views.py in the django project(greatkart)

create templates folder in the rootfolder.

configure the templates with settings.

create static folder inside the greatkart and copy all the js,img,css folder in the static folder..
STATIC_ROOT = BASE_DIR /"static"
STATICFILES_DIRS = [
    "greatkart/static",
]
and then --> python manage.py collectstatic   in the cmd..

for appearning images in the website load static in the html file..

To create App ---> python manage.py startapp category and then configure app in the settings.py

for make migrations --> python manage.py makemigrations
                    --> python manage.py migrate

To access the Django admin panel,we need to have login credentials...(superuser)
--> python manage.py createsuperuser
after that register username and password....

1.username=sujith
email:sujith@gmail.com
password=sujith97

1.First_name:developer
  Last_name:1
  Email:developer1@gmail.com
  password:developer1@123
  username=developer1