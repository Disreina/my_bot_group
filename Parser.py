import requests
from bs4 import BeautifulSoup

REPLACEMENT_URL = "https://mpt.ru/izmeneniya-v-raspisanii/"
TARGET_GROUP = "БИ50-3-24"  

def fetch_replacements():
    response = requests.get(REPLACEMENT_URL)
    response.raise_for_status()  
    soup = BeautifulSoup(response.text, 'html.parser')

    replacements = []

    for table in soup.find_all('table', class_='table table-striped'):
        caption = table.find('caption')
        if caption and TARGET_GROUP in caption.text:
            rows = table.find_all('tr')[1:] 
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue  

                lesson_number = cols[0].text.strip()
                replace_from = cols[1].text.strip()
                replace_to = cols[2].text.strip()
                updated_at = cols[3].text.strip()

                replacement_text = (f"Пара {lesson_number}: {replace_from} заменено на {replace_to} "
                                    f"(добавлено {updated_at})")
                replacements.append(replacement_text)

    return replacements

