from typing import Union

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List
import requests

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# @app.get("/")
# def read_root():
#     return {"Hello": "World"}
#

# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# @app.get("/html/{item_id}", response_class=HTMLResponse)
# async def read_item(request: Request, item_id: int, q: Union[str, None] = None):
#     return templates.TemplateResponse("item.html", {"request": request, "item_id": item_id, "q": q})


chains = {
    "injective":{
        "chain": "injective",
        "net": "injective-mainnet",
        "factoryAddress": "inj1vdu3s39dl8t5l88tyqwuhzklsx9587adv8cnn9",
        "rpcEndpoint": "https://sentry.tm.injective.network:443"
        # "rpcEndpoint": "https://injective-rpc.publicnode.com:443"
    },
    "osmosis":{
        "chain": "osmosis",
        "net": "osmosis-mainnet",
        "factoryAddress": "osmo1ssw6x553kzqher0earlkwlxasfm2stnl3ms3ma2zz4tnajxyyaaqlucd45",
        "rpcEndpoint": "https://rpc.osmosis.zone"
    },
    "sei":{
        "chain": "sei",
        "net": "sei-mainnet",
        "factoryAddress": "sei18rdj3asllguwr6lnyu2sw8p8nut0shuj3sme27ndvvw4gakjnjqqper95h",
        "rpcEndpoint": "https://rpc.wallet.pacific-1.sei.io"
    }
}


@app.get("/fund", response_class=HTMLResponse)
def get_json_data(request: Request, doll: int=100):
    data = []
    for i, chain in chains.items():
        url = f"https://querier-mainnet.levana.finance/v1/perps/markets?network={chain['net']}&factory={chain['factoryAddress']}"
        print (url)

        try:
            response = requests.get(url)
            response.raise_for_status()  # Проверяем статус ответа
            json_data = response.json()
            for market in json_data["markets"]:

                chain_name = chain['chain']
                market_id = market["status"]["market_id"]
                long_funding = round(float(market["status"]["long_funding"]) * 100)
                short_funding = round(float(market["status"]["short_funding"]) * 100)
                long_usd = round(float(market["status"]["long_usd"]))
                short_usd = round(float(market["status"]["short_usd"]))
                status = market["status"]

                lev = 1
                fee_delta = 0
                fee_trade = 0.10 / 100 * doll
                fee_crank = 0.20
                short100 = - float(status["long_funding"]) * float(status["long_usd"]) / (float(status["short_usd"]) * 1 + doll)
                if (float(status["long_funding"]) == 0):
                    short100 = - 0.90 * float(status["long_usd"]) / (float(status["short_usd"]) * 1 + doll)
                # short100 = - 0.90 * float(status["long_usd"]) / (float(status["short_usd"]) * 1 + doll)
                short = short100

                h1 = round((- doll * lev * short / 365) * 1 / 24 - fee_crank - fee_trade, 2)
                h3 = round((- doll * lev * short / 365) * 3 / 24 - fee_crank - fee_trade, 2)
                h6 = round((- doll * lev * short / 365) * 6 / 24 - fee_crank - fee_trade, 2)
                h12 = round((- doll * lev * short / 365) * 12 / 24 - fee_crank - fee_trade, 2)
                day1 = round((- doll * lev * short / 365 - fee_crank) * 1 - fee_trade, 2)
                day7 = round((- doll * lev * short / 365 - fee_crank) * 7 - fee_trade, 2)
                day30 = round((- doll * lev * short / 365 - fee_crank) * 30 - fee_trade, 2)
                per1 = round(day1 / doll * 365 * 100)
                per7 = round(day7 / doll * 365 / 7 * 100)
                per30 = round(day30 / doll * 365 / 30 * 100)

                data.append((chain_name, market_id, long_funding, short_funding, long_usd, short_usd,
                             round(short100 * 100),
                             h1, h3, h6, h12,
                             day1, day7, day30,
                             per1, per7, per30 ))

        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch JSON data: {e}")

    data = sorted(data, key=lambda x: x[6], reverse=False)

    print (data)

    return templates.TemplateResponse("item.html", {"request": request, "data": data, "doll": doll})
