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
        corp_id_struc = await self.extract_corp_ids(char_data_list)
        alliance_id_struc = await self.extract_alliance_ids(char_data_list)
        corp_data_list_task = asyncio.create_task(self.gather_corporation_data(corp_id_struc))
        alliance_data_list_task = asyncio.create_task(self.gather_alliance_data(alliance_id_struc))
        corp_data_list = await corp_data_list_task
        alliance_data_list = await alliance_data_list_task
        data_combined = {
            'char_data_list' : char_data_list,
            'alliance_data_list' : alliance_data_list,
            'corp_data_list' : corp_data_list
        }
        return data_combined

    async def fetch_char_complete(self, name):
        data = await self.fetch_id(name)
        if 'character' in data:
            char = await self.fetch_char_data(data['character'][0])
            char['character_id'] = data['character'][0]
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
        url = 'https://esi.evetech.net/latest/'
        target = 'search/'
        params = [
            ('categories', 'character'), 
            ('datasource', 'tranquility'), 
            ('language', 'en-us'), 
            ('search', name),
            ('strict', 'true')]

        data = await self.make_request(url, target, params)
        return data

    async def make_request(self, url, target, params):
        ok_flag = False
        fail_counter = 0
        while ok_flag != True:
            #print("doing esi call for " + str(target)) #DEBUG
            async with self.session.get(url + str(target), params=params) as response:
                if response.status == 200:
                    ok_flag = True
                    return await response.json()
                else:
                    #print("FAIL Nr " + str(fail_counter) + ", code: " + str(response.status)) #DEBUG
                    fail_counter += 1

    # Make request to /characters/ endpoint using character ID, cached by character ID
    @cached(ttl=86400, cache=Cache.MEMORY, key_builder=keybuild_id)
    async def fetch_char_data(self, charID):
        params = [
            ('datasource', 'tranquility'), 
        ]
        url = 'https://esi.evetech.net/latest/characters/'
        response = await self.make_request(url, charID, params)
        return response
    
    @cached(ttl=604800, cache=Cache.MEMORY, key_builder=keybuild_alliance)
    async def fetch_alliance(self, allianceID):
        params = [
            ('datasource', 'tranquility')
        ]
        url = 'https://esi.evetech.net/latest/alliances/'
        response = await self.make_request(url, allianceID, params)
        return response

    @cached(ttl=86400, cache=Cache.MEMORY, key_builder=keybuild_corporation)
    async def fetch_corporation(self,corporationID):
        params = [
            ('datasource', 'tranquility')
        ]
        url = 'https://esi.evetech.net/latest/corporations/'
        response = await self.make_request(url, corporationID, params)
        return response

    async def extract_corp_ids(self, char_data_list):
        corp_ids = []
        corp_id_occurences = {}
        for entry in char_data_list:
            if entry.get('corporation_id') is not None:
                if entry['corporation_id'] not in corp_ids:
                    corp_ids.append(entry['corporation_id'])
                    corp_id_occurences[entry['corporation_id']] = 1
                else:
                    corp_id_occurences[entry['corporation_id']] += 1

        corp_id_struc = {"corp_ids" : corp_ids, "corp_id_occurences" : corp_id_occurences}
        return corp_id_struc

    async def extract_alliance_ids(self, char_data_list):
        alliance_ids = []
        alliance_id_occurences = {}
        for entry in char_data_list:
            if entry.get('alliance_id') is not None:
                if entry['alliance_id'] not in alliance_ids:
                    alliance_ids.append(entry['alliance_id'])
                    alliance_id_occurences[entry['alliance_id']] = 1
                else:
                    alliance_id_occurences[entry['alliance_id']] += 1

        alliance_id_struc = {"alliance_ids" : alliance_ids, "alliance_id_occurences" : alliance_id_occurences}
        return alliance_id_struc

    # Call function that fetches the alliance data from ESI, then assemble the data to include alliance_id and amount, and return it.
    async def assemble_alliance(self, alliance_id, character_count):
        print("start for alliance: " + str(alliance_id)) #DEBUG
        data = await self.fetch_alliance(alliance_id)
        data['alliance_id'] = alliance_id
        data['character_count'] = character_count
        print("end for alliance: " + str(alliance_id)) #DEBUG
        return data
        
    # create tasks to gather all alliance data and collect them, then transform to a dictionary indexed by alliance ID and return it.    
    async def gather_alliance_data(self, alliance_id_struc):
            print("start alliance data") #DEBUG
            alliance_data_dict = {}
            alliance_data_list = await asyncio.gather(*[self.assemble_alliance(entry, alliance_id_struc['alliance_id_occurences'][entry]) for entry in alliance_id_struc['alliance_ids']])
            for entry in alliance_data_list:
                alliance_data_dict[entry['alliance_id']] = entry
                
            print("end alliance data") #DEBUG
            return alliance_data_dict

    # Call function that fetches the corporation data from ESI, then assemble the data to include corp_id and amount, and return it.
    async def assemble_corporation(self, corp_id, character_count):
        print("start for corp: " + str(corp_id)) #DEBUG
        data = await self.fetch_corporation(corp_id)
        data['corp_id'] = corp_id
        data['character_count'] = character_count
        print("end for corp: " + str(corp_id)) #DEBUG
        return data
        
    # create tasks to gather all corp data and collect them, then transform to a dictionary indexed by corp ID and return it.       
    async def gather_corporation_data(self, corp_id_struc):
            print("start corp data") #DEBUG
            corp_data_dict = {}
            corp_data_list = await asyncio.gather(*[self.assemble_corporation(entry, corp_id_struc['corp_id_occurences'][entry]) for entry in corp_id_struc['corp_ids']])
            
            for entry in corp_data_list:
                corp_data_dict[entry['corp_id']] = entry

            print("end corp data") #DEBUG
            return corp_data_list

async def test():
    with open('chars.json') as f:
        chartext = json.load(f)
        f.close()

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