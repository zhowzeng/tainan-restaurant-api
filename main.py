from functools import lru_cache
from io import StringIO

import pandas as pd
import yaml
import json
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

deploy_url = "https://vast-everglades-41844-ba40e8a9c606.herokuapp.com"

app = FastAPI(
    title="Tainan Restaurant API",
    servers=[
        {"url": deploy_url, "description": "Production server"},
        {"url": "/", "description": "Local test server"},
    ],
)

origins = [
    "http://localhost",
    "https://prod.dvcbot.net",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

df = pd.DataFrame(json.load(open("tainan_restaurant.json", encoding="utf-8-sig")))
df = df[["name", "district", "summary", "introduction", "open_time", "address"]]


@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
@lru_cache()
def read_ai_plugin():
    return {
        "id": "tainan_restaurant",
        "schema_version": "v1",
        "name_for_human": "台南餐飲",
        "name_for_model": "tainan_restaurant",
        "description_for_human": "Tainan Restaurant API",
        "description_for_model": "當你需要查詢台南地區餐飲資料時, 請使用本API, 本API能夠隨機推薦地區餐飲或是查詢特定店家地址、介紹、與營業時間",
        "api": {
            "type": "openapi",
            "url": f"{deploy_url}/.well-known/openapi.yaml",
        },
    }


@app.get("/.well-known/openapi.yaml", include_in_schema=False)
@lru_cache()
def read_openapi_yaml() -> Response:
    openapi_json = app.openapi()
    yaml_string = StringIO()
    yaml.dump(openapi_json, yaml_string, sort_keys=False)
    return Response(yaml_string.getvalue(), media_type="text/yaml")


@app.get(
    "/random_restaurant/{district}",
    description="輸入行政區與數量，隨機回傳該數量的餐廳資訊",
)
def get_random_restaurant_by_district(district: str, number: bool):
    if district not in df["district"].unique():
        return {"message": "台南不存在此行政區"}
    return df[df["district"] == district].sample(number).to_dict(orient="records")


@app.get("/restaurant/{name}", description="輸入店名，回傳店家資訊")
def get_restaurant_info_by_name(name: str):
    if name not in df["name"].unique():
        return {"message": "資料庫無此店家"}
    return df[df["name"] == name].to_dict(orient="records")
