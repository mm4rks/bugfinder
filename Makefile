.DEFAULT_GOAL := run

ifdef PROD
TARGET := production
ENV_FILE := .env.prod
COMPOSE_ARGS := -f docker-compose.prod.yml --env-file .env.prod
else
TARGET := development
ENV_FILE := .env.dev
COMPOSE_ARGS := --env-file .env.dev
endif

USER_ID := $(shell id -u)
GROUP_ID := $(shell id -g)

.PHONY: run 
run:
	@echo "running for $(TARGET)"
	sudo docker compose $(COMPOSE_ARGS) up

.PHONY: build
build: $(ENV_FILE)
	@echo "building image(s) for $(TARGET)"
	sudo docker compose $(COMPOSE_ARGS) build

$(ENV_FILE):
	./generate_env.sh

.PHONY: install
install: dewolf build
	@echo "installing for $(TARGET)"
	test -d .venv || python -m venv .venv
	. .venv/bin/activate; pip install -r requirements.txt
	mkdir -p data/samples
	touch data/db.sqlite3
	sudo chown -R $(USER_ID):$(GROUP_ID) data/
	sudo docker compose $(COMPOSE_ARGS) run web python manage.py makemigrations
	sudo docker compose $(COMPOSE_ARGS) run web python manage.py migrate
	# TODO shared volume permissions
	sudo docker compose $(COMPOSE_ARGS) run --user 0 web python manage.py collectstatic
	sudo chown -R $(USER_ID):$(GROUP_ID) data/
	./install_worker_service.sh
	

.PHONY: dewolf
dewolf:
	./update.sh

.PHONY: filter
filter:
	python filter.py -i data/samples.sqlite3 -o data/filtered.sqlite3

