import traceback
import os
import sys

import requests
from bs4 import BeautifulSoup
import dl_allrecipescom
from pprint import pprint
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.precision', 2)
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
    if os.path.exists('recipes.csv'):
        existing_recipes = pd.read_csv('recipes.csv')
        existing_links = set(existing_recipes['link'].to_list())
        links_to_dl = list(set(all_links) - existing_links)
        pbar = tqdm.tqdm(links_to_dl)
        print(f'Recipe links ({len(all_links)}) - existing recipes ({len(existing_recipes)}) = links to download ({len(links_to_dl)})')
        del existing_links
    else:
        existing_recipes = pd.DataFrame()
        pbar = tqdm.tqdm(all_links)
        print(f'Recipe links ({len(all_links)}) - existing recipes (0) = links to download ({len(all_links)})')

    for link in pbar:
        try:
            pbar.set_description(desc=link)
            items.append(dl_allrecipescom.link_to_dict(link))
        except Exception:
            traceback.print_exc()
        if pbar.n % 100 == 1:
            df = pd.DataFrame(items)
            if len(existing_recipes) == 0:
                existing_recipes = df.copy()
            else:
                existing_recipes.append(df, sort=False)
            if pbar.n % 1000 == 1:
                print(existing_recipes[[c for c in existing_recipes.columns if 'uses_' not in c]].describe())
            existing_recipes.to_csv("recipes.csv")
            pbar.set_description(desc=f"Saving {len(items)} recipes")
            items = []
    existing_recipes.append(pd.DataFrame(items))
    existing_recipes.to_csv("recipes.csv")
    pbar.close()


if __name__ == "__main__":
    main()
