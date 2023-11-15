from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from dateutil import parser
import time
import random
import pymongo
from dotenv import load_dotenv
import os

def request_articles(execution, param_from = datetime.today() - timedelta(days=1), param_to = datetime.today() - timedelta(days=1), url = "https://www.faz.net/suche/?query=&ct=article&ct=blog&ct=storytelling&author=&from=&to="):
    now = datetime.now()
    url = re.sub("from=.*&", "from=" + (param_from - timedelta(days=1)).strftime("%d.%m.%Y") + "&", url)
    url = re.sub("to=.*", "to=" + (param_to - timedelta(days=1)).strftime("%d.%m.%Y"), url)
    print("Requesting: ", url)

    page = urlopen(url)
    soup = BeautifulSoup(page, "html.parser")

    links = soup.find_all("a")

    try:
        page = int(re.search("/s(\d).html", url).groups()[0])
    except:
        page = 1

    links_articles = [link.get("href") for link in links if link.get("href") and re.match("https://.*/suche/.{6,}html", link.get("href"))]

    print("Articles count: ", len(links_articles))

    regex = "https://.*/suche/s" + str(page + 1) + ".html.*"

    links_pages = [link for link in links if link.get("href") and re.match(regex, link.get("href"))]
    
    if len(links_pages) > 0:
        print("Found a next page. Requesting: ", links_pages[0].get("href"))
        time.sleep(random.uniform(2, 5))
        links_articles.extend(request_articles(execution, param_from=param_from, param_to=param_to, url=links_pages[0].get("href")))

    execution["ts"] = now
    execution["source"] = "https://www.faz.net"
    execution["from"] = param_from
    execution["to"] = param_to
    execution["articles_count"] = len(links_articles)

    return links_articles

def parse_article_author(dict, soup):
    try:
        dict["author"] = soup.find("a", attrs="atc-MetaAuthorLink").contents[1]
        dict["hrefAuthor"] = "https://www.faz.net" + soup.find("a", attrs="atc-MetaAuthorLink").get("href")
    except:
        try:
            dict["author"] = soup.find("span", attrs="atc-MetaAuthor").contents[1]
        except:
            try:
                dict["source"] = soup.find("span", attrs="atc-Footer_Quelle").text
            except:
                print("unable to find an author")

def parse_article_premium(dict, soup):
    try:
        dict["premiumArticle"] = True if soup.find("span", attrs="ico-Base atc-HeadlineIcon").find("span", attrs="o-Icon ico-Base_FazPlus") else False
    except: 
        dict["premiumArticle"] = False

def parse_article_keywords(dict, soup):
    try:
        keywords = set()
        [keywords.add(keyword.strip()) for keyword in soup.find("meta", {"name": "keywords"}).get("content").split(",")]
        [keywords.add(keyword.strip()) for keyword in soup.find("meta", {"name": "news_keywords"}).get("content").split(",")]
        dict["keywords"] = list(keywords)
    except:
        print("unable to parse keywords")


def parse_article(url):
    page = urlopen(url)
    soup = BeautifulSoup(page, "html.parser")

    multipage = soup.find("div", attrs="atc-ContainerFunctions_Navigation").find("a", attrs="btn-Base_Link")

    if multipage:
        print("multiplage article found. Requesting: ", multipage.get("href"))
        time.sleep(random.uniform(0.5, 2))
        page = urlopen(multipage.get("href"))
        soup = BeautifulSoup(page, "html.parser")

    article = {}

    article["_id"] = soup.find("span", attrs="js-sharing-link-select-trigger js-sharing-link lay-Sharing_PermalinkUrl").text.split("/")[3].split("?")[0]
    parse_article_keywords(article, soup)
    parse_article_premium(article, soup)
    article["hrefPermalink"] = soup.find("span", attrs="js-sharing-link-select-trigger js-sharing-link lay-Sharing_PermalinkUrl").text
    article["lastUpdate"] = parser.parse(soup.find("time", attrs="atc-MetaTime").get("datetime"))
    article["title"] = soup.title.string
    article["introText"] = soup.find("p", attrs="atc-IntroText").string.strip()
    article["paragraphs"] = [paragraph.text for paragraph in soup.find_all("p", attrs="atc-TextParagraph")]
    parse_article_author(article, soup)

    return article    