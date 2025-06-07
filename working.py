import requests
from bs4 import BeautifulSoup
import pandas as pd

number_words = ['first', 'second', 'third', 'fourth']
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.361681261652"
}

# search = 'fCpGs methylation'
# search_formatted = '+'.join(search.split(' '))
# payload = {'api_key': '684300718cf478bf0749ed95', 'query':search_formatted}

paper_idx = 0
keepSeeking = True
page_num = 0
scrape_results = []

basehref = 'https://www.nature.com'

while keepSeeking:
    if page_num > 10:
        for kk in range(5):
            print('#' * 34)
        print(f'Exceeded max of {page_num-1} pages searched!')
        break

    page_num += 1

    url = f'https://www.nature.com/nature/research-articles?searchType=journalSearch&sort=PubDate&page={page_num}'
    # url = f'https://scholar.google.com/scholar?start={paper_idx}&q={search_formatted}&btnG='

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # resp = requests.get('https://api.scrapingdog.com/google_scholar', params=payload)
    # print (resp.text)

    len(soup.select(".app-article-list-row__item"))

    sections_to_read = soup.select(".app-article-list-row__item")
    if len(sections_to_read) == 0:
        keepSeeking = False
        continue

    for i, el in enumerate(sections_to_read):
        # print(f'i={i}')
        if i > 1000:
            break
        
        paper_details = {}

        ######################

                
        try:
            paper_details['title'] = el.select(".c-card__link")[0].text
        except IndexError:
            if i == 1:
                keepSeeking = False
            break
        except Exception as e:
            print(e)
            break

        paper_details['title_link'] = basehref + el.select(".c-card__link")[0]['href']
        
        authors = [span.get_text(strip=True) for span in el.select('.app-author-list')[0].select('span[itemprop="name"]')]
        for j, auth in enumerate(authors):
            if j >= len(number_words):
                break
            auth_split = auth.split(' ')
            paper_details[f'{number_words[j]}_firstname'] = auth_split[0]
            paper_details[f'{number_words[j]}_lastname'] = auth_split[-1]
            if len(authors) == 3:
                paper_details[f'{number_words[j]}_MI'] = auth_split[1]
            elif len(authors) > 3:
                print(f'{auth} has more than have more three names...')


        ########################

        paper_details = {key: value for key, value in paper_details.items() if value != '' and value is not None}
        scrape_results.append(paper_details)

        paper_idx += 1


scrape_results_df = pd.DataFrame(scrape_results)
