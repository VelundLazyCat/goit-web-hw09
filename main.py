import requests
from bs4 import BeautifulSoup
import json
from mongoengine.errors import NotUniqueError
from models import Author, Quote
import connect_mongo


BASE_URL = 'http://quotes.toscrape.com'


def get_page_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        content = BeautifulSoup(response.content, 'html.parser')
        return content


def get_quotes(content):
    quote_list = []
    quotes = content.find_all('span', class_='text')
    authors = content.find_all('small', class_='author')
    tags = content.find_all('div', class_='tags')
    for i in range(len(quotes)):
        tagsforquote = tags[i].find_all('a', class_='tag')
        quote = {'tags': [t.text for t in tagsforquote],
                 'author': authors[i].text,
                 'quote': quotes[i].text.strip()}
        quote_list.append(quote)
    return quote_list


def get_next_page_url(content):
    next_page_link = content.find('li', class_='next')
    if next_page_link is None:
        return None
    return next_page_link.find('a')['href']


def get_author_list(content, autors_list=[]):
    authors = content.find_all('div', class_='quote')
    for a in authors:
        if a.find('a')['href'] not in autors_list:
            autors_list.append(a.find('a')['href'])
    return autors_list


def get_autor_info(autors_list):
    result = []
    for url in autors_list:
        content = get_page_content(BASE_URL+url)
        result.append({'fullname': content.find('h3', class_='author-title').text,
                       'born_date': content.find_all('span', class_='author-born-date')[0].text,
                       'born_location': content.find('span', class_='author-born-location').text,
                       'description': content.find('div', class_='author-description').text.strip()})
    return result


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f)


def make_json_collections(base_url):
    quotes = []
    authors = []
    url = ''
    while True:
        content = get_page_content(base_url+url)
        quotes.extend(get_quotes(content))
        authors = get_author_list(content, authors)
        url = get_next_page_url(content)
        if not url:
            break
    authors = get_autor_info(authors)
    save_to_json(quotes, 'quotes.json')
    save_to_json(authors, 'authors.json')


def seed_authors():
    with open('authors.json', encoding='utf-8') as fd:
        data = json.load(fd)
        for el in data:
            try:
                author = Author(fullname=el.get('fullname'), born_date=el.get('born_date'),
                                born_location=el.get('born_location'), description=el.get('description'))
                author.save()
            except NotUniqueError:
                print(f"Автор вже існує {el.get('fullname')}")


def seed_quotes():
    with open('quotes.json', encoding='utf-8') as fd:
        data = json.load(fd)
        for el in data:
            try:
                author, *_ = Author.objects(fullname=el.get('author'))
                quote = Quote(quote=el.get('quote'),
                              tags=el.get('tags'), author=author)
                quote.save()
            except NotUniqueError:
                print(f"Цитата вже існує {el.get('quote')}")


if __name__ == '__main__':
    make_json_collections(BASE_URL)
    seed_authors()
    seed_quotes()
