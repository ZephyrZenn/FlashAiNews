import datetime
import time

import feedparser

from parsers import parse_opml, parse_html_content

from services import import_opml_config

import_opml_config("feed.opml")

# urls =  parse_and_get_url('feed.opml')
# url = random.choice(list(urls.values()))
# print("Query:", url[0])
# print(get_content(url=url[0]))
