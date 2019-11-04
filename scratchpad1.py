import aiohttp
import asyncio
import time
import json
from aiocache import Cache
from aiocache import cached

def keybuild_search(f, selfvar, name):
    return name

def keybuild_id(f, session, charID):
    return charID

def keybuild_alliance(f, session, allianceID):
    return allianceID

def keybuild_corporation(f, session, corporationID):
    return corporationID

class ESIClient:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *excinfo):
        await self.session.close()

   
    async def fetch_all_names(self, name_list):
        char_data_list = await asyncio.gather(*[self.fetch_char_complete(name) for name in name_list])  
        return char_data_list

    async def fetch_char_complete(self, name):
        data = await self.fetch_id(name)
        if 'character' in data:
            char = await self.fetch_char_data(data['character'][0])
            return char

        else:
            char = {
                "invalid" : True,
                "name" : name
                }
            return char 

    # Make request to /search/ endpoint using character name to get character ID, cached by character name
    @cached(ttl=604800, cache=Cache.MEMORY, key_builder=keybuild_search)
    async def fetch_id(self, name):
        url = 'https://esi.evetech.net/latest/search/'
        params = [
            ('categories', 'character'), 
            ('datasource', 'tranquility'), 
            ('language', 'en-us'), 
            ('search', name),
            ('strict', 'true')]

        async with self.session.get(url, params=params) as response:
            data = await response.json()
            return data

    # Make request to /characters/ endpoint using character ID, cached by character ID
    @cached(ttl=86400, cache=Cache.MEMORY, key_builder=keybuild_id)
    async def fetch_char_data(self, charID):
        params = [
            ('datasource', 'tranquility'), 
        ]
        url = 'https://esi.evetech.net/latest/characters/'
        async with self.session.get(url + str(charID), params=params) as response:
            return await response.json()
    
    @cached(ttl=604800, cache=Cache.MEMORY, key_builder=keybuild_alliance)
    async def fetch_alliance(self, allianceID):
        params = [
            ('datasource', 'tranquility')
        ]
        url = 'https://esi.evetech.net/latest/alliances/'
        async with self.session.get(url + str(allianceID), params = params) as response:
            return await response.json()

    @cached(ttl=86400, cache=Cache.MEMORY, key_builder=keybuild_corporation)
    async def fetch_corporation(self,corporationID):
        params = [
            ('datasource', 'tranquility')
        ]
        url = 'https://esi.evetech.net/latest/corporations/'
        async with self.session.get(url + str(corporationID), params=params) as response:
            return await response.json()

    async def extract_corp_ids(self, char_data_list):
        corp_ids = []
        for entry in char_data_list:
            if entry.get('corporation_id') is not None:
                if entry['corporation_id'] not in corp_ids:
                    corp_ids.append(entry['corporation_id'])

        return corp_ids

    async def extract_alliance_ids(self, char_data_list):
        alliance_ids = []
        for entry in char_data_list:
            if entry.get('alliance_id') is not None:
                if entry['alliance_id'] not in alliance_ids:
                    alliance_ids.append(entry['alliance_id'])
            
        return alliance_ids

    async def gather_alliance_data(self, alliance_ids):
        alliance_data_dict = {}
        for entry in alliance_ids:
            data = await fetch_alliance(entry)
            alliance_data_dict[entry] = data

        return alliance_data_dict

    async def gather_corporation_data(self, corp_ids):
        corp_data_dict = {}
        for entry in corp_ids:
            data = await fetch_corporation(entry)
            corp_data_dict[entry] = data
        
        return corp_data_dict

async def test():
    with open('charssmall.json') as f:
        chartext = json.load(f)
        f.close()
    #async with ESIClient() as esiclient:
    #    data = await esiclient.fetch_all_names(chartext)
    #    return data
    esiclient = ESIClient()
    print("client created")
    data = await esiclient.fetch_all_names(chartext)
    print("data fetched")
    await esiclient.session.close()
    print("session closed")
    return data



if __name__ == "__main__":
    data = asyncio.run(test())
    print(data)
    #start = time.time()
    #data = asyncio.run(full_fetch(chartext))
    #end = time.time()
    #print(end - start)
    #start = time.time()
    #data = asyncio.run(full_fetch(chartext))
    #end = time.time()
    #print(end - start)
    #input()