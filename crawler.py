import argparse
import ctypes
import json
import os
import time
import traceback
from datetime import datetime
from pathlib import Path
from random import randint
from typing import Optional

import requests
import urllib3
from bs4 import BeautifulSoup

from libchrome import Chrome
from liblogger import log_err, log_inf

urllib3.disable_warnings()

COOKIE = ""
USER_AGENT = ""

CUR_DIR = str(Path(__file__).parent.absolute())
TEMP_DIR = os.path.join(CUR_DIR, "temp")
OUTPUT_DIR = os.path.join(CUR_DIR, "output")
DONE_MARKER_NAME = "done"


CHROME = None

# Nürnberg
# HOME_URL = "https://www.hwk-mittelfranken.de/betriebe/suche-75,0,bdbsearch.html?search-searchterm=&search-filter-zipcode=90402&search-filter-radius=250&search-filter-jobnr=&search-job=&search-local=&search-filter-training=&search-filter-experience="
# BASE_URL = "https://www.hwk-mittelfranken.de"
# COOKIE_DOMAIN = ".hwk-mittelfranken.de"
# TOTAL_PAGES = 1439
# PAGE_SIZE = 10

# Rostock
# HOME_URL = "https://www.hwk-omv.de/betriebe/suche-18,57,bdbsearch.html?search-searchterm=&search-filter-zipcode=Rostock&search-filter-radius=250&search-filter-jobnr=&search-job=&search-local=&search-filter-training=&search-filter-experience="
# BASE_URL = "https://www.hwk-omv.de"
# COOKIE_DOMAIN = ".hwk-omv.de"
# TOTAL_PAGES = 587
# PAGE_SIZE = 10

# Köln
HOME_URL = "https://www.hwk-koeln.de/betriebe/suche-32,0,bdbsearch.html?search-searchterm=&search-filter-zipcode=50667&search-filter-radius=250&search-filter-jobnr=&search-job=&search-local=&search-filter-experience="
BASE_URL = "https://www.hwk-koeln.de"
COOKIE_DOMAIN = ".hwk-koeln.de"
TOTAL_PAGES = 2716
PAGE_SIZE = 10


def gen_page_url(page_index: int) -> str:
    # Nürnberg
    # page_link = f"https://www.hwk-mittelfranken.de/betriebe/suche-75,0,bdbsearch.html?search-searchterm=&search-job=&search-local=&search-filter-zipcode=90402&search-filter-latitude=49.453333&search-filter-longitude=11.091667&search-filter-radius=250&search-filter-jobnr=&search-filter-training=&search-filter-experience=&limit={PAGE_SIZE}&offset={page_index * PAGE_SIZE}"

    # Rostock
    # page_link = f"https://www.hwk-omv.de/betriebe/suche-18,57,bdbsearch.html?limit={PAGE_SIZE}&search-searchterm=&search-job=&search-local=&search-filter-zipcode=Rostock&search-filter-radius=250&search-filter-jobnr=&search-filter-training=&search-filter-experience=&offset={page_index * PAGE_SIZE}"

    # Köln
    page_link = f"https://www.hwk-koeln.de/betriebe/suche-32,0,bdbsearch.html?limit={PAGE_SIZE}&search-searchterm=&search-job=&search-local=&search-filter-zipcode=50667&search-filter-latitude=50.941389&search-filter-longitude=6.953611&search-filter-radius=250&search-filter-jobnr=&search-filter-experience=&offset={page_index * PAGE_SIZE}"

    return page_link


def mark_as_done(dir_path: str):
    try:
        with open(os.path.join(dir_path, DONE_MARKER_NAME), "w") as f:
            f.write("done")
    except:
        traceback.print_exc()


def is_done(dir_path: str) -> bool:
    ret = False
    try:
        ret = os.path.isfile(os.path.join(dir_path, DONE_MARKER_NAME))
    except:
        traceback.print_exc()
    return ret


def get_cookie() -> Optional[str]:
    cookie_header = None
    if CHROME != None:
        CHROME.clear_cookie()
        while not CHROME.goto(
            url2go=HOME_URL,
            wait_elem_selector=".searchhit-result",
            wait_timeout=300.0,
        ):
            pass

        while True:
            cookies = CHROME.cookie(COOKIE_DOMAIN)
            if cookies != None:
                cookie_header = ""
                for cookie in cookies:
                    cookie_header += f"{cookie['name']}={cookie['value']}; "
                cookie_header = cookie_header.strip().rstrip(";")

                if cookie_header == "":
                    # log_err("Cookie is empty, Retry get cookie")
                    time.sleep(0.1)
                else:
                    break
            else:
                log_err("Cookie is none")
    else:
        log_err("chrome is none")
    return cookie_header


