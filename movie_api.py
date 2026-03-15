import requests
from config import OMDB_API

cache = {}

def search_movie(title, year=None):

    key = f"{title}_{year}"

    if key in cache:
        return cache[key]

    if year:
        url = f"http://www.omdbapi.com/?t={title}&y={year}&apikey={OMDB_API}"
    else:
        url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API}"

    res = requests.get(url, timeout=10)
    data = res.json()

    cache[key] = data

    return data
