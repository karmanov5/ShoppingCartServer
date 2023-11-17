from threading import Thread
import socket, time, json
from random import choice, randint
from string import ascii_letters
from product import product, productEncoder

# all_products = []
# with open('products.txt', 'r', encoding='utf-8') as f:
#      all_products =[s.strip() for s in f.readlines()]

class client:

    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def connect(self, address: str, port: int):
        try:
            self.socket.connect((address, port))
            print('client connected to server')
            Thread(target=self.__process_server).start()
        except Exception as ex:
            print(ex)
    
    
    def __process_server(self):
        send_data = dict(name='Test', personal_id=''.join([choice(ascii_letters) for _ in range(10)]))
        self.socket.send(json.dumps(send_data, ensure_ascii=False, indent=4).encode('utf-8'))
        i = 0
        while i < 5:
            try:
                # p = product(randint(0, 1000), choice(all_products), from_person='Test')
                # data = dict(command='add_product', data=p)
                # data = json.dumps(data, cls=productEncoder)
                # self.socket.send(data.encode('utf-8'))
                i += 1
                time.sleep(1)
            except Exception as ex:
                print(ex)
                self.socket.close()
                break
        self.socket.close()