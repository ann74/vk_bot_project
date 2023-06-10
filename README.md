![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Python](https://img.shields.io/badge/AIOHTTP-7B68EE?style=for-the-badge&logo=aiohttp&logoColor=black)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/Rabbitmq-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
# VK-бот "Поле чудес"

Бот организует игру "Поле чудес" в групповых чатах ВК:
- Игра иммитирует правила известной телевизионной игры
- Процесс игры осущетвляется через кнопки клавиатуры, ответы вводятся в чате
- Количество участников от 2-х до 5-ти
- Начинается по кнопке старта
- Игроки присоединяются по кнопке
- Игра начинается по таймеру, если участников меньше 5-ти
- Таймер на ход игрока
- Игроки могут выходить из игры, если не осталось ни одного, игра завершается
- Можно посмотреть информацию о последней игре

## Реализация
- Три отдельных процесса в одном приложении:
  - Poling - получает события из ВК API
  - BotManager - логика игры
  - Sender - посылает сообщения в чаты
- Общение между процессами через очереди RabbitMQ
- Admin API: регистрация админа, CRUD для вопросов
- База данных PostgreSQL
- Приложение, postgres и rabbitmq работают в docker контейнерах

## Стек
- aiohttp
- asyncio
- postgresql
- sqlalchemy
- alembic
- rabbitmq

## Зависимости
В файле requirements.txt

## Запуск
`docker-compose up -d`





