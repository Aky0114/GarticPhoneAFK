import re
import os
import json
import time
import uuid
import httpx
import random
import string
import pathlib
import tkinter
import secrets
import colorama
import websocket
import threading

from tkinter import messagebox

class GarticPhoneClient:
    def __init__(self):
        self.ws = ""
        self.client = httpx.Client()

        self.headers = {
            "Origin": "https://garticphone.com",
            "Referer": "https://garticphone.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
        }
        self.endpoint = ""
        self.sid = ""
        self.id = ""

    def send_requests(self, room_id):
        randomize_icon = str(random.randint(1, 37))

        self.endpoint = self.client.get(
            f"https://garticphone.com/api/server?code={room_id}",
            headers = self.headers
        ).text

        response = self.client.get(
            self.endpoint + f"/socket.io/?EIO=3&transport=polling&t={self.generate_random_key()}",
            headers = self.headers
        )
        self.sid = re.findall(r"sid\":\"(.*?)\"", response.text)[0]

        user_data = f"42[1,\"{str(uuid.uuid4())}\",\"{random.choice(names)}\",{randomize_icon},\"en\",false,\"{room_id}\",null,null]"
        user_data = f"{str(len(user_data))}:{user_data}"
        self.client.post(
            self.endpoint + f"/socket.io/?EIO=3&transport=polling&sid={self.sid}&t={self.generate_random_key()}",
            headers = self.headers,
            data = user_data
        )

        response = self.client.get(
            self.endpoint + f"/socket.io/?EIO=3&transport=polling&sid={self.sid}&t={self.generate_random_key()}",
            headers = self.headers
        )
        if response.text[5:] == "[1,{\"error\":4}]":
            return False
        self.id = re.findall(r"\"id\":(.*?),", response.text)[0]
        return True

    def generate_random_key(self):
        chars = string.ascii_uppercase + string.ascii_lowercase
        return "".join(secrets.choice(chars) for x in range(7))

    def ping_loop(self):
        while True:
            time.sleep(10)
            self.send_string("2")
    
    def send_string(self, string):
        self.ws.send(string)
    
    def get_string(self):
        response = self.ws.recv()
        if response:
            return response
        
    def main(self, room_id):
        result = self.send_requests(room_id)
        if not result:
            return "Max"
        self.ws = websocket.WebSocket()
        self.ws.connect(self.endpoint.replace("https", "wss") + f"/socket.io/?EIO=3&transport=websocket&sid={self.sid}")

        self.send_string("2probe")
        self.send_string("5")
        self.send_string("2")
        threading.Thread(target=self.ping_loop).start()

        while True:
            response = self.get_string()
            if response.startswith("42"):
                parsed_response = json.loads(response[2:])
                packet_id = str(parsed_response[1])
                if len(parsed_response) > 2:
                    data = parsed_response[2]
                else:
                    data = None

                if packet_id == "11":
                    if data["turnNum"] % 2 == 0:
                        self.send_string("42[2,6,{\"t\":%turn-count%,\"v\":\"%word%\"}]".replace("%turn-count%", str(data["turnNum"])).replace("%word%", random.choice(words)))
                        self.send_string("42[2,15,true]")
                    else:
                        self.send_string("42[2,7,{\"t\":%turn-count%,\"d\":1,\"v\":[1,1,[\"#000000\",6,1],[369,196]]}]".replace("%turn-count%", str(data["turnNum"])))
                        self.send_string("42[2,7,{\"t\":%turn-count%,\"d\":3,\"v\":[1,1,[\"#000000\",6,1],[369,196]]}]".replace("%turn-count%", str(data["turnNum"])))
                        self.send_string("42[2,15,true]")
                elif packet_id == "14":
                    if str(data) == self.id:
                        return "Kick"

words = []
names = []
process = False

def run(room_id):
    while True:
        client = GarticPhoneClient()
        reason = client.main(room_id)
        if reason == "Max":
            return

def start(invite_code, join_count, interval):
    global process
    if process:
        messagebox.showerror("実行エラー", "すでに実行中です")
        return
    elif invite_code == "":
        messagebox.showerror("招待コードエラー", "GarticPhoneの招待コードは必ず必要です")
        return
    elif not join_count.isnumeric():
        messagebox.showerror("参加数エラー", "参加数の値が無効です")
        return
    elif not interval.isnumeric():
        messagebox.showerror("インターバルエラー", "インターバルの値が無効です")
        return
    process = True
    thread_list = []
    for i in range(int(join_count)):
        thread = threading.Thread(target=run, args=(invite_code,))
        thread_list.append(thread)
        thread.start()
        time.sleep(int(interval))
    messagebox.showinfo("開始", "処理を開始しました")
    for thread in thread_list:
        thread.join()
    process = False
    messagebox.showinfo("完了", "すべての処理が完了しました")

