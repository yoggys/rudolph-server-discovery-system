import os, sys
import socketserver, socket
import asyncio
import sqlite3
from datetime import datetime
from multiprocessing import Process

red = "\033[1;31m" 
blue = "\033[1;34m"  
white = "\033[0;1m"
green = "\033[1;32m"
sep = "\n------------------------\n"
connected = []

class Server(socketserver.StreamRequestHandler):
    last = datetime.now()
    inp = os.fdopen(os.dup(sys.stdin.fileno()))
    state = True
    login = ''
    passw = ''
    info = ''

    def check(self):
        db_name = 'server.sqlite'
        try:
            db = sqlite3.connect(db_name)
            cursor = db.cursor()
            cursor.execute(f"SELECT * FROM users WHERE username = '{self.login}'")
            result = cursor.fetchone()
            if result is not None:
                cursor.execute(f"SELECT * FROM users WHERE username = '{self.login}' AND password = '{self.passw}'")
                result = cursor.fetchone()
                if result is not None:
                    self.info = f"{red}<SUCCESS> {white}Witamy ponownie {blue}{self.login}{white}!"
                    return 0
                else:
                    self.info = f"{red}<ERROR> {white}Podano błędne dane logowania dla {blue}{self.login}{white}!"
                    return 2
            else:
                self.info = f"{red}<ERROR> {white}Brak zarejestrowanego użytkownika o podanej nazwie {blue}{self.login}{white}!"
                return 1
        except Exception as e:
            print(e)
            self.info = f"{red}<ERROR> {white}Problem z połączeniem do bazy danych {blue}{db_name}{white}"
            return 3

    def handle(self):
        print(f"{sep}{red}<SYSTEM>{blue} {self.client_address[0]}:{self.client_address[1]}{white} dołączył do serwera!{sep}")

        connected.append(f'{self.client_address[0]}:{self.client_address[1]}')
        
        self.login_write()
        self.login_read()
        
        val = self.check()

        print(f'{sep}{self.info}{sep}')
        self.request.sendall(bytes(f"{self.info}\n", encoding="utf-8", errors='replace'))
        if val == 0 and len(self.login) >= 4 and len(self.passw) >= 4:
            wr = Process(target=self.write)
            wr.start()

            loop = Process(target=self.get_info_task)
            loop.start()

            rd = Process(target=self.read, args=(wr,))
            rd.start()

            wr.join()
            rd.terminate()
            loop.terminate()
        if val != 0:
            print(f"{sep}{red}<SYSTEM>{blue} {self.client_address[0]}:{self.client_address[1]} {white}odłączył się od serwera!{sep}")
        connected.remove(f'{self.client_address[0]}:{self.client_address[1]}')
        self.connection.close()

    def login_read(self):
        while True:
            mess = str(self.request.recv(10000).strip(),encoding="utf-8", errors='replace')
            if mess == "":
                self.state = False
                break
            if self.state:
                print(mess)
                self.login = mess
                self.state = False
            else:
                print(mess)
                self.passw = mess
                self.state = True
                break

    def login_write(self):
        print(f"{red}<CLIENT> {white}Wysyłam prośbę o zalogowanie do {blue}{self.client_address[0]}:{self.client_address[1]}{white}!")
        self.request.sendall(bytes("LOGIN\n",encoding="utf-8", errors='replace'))

    def read(self, wr):
        while True:
            mess = str(self.request.recv(10000).strip(),encoding="utf-8", errors='replace')
            if mess == "":
                print(f"{sep}{red}<SYSTEM>{blue} {self.client_address[0]}:{self.client_address[1]} {white}odłączył się od serwera!{sep}")
                wr.terminate()
                break
            elif "#CPU_INFO" in mess:
                with open(f'./logs/{self.client_address[0]}:{self.client_address[1]}', 'w') as file:
                    file.writelines(f"#MAC_ADDRESS_AND_PORT\n{self.client_address[0]}:{self.client_address[1]}\n\n")
                    file.write(mess)
                    file.close()
            elif "STATE" in mess:
                sys.stdin = self.inp
                print(f"{red}<CLIENT> {white}Wysyłam odpowiedź na zapytanie {red}\"STATE\"{white} do {blue}{self.client_address[0]}:{self.client_address[1]}{white}!")
                self.request.sendall(bytes("ONLINE\n",encoding="utf-8", errors='replace'))
            
    def write(self):
        sys.stdin = self.inp
        while True:
            mess = input()
            if mess == "END":
                print(f'{red}<SYSTEM> {white}zamknięto server!')
                break
                

    def get_info_task(self):
        while True:
            if int((datetime.now()-self.last).seconds) >= 15:
                print(f"{red}<SYSTEM> {white}Pobieram informacje od {blue}{self.client_address[0]}:{self.client_address[1]}{white}!\n")
                self.request.sendall(bytes("GET\n",encoding="utf-8", errors='replace'))
                self.last = datetime.now()

