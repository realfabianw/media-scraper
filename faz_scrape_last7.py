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
import scraper_faz

load_dotenv()
mongodb_uri = os.getenv("MONGODB_URI")

mongoclient = pymongo.MongoClient(mongodb_uri)
mongodb = mongoclient["media-scraper"]
mongo_articles = mongodb["articles"]
mongo_execs = mongodb["executions"]

for i in reversed(range(7)):
    print("Time index:", i)
    execution = {}

    articles = scraper_faz.request_articles(
        execution,
        param_from=datetime.today()-timedelta(days=i),
        param_to=datetime.today()-timedelta(days=i)
    )

    articles_parsed = 0
    articles_inserted = 0
    for article_href in articles:
        try:
            time.sleep(random.uniform(1, 3))
            print("Scraping: ", article_href)
            article_data = scraper_faz.parse_article(article_href)
            print("Parsed: ", article_data)
            articles_parsed += 1
            try:
                mongo_articles.insert_one(article_data)
                print("Inserted instance into database.")
                articles_inserted += 1
            except Exception as ex:
                print("Unable to persist instance: ", ex)
        except:
            print("unable to scrape the article")
        
    execution["articles_parsed"] = articles_parsed
    execution["articles_inserted"] = articles_inserted
    mongo_execs.insert_one(execution)