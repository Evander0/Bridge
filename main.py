import requests
import json
import edge_tts
import asyncio
import websocket
import tkinter
import time
import threading
from playsound import playsound
import os

Chat_API = 'http://127.0.0.1:19327/v1/chat/completions'
Live2D_API = 'ws://127.0.0.1:10086/api'
enable_Live2D = True
enable_gui = True
prompt_index = [
    "你是一个乐于助人的助手。",

    "屑猫还没写完",

    ""
]
system_prompt = prompt_index[0]
voice_list = [
    'zh-CN-XiaoxiaoNeural',  # 0 Female
    'zh-CN-XiaoyiNeural',  # 1 Female recomanded
    'zh-CN-YunjianNeural',  # 2 Male
    'zh-CN-YunxiNeural',  # 3 Male recomanded
    'zh-CN-YunxiaNeural',  # 4 Male
    'zh-CN-YunyangNeural'  # 5 Male
]
voice = voice_list[3]
enable_tts = False
log_path = 'log/'
log_file = 'chat.log'
audio_file = 'tmp.mp3'


def post_msg():
    global thread_response_alive
    json_data = json.dumps({
        "messages": log,
        "max_tokens": 128,
        "temperature": 0.8,
        "num_beams": 4,
        "top_k": 40,
        "top_p": 0.75,
        "repetition_penalty": 1.0
    })
    thread_response_alive = True
    raw = requests.post(Chat_API, data=json_data, headers={'Content-Type': 'application/json'}).content
    response_msg = json.loads(raw)["choices"]
    response_sector = list(response_msg)[index_msg]
    thread_response_alive = False
    return response_sector["message"]["content"]


def tts(text):
    global thread_tts_alive
    thread_tts_alive = True
    asyncio.run(tts_backend(text))
    playsound(log_path + audio_file)
    os.remove(log_path + audio_file)
    thread_tts_alive = False


async def tts_backend(text):
    rate = '+0%'
    volume = '+0%'
    tts = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    await tts.save(log_path + audio_file)


def live2d_send(response):
    ws = websocket.WebSocket()
    try:
        ws.connect(Live2D_API)
    except Exception as e:
        print('WS异常：', e)
    msg = json.dumps({
        "msg": 11000,
        "msgId": 1,
        "data": {
            "id": 0,
            "text": response,
            "textFrameColor": 0x000000,
            "textColor": 0xFFFFFF,
            "duration": 10000
        }
    })
    ws.send(msg)
    ws.close()


def chat_main(input):
    time_start = time.time()
    global index_msg
    index_msg += 2
    log.append({"role": "user", "content": input})
    log_f.write("user: " + input + "\n")
    log_f.flush()
    response = post_msg()
    log.append({"role": "assistant", "content": response})
    log_f.write("assistant: " + response + "\n")
    log_f.flush()
    print('time cost', (time.time() - time_start), 's')
    output(response, "AI: ")


def enter_read(event):
    global thread_response_alive, thread_tts_alive
    if thread_response_alive or thread_tts_alive:
        return
    msg = gui_input.get()
    if msg != "":
        if msg[0] == "/":
            command(msg)
            gui_input.delete(0, tkinter.END)
        else:
            print("User: " + msg)
            thread_response = threading.Thread(target=chat_main, args=(msg,))
            thread_response.start()
            gui_input.delete(0, tkinter.END)


def on_click(event):
    start_x = event.x
    start_y = event.y


def on_move(event):
    x, y = event.widget.winfo_pointerxy()
    window.geometry("+%s+%s" % (x - 10, y - 10))
    # window.geometry("+%s+%s" % (x + event.x - start_x, y + event.y - start_y))


def visibility(event):
    x, y = event.x, event.y
    if 2 < x < 138 and 2 < y < 18:
        window.attributes("-alpha", 0.8)
    else:
        window.attributes("-alpha", 0.2)


def command(input):
    global enable_Live2D, enable_tts, voice
    input = input.lower()
    command_list = input[1:].split(" ")
    if command_list[0] == "set":
        if command_list[1] == "live2d":
            if command_list[2] == "on":
                enable_Live2D = True
                output("Live2D发送已开启")
            elif command_list[2] == "off":
                enable_Live2D = False
                output("Live2D发送已关闭")
            else:
                output("未知Live2D指令")

        elif command_list[1] == "tts":
            if command_list[2] == "on":
                enable_tts = True
                output("TTS已开启")
            elif command_list[2] == "off":
                enable_tts = False
                output("TTS已关闭")
            elif int(command_list[2]) in range(0, 5):
                voice = voice_list[int(command_list[2])]
                output("TTS音源已设置为：" + voice)
            else:
                output("未知TTS指令")
    elif command_list[0] == "exit":
        quit()
    else:
        output("未知的指令")


def output(message, front=""):
    print(front + message)
    if enable_Live2D:
        live2d_send(message)
    if enable_tts:
        thread_tts = threading.Thread(target=tts, args=(message,))
        thread_tts.start()


if not os.path.exists(log_path):
    os.makedirs(log_path)
    print("Log dir not found, creating")
log_f = open(log_path + log_file, "a")
log = [
    {"role": "system", "content": system_prompt}
]
index_msg = 0
log_f.write("system: " + system_prompt + "\n")
log_f.flush()
thread_response_alive = False
thread_tts_alive = False
if enable_gui:
    start_x, start_y = 0, 0
    window = tkinter.Tk()
    gui_input = tkinter.Entry(window, width=20)
    gui_move = tkinter.Button(window, text="移动", font=('黑体', 10))
    window.attributes("-alpha", 1)
    window.config(background='#2B2D30')
    gui_move.configure(bg='#1E1F22', fg='#BEBEBE')
    gui_input.configure(bg='#1E1F22', fg='#F5F5F5')
    window.overrideredirect(True)
    gui_move.pack(side=tkinter.LEFT)
    gui_input.pack(side=tkinter.RIGHT)
    window.bind('<Motion>', visibility)
    gui_move.bind('<Button-1>', on_click)
    gui_move.bind('<B1-Motion>', on_move)
    gui_input.bind("<Return>", enter_read)
    window.mainloop()
else:
    while 1:
        usr_input = input("User：")
        # usr_input = "你好"
        while thread_tts_alive:
            time.sleep(1)
        if usr_input != "":
            if usr_input[0] == "/":
                command(usr_input)
            else:
                chat_main(usr_input)