def unregister():
    print(f'{white}{sep}Wpisz nazwe użytkownika któremu chcesz zabrać dostęp (wpisz {red}\"EXIT\"{white} aby anulować){sep}')
    db = sqlite3.connect('server.sqlite')
    cursor = db.cursor()
    while True:
        login=input(f"{sep}{white}Podaj login: {blue}")
        if login == "EXIT":
            print(f'{white}')
            break
        cursor.execute(f"SELECT * FROM users WHERE username = '{login}'")
        result = cursor.fetchone()
        if result is None:
            print(f"{white}{sep}{red}Taka nazwa nie jest zarejestrowana!{white}")
            continue

        cursor.execute(f"DELETE FROM users WHERE username = '{login}'")
        db.commit()
        print(f'{white}')
        print(f"{sep}{green}Pomyślnie zabrano dostęp użytkownikowi {blue}{login}{white}")
        break
def register():
    print(f'{white}{sep}Pamiętaj, że login i hasło muszą zawierać minimum 4 znaki! (wpisz {red}\"EXIT\"{white} aby anulować){sep}')
    db = sqlite3.connect('server.sqlite')
    cursor = db.cursor()
    while True:
        login=input(f"{sep}{white}Podaj login: {blue}")
        if login == "EXIT":
            print(f'{white}')
            break
        cursor.execute(f"SELECT * FROM users WHERE username = '{login}'")
        result = cursor.fetchone()
        if result is not None:
            print(f"{white}{sep}{red}Taka nazwa jest już zarejestrowana!{white}")
            continue
        if len(login.split()[0]) < len(login) or len(login) < 4:
            print(f"{white}{sep}{red}Login nie spełnia wymogów!{white}")
            continue

        passw=input(f"{white}Podaj hasło: {blue}")
        if passw == "EXIT":
            print(f'{white}')
            break
        if len(passw.split()[0]) < len(passw) or len(passw) < 4:
            print(f"{white}{sep}{red}Hasło nie spełnia wymogów!{white}")
            continue
        
        sql = ("INSERT INTO users(username, password) VALUES(?,?)")
        val = (login, passw)
        cursor.execute(sql, val)
        db.commit()
        print(f'{white}')
        print(f"{sep}{green}Pomyślnie zarejestrowano użytkownika {blue}{login}{green} z hasłem {blue}{passw}{white}")
        break

print(f"{sep}{green}Program do włączenia serwera{white}")
while True:
    mode = input(f"{sep.strip()}\n{blue}Tryb pracy: \n{red}1) {white}Ustawienia domyślne \n{red}2) {white}Ustawienia własne \n{red}3) {white}Udziel dostępu do serwera \n{red}4) {white}Zabierz dostęp do serwera \n{red}5) {white}Wyjdź z programu{sep}")
    if mode == '1':
        host="localhost"
        port=1234
        break
    elif mode == '2':
        host=input(f"{sep}{white}Podaj host\'a: {blue}")
        port=int(input(f"{white}Podaj port: {blue}"))
        break
    elif mode == '3':
        register()
    elif mode == '4':
        unregister()
    elif mode == '5':
        print(f"{sep}{red}Program został zamknięty!{white}{sep}")
        sys.exit(0)
    else:
        print(f"{sep}{red}Podano błędny tryb pracy!{white}")

val = False
try:
    
    server = socketserver.TCPServer((host, port), Server)
    
    print(f"{white}{sep}{red}<SYSTEM>{white} Serwer został utworzony: {blue}{host}:{port}{white}!{sep}")
    val = True
    server.serve_forever()
except:
    if not val:
        print(f"{red}<SYSTEM>{white} Nie można utworzyć serwera: {blue}{host}:{port}{white}!\n")
    else:
        print(f"{red}<SYSTEM>{white} Serwer został zamknięty: {blue}{host}:{port}{white}!\n")
