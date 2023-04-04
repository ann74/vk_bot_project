import json

start_keyboard = {
    "one_time": False,
    "inline": False,
    "buttons": [
        [
            {
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"startgame\"}",
                    "label": "Начать игру"
                },
                "color": "positive"
            },
        ],
        [
            {
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"info\"}",
                    "label": "Информация о последней игре"
                },
                "color": "negative"
            },
        ]
    ]
}
start_keyboard = str(json.dumps(start_keyboard))

start_keyboard_callback = {
    "one_time": True,
    "inline": False,
    "buttons": [
        [
            {
                "action": {
                    "type": "callback",
                    "payload": "{\"button\": \"startgame\"}",
                    "label": "Начать игру"
                },
                "color": "primary"
            },
        ]
    ]
}
start_keyboard_callback = str(json.dumps(start_keyboard_callback))

union_keyboard = {
    "one_time": False,
    "inline": False,
    "buttons": [
        [
            {
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"uniongame\"}",
                    "label": "Присоединиться к игре"
                },
                "color": "primary"
            },
        ]
    ]
}

union_keyboard = str(json.dumps(union_keyboard))

main_keyboard = {
    "one_time": False,
    "inline": False,
    "buttons": [
        [
            {
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"drum\"}",
                    "label": "Крутить барабан"
                },
                "color": "primary"
            },
        ],
        [
            {
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"word\"}",
                    "label": "Назвать слово"
                },
                "color": "positive"
            },
            {
                "action": {
                    "type": "text",
                    "payload": "{\"button\": \"leave\"}",
                    "label": "Покинуть игру"
                },
                "color": "negative"
            },
        ],
    ]
}

main_keyboard = str(json.dumps(main_keyboard))
