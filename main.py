from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import Engine
from bs4 import BeautifulSoup
from typing import Optional
import requests
import math
import time
import re

from model import *
from config import *

class Scraper:
    LANG_SETTINGS = {
        "de": {
            "time_regex": r"((\d+)T )?((\d+)Std ?)?((\d+) Min)?",
            "free_text": "Kostenlos"
        },
        "pl": {
            "time_regex": r"((\d+)d )?((\d+)h )?((\d+)m)?",
            "free_text": "Bezpłatna"
        }
    }

    def __init__(self, engine: Engine, webhook_url: str, polling_interval: int, lang_code: str = "de"):
        self.interval = polling_interval
        self.engine = engine
        self.webhook_url = webhook_url

        if lang_code not in self.LANG_SETTINGS:
            raise ValueError(f"Language {lang_code} not supported")

        self.lang = self.LANG_SETTINGS[lang_code]

    def run(self):
        while True:
            with Session(self.engine) as session:
                stmt = select(WatchedTerm)
                for term in session.scalars(stmt):
                    url = self.make_scrap_url(term.url, term.max_price)
                    self.scrap(url, term.max_price, term.max_likes)
            
            time.sleep(self.interval)

    def scrap(self, url, max_price, max_likes):
        contents = self.get_site_contents(url)
        if contents is None:
            print("scrap failed")
            return

        bs = BeautifulSoup(contents, "html.parser")

        items = bs.find_all("div", class_="s-item__info clearfix")
        for item in items:
            link_elem = item.find("a", class_="s-item__link")
            link = link_elem["href"]
            title = link_elem.find("h3", class_="s-item__title").text.strip()

            price = self.handle_price(item.find("span", class_="s-item__price").text.strip())

            # get shipping price
            ship_elem = item.find("span", class_="s-item__shipping s-item__logisticsCost")
            ship_cost = 0.0

            if ship_elem is not None:
                ship_cost = self.handle_price(ship_elem.text.strip())

            try:
                bids = int(item.find("span", class_="s-item__bids s-item__bidCount").text.split()[0])
            except:
                bids = 1000

            # parse remaining time
            tmp = item.find("span", class_="s-item__time-left").text
            m = re.search(self.lang["time_regex"], tmp)
            if m is None:
                print("failed to match remaining time:", tmp)
                continue

            days, hours, mins = m.group(2) or 0, m.group(4) or 0, m.group(6) or 0

            total_price = round(price + ship_cost, 2)

            if total_price <= max_price and bids < 2 and hours == 0 and days == 0:
                self.notify(title, f"""
                Total price: EUR {total_price}
                Time left: {hours} hours {mins} mins
                Link: {link}
                """)
                print(title, link, price, ship_cost, days, hours, mins)
                print()

    def notify(self, title: str, description: str):
        url = self.webhook_url
        data = {
            "content" : "",
            "username" : "Ebay"
        }

        data["embeds"] = [{
            "title": title,
            "description": description
        }]

        result = requests.post(url, json = data)

        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        else:
            print("Payload delivered successfully, code {}.".format(result.status_code))

    @staticmethod
    def get_site_contents(url: str) -> bytes:
        r = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/123.0.2420.97"
        })
        if not r.ok:
            print(r.status_code)
            return None
        return r.content

    def handle_price(self, price: str) -> Optional[float]:
        if self.lang["free_text"] in price:
            return 0.0

        m = re.search(r"[^\d]*(\d+,\d+)[^\d]*", price)
        if not m:
            return None
        return round(float(m.group(1).replace(",", ".")), 2)

    @staticmethod
    def make_scrap_url(url, max_price: int, page: int = 1) -> str:
        return url + f"?LH_Auction=1&rt=nc&_udhi={math.ceil(max_price)}&mag=1&_pgn={page}"
        

def main():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    scraper = Scraper(engine, WEBHOOK_URL, SCRAP_INTERVAL)

    scraper.run()

if __name__ == "__main__":
    main()

