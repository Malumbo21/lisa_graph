init:
	python manage.py makemigrations stock_data && python manage.py migrate
run:
	python manage.py runserver
