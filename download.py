"""
Nature Article Scraper and Database Loader
------------------------------------------

This script scrapes research articles from Nature's website
and inserts metadata into a MySQL database. The metadata includes article title, 
DOI, publication date, article type, and author information. The script avoids 
duplicate entries by checking the DOI before inserting a new article.


Command-Line Arguments:
-----------------------
--start_page    (int)   Page number to start scraping from (default: 1)
--max_pages     (int)   Maximum number of pages to scrape (default: 50)
--db_config     (str)   Path to db_login.json with database credentials (default: data/db_login.json)

Example Usage:
--------------
python scrape_nature.py --start_page 41 --max_pages 60 --db_config data/db_login.json

Dependencies:
-------------
- MySQL database with `ARTICLES`, `AUTHORS`, and `ARTICLES_AUTHORS` tables
- Python packages: pandas, sqlalchemy, beautifulsoup4
- Custom modules: src.util, src.sitelogic.Nature, src.sitelogic.NatureArticle

Tables involved:
-------------
- ARTICLES: stores metadata for each article
- AUTHORS: stores individual author information (name, ORCID)
- ARTICLES_AUTHORS: many-to-many linking table between articles and authors

Author: Daniel Monyak
Date: 6-12-25
"""

# Import necessary libraries
import pandas as pd
from sqlalchemy import create_engine, MetaData, insert, select, and_
import src.util as util
import src.sitelogic.Nature as nat_sl
import src.sitelogic.NatureArticle as natArt_sl
import json
import os
import re
import argparse

# ----------------------------------------
# Command-line argument parsing
# ----------------------------------------
parser = argparse.ArgumentParser(description="Scrape Nature research articles and load into MySQL database.")

parser.add_argument("--start_page", type=int, default=1,
                    help="Page number to start scraping from (default: 1)")

parser.add_argument("--max_pages", type=int, default=50,
                    help="Maximum number of pages to scrape (default: 50)")

parser.add_argument("--db_config", type=str, default=os.path.join('data', 'db_login.json'),
                    help="Path to db_login.json with database credentials")

args = parser.parse_args()

# Target database name and base URL for Nature research articles
database = 'Nature'
# url_unformatted = 'https://www.nature.com/nature/research-articles?searchType=journalSearch&sort=PubDate&page={page_num}'
url_unformatted = 'https://www.nature.com/search?q=breast+cancer&order=relevance&page={page_num}'

##### MySQL Connection Setup

# Load database login credentials from JSON file
with open(args.db_config, 'r') as f:
    db_login = json.load(f)


# Create SQLAlchemy engine and reflect existing database schema
engine = create_engine(f"mysql+mysqlconnector://{db_login['user']}:{db_login['password']}@localhost/{database}")
metadata = MetaData()
metadata.reflect(bind=engine)

# Get table references
ARTICLES = metadata.tables['ARTICLES']
AUTHORS = metadata.tables['AUTHORS']
ARTICLES_AUTHORS = metadata.tables['ARTICLES_AUTHORS']
TITLEWORDS = metadata.tables['TITLEWORDS']

# Create mysql.connector
import mysql.connector
connector = mysql.connector.connect(
    host='localhost',
    # user=db_login['user'],
    user='tableau',
    password=db_login['password'],
    database=database
)

###################################################

keepSeeking = True
page_num = args.start_page - 1  # we increment at top of loop

