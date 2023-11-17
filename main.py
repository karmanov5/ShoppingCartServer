from server import server
from client import client
from time import sleep

def main():
    s = server(4667)
    s.start()
    # c = client()
    # c.connect("192.168.1.51", 4667)
    

if __name__ == "__main__":
    main()