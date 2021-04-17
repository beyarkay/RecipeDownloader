import requests
from bs4 import BeautifulSoup
import dl_allrecipescom
from pprint import pprint

def main():
    all_links = dl_allrecipescom.fetch_item_links(limit=10)
    items = []
    for link in all_links:
        items.append(dl_allrecipescom.link_to_dict(link))
        pprint(items[-1])

if __name__ == "__main__":
    main()