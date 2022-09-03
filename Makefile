lint:
	python -m flake8 app
	python -m flake8 tests

migrate:
	python -m alembic upgrade head

test:
	python -m pytest

docker:
	docker-compose up --build

coverage:
	python -m pytest --cov=app --cov-report=xml
