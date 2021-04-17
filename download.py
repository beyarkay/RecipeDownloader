import traceback

import requests
from bs4 import BeautifulSoup
import dl_allrecipescom
from pprint import pprint
import pandas as pd
import tqdm

def main():
    all_links = dl_allrecipescom.fetch_item_links(limit=200)
    items = []
    for link in tqdm.tqdm(all_links):
        try:
            items.append(dl_allrecipescom.link_to_dict(link))
        except Exception:
            traceback.print_exc()
        #pprint(items[-1])
    pd.DataFrame(items).to_csv("recipes.csv")

if __name__ == "__main__":
    main()