# Loop over Nature article pages
while keepSeeking:
    # Stop after hard limit of pages
    if page_num >= args.max_pages:
        for kk in range(5):
            print('#' * 34)
        print(f'Exceeded max of {page_num} pages searched!')
        break

    page_num += 1

    # Skip pages before 41 (e.g., if continuing from previous run)
    if page_num < 0:
        continue

    print(f'Page: {page_num}')
    
    # Get parsed HTML (BeautifulSoup) of the current page
    soup = util.getSoup(url_unformatted.format(page_num=page_num))

    # Extract article sections from the page
    sections_to_read = soup.select(nat_sl.section_identifier)

    # If no articles found, stop searching
    if len(sections_to_read) == 0:
        keepSeeking = False
        continue

    # Loop through each article preview on the page
    for i, el in enumerate(sections_to_read):
        print(f'Article: {i}')

        # Safety check to prevent runaway scraping
        if i >= 1000:
            print(f'Reached {i} articles...')
            break
        
        articles_entry = {}

        ######################
        # Extract article title
        try:
            articles_entry['TITLE'] = nat_sl.title(el)
        

            # Extract article URL and fetch article-specific page
            articles_entry['TITLE_LINK'] = nat_sl.title_link(el)
            article_soup = util.getSoup(articles_entry['TITLE_LINK'])

            # Extract DOI from article page
            articles_entry['DOI'] = natArt_sl.doi(article_soup)
            
            # Extract metrics from article page
            articles_entry.update(natArt_sl.metrics(article_soup))

            # Extract dates from article page
            articles_entry.update(natArt_sl.dateList(article_soup))

            # Extract journal name from article apge
            articles_entry['JOURNAL'] = natArt_sl.journal(article_soup)

            with engine.begin() as conn:
                # Check if article already exists in database by DOI
                if util.elemInDB(articles_entry['DOI'], 'DOI', ARTICLES, conn):
                    print('Already seen')
                    continue

            # Extract additional metadata
            articles_entry['ARTICLE_TYPE'] = nat_sl.article_type(el)
            articles_entry['DATE_PUBLISHED'] = nat_sl.date_published(el)

            authors = nat_sl.authors(el)

            # Convert raw author names into dictionary format
            author_dict = util.getAuthorDict(authors)

            # Merge author fields into article entry
            articles_entry.update(author_dict)

            # Extract detailed author data from article page
            authors_proper = natArt_sl.authors(article_soup)
            auth_proper_orcid = natArt_sl.orcid_id(article_soup)

        except IndexError:
            continue
        except Exception as e:
            # Unexpected error
            print(e)
            break
    
        try:
            with engine.begin() as conn:
                # Insert article record into ARTICLES table
                result = util.myInsert(articles_entry, ARTICLES, conn, rm_nones=True, trunc=True)
                article_id_last = result.inserted_primary_key[0]  # Retrieve auto-generated article ID

                auth_id_seen = set()  # Track which author IDs have already been linked to avoid duplicates
                for auth_i, auth in enumerate(authors_proper):
                    auth_single_dict = util.getSingleAuthorDict(auth)
                    if auth_single_dict['FIRSTNAME'] == '': # e.g. companies listed as authors
                        continue

                    auth_single_dict['ORCID'] = auth_proper_orcid[auth_i]
                    
                    # Try to find author by ORCID if available
                    if auth_proper_orcid[auth_i] is not None:
                        select_result = conn.execute(
                            select(AUTHORS.c.ID).where(AUTHORS.c.ORCID == auth_single_dict['ORCID'])
                        )
                    else:
                        # Fallback: find by name (less reliable)
                        select_result = conn.execute(
                            select(AUTHORS.c.ID).where(
                                and_(AUTHORS.c.FIRSTNAME == auth_single_dict['FIRSTNAME'],
                                     AUTHORS.c.LASTNAME == auth_single_dict['LASTNAME'])
                            )
                        )
                    select_first = select_result.first()

                    # Insert new author if not found
                    if select_first is None:
                        insert_result = util.myInsert(auth_single_dict, AUTHORS, conn, rm_nones=True, trunc=True)
                        assert len(insert_result.inserted_primary_key) == 1
                        auth_id = insert_result.inserted_primary_key[0]
                    else:
                        # Use existing author ID
                        auth_id = select_first[0]
                    
                    if auth_id not in auth_id_seen:
                        auth_id_seen.add(auth_id)
                        # Insert article-author relationship
                        _ = util.myInsert(dict(ARTICLE_ID=article_id_last, AUTHOR_ID=auth_id),
                                   ARTICLES_AUTHORS, conn)

            # Add words to TITLEWORDS
            # cursor = conn.cursor()
            with connector.cursor() as cursor:
                cleaned_title = re.sub(r'[^a-zA-Z0-9]', ' ', articles_entry['TITLE']).split(' ')
                for w in cleaned_title:
                    cursor.callproc('AddOrIncrementWord', [w.lower()])

            connector.commit()

        except Exception as e:
            # Catch any database or parsing issues for debugging
            print(page_num)
            print(i)
            print(articles_entry['TITLE'])
            keepSeeking = False
            print(e)
            break

conn.close()

print(f"\nScraping complete. Started from page {args.start_page}, stopped at page {page_num}.")
