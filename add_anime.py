import re
from main import DatabaseManager
from bs4 import BeautifulSoup
from requests import get


if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
    }

    url = input('url: ')
    response = get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # === Постер ===
    poster_img = soup.find('div', class_='b-db_entry-poster').find('img')
    name_anime = poster_img.get('alt')
    img_anime_http = poster_img.get('src')

    # === Эпизоды ===
    key_label = soup.find('div', class_='key', string='Эпизоды:')
    line_block = key_label.find_parent('div', class_='line')
    some_apizod = int(line_block.find('div', class_='value').text.strip())

    # === Жанры ===
    genre_label = soup.find('div', class_='key', string='Жанры:')
    genre_value_block = genre_label.find_next('div', class_='value')
    genres = [tag.text for tag in genre_value_block.find_all('span', class_='genre-ru')]

    # === Год ===
    status_label = soup.find('div', class_='key', string='Статус:')
    release_year = None
    if status_label:
        match = re.search(r'\b(\d{4})\b', status_label.find_next('div', class_='value').text)
        if match:
            release_year = int(match.group(1))

    # === Проверка ===
    print(name_anime)
    print(type(get(img_anime_http).content))
    print(some_apizod)
    print(genres)

    # === Внесение изменений в бд ===
    bd = DatabaseManager()
    # bd.add_film(name_anime, )
    # bd.update_film_poster


