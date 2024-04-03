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
def get_json_data(request: Request, doll: int=1000, step: int=50):
    data = []
    data_opt = []
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
                long_funding = float(market["status"]["long_funding"])
                short_funding = float(market["status"]["short_funding"])
                long_usd = float(market["status"]["long_usd"])
                short_usd = float(market["status"]["short_usd"])
                status = market["status"]

                lev = 1
                fee_delta = 0
                fee_trade = 0.10 / 100 * doll
                fee_crank = 0.20
                funding_rate_max_annualized = float(status["config"]["funding_rate_max_annualized"])
                # short100_funding_rate_max_annualized = funding_rate_max_annualized * float(status["long_usd"]) / (float(status["long_usd"]) + float(status["short_usd"]) + doll)
                # if(short100_funding_rate_max_annualized > funding_rate_max_annualized):
                #     short100_funding_rate_max_annualized = funding_rate_max_annualized
                # short100 = - short100_funding_rate_max_annualized * float(status["long_usd"]) / (float(status["short_usd"]) * 1 + doll)
                # if (float(status["long_funding"]) == 0):
                #     short100 = - funding_rate_max_annualized * float(status["long_usd"]) / (float(status["short_usd"]) * 1 + doll)

                short100 = short_plus_doll(funding_rate_max_annualized, long_usd, short_usd, doll)
                print (short100)
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

                data.append((chain_name, market_id, round(long_funding * 100), round(short_funding * 100), round(long_usd), round(short_usd),
                             round(short100 * 100),
                             h1, h3, h6, h12,
                             day1, day7, day30,
                             per1, per7, per30 ))
                data_opt.append((chain_name, market_id, funding_rate_max_annualized, long_funding, short_funding, long_usd, short_usd, 0, 0, 0, 0))

        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch JSON data: {e}")

    data = sorted(data, key=lambda x: x[6], reverse=False)

    # print (data)
    # print (data_opt)
    data_opt = opt_doll(data_opt, total_step=doll, step=step)
    data_opt = sorted(data_opt, key=lambda x: x[9], reverse=False)
    for i in range(len(data_opt)):
        data_opt[i] = (data_opt[i][:2] + (round(data_opt[i][2]*100),)+ (round(data_opt[i][3]*100),) + (round(data_opt[i][4]*100),) + (round(data_opt[i][5]),) + (round(data_opt[i][6]),) + (round(data_opt[i][7]),) + (round(data_opt[i][8]),) + (round(data_opt[i][9]*100),))
        # print (data_opt[i][3])


    # print (data_opt)



    return templates.TemplateResponse("item.html", {"request": request, "data": data, "data_opt": data_opt, "doll": doll, "step": step})

def short_plus_doll(funding_rate_max_annualized, long_usd, short_usd, doll):
    # print (funding_rate_max_annualized, long_usd, short_usd, doll)
    # funding_rate_max_annualized = float(status["config"]["funding_rate_max_annualized"])
    short100_funding_rate_max_annualized = funding_rate_max_annualized * long_usd / (
                long_usd + short_usd + doll)
    if (short100_funding_rate_max_annualized > funding_rate_max_annualized):
        short100_funding_rate_max_annualized = funding_rate_max_annualized
    short_plus_doll = - short100_funding_rate_max_annualized * long_usd / (short_usd + doll)
    if (short_usd == 0):
        short_plus_doll = - funding_rate_max_annualized * long_usd / (short_usd + doll)
    return short_plus_doll

def opt_doll(data_opt, total_step=100, step=5 ):
    # step = 5
    # total_step = 100
    # data_opt.append((chain_name, market_id, funding_rate_max_annualized, long_funding, short_funding, long_usd,
    #                  short_usd, short_funding_sum_total, short_funding_step, short_funding_pers))
    # data_opt.append((chain_name, market_id, funding_rate_max_annualized, long_funding, short_funding, long_usd,
    #                  short_usd, 7 short_funding_sum_total, 8 short_funding_step, 9 short_funding_pers))
    for s in range(int(total_step/step)):
    # for s in range(int(2)):
        # Шаг 1: Увеличить значение short_funding_step для всех строк на step
        for i in range(len(data_opt)):
            data_opt[i] = data_opt[i][:8] + (data_opt[i][8] + step,) + data_opt[i][9:]

        # Шаг 2: Посчитать значение short_funding_pers для всех строк
        # def func_abc():
        #     # Реализуйте вашу функцию func_abc здесь
        #     pass

        for i in range(len(data_opt)):
            data_opt[i] = data_opt[i][:9] + (short_plus_doll(data_opt[i][2], data_opt[i][5], data_opt[i][6], data_opt[i][8] ),) + data_opt[i][10:]
            # print (short_plus_doll(data_opt[i][2], data_opt[i][5], data_opt[i][5], data_opt[i][8] ))

        # Шаг 3: Найти максимальное значение short_funding_pers
        max_pers = min(data_opt, key=lambda x: x[9])[9]

        # Шаг 4: Добавить значение short_funding_sum_total для строки с максимальным значением short_funding_pers
        for i in range(len(data_opt)):
            if data_opt[i][9] == max_pers:
                # data_opt[i] = data_opt[i][:7] + (data_opt[i][7] + step,) + data_opt[i][8:9] + (data_opt[i][9] + step,) + \
                #               data_opt[i][10:]
                data_opt[i] = data_opt[i][:7] + (data_opt[i][7] + step,) + data_opt[i][8:]

        # Шаг 5: Присвоить всем строкам значение short_funding_step равное short_funding_sum_total
        for i in range(len(data_opt)):
            data_opt[i] = data_opt[i][:8] + (data_opt[i][7],) + data_opt[i][9:]


    return data_opt