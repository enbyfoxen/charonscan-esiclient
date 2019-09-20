import aiohttp
import asyncio
import time
import json
from aiocache import Cache
from aiocache import cached

with open('chars.json') as f:
    chartext = json.load(f)
    f.close()

async def fetch_charData(namelist):
    # perform the requests for IDs and character data
    async def fetch(session, url, name):
        data = await fetch_id(session, url, name)
        char = await fetch_char(session, data['character'][0])
        return char
    
    # make request to /search/ endpoint using character name to get character ID, cached by character name
    @cached(ttl=1000, cache=Cache.MEMORY, key_builder=keybuild_search)
    async def fetch_id(session, url, name):
        params = [
            ('categories', 'character'), 
            ('datasource', 'tranquility'), 
            ('language', 'en-us'), 
            ('search', name),
            ('strict', 'true')]

        async with session.get(url, params=params) as response:
            data = await response.json()
            return data

    # make request to /characters/ endpoint using character ID, cached by character ID
    @cached(ttl=1000, cache=Cache.MEMORY, key_builder=keybuild_id)
    async def fetch_char(session, charID):
        params = [
            ('datasource', 'tranquility'), 
        ]
        url = 'https://esi.evetech.net/latest/characters/'
        async with session.get(url + str(charID), params=params) as response:
            return await response.json()

    async def fetch_all(name_list):
        url = 'https://esi.evetech.net/latest/search/'
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(*[fetch(session, url, name) for name in name_list], return_exceptions=True)
            return results

    return await fetch_all(namelist)

async def full_fetch(namelist):
    data = await fetch_charData(namelist)
    return data

def keybuild_id(f, session, charID):
    return charID

def keybuild_search(f, session, url, name):
    return name

if __name__ == "__main__":
    start = time.time()
    data = asyncio.run(full_fetch(chartext))
    end = time.time()
    print(end - start)
    start = time.time()
    data = asyncio.run(full_fetch(chartext))
    end = time.time()
    print(end - start)
    input()