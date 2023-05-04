.PHONY: run dev prod run-prod

.DEFAULT_GOAL := run

run:
	sudo ./processor.sh dev

run-prod:
	sudo ./processor.sh prod

dev:
	./install.sh dev

prod:
	./install.sh prod

# user:
# 	sudo docker compose run web python manage.py createsuperuser
