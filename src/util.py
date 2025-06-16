"""
util.py — Utility Functions for Web Scraping and Database Insertion
-------------------------------------------------------------------

This module provides helper functions for:

- Parsing and cleaning author names from article metadata
- Generating structured dictionaries of author fields (FIRST, SECOND, THIRD)
- Removing null or empty values from dictionaries
- Making HTTP requests with appropriate headers and parsing HTML with BeautifulSoup
- Truncating string values to comply with database schema constraints
- Checking for existing records in a database table
- Performing safe inserts into a SQLAlchemy-connected MySQL database

Typical Usage:
--------------
Used as a utility layer by web scrapers that collect scientific publication data
and store it in structured relational tables (ARTICLES, AUTHORS, ARTICLES_AUTHORS).

Functions:
----------
- getSingleAuthorDict(auth) → dict
- getAuthorDict(authors) → dict
- removeNones(dict_x) → dict
- getSoup(url) → BeautifulSoup
- truncateEntries(entry, table) → dict
- myInsert(entry, DB, conn, rm_nones=False, trunc=False) → InsertResult
- elemInDB(elem, field, DB, conn) → bool

Dependencies:
-------------
- requests
- bs4 (BeautifulSoup)
- sqlalchemy

Author: Daniel Monyak
Date: 6-15-2025
"""

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, MetaData, insert, select, and_

# Custom HTTP headers to mimic a browser and avoid blocks during web scraping
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.361681261652"
}

# Used to label the first three authors in structured output
number_words = ['FIRST', 'SECOND', 'THIRD']

def getSingleAuthorDict(auth):
    """
    Splits a full author name into first and last name fields.

    Parameters:
        auth (str): Full name of the author as a string (e.g., "Alice B Smith").

    Returns:
        dict: Dictionary with 'FIRSTNAME' and 'LASTNAME' keys.
    """
    auth_split = auth.split(' ')
    author_dict = {}
    author_dict['FIRSTNAME'] = ' '.join(auth_split[:-1])
    author_dict['LASTNAME'] = auth_split[-1]
    return author_dict

def getAuthorDict(authors):
    """
    Processes a list of author names and returns a dictionary with
    structured first and last name fields for the first three authors.

    Parameters:
        authors (list of str): List of author name strings.

    Returns:
        dict: Dictionary with keys like 'FIRST_FIRSTNAME', 'FIRST_LASTNAME', etc.
    """
    author_dict = {}
    for j, auth in enumerate(authors):
        if j >= len(number_words):
            break

        author_dict_temp = getSingleAuthorDict(auth)
        author_dict[f'{number_words[j]}_FIRSTNAME'] = author_dict_temp['FIRSTNAME']
        author_dict[f'{number_words[j]}_LASTNAME'] = author_dict_temp['LASTNAME']

    return author_dict

def removeNones(dict_x):
    """
    Removes keys from a dictionary where the value is None or an empty string.

    Parameters:
        dict_x (dict): Dictionary to clean.

    Returns:
        dict: Dictionary without None or empty string values.
    """
    return {key: value for key, value in dict_x.items() if value != '' and value is not None}

def getSoup(url):
    """
    Sends a GET request to a URL and parses the HTML content with BeautifulSoup.

    Parameters:
        url (str): The URL of the page to retrieve.

    Returns:
        BeautifulSoup: Parsed HTML content of the page.
    """
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.text, 'html.parser')

def truncateEntries(entry, table):
    """
    Truncates string fields in a dictionary to the maximum allowed lengths
    defined in a SQLAlchemy table schema.

    Parameters:
        entry (dict): Dictionary of values to be inserted.
        table (sqlalchemy.Table): Table schema used to determine max lengths.

    Returns:
        dict: Dictionary with truncated string values.
    """
    new_entry = {}
    for col in table.columns:
        if col.name in entry:
            val = entry[col.name]
        else:
            continue

        if isinstance(val, str):
            max_len = getattr(col.type, 'length', None)
            if max_len:
                val = val[:max_len]
        new_entry[col.name] = val
    return new_entry

def myInsert(entry, DB, conn, rm_nones=False, trunc=False):
    """
    Inserts a dictionary of values into a database table.

    Parameters:
        entry (dict): Dictionary of values to insert.
        DB (sqlalchemy.Table): Table object where data will be inserted.
        conn (sqlalchemy.Connection): Active SQLAlchemy connection object.
        rm_nones (bool): If True, remove None or empty values before insert.
        trunc (bool): If True, truncate strings to match column lengths.

    Returns:
        ResultProxy: SQLAlchemy result object containing insert metadata.
    """
    if rm_nones:
        entry = removeNones(entry)
    if trunc:
        entry = truncateEntries(entry, DB)
    insert_result = conn.execute(
        insert(DB).values(entry)
    )
    return insert_result

def elemInDB(elem, field, DB, conn):
    """
    Checks whether a value exists in a specified column of a database table.

    Parameters:
        elem: Value to check for.
        field (str): Name of the column to check.
        DB (sqlalchemy.Table): SQLAlchemy Table object to search.
        conn (sqlalchemy.Connection): Active database connection.

    Returns:
        bool: True if the element exists in the table; False otherwise.
    """
    col = getattr(DB.c, field)
    select_result = conn.execute(
        select(col).where(col == elem)
    )
    select_first = select_result.first()
    return select_first is not None
