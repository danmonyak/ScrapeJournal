        
        try:
            paper_details['title'] = el.select(".gs_rt")[0].text
            if '[HTML][HTML] ' in paper_details['title']:
                paper_details['title'] = paper_details['title'].split('[HTML][HTML] ')[1]
        except IndexError:
            if i == 1:
                keepSeeking = False
            break
        except Exception as e:
            print(e)
            break

        paper_details['title_link'] = el.select(".gs_rt a")[0]["href"]
        paper_details['journal_link'] = el.select(".gs_a")[0].text.split(' ')[-1]

        authors = el.select(".gs_a")[0].text.split('\xa0')[0].split('…')[0].split(', ')
        for j, auth in enumerate(authors):
            # print(f'j={j}')
            if j >= len(number_words):
                break
            auth_split = auth.split(' ')
            paper_details[f'{number_words[j]}_first_initials'] = auth_split[0]
            paper_details[f'{number_words[j]}_lastname'] = auth_split[1]
