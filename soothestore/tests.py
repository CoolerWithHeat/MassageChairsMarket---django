import requests

token = '3d4b0c8396313ed640876a2d707e8521a4a1575a'
request = requests.get('http://192.168.0.105/serverdestination/GetAllFAQs/')
print(request.json())
# import websocket

# def on_message(ws, message):
#     print(message)

# def on_error(ws, error):
#     print(error)

# def on_close(ws, close_status_code, close_msg):
#     print("### closed ###")

# def on_open(ws):
#     print("Opened connection")

# token = '3d4b0c8396313ed640876a2d707e8521a4a1575a'
# # token = None
# landed_page = 2
# if __name__ == "__main__":
#     websocket.enableTrace(True)
#     ws = websocket.WebSocketApp(f"ws://127.0.0.1:7999/analyticsdestination/{landed_page}/{token}",
#                               on_open=on_open,
#                               on_message=on_message,
#                               on_error=on_error,
#                               on_close=on_close)

#     ws.run_forever(reconnect=5)