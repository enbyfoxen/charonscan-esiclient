import aiohttp
import asyncio
import time

async def fetchIDs(namelist):    
    async def fetch(session, url, name):
        params = [
            ('categories', 'character'), 
            ('datasource', 'tranquility'), 
            ('language', 'en-us'), 
            ('search', name),
            ('strict', 'true')]

        async with session.get(url, params=params) as response:
            data = await response.json()
            return {"name":name, "charID": data['character'][0]}

    async def fetch_all(name_list):
        url = 'https://esi.evetech.net/latest/search/'
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(*[fetch(session, url, name) for name in name_list], return_exceptions=True)
            return results

    return await fetch_all(namelist)

async def fetch_charData(charID_list):    
    async def fetch(session, charID):
        params = [
            ('datasource', 'tranquility'), 
        ]
        url = 'https://esi.evetech.net/latest/characters/'
        async with session.get(url + str(charID), params=params) as response:
            return await response.json()

    async def fetch_all(charID_list):
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(*[fetch(session, entry['charID']) for entry in charID_list], return_exceptions=True)
            return results

    return await fetch_all(charID_list)

async def full_fetch(namelist):
    ids = await fetchIDs(namelist)
    data = await fetch_charData(ids)
    return data

if __name__ == "__main__":
    names = ['Elena Amarin', 'Ilian Amarin', 'Arden Amarin']
    start = time.time()
    data = asyncio.run(full_fetch(names))
    end = time.time()
    print(data)
    print(end - start)