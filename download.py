import traceback
import os
import sys

import requests
from bs4 import BeautifulSoup
import dl_allrecipescom
from pprint import pprint
import pandas as pd
import tqdm


def main():
    if os.path.exists("recipe_links.txt"):
        print("Using links from recipe_links.txt")
        with open("recipe_links.txt", "r") as f:
            all_links = [l.strip() for l in f.readlines()]
    else:
        print("Scraping links from the internet")
        limit = 10_000 if len(sys.argv) != 2 else int(sys.argv[1])
        all_links = dl_allrecipescom.fetch_item_links(limit=limit)
    items = []
    pbar = tqdm.tqdm(all_links)
    for link in pbar:
        try:
            pbar.set_description(desc=link)
            items.append(dl_allrecipescom.link_to_dict(link))
        except Exception:
            traceback.print_exc()
        if pbar.n % 10 == 0 and pbar.n > 0:
            pd.DataFrame(items).to_csv("recipes.csv")
    pd.DataFrame(items).to_csv("recipes.csv")
    pbar.close()


if __name__ == "__main__":
    main()
