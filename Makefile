.PHONY: help install assets dev-assets migrate seed run test docker docker-down docker-logs clean

help:  ## Показать список команд
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

install:  ## Создать venv и поставить зависимости
	python3 -m venv .venv
	.venv/bin/pip install -r requirements-dev.txt

assets:  ## Собрать фронтенд (Vite + Tailwind)
	npm install
	npm run build

dev-assets:  ## Дев-сервер Vite с HMR (запускать рядом с make run)
	npm run dev

migrate:  ## Применить миграции
	.venv/bin/python manage.py migrate

seed:  ## Загрузить демо-данные
	.venv/bin/python manage.py seed_demo

run:  ## Запустить сервер разработки
	.venv/bin/python manage.py runserver

test:  ## Прогнать тесты
	.venv/bin/python -m pytest

docker:  ## Поднять приложение в Docker
	docker compose up --build

docker-down:  ## Остановить и удалить контейнеры вместе с данными
	docker compose down -v

docker-logs:  ## Показать логи приложения
	docker compose logs -f web

clean:  ## Удалить локальную БД и кэши
	rm -f db.sqlite3
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache staticfiles
