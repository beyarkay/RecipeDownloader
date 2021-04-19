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

    ratings_element = soup.select_one(".ratings-list")
    if ratings_element:
        rating_keys = [int(stars.text.strip().replace(" star values:", "")) for stars in
                       ratings_element.select("span.rating-stars")]
        rating_vals = [stars.text.strip().replace(" star values:", "") for stars in
                       ratings_element.select("span.rating-count")]
    else:
        rating_keys = [5, 4, 3, 2, 1]
        rating_vals = ["0", "0", "0", "0", "0"]
    ratings = {f'{k}_out_of_5': int(v.replace(",", "")) for k, v in zip(rating_keys, rating_vals)}

    rating_sum = sum([int(v) * k for k, v in zip(rating_keys, rating_vals)])
    rating_n = sum([int(v) for k, v in zip(rating_keys, rating_vals)])
    rating_avg = (rating_sum / rating_n if rating_n else None)

    num_ratings = [int(re.sub(" Rating(s)?|,", "", l.text.strip())) for l in soup.select("span.ugc-ratings-item") if
                   re.match(r".*\d+.*", l.text.strip())]
    num_ratings = num_ratings[0] if num_ratings else 0
    num_reviews = [int(re.sub(" Review(s)?|,", "", l.text.strip())) for l in
                   soup.select("a.ugc-ratings-link.ugc-reviews-link") if re.match(r".*\d+.*", l.text.strip())]
    num_reviews = num_reviews[0] if num_reviews else 0

    meta_keys = [l.text.strip().lower().replace(":", "") for l in soup.select("div.recipe-meta-item-header")]
    meta_vals = [l.text.strip().lower().replace(":", "") for l in soup.select("div.recipe-meta-item-body")]
    meta_info = {k: v for k, v in zip(meta_keys, meta_vals)}

    nutrition = soup.select_one("div.partial.recipe-nutrition-section") \
        .select_one("div.section-body") \
        .text.replace("Full Nutrition", "").strip().split("; ")
    nutri_data = {}
    for n in nutrition:
        k = ""
        v = ""
        for item in n.split(" "):
            unit = ""
            if re.match(r"\d+(\.\d+)?g\.?", item):
                v = float(item.replace("g", ""))
                unit = "_g"
            elif re.match(r"\d+(\.\d+)?mg\.?", item):
                v = float(re.sub("mg(\.)?", "", item))
                unit = "_mg"
            elif re.match(r"\d+(\.\d+)?", item):
                v = float(item)
            else:
                k = item
        if k and v:
            nutri_data[k + unit] = v

    ingredients = [i.text.strip() for i in soup.select('.ingredients-item-name')]
    title = soup.select_one("h1.headline.heading-content").text


    cook_item = soup.select_one("a.author-block.authorBlock.authorBlock--link")
    if cook_item:
        cook_link = cook_item.get("href")
        cook_name = cook_item.select_one("span.author-name").text.strip()
    else:
        cook_link = None
        cook_name = "Anonymous"

    item = {
        "cook_link": cook_link,
        "cook_name": cook_name,
        "duration": duration,
        "link": link,
        "num_ratings": num_ratings,
        "num_reviews": num_reviews,
        "rating_avg": rating_avg,
        "title": title,
    }


def prev_link_from_initial(link: typing.AnyStr) -> typing.Dict:
    pass


def next_link_from_initial(link: typing.AnyStr) -> typing.Dict:
    pass
