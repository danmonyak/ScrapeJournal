"""
NatureArticle.py — Detailed Article Metadata Extractors for Nature.com
----------------------------------------------------------------------

This module provides functions to extract detailed metadata from individual
Nature article pages using BeautifulSoup. These functions are intended to
be used after navigating to the full article page (not the search listing).

Each function assumes a parsed BeautifulSoup object (`soup`) of the article's HTML.

Functions:
----------
- authors(soup): Extracts the list of author names.
- orcid_id(soup): Extracts the ORCID IDs for each author (if available).
- doi(soup): Extracts the article's DOI.
- metrics(soup): Extracts article-level metrics (views, citations, etc.).
- dateList(soup): Extracts key publication dates (received, accepted, published).
- journal(soup): Extracts the name of the journal the article appears in.

Author: Daniel Monyak
Date: 6-15-25
"""

from datetime import datetime

def authors(soup):
    """
    Extracts the list of author names from the article page.

    Parameters:
        soup (bs4.BeautifulSoup): Parsed HTML of the article page.

    Returns:
        list of str: List of author names.
    """
    return [elel.get_text(strip=True) for elel in soup.select('.c-article-author-list')[0].select('a[data-test="author-name"]')]

def orcid_id(soup):
    """
    Extracts ORCID IDs for each author, if available.

    Parameters:
        soup (bs4.BeautifulSoup): Parsed HTML of the article page.

    Returns:
        list of str or None: List of ORCID IDs matching the authors, or None if not found.
    """
    ret = []
    for author_item in soup.select('.c-article-author-list__item'):
        js_orcid = author_item.select('a[class="js-orcid"]')
        if len(js_orcid) > 0:
            ret.append(
                js_orcid[0]['href'].split('orcid.org/')[-1]
            )
        else:
            ret.append(None)
    return ret

def doi(soup):
    """
    Extracts the article's DOI from the bibliographic section.

    Parameters:
        soup (bs4.BeautifulSoup): Parsed HTML of the article page.

    Returns:
        str or None: DOI string if found, otherwise None.
    """
    possible_doi = [span.get_text(strip=True) for span in soup.select('span[class="c-bibliographic-information__value"]')]
    for pdoi in possible_doi:
        if 'doi.org' in pdoi:
            return pdoi.split('doi.org/')[-1]
    return None

def metrics(soup):
    """
    Extracts metrics such as Views and Citations from the article.

    Parameters:
        soup (bs4.BeautifulSoup): Parsed HTML of the article page.

    Returns:
        dict: A dictionary of metrics with keys like 'VIEWS', 'CITATIONS', etc.
    """
    metrics_data = {}
    for li in soup.select('.c-article-metrics-bar__wrapper')[0].select('p[class="c-article-metrics-bar__count"]'):
        txt_ls = li.getText().split(' ')
        num_txt = txt_ls[0]
        if num_txt.endswith('k'):
            num_int = int(num_txt.rstrip('k')) * 1000
        else:
            num_int = int(num_txt)
        metrics_data[txt_ls[1].upper()] = num_int
    return metrics_data

fields_desired = ['Received', 'Accepted', 'Published']
def dateList(soup):
    """
    Extracts important publication dates such as received, accepted, and published.

    Parameters:
        soup (bs4.BeautifulSoup): Parsed HTML of the article page.

    Returns:
        dict: A dictionary mapping 'RECEIVED', 'ACCEPTED', and 'PUBLISHED' to ISO date strings.
    """
    date_data = {}
    li_list = soup.select('li[class="c-bibliographic-information__list-item"]')
    for li in li_list:
        txt_ls = li.getText().split(':')
        if txt_ls[0] in fields_desired:
            date_str = txt_ls[1].strip()
            date_obj = datetime.strptime(date_str, "%d %B %Y")
            formatted_date = date_obj.strftime("%Y-%m-%d")
            date_data[txt_ls[0].upper()] = formatted_date
    return date_data

def journal(soup):
    """
    Extracts the name of the journal where the article was published.

    Parameters:
        soup (bs4.BeautifulSoup): Parsed HTML of the article page.

    Returns:
        str: The journal name.
    """
    return soup.select('p[class="c-article-info-details"]')[0].select('a[data-test="journal-link"]')[0].getText()
