
import json
import os
from random import choice
from typing import NamedTuple, Dict, Any, Set
import time
import telepot
import logging
import requests
from bs4 import BeautifulSoup
from config import TOKEN, desktop_agents_, list_time_work

py_logger = logging.getLogger("game_news")
py_logger.setLevel(logging.INFO)
py_handler = logging.FileHandler(f"{__name__}.log", mode='w')
py_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
py_handler.setFormatter(py_formatter)
py_logger.addHandler(py_handler)

CWD = os.getcwd()
RESULTS_DIR = os.path.join(CWD, 'data')

list_time = list_time_work
desktop_agents = desktop_agents_
bot = telepot.Bot(TOKEN)

def random_headers():
    return {'User-Agent': choice(desktop_agents),'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}


class ArticleInfo(NamedTuple):
    title: str
    text: str

    def to_dict(self) -> Dict[str, Any]:
        dct = self._asdict()
        return dct

class ParsingError(Exception):
    def __init__(self, message: str, exception: Exception) -> None:
        self.exception = exception
        self.message = message

class RequestError(Exception):
    def __init__(self, message: str, exception: Exception) -> None:
        self.exception = exception
        self.message = message

def parse_link_for_get_links(url: str, links: set, datetimeNow: str)->Set :
    html_ = requests.get(url,headers=random_headers()).content
    soup = BeautifulSoup(html_, 'html.parser')
    py_logger.info(url)
    timeout_ = choice(list_time)
    py_logger.info(timeout_)
    time.sleep(timeout_)
    for link in soup.find_all('div', class_ = "_card_11mk8_1"):
        l = link.find('a').get('href')
        publication_dt = link.find('span').text
        py_logger.info("["+publication_dt[:4]+"]"+" "+"["+datetimeNow[:4]+"]")
        if publication_dt[:4] == datetimeNow[:4]:
            py_logger.info(f"links:{len(links)}")
            if l != None and l.startswith('/newsdata/'):
                img = requests.get(link.find('img')['src'])
                with open(f'image{l[10:15]}.jpg', 'wb') as file:
                    file.write(img.content)
                links.add('https://stopgame.ru' + l)
    return links
def get_all_articles__stop_game(datetimeNow: str) -> Set[str]:
    links = set()
    i = 1
    while (len(links) < 1) and (i < 10):
        url = f'https://stopgame.ru/news/all/p{i}'
        i = i + 1
        links = parse_link_for_get_links(url, links, datetimeNow)
    url = f'https://stopgame.ru/news/all/p{i}'
    links = parse_link_for_get_links(url, links, datetimeNow)
    return links

def parse_article__stop_game(url: str) -> ArticleInfo:
    try:
        response = requests.get(url, headers=random_headers())
        response.raise_for_status()
        html = response.content.decode('utf-8')
    except Exception as e:
        raise RequestError('wrong request', e)

    try:
        text_c = ""
        soup = BeautifulSoup(html, 'html.parser')
        title_pub = soup.find('h1').text
        for content in soup.find("div", class_="_content_1gk4z_10").find_all("p",
                                                                             class_="_text_1gk4z_108 _text-width_1gk4z_108"):
            text_c += " " + content.text
        content_count = 250
        if(len(text_c) > 250):
            content_count = 200
            while (text_c[content_count] != '.') and (content_count < 350):
                content_count += 1
            if content_count > 348:
                content_count = 200
                while (text_c[content_count] != '.') and (content_count > 120):
                    content_count -= 1
        return ArticleInfo(
            title=title_pub,
            text=f'{text_c[:content_count]}. '
        )
    except Exception as e:
        raise ParsingError('wrong content of page', e)


def handle(msg) -> None:
    chat_id = msg['chat']['id']
    message_text = msg["text"]
    py_logger.info("start game news")
    py_logger.info("getting links")

    datetimeNow = message_text
    links = get_all_articles__stop_game(datetimeNow)
    for link in links:
        try:
            time.sleep(choice(list_time))
            py_logger.info(" parsing start " + link)
            info = parse_article__stop_game(link)
            py_logger.info(" saving file")
            caption = f'<b>{info.title}</b> \n {info.text} [<a href="'+ link + '">. . .</a>]'
            py_logger.info("send")
            bot.sendPhoto(chat_id = -1002122792459, photo=open(f'image{link[29:34]}.jpg', 'rb'), caption=caption, parse_mode='HTML')
            py_logger.info(f'Photo: {link[29:34]}')
            os.remove(f'image{link[29:34]}.jpg')
            py_logger.info(" parsing link final")
        except:
            py_logger.warning(" stop parsing")
    bot.sendMessage(chat_id, text='final')
    py_logger.info("final")
bot.message_loop({'chat': handle})

while True:
    n = input('To stop enter "stop":')
    if n.strip() == 'stop':
        break