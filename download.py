import traceback
import os
import sys
from multiprocessing import Pool, TimeoutError

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
        print(f'Recipe links ({len(all_links)}) - existing recipes ({len(existing_recipes)}) = links to download ({len(links_to_dl)})')
        del existing_links
    else:
        existing_recipes = pd.DataFrame()
        links_to_dl = all_links[:]
        print(f'Recipe links ({len(all_links)}) - existing recipes ({len(existing_recipes)}) = links to download ({len(links_to_dl)})')


    pbar = tqdm.tqdm(links_to_dl)
    NUM_PROCESSES = 4
    with Pool(processes=NUM_PROCESSES) as pool:
        while len(links_to_dl) > 0:
            results = []
            links = []
            for _ in range(min(NUM_PROCESSES, len(links_to_dl))):
                links.append(links_to_dl.pop())
                results.append(pool.apply_async(dl_allrecipescom.link_to_dict, (links[-1],)))
            for link, res in zip(links, results):
                try:
                    items.append(res.get(timeout=10))
                    pbar.set_description(desc=link)
                    pbar.update()
                except TimeoutError as e:
                    links_to_dl.append(link)
                    traceback.print_exc()
                except Exception:
                    traceback.print_exc()

            if len(items) > 100:
                df = pd.DataFrame(items)
                #print(f"{len(df)} + {len(existing_recipes)} = {len(df) + len(existing_recipes)}")
                if len(existing_recipes) == 0:
                    existing_recipes = df.copy()
                else:
                    existing_recipes = pd.concat([existing_recipes, df], ignore_index=True, sort=False)
                existing_recipes.to_csv("recipes.csv")
                items = []

    existing_recipes.append(pd.DataFrame(items))
    existing_recipes.to_csv("recipes.csv")
    pbar.close()


if __name__ == "__main__":
    main()