def main():
    # Global
    global words
    global names

    # Init
    colorama.init(convert=True)

    # Load
    if not os.path.exists("words.txt"):
        messagebox.showerror("ロードエラー", "words.txtが見つかりませんでした")
        return
    elif not os.path.exists("names.txt"):
        messagebox.showerror("ロードエラー", "names.txtが見つかりませんでした")
        return
    with open("words.txt", "r", encoding="utf-8", errors="ignore") as words_file:
        words = words_file.read().split("\n")
    if len(words) < 1:
        messagebox.showerror("ロードエラー", "words.txtに最低1つワードを設定する必要があります")
        return
    with open("names.txt", "r", encoding="utf-8", errors="ignore") as names_file:
        names = names_file.read().split("\n")
    if len(names) < 1:
        messagebox.showerror("ロードエラー", "names.txtに最低1つ名前を設定する必要があります")
        return
    
    # Gui
    window = tkinter.Tk()

    window.geometry("500x484")
    window.configure(bg = "#505050")
    window.title("GarticPhone AFK")

    # Canvas
    canvas = tkinter.Canvas(
        window,
        bg = "#505050",
        height = 484,
        width = 500,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )
    canvas.place(x = 0, y = 0)
    canvas.create_text(
        144.0,
        29.0,
        anchor="nw",
        text="GarticPhone AFK",
        fill="#FFFFFF",
        font=("Inter", 25 * -1)
    )

    # Invite Code
    invite_code_input_image = tkinter.PhotoImage(
        file=pathlib.Path(__file__).parent / pathlib.Path("assets\\input.png")
    )
    canvas.create_image(
        305.5,
        130.0,
        image=invite_code_input_image
    )
    invite_code_input = tkinter.Entry(
        bd=0,
        bg="#303030",
        fg="#000716",
        highlightthickness=0
    )
    invite_code_input.place(
        x=156.0,
        y=108.0,
        width=299.0,
        height=42.0
    )
    canvas.create_text(
        18.0,
        119.0,
        anchor="nw",
        text="Invite Code",
        fill="#FFFFFF",
        font=("Inter", 17 * -1)
    )

    # Start Button
    start_button_image = tkinter.PhotoImage(
        file=pathlib.Path(__file__).parent / pathlib.Path("assets\\button.png")
    )
    start_button = tkinter.Button(
        image=start_button_image,
        borderwidth=0,
        highlightthickness=0,
        command=lambda: threading.Thread(target=start, args=(invite_code_input.get(), join_count_input.get(), interval_input.get(),)).start(),
        relief="flat"
    )
    start_button.place(
        x=78.0,
        y=390.0,
        width=343.0,
        height=44.0
    )

    # Join Count
    join_count_input_image = tkinter.PhotoImage(
        file=pathlib.Path(__file__).parent / pathlib.Path("assets\\input.png")
    )
    canvas.create_image(
        305.5,
        224.0,
        image=join_count_input_image
    )
    join_count_input = tkinter.Entry(
        bd=0,
        bg="#303030",
        fg="#000716",
        highlightthickness=0
    )
    join_count_input.place(
        x=156.0,
        y=202.0,
        width=299.0,
        height=42.0
    )
    canvas.create_text(
        18.0,
        213.0,
        anchor="nw",
        text="Join Count",
        fill="#FFFFFF",
        font=("Inter", 17 * -1)
    )

    # Interval
    interval_input_image = tkinter.PhotoImage(
        file=pathlib.Path(__file__).parent / pathlib.Path("assets\\input.png")
    )
    canvas.create_image(
        305.5,
        318.0,
        image=interval_input_image
    )
    interval_input = tkinter.Entry(
        bd=0,
        bg="#303030",
        fg="#000716",
        highlightthickness=0
    )
    interval_input.place(
        x=156.0,
        y=296.0,
        width=299.0,
        height=42.0
    )
    canvas.create_text(
        18.0,
        306.0,
        anchor="nw",
        text="Interval",
        fill="#FFFFFF",
        font=("Inter", 17 * -1)
    )

    # Open Window
    window.resizable(False, False)
    window.mainloop()

if __name__ == "__main__":
    main()