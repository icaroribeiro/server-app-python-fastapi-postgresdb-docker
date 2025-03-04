# Set of Database tasks
# --------------------------------------------------
startup-database:
	docker-compose up --build -d database

shutdown-database:
	docker-compose down -v --rmi local database

# Set of Server APP tasks
# --------------------------------------------------
startup-server:
	docker-compose up --build -d server

shutdown-server:
	docker-compose down -v --rmi local server
