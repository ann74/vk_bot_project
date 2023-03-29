import json

start_keyboard = {
   "one_time": True,
   "inline": False,
   "buttons": [
      [
         {
            "action": {
               "type": "text",
               "payload": "{\"button\": \"1\"}",
               "label": "Начать игру"
            },
            "color": "primary"
         },
      ]
   ]
}
start_keyboard = str(json.dumps(start_keyboard))

start_keyboard_1 = {
   "one_time": True,
   "inline": False,
   "buttons": [
      [
         {
            "action": {
               "type": "callback",
               "payload": "{}",
               "label": "Начать игру"
            },
            "color": "primary"
         },
      ]
   ]
}
start_keyboard_1 = str(json.dumps(start_keyboard_1))

