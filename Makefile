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
	sudo docker compose -f docker-compose.new.yml up -d

detach:
	sudo docker compose -f docker-compose.new.yml up

down:
	sudo docker compose -f docker-compose.new.yml down

build:
	sudo docker compose -f docker-compose.new.yml build

logs:
	sudo docker compose -f docker-compose.new.yml logs -f

shell:
	sudo docker compose -f docker-compose.new.yml exec web /bin/bash

mig:
	sudo docker compose -f docker-compose.new.yml exec web python manage.py makemigrations
	sudo docker compose -f docker-compose.new.yml exec web python manage.py migrate

migrate:
	sudo docker compose -f docker-compose.new.yml exec web python manage.py migrate

super:
	sudo docker compose -f docker-compose.new.yml exec web python manage.py createsuperuser

clean:
	sudo docker compose -f docker-compose.new.yml down -v --rmi all --remove-orphans

test:
	sudo docker compose -f docker-compose.new.yml exec web python manage.py test

collectstatic:
	sudo docker compose -f docker-compose.new.yml exec web python manage.py collectstatic --noinput

restart:
	sudo docker compose -f docker-compose.new.yml restart

ps:
	sudo docker compose -f docker-compose.new.yml ps
