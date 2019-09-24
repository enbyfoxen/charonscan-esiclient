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
    
    # Return 422 unprocessable entity if the json payload is missing the key 'string'
    jsondat = await request.json()
    if 'string' not in jsondat:
        return web.Response(text="JSON data error, 'string' key missing from object\n", status=422)

    # Return 422 unprocessable entity if the json payload contains invalid characters or lines of invalid length.
    # Add 'string-invalid' header as true for easier client side reading
    parsed = await parse_local(jsondat['string'])
    if parsed == None:
        resp = web.Response(text="String invalid, the provided string contains data that cannot possibly be EVE Character names\n", status=422)
        resp.headers['string-invalid'] = 'true'
        return resp

    data = await esiclient.full_fetch(parsed)
    resp = web.json_response(data)
    resp.headers['string-invalid'] = 'false'
    return resp


# This parses the local  string into a list of string.
# It returns none if there are invalid entries in the list, as that means malformed user input.
async def parse_local(local_string):
    local_list = local_string.splitlines()
    match_list = []
    for entry in local_list:
        match = regex.match(regex_localscan, entry)
        if match != None:
            match_list.append(match.group(0))

    if match_list.__len__() < local_list.__len__():
        return None
    else:
        return match_list

app = web.Application()
app.add_routes(routes)
web.run_app(app, path='/tmp/esiclient.sock')