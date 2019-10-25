import aiohttp
import asyncio
import time
import json
from aiocache import Cache
from aiocache import cached

with open('charssmall.json') as f:
    chartext = json.load(f)
    f.close()

async def fetch_charData(namelist):
    # Perform the requests for IDs and character data
    async def fetch(session, url, name):
        data = await fetch_id(session, url, name)
        if 'character' in data:
            char = await fetch_char(session, data['character'][0])
            return char

        else:
            char = {
                "invalid" : True,
                "name" : name
                }
            return char
    
    # Make request to /search/ endpoint using character name to get character ID, cached by character name
    @cached(ttl=604800, cache=Cache.MEMORY, key_builder=keybuild_search)
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

    # Make request to /characters/ endpoint using character ID, cached by character ID
    @cached(ttl=86400, cache=Cache.MEMORY, key_builder=keybuild_id)
    async def fetch_char(session, charID):
        params = [
            ('datasource', 'tranquility'), 
        ]
        url = 'https://esi.evetech.net/latest/characters/'
        async with session.get(url + str(charID), params=params) as response:
            return await response.json()

    @cached(ttl=604800, cache=Cache.MEMORY, key_builder=keybuild_alliance)
    async def fetch_alliance(session, allianceID):
        params = [
            ('datasource', 'tranquility')
        ]
        url = 'https://esi.evetech.net/latest/alliances/'
        async with session.get(url + str(allianceID), params=params) as response:
            return await response.json()
    
    @cached(ttl=86400, cache=Cache.MEMORY, key_builder=keybuild_corporation)
    async def fetch_corporation(session, corporationID):
        params = [
            ('datasource', 'tranquility')
        ]
        url = 'https://esi.evetech.net/latest/corporations/'
        async with session.get(url + str(corporationID), params=params) as response:
            return await response.json()

    async def fetch_all(name_list):
        url = 'https://esi.evetech.net/latest/search/'
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(*[fetch(session, url, name) for name in name_list])
            return results

    async def extract_corp_ids(char_data_list):
        corp_ids = []
        for entry in char_data_list:
            if entry.get('corporation_id') is not None:
                if entry['corporation_id'] not in corp_ids:
                    corp_ids.append(entry['corporation_id'])

        return corp_ids
    
    async def extract_alliance_ids(char_data_list):
        alliance_ids = []
        for entry in char_data_list:
            if entry.get('alliance_id') is not None:
                if entry['alliance_id'] not in alliance_ids:
                    alliance_ids.append(entry['alliance_id'])
            
        return alliance_ids
    
    async def gather_alliance_data(alliance_ids):
        for entry in alliance_ids:

                
    char_data_list = await fetch_all(namelist)
    corp_ids = await extract_corp_ids(char_data_list)
    alliance_ids = await extract_alliance_ids(char_data_list)
    print(alliance_ids)
    print(corp_ids)
    return await fetch_all(namelist)
    
async def full_fetch(namelist):
    data = await fetch_charData(namelist)
    return data

def keybuild_id(f, session, charID):
    return charID

def keybuild_search(f, session, url, name):
    return name

def keybuild_alliance(f, session, allianceID):
    return allianceID

def keybuild_corporation(f, session, corporationID):
    return corporationID

if __name__ == "__main__":
    data = asyncio.run(full_fetch(chartext))
    #print(data)
    #start = time.time()
    #data = asyncio.run(full_fetch(chartext))
    #end = time.time()
    #print(end - start)
    #start = time.time()
    #data = asyncio.run(full_fetch(chartext))
    #end = time.time()
    #print(end - start)
    #input()