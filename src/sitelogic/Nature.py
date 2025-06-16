"""
Nature.py — Selectors and Parsers for Nature Journal Articles
--------------------------------------------------------------

This module defines parsing functions for extracting article metadata
from HTML pages on the Nature journal website. It uses BeautifulSoup
elements (already parsed) to extract specific fields from each article card.

Each function expects a BeautifulSoup element corresponding to a single
article entry in a Nature research-articles listing page.

Constants:
----------
- basehref: Base URL for Nature journal, used for resolving relative links.
- section_identifier: CSS selector string used to locate article entries in a listing page.

Functions:
----------
- title(el): Extracts the title text from the article card.
- title_link(el): Constructs the full article URL from the relative link.
- authors(el): Returns a list of author names from the article metadata.
- article_type(el): Extracts the type of article (e.g., Research, News).
- date_published(el): Extracts the publication date in ISO format.

Author: Daniel Monyak
Date: 6-15-25
"""

basehref = 'https://www.nature.com'
section_identifier = '.app-article-list-row__item'

def title(el):
    """
    Extracts the title text of the article from the card element.

    Parameters:
        el (bs4.element.Tag): The BeautifulSoup element representing an article card.

    Returns:
        str: The article's title.
    """
    return el.select(".c-card__link")[0].text

def title_link(el):
    """
    Constructs the full URL to the article using the relative href from the card.

    Parameters:
        el (bs4.element.Tag): The BeautifulSoup element representing an article card.

    Returns:
        str: The full article URL.
    """
    return basehref + el.select(".c-card__link")[0]['href']

def authors(el):
    """
    Extracts the list of author names from the article element.

    Parameters:
        el (bs4.element.Tag): The BeautifulSoup element representing an article card.

    Returns:
        list of str: List of author names.
    """
    return [span.get_text(strip=True) for span in el.select('.app-author-list')[0].select('span[itemprop="name"]')]

def article_type(el):
    """
    Extracts the article type label from the card (e.g., 'Research').

    Parameters:
        el (bs4.element.Tag): The BeautifulSoup element representing an article card.

    Returns:
        str: The article type.
    """
    return el.select('.c-meta__type')[0].text

def date_published(el):
    """
    Extracts the publication date in ISO 8601 format.

    Parameters:
        el (bs4.element.Tag): The BeautifulSoup element representing an article card.

    Returns:
        str: Publication date in 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SSZ' format.
    """
    return el.select('time')[0]['datetime']
