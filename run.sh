#!/bin/bash

# Скрипт для запуску Retail AI Помічника для Покупок

# Функція для відображення допомоги
show_help() {
    echo "Використання: ./run.sh [опції]"
    echo ""
    echo "Опції:"
    echo "  -h, --help       Показати цю довідку"
    echo "  -d, --debug      Запустити у режимі налагодження"
    echo "  -l, --log FILE   Вказати файл для логування (за замовчуванням: retail_agent.log)"
    echo ""
    echo "Приклади:"
    echo "  ./run.sh                     # Запустити у звичайному режимі"
    echo "  ./run.sh --debug             # Запустити у режимі налагодження"
    echo "  ./run.sh --log custom.log    # Використовувати custom.log для логування"
    echo ""
}

# Ініціалізація змінних за замовчуванням
DEBUG_MODE=""
LOG_FILE="retail_agent.log"

# Перевірка наявності Python
if ! command -v python3 &> /dev/null; then
    echo "Помилка: Python 3 не знайдено. Будь ласка, встановіть Python 3."
    exit 1
fi

# Перевірка наявності файлу .env
if [ ! -f .env ]; then
    echo "Увага: Файл .env не знайдено. Створіть файл .env з необхідними змінними оточення."
    echo "Приклад вмісту .env:"
    echo "OPENAI_API_KEY=ваш_ключ_openai"
    echo "ODOO_URL=https://ваш_сервер_odoo/api"
    echo "ODOO_DB=назва_бази_даних"
    echo "ODOO_USERNAME=користувач"
    echo "ODOO_PASSWORD=пароль"
    echo ""
    read -p "Бажаєте продовжити без файлу .env? (y/n): " choice
    if [ "$choice" != "y" ]; then
        exit 1
    fi
fi

# Обробка аргументів командного рядка
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--debug)
            DEBUG_MODE="--debug"
            shift
            ;;
        -l|--log)
            if [[ $# -lt 2 ]]; then
                echo "Помилка: Аргумент --log потребує значення."
                exit 1
            fi
            LOG_FILE="$2"
            shift 2
            ;;
        *)
            echo "Невідомий аргумент: $1"
            show_help
            exit 1
            ;;
    esac
done

# Перевірка наявності необхідних файлів
if [ ! -f main.py ]; then
    echo "Помилка: Файл main.py не знайдено. Переконайтесь, що ви знаходитесь у правильній директорії."
    exit 1
fi

# Перевірка наявності всіх залежностей
echo "Перевірка залежностей..."
if ! python3 -c "import pkg_resources; [pkg_resources.require(l.strip()) for l in open('requirements.txt')]" 2>/dev/null; then
    echo "Деякі залежності відсутні. Бажаєте встановити їх зараз? (y/n): "
    read choice
    if [ "$choice" = "y" ]; then
        echo "Встановлення залежностей..."
        python3 -m pip install -r requirements.txt
    else
        echo "Залежності не встановлено. Запуск може завершитися помилкою."
    fi
fi

# Запуск агента
echo "Запуск Retail AI Помічника для Покупок..."
python3 main.py $DEBUG_MODE --log-file "$LOG_FILE"
