import traceback

import requests
from bs4 import BeautifulSoup
import dl_allrecipescom
from pprint import pprint
import pandas as pd
import tqdm


def main():
    all_links = dl_allrecipescom.fetch_item_links(limit=1000)
    items = []
    pbar = tqdm.tqdm(all_links)
    for i, link in enumerate(pbar):
        try:
            pbar.set_description(desc=link)
            items.append(dl_allrecipescom.link_to_dict(link))
        except Exception:
            traceback.print_exc()
        if i % 10 == 0:
            pd.DataFrame(items).to_csv("recipes.csv")
    pd.DataFrame(items).to_csv("recipes.csv")


if __name__ == "__main__":
    main()
