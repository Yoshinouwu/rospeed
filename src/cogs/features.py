import requests
import numpy as np
import orjson as json
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import RequestException

roblox_cookie = {"ROBLOSECURITY":"_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_E454E1C1B245913064EABA60188D44852E803BEC3EBA6D8A57243EEEA6E06074A4D4751433F24A1B950F86E22043EC27D832130AFEB09D0FF97A598A94EC7922D12236E26B8637CA681835C59FFBDFF992865A392862E4F7B0ED6BE20270394321B7F6D1D8F9CC2500FB6997BF020E86B7BE4111AC56B119961B8EF16223F07C7F854850BECAFF839C1478A4CC970C6052FA18A7AFF4D80484321A4102B53D46F0FA26C30E6F4FCD5BA60C9C5305D17E385D60CB8CB565D23B9FD0CFB5BD1951D5B8FD685B772455CA2E784F2789FA181B7FF05DDF27D7EEBD681DF8E18EBAF677F6B62B70BAABB494ADB78CC309775D663ED6927A31A9F0819A5C7963532FA505B3085E766C74515F05B5F91BFB42D655953253BA594CD17DB2F6E9D5115F6D2184B88EF9EB3E098FCD05B84F799C26E4A841F8BB99DE4FE2CB88D92539229374D050DF945BE578AA6D120F61094335289260F987469BD0797FF722DCB6D7C60AF09E68A0A142ECEB431F336B06CEEDE720BFC6EE8697F0EFE1A131B82072EE54ABFE934E9DE24CBAA8437B6E2658A968CE0E39D1DD7E742843FC55CCF3DA7F8BC39F9ECAFE2282193F2408D3F4A65860674BB7E7312C593DB8294B6EC42118E374B20A1A30BE2A83BA343D054A665C175B344590052FC8B25F36A56AFC1EBBA96FEE78"}

def retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    """
    retry session function that retries a request in case of connection errors or status codes
    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_page(url):
    try:
        response = retry_session().get(url)
        check = response.json()
        if "data" in check:
            clothings = np.array(check['data'])
        else:
            clothings = np.array([])

        if "nextPageCursor" in check and check['nextPageCursor']:
            return clothings, check['nextPageCursor']
        else:
            return clothings, ""
    except RequestException as e:
        print(f"Error requesting page {url}: {e}")
        return np.array([]), ""

def fclothings(id):
    clothings = 0
    cursor = None


    url = f"https://catalog.roblox.com/v1/search/items/details?Category=3&CreatorTargetId={id}&CreatorType=2&Limit=30"
    clothings_data, cursor = get_page(url)
    clothings += len(clothings_data)


    while cursor:
        urls = [
            f"https://catalog.roblox.com/v1/search/items/details?Category=3&CreatorTargetId={id}&CreatorType=2&Limit=30&cursor={cursor}" for _ in range(10)
        ]
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(get_page, urls))

        for result in results:
            clothings_data, cursor = result
            clothings += len(clothings_data)

    return clothings

def frobux(id):
    global roblox_cookie
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        session = requests.Session()
        session.mount('https://', HTTPAdapter(max_retries=retries))
        try:
            future = executor.submit(session.get, f'https://economy.roblox.com/v1/groups/{id}/currency', cookies=roblox_cookie, timeout=5)
        except RequestException as e:
            print(e)
            return 0
        
        try:
            response = future.result()
            data = json.loads(response.text)
            if "robux" in data:
                robux = data.get("robux", 0)
            else:
                robux = 0
        except RequestException as e:
            print(e)
            return 0
    
    return robux

def fgamevisits(id):
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=retries))

    with ThreadPoolExecutor(max_workers=10) as executor:
        future = executor.submit(session.get, f'https://games.roblox.com/v2/groups/{id}/games?accessFilter=All&sortOrder=Asc&limit=100', timeout=5)

        try:
            response = future.result()
            os = response.json()
            if "data" in os:
                data = os["data"]
            else:
                data = 0

        except requests.exceptions.RequestException as e:
            print(e)
            return 0

    if not data:
        return 0

    visits = np.array([game["placeVisits"] for game in data])
    total_visits = np.sum(visits)
    
    return total_visits