def fetch(url: str, delay: float = 1.0) -> Optional[BeautifulSoup]:
    global COOKIE

    ret = None
    try:
        if not url.startswith(BASE_URL):
            url = BASE_URL + url

        while True:
            try:
                time.sleep(delay)
                resp = requests.get(
                    url,
                    headers={
                        "Cookie": COOKIE,
                        "User-Agent": USER_AGENT,
                    },
                    verify=False,
                    timeout=15.0,
                )

                if resp.status_code == 200:
                    if "Just a moment..." in resp.text:
                        log_err("cloudflare")
                    else:
                        ret = BeautifulSoup(resp.text, "html.parser")
                        break
                else:
                    log_err(f"request error: {resp.status_code}")

                log_inf("fetch new cookie")
                COOKIE = get_cookie()
                log_inf(f"cookie > {COOKIE}")
            except:
                traceback.print_exc()
    except:
        traceback.print_exc()
    return ret


def crawl_page(page_index: int, page_link: str):
    try:
        page_dir = os.path.join(OUTPUT_DIR, ("page_%04d" % page_index))
        os.makedirs(page_dir, exist_ok=True)

        if is_done(page_dir):
            log_inf(f"page {page_index} is already done")
        else:
            log_inf(f"page {page_index} > {page_link}")

            # fetch company list
            soup = fetch(page_link)
            if soup != None:
                result_elems = soup.select(".searchhit-result")
                for i, result_elem in enumerate(result_elems):
                    log_inf(f"crawl page {page_index} > info {i}")

                    info_fpath = os.path.join(page_dir, f"{i}.json")
                    if os.path.isfile(info_fpath):
                        log_inf(f"page {page_index} > info {i} is already done")
                        continue
                    info = {
                        "name": "#",
                        "address": "#",
                        "email": "#",
                        "telephone": "#",
                        "mobile": "#",
                        "fax": "#",
                    }
                    link_elem = result_elem.select_one("a")
                    if link_elem != None:
                        info_link = link_elem.attrs["href"]
                        name = link_elem.text.strip()
                        info["name"] = name

                        # fetch info
                        soup = fetch(info_link)
                        if soup != None:
                            cards = soup.select(".container.content>div.row:nth-child(2)>div.col-md-3")

                            # address
                            p_elem = cards[0].select_one("p")
                            if p_elem != None:
                                content = p_elem.decode_contents()
                                words = content.split("<br/>")
                                street = words[1].strip()
                                zip = words[2].split(" ", 1)[0].strip()
                                city = words[2].split(" ", 1)[1].strip()
                                address = f"{city} {street}"
                                info["address"] = address
                            else:
                                log_err("p_elem is none")

                            if len(cards) > 1:
                                p_elem = cards[1].select_one("p")
                                if p_elem != None:
                                    # email
                                    email_elem = p_elem.select_one("a.mail")
                                    if email_elem != None:
                                        email = email_elem.text.strip()
                                        info["email"] = email.replace("--at--", "@")
                                    else:
                                        log_err("email elem is none")

                                    # phone
                                    contact = p_elem.decode_contents()
                                    words = contact.split("<br/>")
                                    for word in words:
                                        word = word.lower().strip()
                                        if word.startswith("telefon"):
                                            info["telephone"] = word.replace("telefon", "").strip()
                                        elif word.startswith("handy"):
                                            info["mobile"] = word.replace("handy", "").strip()
                                        elif word.startswith("fax"):
                                            info["fax"] = word.replace("fax", "").strip()
                                else:
                                    log_err("p_elem is none")
                            else:
                                log_err("no contact")
                        else:
                            log_err("failed fetch company content")
                    else:
                        log_err("failed get link elem")

                    tmp_fpath = info_fpath + ".tmp"
                    with open(tmp_fpath, "w") as f:
                        json.dump(info, f, indent=2)

                    os.rename(tmp_fpath, info_fpath)
            else:
                log_err("failed fetch page content")
        mark_as_done(page_dir)
    except:
        traceback.print_exc()


def work(start: int, count: int):
    try:
        global CHROME, USER_AGENT

        begin_page = start
        end_page = min(TOTAL_PAGES, start + count)
        if count == 0:
            end_page = TOTAL_PAGES

        log_inf(f"From {begin_page} page To {end_page} page")
        ctypes.windll.kernel32.SetConsoleTitleW(f"From {begin_page} page To {end_page} page")

        CHROME = Chrome(
            width=800 + randint(0, 200),
            height=600 + randint(0, 100),
            user_data_dir=os.path.join(TEMP_DIR, f"profile_{datetime.now().timestamp()}"),
        )
        CHROME.start()
        USER_AGENT = CHROME.run_script("navigator.userAgent")

        for i in range(begin_page, end_page):
            crawl_page(page_index=i, page_link=gen_page_url(i))

        CHROME.quit()
        log_inf("All done.")
    except:
        traceback.print_exc()


def main():
    global STATE, FROM_CITY, CITY_COUNT
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start",
        dest="start",
        type=int,
        default=0,
        required=False,
        help="Start page index. Default is 0.",
    )
    parser.add_argument(
        "--count",
        dest="count",
        type=int,
        default=0,
        required=False,
        help="Page count. Default is 0 which means all the following pages.",
    )
    args = parser.parse_args()

    work(start=args.start, count=args.count)
    input("Press ENTER to exit.")


if __name__ == "__main__":
    main()
