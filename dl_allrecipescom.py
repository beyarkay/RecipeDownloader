import traceback
import datetime
import typing

import tqdm
from bs4 import BeautifulSoup
import requests
import datetime
import re
from pprint import pprint

ROOTS = [
        "https://www.allrecipes.com/recipes/76/appetizers-and-snacks/",
        "https://www.allrecipes.com/recipes/88/bbq-grilling/",
        "https://www.allrecipes.com/recipes/156/bread/",
        "https://www.allrecipes.com/recipes/78/breakfast-and-brunch/",
        "https://www.allrecipes.com/recipes/79/desserts/",
        "https://www.allrecipes.com/recipes/17562/dinner/",
        "https://www.allrecipes.com/recipes/1642/everyday-cooking/",
        "https://www.allrecipes.com/recipes/84/healthy-recipes/",
        "https://www.allrecipes.com/recipes/85/holidays-and-events/",
        "https://www.allrecipes.com/recipes/17567/ingredients/",
        "https://www.allrecipes.com/recipes/17561/lunch/",
        "https://www.allrecipes.com/recipes/80/main-dish/",
        "https://www.allrecipes.com/recipes/92/meat-and-poultry/",
        "https://www.allrecipes.com/recipes/95/pasta-and-noodles/",
        "https://www.allrecipes.com/recipes/96/salad/",
        "https://www.allrecipes.com/recipes/93/seafood/",
        "https://www.allrecipes.com/recipes/81/side-dish/",
        "https://www.allrecipes.com/recipes/94/soups-stews-and-chili/",
        "https://www.allrecipes.com/recipes/236/us-recipes/",
        "https://www.allrecipes.com/recipes/86/world-cuisine/",
        #"https://www.allrecipes.com/recipes/16798/main-dish/quiche/vegetarian-quiche/",
        #"https://www.allrecipes.com/recipes/16800/main-dish/pasta/lasagna/vegetarian-lasagna/",
        #"https://www.allrecipes.com/recipes/17684/everyday-cooking/vegetarian/whole-grain/",
        #"https://www.allrecipes.com/recipes/1947/everyday-cooking/quick-and-easy/",
        #"https://www.allrecipes.com/recipes/201/meat-and-poultry/chicken/",
        #"https://www.allrecipes.com/recipes/201/meat-and-poultry/chicken/",
        #"https://www.allrecipes.com/recipes/2272/main-dish/savory-pies/vegetarian-pie/",
        #"https://www.allrecipes.com/recipes/265/everyday-cooking/vegetarian/main-dishes/",
        #"https://www.allrecipes.com/recipes/362/desserts/cookies/",
        #"https://www.allrecipes.com/recipes/78/breakfast-and-brunch/",
        #"https://www.allrecipes.com/recipes/87/everyday-cooking/vegetarian/",
        #"https://www.allrecipes.com/recipes/92/meat-and-poultry/",
        #"https://www.allrecipes.com/recipes/94/soups-stews-and-chili/",
        #"https://www.allrecipes.com/recipes/96/salad/",
]


def fetch_item_links(limit=100) -> typing.List:
    all_links = []
    if limit != 0:
        pbar = tqdm.tqdm(total=limit)
    else:
        pbar = tqdm.tqdm(total=limit)
    count = 0
    for root in ROOTS:
        try:
            link = root
            while link is not None and (len(all_links) < limit or limit == 0):
                item_links, link = fetch_one_page_of_links(link, pbar)
                if link is not None:
                    pbar.set_description(desc=link.replace(r"https://www.allrecipes.com/", ".../") + " (adding links to set)")
                else:
                    pbar.set_description(desc="Moving on to next root link")
                    with open("recipe_links.txt", "w+") as f:
                        f.writelines("\n".join(all_links))

                all_links.extend(item_links)
                all_links = list(set(all_links))
                pbar.update(len(all_links) - pbar.n)
                if count % 10 == 0:
                    with open("recipe_links.txt", "w+") as f:
                        f.writelines("\n".join(all_links))
                count += 1

        except Exception:
            with open("recipe_links.txt", "w+") as f:
                f.writelines("\n".join(all_links))
            traceback.print_exc()
    pbar.close()
    return all_links[:limit]


