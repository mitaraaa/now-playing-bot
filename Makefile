up:
	docker compose up

down:
	docker compose down

build:
	docker build -t mitaraaa/now-playing-app:1 .

logs:
	docker compose logs -f --tail 10
