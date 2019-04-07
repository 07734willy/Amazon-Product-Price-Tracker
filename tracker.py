from bs4 import BeautifulSoup
import requests
import time
import threading
import sys
from win10toast import ToastNotifier
import signal

class ShopItem:
    def __init__(self, url):
        self.url = url
        self.soup  = self.get_soup()
        self.name  = self.get_name()
        self.price = self.get_price()
        self.price_val = float(self.price.replace(",", "")[1:]) if self.price else None

    def get_soup(self):
        try:
            req = requests.get(self.url)
            return BeautifulSoup(req.text, "lxml")
        except:
            time.sleep(1)
            return self.get_soup()

    def get_name(self):
        try:
            return self.soup.find("span", {"id": "productTitle"}).text.strip()
        except:
            return None

    def get_price(self):
        try:
            return self.soup.find("span", {"id": "priceblock_ourprice"}).text
        except:
            return None

    def clamp_name(self, size):
        if len(self.name) > size:
            return self.name[:size-3] + "..."
        return self.name

class PriceChecker:
    def __init__(self, url, refresh_delay=60):
        self.item = ShopItem(url)
        self.refresh_delay = refresh_delay
        self.price_check()

    def price_check(self):
        new_item = ShopItem(self.item.url)
        if not self.item.price:
            self.item = new_item
            self.thread = threading.Timer(1, self.price_check)
            self.thread.start()
            return

        # ***************************************************
        # You can change this '!=' to `==` to test the script
        # ***************************************************
        if new_item.price != self.item.price:
            self.notify_change(new_item)
            self.item = new_item
        self.thread = threading.Timer(self.refresh_delay, self.price_check)
        self.thread.start()

    def notify_change(self, new_item):
        print("Price Change\n  \"{}\"\n  {} -> {}\n  {}\n".format(new_item.name, self.item.price, new_item.price, self.item.url))
        for _ in range(3):
            try:
                ToastNotifier().show_toast("Amazon Price Change", "\"{}\"\n{} -> {}".format(self.item.clamp_name(80), self.item.price, new_item.price))
                return
            except:
                time.sleep(1)

def kill_threads(signum, frame):
    for checker in price_checkers:
        checker.thread.cancel()
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2 or not sys.argv[1]:
        print("Usage: python {} <file_of_urls>".format(sys.argv[0]))
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        price_checkers = [PriceChecker(url, 3) for url in f.read().split("\n") if url]

    signal.signal(signal.SIGINT, kill_threads)
    signal.signal(signal.SIGTERM, kill_threads)

    while price_checkers:
        time.sleep(0.1)
