#!/bin/bash

# Скрипт для управления контейнерами проекта TMB

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

function show_help {
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  start       - Запустить контейнеры"
    echo "  stop        - Остановить контейнеры"
    echo "  restart     - Перезапустить контейнеры"
    echo "  status      - Показать статус контейнеров"
    echo "  logs        - Показать логи контейнеров"
    echo "  psql        - Подключиться к PostgreSQL"
    echo "  redis       - Подключиться к Redis"
    echo "  clean       - Остановить контейнеры и удалить тома"
    echo "  help        - Показать эту справку"
}

function start_containers {
    echo "Запуск контейнеров..."
    docker-compose -f "$COMPOSE_FILE" up -d
    echo "Контейнеры запущены."
}

function stop_containers {
    echo "Остановка контейнеров..."
    docker-compose -f "$COMPOSE_FILE" down
    echo "Контейнеры остановлены."
}

function restart_containers {
    echo "Перезапуск контейнеров..."
    docker-compose -f "$COMPOSE_FILE" restart
    echo "Контейнеры перезапущены."
}

function show_status {
    echo "Статус контейнеров:"
    docker-compose -f "$COMPOSE_FILE" ps
}

function show_logs {
    echo "Логи контейнеров:"
    docker-compose -f "$COMPOSE_FILE" logs
}

function connect_psql {
    echo "Подключение к PostgreSQL..."
    docker exec -it tmb_postgres psql -U postgres -d app_db
}

function connect_redis {
    echo "Подключение к Redis..."
    docker exec -it tmb_redis redis-cli
}

function clean_all {
    echo "Остановка контейнеров и удаление томов..."
    docker-compose -f "$COMPOSE_FILE" down -v
    echo "Контейнеры остановлены и тома удалены."
}

# Проверка наличия аргументов
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Обработка команд
case "$1" in
    start)
        start_containers
        ;;
    stop)
        stop_containers
        ;;
    restart)
        restart_containers
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    psql)
        connect_psql
        ;;
    redis)
        connect_redis
        ;;
    clean)
        clean_all
        ;;
    help)
        show_help
        ;;
    *)
        echo "Неизвестная команда: $1"
        show_help
        exit 1
        ;;
esac

exit 0