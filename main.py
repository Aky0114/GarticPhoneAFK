import re
import os
import json
import time
import uuid
import httpx
import random
import string
import secrets
import colorama
import websocket
import threading

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
        self.id = str(json.loads(response.text[6:])[1]["user"]["id"])

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
        self.send_requests(room_id)
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
                        print(colorama.Fore.RED + f"[{threading.current_thread().name}] Kickされました" + colorama.Fore.RESET)
                        return

welcome_ascii = """

░██████╗░░█████╗░██████╗░████████╗██╗░█████╗░  ██████╗░██╗░░██╗░█████╗░███╗░░██╗███████╗
██╔════╝░██╔══██╗██╔══██╗╚══██╔══╝██║██╔══██╗  ██╔══██╗██║░░██║██╔══██╗████╗░██║██╔════╝
██║░░██╗░███████║██████╔╝░░░██║░░░██║██║░░╚═╝  ██████╔╝███████║██║░░██║██╔██╗██║█████╗░░
██║░░╚██╗██╔══██║██╔══██╗░░░██║░░░██║██║░░██╗  ██╔═══╝░██╔══██║██║░░██║██║╚████║██╔══╝░░
╚██████╔╝██║░░██║██║░░██║░░░██║░░░██║╚█████╔╝  ██║░░░░░██║░░██║╚█████╔╝██║░╚███║███████╗
░╚═════╝░╚═╝░░╚═╝╚═╝░░╚═╝░░░╚═╝░░░╚═╝░╚════╝░  ╚═╝░░░░░╚═╝░░╚═╝░╚════╝░╚═╝░░╚══╝╚══════╝

"""

words = []
names = []

def title_loop():
    while True:
        thread_count = str(len(threading.enumerate()))
        os.system(f"title GarticPhoneAFK / Threads: {thread_count}")

def run(room_id):
    client = GarticPhoneClient()
    client.main(room_id)

def main():
    global words
    global names
    colorama.init(convert=True)
    threading.Thread(target=title_loop).start()
    print(colorama.Fore.BLUE + welcome_ascii + colorama.Fore.RESET)
    print(colorama.Fore.BLUE + "GARTIC PHONE ARASHI BOT v1.0.0" + colorama.Fore.RESET)
    print("\n")
    time.sleep(1)
    if not os.path.exists("words.txt"):
        print(colorama.Fore.RED + "words.txtが見つかりませんでした" + colorama.Fore.RESET)
        return
    elif not os.path.exists("names.txt"):
        print(colorama.Fore.RED + "names.txtが見つかりませんでした" + colorama.Fore.RESET)
        return
    with open("words.txt", "r", encoding="utf-8", errors="ignore") as words_file:
        words = words_file.read().split("\n")
    if len(words) < 1:
        print(colorama.Fore.RED + "最低1つワードを設定する必要があります" + colorama.Fore.RESET)
        return
    with open("names.txt", "r", encoding="utf-8", errors="ignore") as names_file:
        names = names_file.read().split("\n")
    if len(names) < 1:
        print(colorama.Fore.RED + "最低1つ名前を設定する必要があります" + colorama.Fore.RESET)
        return
    gartic_phone_code = input(colorama.Fore.LIGHTMAGENTA_EX + "Gartic Phone Code > " + colorama.Fore.RESET).replace("https://garticphone.com/ja/?c=", "")
    threads = input(colorama.Fore.LIGHTYELLOW_EX + "参加数(Default: 5) > " + colorama.Fore.RESET)
    interval = input(colorama.Fore.LIGHTRED_EX + "インターバル(Default: 0) > ")
    if gartic_phone_code == None:
        print(colorama.Fore.RED + "無効なコードです" + colorama.Fore.RESET)
        return
    elif threads == "":
        threads = "5"
    elif interval == "":
        interval = "0"
    if not threads.isnumeric():
        print(colorama.Fore.RED + "無効な参加数です" + colorama.Fore.RESET)
        return
    elif not interval.isnumeric():
        print(colorama.Fore.RED + "無効なインターバルです" + colorama.Fore.RESET)
        return
    thread_list = []
    for i in range(int(threads)):
        thread = threading.Thread(target=run, args=(gartic_phone_code,))
        thread_list.append(thread)
        thread.start()
        time.sleep(int(interval))
    for thread in thread_list:
        thread.join()
    print(colorama.Fore.GREEN + "すべての処理が完了しました" + colorama.Fore.RESET)

if __name__ == "__main__":
    main()