
import unittest
from core.crawler import fetch_all_contents

class CrawlerServiceTest(unittest.TestCase):
    
    def test_download_content(self):
        t = fetch_all_contents(urls=["https://www.stcn.com/article/detail/3362713.html"]) 
        print(t)