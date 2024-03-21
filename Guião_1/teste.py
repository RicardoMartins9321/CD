from src.client import Client

if __name__ == "__main__":
    c = Client("Teste")
    c.connect()
    
    c.loop()