import datetime
import typing

import tqdm
from bs4 import BeautifulSoup
import requests
import datetime
import re
from pprint import pprint

ROOTS = [
    "https://www.allrecipes.com/recipes/87/everyday-cooking/vegetarian/"
]


def fetch_item_links(limit=100) -> typing.List:
    all_links = []
    if limit != 0:
        pbar = tqdm.tqdm(total=limit)
    else:
        pbar = tqdm.tqdm(total=limit)
    for root in ROOTS:
        link = root
        while link is not None and (len(all_links) < limit or limit == 0):
            item_links, link = fetch_one_page_of_links(link)
            all_links.extend(item_links)
            all_links = list(set(all_links))
            pbar.set_description(desc=link.replace(r"https://www.allrecipes.com/", ".../"))
            pbar.update(len(all_links) - pbar.n)
    pbar.close()
    return all_links[:limit]


def fetch_one_page_of_links(link: typing.AnyStr) -> typing.Tuple:
    start = datetime.datetime.now()
    r = requests.get(link)
    duration = datetime.datetime.now() - start
    # print(f"\tFetching {link} took {duration.total_seconds()}s")
    soup = BeautifulSoup(r.text, 'html.parser')

    # ====================================================================
    #   Collect all the item links on this page.
    #   They could either start with https://www.allrecipes.com/recipe/...
    #    or just with /recipe/...
    # ====================================================================

    item_links = [link.get("href") for link in soup.select("a") if
                  re.match(r".+www\.allrecipes\.com/recipe/.+", link.get("href", ""))]
    item_links.extend(["https://www.allrecipes.com" + link.get("href") for link in soup.select("a") if
                       re.match(r"^/recipe/", link.get("href", ""))])

    # =================================================================
    #   Get the link for the next page.
    #   It'll either be in a 'next page' button or a 'load more' button
    # =================================================================
    next_page_link = [next_page.get("href", None) for next_page in
                      soup.select("a.category-page-list-related-load-more-button")]
    if not next_page_link:
        next_page_link = [next_page.get("href", None) for next_page in
                          soup.select("a.category-page-list-related-nav-next-button")]
        if not next_page_link:
            next_page_link = [None]

    # Return the found links, and the link to take us to the next page.
    return item_links, next_page_link[0]


def link_to_dict(link: typing.AnyStr) -> typing.Dict:
    # print(f"Parsing link {link}")
    start = datetime.datetime.now()
    r = requests.get(link)
    duration = datetime.datetime.now() - start
    soup = BeautifulSoup(r.text, 'html.parser')

    rating_keys = [int(stars.text.strip().replace(" star values:", "")) for stars in
                   soup.select_one(".ratings-list").select("span.rating-stars")]
    rating_vals = [stars.text.strip().replace(" star values:", "") for stars in
                   soup.select_one(".ratings-list").select("span.rating-count")]
    ratings = {k: v.replace(",", "") for k, v in zip(rating_keys, rating_vals)}

    meta_keys = [l.text.strip().lower().replace(":", "") for l in soup.select("div.recipe-meta-item-header")]
    meta_vals = [l.text.strip().lower().replace(":", "") for l in soup.select("div.recipe-meta-item-body")]
    meta_info = {k: v for k, v in zip(meta_keys, meta_vals)}

    num_ratings = [re.sub(" Ratings", "", l.text.strip()) for l in soup.select("span.ugc-ratings-item") if
                       re.match(r".*\d+.*", l.text.strip())][0]
    num_reviews = [re.sub(" Reviews", "", l.text.strip()) for l in
                       soup.select("a.ugc-ratings-link.ugc-reviews-link") if re.match(r".*\d+.*", l.text.strip())][0]

    nutrition = soup.select_one("div.partial.recipe-nutrition-section") \
        .select_one("div.section-body") \
        .text.replace("Full Nutrition", "").strip().split("; ")

    ingredients = [i.text.strip() for i in soup.select('.ingredients-item-name')]
    title = soup.select_one("h1.headline.heading-content").text


    rating_sum = sum([int(v)*k for (k, v) in ratings.items()])
    rating_n = sum([int(v) for (k, v) in ratings.items()])
    rating_avg = rating_sum/rating_n

    return {
        "ingredients": ingredients,
        "link": link,
        "num_ratings": num_ratings,
        "num_reviews": num_reviews,
        "title": title,
        "ratings": ratings,
        "rating_avg": rating_avg,
        "meta_info": meta_info,
        "duration": duration,
        "nutrition": nutrition
    }


def prev_link_from_initial(link: typing.AnyStr) -> typing.Dict:
    pass


def next_link_from_initial(link: typing.AnyStr) -> typing.Dict:
    pass
