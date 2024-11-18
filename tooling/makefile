
all:
	@echo "Available Commands:"
	@echo "  make up    - Start All Stacks"
	@echo "  make down  - Stop All Stacks"
	@echo "  make clear - Stop All Stacks and Remove All RTMD Volumes/Data"
	@echo "  make size  - Display the Size of Docker Volumes"
	
up:
	@cd broker && docker-compose up -d --build
	@cd ignition && docker-compose up -d --build
	@cd influx && docker-compose up -d --build
	@cd mes && docker-compose up -d --build
	@cd player && docker-compose up -d --build
	
down:
	@cd player && docker-compose down || exit 0
	@cd mes && docker-compose down || exit 0
	@cd influx && docker-compose down || exit 0
	@cd ignition && docker-compose down || exit 0
	@cd broker && docker-compose down || exit 0
	
clear: down
	@echo "Removing Volumes..."
	@docker volume rm rtmd-ignition || exit 0
	@docker volume rm rtmd-historian || exit 0
	@docker volume rm rtmd-influx || exit 0
	@docker volume rm rtmd-mes || exit 0

size:
	@docker system df -v | grep "^rtmd-"