def fetch_one_page_of_links(link: typing.AnyStr, pbar: tqdm.tqdm) -> typing.Tuple:
    pbar.set_description(desc=link.replace(r"https://www.allrecipes.com/", ".../") + " (fetching page)")
    start = datetime.datetime.now()
    if "https://www.allrecipes.com/" in link:
        r = requests.get(link)
    else:
        print(f"Link {link} doesn't contain 'https://www.allrecipes.com/', attempting to prepend it")
        r = requests.get('https://www.allrecipes.com' + link)
    duration = datetime.datetime.now() - start
    pbar.set_description(desc=link.replace(r"https://www.allrecipes.com/", ".../") + " (making soup)")
    # print(f"\tFetching {link} took {duration.total_seconds()}s")
    soup = BeautifulSoup(r.text, 'html.parser')
    pbar.set_description(desc=link.replace(r"https://www.allrecipes.com/", ".../") + " (scraping links)")

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
    title_element = None
    attempts = 0
    while title_element is None and attempts < 12:
        attempts += 1
        try:
            r = requests.get(link, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            title_element = soup.select_one("h1.headline.heading-content")
        except requests.exceptions.ReadTimeout as e:
            continue
    duration = datetime.datetime.now() - start
    if attempts >= 12:
        item = {
            "duration": duration,
            "link": link,
        }
        return item

    title = title_element.text
    
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

    nutrition_section = soup.select_one("div.partial.recipe-nutrition-section")
    nutri_data = {}
    if nutrition_section:
        nutrition = nutrition_section.select_one("div.section-body") \
            .text.replace("Full Nutrition", "").strip().split("; ")
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

    ingredient_wordvec = __ingredients_to_wordvec(ingredients)

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
    item.update(meta_info)
    item.update(ratings)
    item.update(nutri_data)
    item.update({f"uses_{k}": v for k, v in ingredient_wordvec.items()})

    return item


def __ingredients_to_wordvec(ingredients: typing.List):
    # ing = df['ingredients'].apply(lambda x: pd.Series(re.sub("\['|'\]", "", x).split("', '")))
    # ingredients = [(re.sub("\['|'\]", "", i).split("', '")) for i in df['ingredients'].to_list()]
    # ingredients = [item for subl in ingredients for item in subl]
    subbed = []
    for ing in ingredients:
        # 'Thin' spaces between fractions and whole numbers
        item = re.sub(r"\\u2009", "", ing).lower()
        # Halves, Quarters
        item = re.sub(r"(\D|^)¼", "0.25", item)
        item = re.sub(r"(\D|^)½", "0.5", item)
        item = re.sub(r"(\D|^)¾", "0.75", item)
        # Thirds
        item = re.sub(r"(\D|^)⅔", "0.666", item)
        item = re.sub(r"(\D|^)⅓", "0.333", item)
        # Eighths
        item = re.sub(r"(\D|^)⅛", "0.125", item)
        item = re.sub(r"(\D|^)⅜", "0.375", item)
        item = re.sub(r"(\D|^)⅞", "0.875", item)

        # And now the same, but this time for numbers formatted like 1¼ and not just ¼
        item = re.sub(r"¼", ".25", item)
        item = re.sub(r"½", ".5", item)
        item = re.sub(r"¾", ".75", item)
        item = re.sub(r"⅔", ".666", item)
        item = re.sub(r"⅓", ".333", item)
        item = re.sub(r"⅛", ".125", item)
        item = re.sub(r"⅜", ".375", item)
        item = re.sub(r"⅞", ".875", item)

        # Remove prepositions
        item = re.sub(r"\b(and|or|but|on|in|into|onto|to|as|for|of|from|with)\b", " ", item)

        # Remove special characters and digits
        item = re.sub(r"\d|\.|,|\(|\)|\*|\\|/|\"|\'|®|™|\[|]|%", " ", item)

        # Remove units of measurement
        item = re.sub(r"\b(ounce(s)?|(-)?inch(es)?|pound(s)?|cup(s)?|tablespoon(s)?" + \
                      r"|teaspoon(s)?|can(s)?|(extra )?large|small|medium|big|long|short" + \
                      r"|chunk(s)?|package(s)?|pkg(s)?|bag(s)?" + \
                      r")\b", "", item)

        # Remove duplicated dashes
        item = re.sub(r"-+", "-", item)
        # Remove orphaned or trailing or leading dashes
        item = re.sub(r"^\s*-", " ", item)
        item = re.sub(r"-\s*$", " ", item)
        item = re.sub(r"\s-\s", " ", item)

        # Strip and single out any duplicated whitespace
        item = re.sub(r"\s+", " ", item).strip()

        subbed.append(item)
    subbed = " ".join(subbed).split(" ")
    wordvec = {}
    for item in subbed:
        wordvec[item] = 1 if (item not in wordvec.keys()) else wordvec[item] + 1
    sorted_keys = sorted(wordvec, key=wordvec.get, reverse=True)
    sorted_vals = [wordvec[key] for key in sorted_keys]
    wordvec = {k: v for k, v in zip(sorted_keys, sorted_vals)}
    return wordvec


def prev_link_from_initial(link: typing.AnyStr) -> typing.Dict:
    pass


def next_link_from_initial(link: typing.AnyStr) -> typing.Dict:
    pass
