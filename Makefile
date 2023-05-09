.DEFAULT_GOAL := run

.PHONY: run 
ifdef PROD
run:
	@echo "PROD"
	sudo docker compose -f docker-compose.prod.yml --env-file .env.prod up
else
run:
	@echo "DEV"
	sudo docker compose --env-file .env.dev up
endif


.PHONY: build
ifdef PROD
build:
	@echo "PROD"
	git pull
	sudo docker compose -f docker-compose.prod.yml --env-file .env.prod build
else
build:
	@echo "DEV"
	git pull
	sudo docker compose --env-file .env.dev build
endif

.PHONY: update
ifdef PROD
update:
	@echo "PROD"
	git pull
	sudo docker compose -f docker-compose.prod.yml --env-file .env.prod run web python manage.py makemigrations
	sudo docker compose -f docker-compose.prod.yml --env-file .env.prod run web python manage.py migrate
	sudo docker compose -f docker-compose.prod.yml --env-file .env.prod run web python manage.py collectstatic
else
update:
	@echo "DEV"
	git pull
	sudo docker compose .env.dev run web python manage.py makemigrations
	sudo docker compose .env.dev run web python manage.py migrate
	sudo docker compose .env.dev run web python manage.py collectstatic
endif

