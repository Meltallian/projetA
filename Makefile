.PHONY: up down build logs shell migrate makemigrations createsuperuser clean help

help:
	@echo "Available commands:"
	@echo "  make up              - Start all containers in detached mode"
	@echo "  make down            - Stop all containers"
	@echo "  make build           - Rebuild all containers"
	@echo "  make logs            - View logs from all containers"
	@echo "  make shell           - Open a shell in the web container"
	@echo "  make migrate         - Run Django migrations"
	@echo "  make makemigrations  - Create new Django migrations"
	@echo "  make createsuperuser - Create a Django superuser"
	@echo "  make clean           - Remove all containers, volumes, and images"

up:
	sudo docker compose up -d
	sudo docker compose exec web python manage.py makemigrations
	sudo docker compose exec web python manage.py migrate
	sudo docker compose exec web python manage.py ensure_default_users

detach:
	sudo docker compose up
	sudo docker compose exec web python manage.py makemigrations
	sudo docker compose exec web python manage.py migrate
	sudo docker compose exec web python manage.py ensure_default_users

down:
	sudo docker compose down

build:
	sudo docker compose build

logs:
	sudo docker compose logs -f

shell:
	sudo docker compose exec web /bin/bash

mig:
	sudo docker compose exec web python manage.py makemigrations
	sudo docker compose exec web python manage.py migrate
	sudo docker compose exec web python manage.py ensure_default_users

migrate:
	sudo docker compose exec web python manage.py migrate

super:
	sudo docker compose exec web python manage.py createsuperuser

clean:
	sudo docker compose down -v --rmi all --remove-orphans

test:
	sudo docker compose exec web python manage.py test

collectstatic:
	sudo docker compose exec web python manage.py collectstatic --noinput

restart:
	sudo docker compose restart

ps:
	sudo docker compose ps