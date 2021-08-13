import os, sys
from telnetlib import *
import asyncio
from multiprocessing import Process

sep = "\n------------------------\n"
red = "\033[1;31m" 
blue = "\033[1;34m"  
white = "\033[0;1m"
green = "\033[1;32m"

class Connection():
    inp = os.fdopen(os.dup(sys.stdin.fileno()))
    check = 0

    def __init__(self, host, port):
        try:
            self.connection = Telnet(host, port)
        except:
            print(f"{sep}{red}<SYSTEM> {white}Nie można nawiązać połączenia z podanym serwerem {blue}{host}:{port}{white}!")
            return
        print(f"{sep}{red}<SYSTEM> {white}Nawiązano połączenie z serwerem {blue}{host}:{port}{white}!\nWpisz {red}\"END\"{white} aby zakończyć połączenie lub {red}\"STATE\"{white} aby sprawdzić status serwera{sep}")

        wr = Process(target=self.write)
        wr.start()

        rd = Process(target=self.read, args=(wr,))
        rd.start()

        wr.join()
        rd.terminate()
        
        self.connection.close()
        
    def get_info(self):
        def key(key):
            os.system(f'echo "\n#{key}" >> tmp')

        key('CPU_INFO')
        os.system(f'cat /proc/cpuinfo >> tmp')

        key('RAM_MEMORY_INFO')
        os.system(f'cat /proc/meminfo >> tmp')

        key('PROCESSES_BY_MEMORY_USAGE')
        os.system(f'ps -eo pid,%mem --sort=-%mem | head -n 20 >> tmp')

        key('PROCESSES_BY_CPU_USAGE')
        os.system(f'ps -eo pid,%cpu --sort=-%cpu | head -n 20 >> tmp')

        with open ("tmp", "r") as tmp:
            data=tmp.read()
            tmp.close()
        self.connection.write(bytes(f"{data}\n",encoding="utf-8", errors='replace'))
        os.system(f'rm tmp')

    def read(self, wr):
        while True:
            mess = str(self.connection.read_some(), encoding="utf-8", errors='replace') 
            if mess == "":
                print(f'{red}<SYSTEM> {white}Serwer został zamknięty!')
                wr.terminate()
                return
            if "LOGIN" in mess:
                print(f"{red}<SERWER> {white}Podaj login, a następnie hasło:")
            if "GET" in mess:
                print(f"{red}<SERWER> {white}Pobieram informacje o urządzeniu!")
                self.get_info()
            if "ONLINE" in mess:
                print(f"{red}<SERWER> {white}Jesteś połączony!")
            if "<SUCCESS>" in mess:
                print(f"{red}<SERWER> {white}Logowanie zakończone powodzeniem!")
            if "<ERROR>" in mess:
                print(f"{red}<SERWER> {white}Wystąpił problem z zalogowaniem się, sprawdź dane lub spróbuj ponownie później!")
                wr.terminate()
                return

    def write(self):
        sys.stdin = self.inp
        while True:
            mess = input()
            if self.check == 0:
                self.connection.write(bytes(f"{mess}"+'\n',encoding="utf-8", errors='replace'))
                self.check += 1
            elif self.check == 1:
                self.connection.write(bytes(f"{mess}"+'\n',encoding="utf-8", errors='replace'))
                self.check += 1
            elif mess == "END":
                print(f'{red}<SYSTEM> {white}Zakończono połączenie!')
                return
            elif mess == "STATE":
                self.connection.write(bytes("STATE"+'\n',encoding="utf-8", errors='replace'))
            
            

print(f"{sep}{green}Program do połączenia się z serwerem{white}")
while True:
    mode = input(f"{sep.strip()}\n{blue}Tryb pracy: \n{red}1) {white}Ustawienia domyślne \n{red}2) {white}Ustawienia własne \n{red}3) {white}Wyjdź z programu{sep}")
    if mode == '1':
        host="localhost"
        port=1234
        break
    elif mode == '2':
        host=input(f"{sep}{white}Podaj host\'a: {blue}")
        port=int(input(f"{white}Podaj port: {blue}"))
        break
    elif mode == '3':
        print(f"{sep}{red}Program został zamknięty!{white}{sep}")
        sys.exit(0)
    else:
        print(f"{sep}{red}Podano błędny tryb pracy!{white}")
    
conn=Connection(host, port)






    
