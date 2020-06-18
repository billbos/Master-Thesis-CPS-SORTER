  
all: setup

venv/bin/activate:
	if which virtualenv-2.7 >/dev/null; then virtualenv-2.7 venv; else virtualenv venv; fi

run: venv/bin/activate requirements.txt
	. venv/bin/activate; python manage.py runserver -h 0.0.0.0 -d -r

setup: venv/bin/activate requirements.txt
	. venv/bin/activate; pip install -Ur requirements.txt
	cd static && bower install

init: venv/bin/activate requirements.txt
	. venv/bin/activate; python manage.py db upgrade 

celery:
	. venv/bin/activate; python celery_run.py worker

