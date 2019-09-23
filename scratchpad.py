from aiohttp import web
import regex
import json
import esiclient

### regex patterns ###
# Pattern to check if possible EVE username
regex_localscan = regex.compile(r"^([A-Za-z0-9\-' ]{3,37})$")
### regex pattersn end ###

routes = web.RouteTableDef()

@routes.post('/local')
async def post(request):
    if request.headers['Content-Type'] != 'application/json':
        return web.Response(text="Wrong Content-Type, JSON required\n", status=415)
    
    json = await request.json()
    await esi
    
# This parses the loca string into a list of string.
# It returns none if there are invalid entries in the list, as that means malformed user input.
async def parse_local(local_string):
    local_list = local_string.splitlines()
    match_list = []
    for entry in local_list:
        match = regex.match(regex_localscan, entry)
        if match.__len__() != 0:
            match_list.append(match)

    if match_list.__len__() < local_list.__len__():
        return None
    else:
        return match_list

app = web.Application()
app.add_routes(routes)
web.run_app(app, path='/tmp/server.sock')