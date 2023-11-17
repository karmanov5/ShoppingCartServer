from threading import Thread
import socket, time
from product import product, productEncoder
from person import person, personEncoder
from datetime import datetime
import os, json, firebase_admin
from firebase_admin import messaging
from firebase_admin._messaging_utils import Notification




class server:

    __products = []
    __clients = []
    __categories = []

   

    def __init__(self, port: int) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = socket.gethostbyname(socket.gethostname())
        self.port = port
        self.socket.bind((self.address, self.port))
        self.__working = True
        cred = firebase_admin.credentials.Certificate('adminsdk.json')
        self.fb_app = firebase_admin.initialize_app(credential=cred)
        self.__load_clients()
        self.__load_products()
        self.__load_categories()
        


    def start(self):
        t = Thread(target=self.__process_server, args=())
        t.start()
        self.__working = True


    def __process_server(self):
        self.socket.listen()
        print(datetime.now(), "server start on", self.address, ":", self.port)
        while self.__working:
            cl, _ = self.socket.accept()
            Thread(target=self.__test_client, args=(cl,)).start()   
            

    def __test_client(self, client: socket.socket):
        try:
            
            data = client.recv(1024)
            if not data:
                raise Exception('client not responding!')
            json_data = json.loads(data.decode('utf-8'))
            
            if 'name' not in json_data and 'personal_id' not in json_data:
                raise Exception('wrong answer from client!')
            else:
                name = json_data['name']
                personal_id = json_data['personal_id']
                token = json_data['token']

                message = messaging.Message()
                send_data = dict(event="get_products")
                send_data['data'] = self.__products
                send_data['categories'] = self.__categories
                message.data = dict(data=json.dumps(send_data, ensure_ascii=True, indent=4, cls=productEncoder))
                message.token = token
                messaging.send(message=message, app=self.fb_app)
                
                for cl in self.__clients:
                    if cl.name == name and cl.personal_id == personal_id:
                        try:
                            cl.socket.close()
                        except:
                            pass
                        cl.socket = client
                        cl.token = token
                        print(datetime.now(), "reconnect client:", cl.socket.getpeername(), "name:", name, 'personal_id:', personal_id)
                        self.__process_client(cl)
                        break
                else:
                    p = person(name, client, personal_id, token)
                    self.__clients.append(p)
                    self.__save_clients()
                    print(datetime.now(), "new client:", client.getpeername(), 'name:', name, 'personal_id:', personal_id)
                    self.__process_client(p)
                
                

        except Exception as ex:
            print(ex)
            print(datetime.now(), 'disconnect client', client.getpeername())
            client.close()





    def __process_client(self, person: person):
        try:
            while True:
                
                data = person.socket.recv(1024)
                if not data:
                    break
                self.__process_json_data(data.decode('utf-8'), person)

            
            raise Exception('client not responding!')
        except Exception as ex:
            print(ex)
            print("socket close!")



    def __process_json_data(self, data: str, person: person):
        json_data = json.loads(data)
        print(datetime.now(), json_data, 'from', person.name)
        command = json_data["command"]
        send_data = dict(event=command)
        message = messaging.Message()
        
        if command == "get_products":
            send_data['data'] = self.__products
            send_data['categories'] = self.__categories
            message.data = dict(data=json.dumps(send_data, ensure_ascii=True, indent=4, cls=productEncoder))
            message.token = person.token
            messaging.send(message=message, app=self.fb_app)
            return
        elif command == "add_product":
            _product = json_data['data']
            p = product(id=_product['Id'], name=_product['Name'], price=_product['Price'], count=_product['Count'], isWeight=_product['IsWeight'], completed=_product['Completed'], from_person=_product['From_Person'], category=_product['Category'])
            if p.Category not in self.__categories:
                self.__categories.append(p.Category)
                self.__save_categories()
            self.__products.append(p)
            message.notification = Notification(f"Добавление продукта в список {p.Category}!", f"Добавлен продукт {p.Name}, стоимость {p.Price * p.Count} руб")
            self.__save_products()
            print(self.__products)
            send_data['data'] = _product
        elif command == "add_category":
            _category = json_data['data']
            if _category not in self.__categories:
                self.__categories.append(_category)
                self.__save_categories()
            message.notification = Notification("Добавлена новая категория продуктов!", f"Добавлена категория {_category}")
            send_data['data'] = _category
        elif command == "remove_product":
            _product = json_data['data']
            p = [_p for _p in self.__products if _p.Id == _product['Id'] and _p.Name == _product['Name']][0]
            self.__products.remove(p)
            self.__save_products()
            message.notification = Notification(f"Удален товар из {_product['Category']}!", f"Убран товар {_product['Name']}")
            send_data['data'] = _product
        elif command == 'remove_products':
            _products = json_data['data']
            products = [_p for _p in self.__products for __p in _products if _p.Id == __p['Id'] and _p.Name == __p['Name']]
            for p in products:
                self.__products.remove(p)
            self.__save_products()
            send_data['data'] = _products
        elif command == 'change_product':
            _product = json_data['data']
            oldName = ''
            for p in self.__products:
                if p.Id == _product['Id']:
                    oldName = p.Name
                    p.Name = _product['Name']
                    p.set_price(_product['Price'])
                    p.set_count(_product['Count'])
                    p.IsWeight = _product['IsWeight']
                    break
            self.__save_products()
            message.notification = Notification(f"Изменен товар в {_product['Category']}!", f"Проверьте список, в нем поменялся {oldName}")
            send_data['data'] = _product
        
        elif command == 'complete_product':
            _product = json_data['data']
            for p in self.__products:
                if p.Name == _product['Name'] and p.Id == _product['Id']:
                    send_data['category'] = p.Category
                    p.set_complete(True)
                    _product['Completed'] = True
                    _product['Category'] = p.Category = 'Завершенные'
                    break
            send_data['data'] = _product
            message.notification = Notification("Покупка товара", f"Товар {_product['Name']} куплен")
            self.__save_products()
            
        elif command == 'change_user':
            __user = json_data['data']
            for p in self.__clients:
                if p.personal_id == __user['personal_id']:
                    p.name = __user['userName']
                    break
            send_data['data'] = __user
        

        message.data = dict(data=json.dumps(send_data, ensure_ascii=True, indent=4, cls=productEncoder)) 
        for p in self.__clients:
            message.token = p.token
            messaging.send(message=message, app=self.fb_app)
            



    def __save_clients(self):
        with open('clients.json', 'w', encoding='utf-8') as file:
            json.dump(self.__clients, file, cls=personEncoder, indent=4)

    def __save_products(self):
        with open('products.json', 'w', encoding='utf-8') as file:
            json.dump(self.__products, file, cls=productEncoder, indent=4)


    def __load_clients(self):
        self.__clients = []
        if os.path.exists("clients.json"):
            with open("clients.json", 'r', encoding='utf-8') as file:
                self.__clients = json.load(file, object_hook=lambda obj: person(name=obj['name'], socket=None, personal_id=obj['personal_id'], token=obj['token']))

    def __load_products(self):
        self.__products = []
        if os.path.exists('products.json'):
            with open("products.json", 'r', encoding='utf-8') as file:
                self.__products = json.load(file, object_hook=lambda obj: product(id=obj['Id'],
                                                                                    name=obj['Name'],
                                                                                    price=obj['Price'],
                                                                                    count=obj['Count'],
                                                                                    isWeight=obj['IsWeight'],
                                                                                    completed=obj['Completed'],
                                                                                    from_person=obj['From_Person'],
                                                                                    category=obj['Category']))

    def __load_categories(self):
        self.__categories = ['Стандартные', 'Завершенные']
        if os.path.exists("categories.json"):
            with open("categories.json", 'r', encoding='utf-8') as file:
                self.__categories = json.load(file)
                self.__categories.append('Завершенные')

    def __save_categories(self):
        with open('categories.json', 'w', encoding='utf-8') as file:
            json.dump(self.__categories, file, indent=4)

            
