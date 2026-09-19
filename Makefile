PORT ?= 3000
IP ?= 0.0.0.0

run: migrate
	echo "ip is $(shell hostname -I)"
	uv run python manage.py runserver $(IP):$(PORT)

migrate:
	uv run python manage.py makemigrations
	uv run python manage.py migrate

push:
	git add . && git commit -m "push from makefile lenovo ubuntu" && git push origin main

superuser:
	uv run python manage.py createsuperuser