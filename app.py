import logging
from src.scraping import Scraping
from dotenv import load_dotenv

logging.basicConfig(filename='./log/scaping.log', level=logging.INFO)
load_dotenv()

if __name__ == "__main__":
    scraping = Scraping(
        url="https://prtimes.jp",
        query={
            "run" : "html",
            "page" : "searchkey",
            "search_word" : "ヘルスケア"
        },
        num_page=10
    )
    scraping.run()


