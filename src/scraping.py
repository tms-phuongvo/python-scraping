import threading
import time
import os
import logging
import pandas as pd
import urllib.parse
from typing import List

from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapegraphai.graphs import SmartScraperGraph
from bs4 import BeautifulSoup, Tag
from itertools import islice 

from src.graph_config import get_graph_config
from src.process_csv import save_csv
from src.prompt import prompt

class Scraping:

    graph_config = get_graph_config('gpt-3.5-turbo', os.getenv('OPEN_API_KEY'))

    def __init__(self, url: str, query: dict[str: str], num_page: int):
        self.url = url
        self.query = query
        self.num_page = num_page
        self.driver = webdriver.Chrome()
        self.chunk_size = 5
        self.detail_data = []
        self.lock = threading.Lock()

    # Public
    def run(self):
        url = f"{self.url}/main/action.php?{ urllib.parse.urlencode(self.query) }"
        data = self.__scraping_home_page(url, self.num_page)
        save_csv('article', pd.DataFrame(data))
        self.__scraping_detail(pd.DataFrame(data)["link_url"].to_list())

    # Private
    def __scraping_home_page(self, url: str, num_page: int = 5):
        logging.info(f"BEGIN SCRAPING HOME {url}")
        self.driver.get(url)

        data = []
        page_count = 1

        time.sleep(2)

        while page_count < num_page:
            try:
                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.css-1rd8oy0"))
                )
                self.driver.execute_script("arguments[0].click();", load_more_button)
                page_count += 1
                time.sleep(2)
            except:
                logging.error(f'No more "Load More" button found or reached the end of the page.')

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        articles: List[Tag]  = soup.find_all("article", class_="css-i15bus")

        for article in articles:
            link_url = article.find("a", class_="css-1r0dtqf").attrs["href"].strip()
            if link_url is not None and link_url != '':
                link_url = self.url + article.find("a", class_="css-1r0dtqf").attrs["href"].strip()
            
            data.append({
                "link_url": link_url,
            })

        self.driver.quit()

        logging.info(f"END SCRAPING HOME {url}")
        return data
    
    def __scraping_detail(self, data: List):
        with ThreadPoolExecutor(max_workers=10) as executor:
            chunk_pages = self.__chunk(data, self.chunk_size)
            futures = []
            for chunk_page in chunk_pages:
                future = executor.submit(self.__scraping_worker, chunk_page)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"An error occurred: {str(e)}")
            
            save_csv("company_detail", pd.DataFrame(self.detail_data))

    def __scraping_worker(self, data: List):
        for article_link in data:
            logging.info(f"BEGIN SCRAPING {article_link}")
            try:
                smart_scraper_graph = SmartScraperGraph(
                    prompt=prompt,
                    source=article_link,
                    config=self.graph_config,
                )
                result = smart_scraper_graph.run()
                with self.lock:
                    self.detail_data.append(result)
                logging.info(f"END SCRAPING {article_link}")
            except Exception as e:
                logging.error(f"Error scraping {article_link}: {str(e)}")
    
    def __chunk(self, arr_range: List, arr_size: int): 
        arr_range = iter(arr_range) 
        return iter(lambda: tuple(islice(arr_range, arr_size)), ()) 


    
    
    