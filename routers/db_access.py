from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd

router = APIRouter(prefix="/db", tags=["scripts"],)
templates = Jinja2Templates(directory="templates")

@router.get("/transactions/{credit_card}/{format_type}/")
async def get_transactions(request: Request, credit_card: str, format_type:str): #read from the database
    df = pd.read_csv("data/transactions.csv")
    df = df[df["Credit Card ID"]==credit_card]
    if format_type == 'html':
        return Response(content=df.to_html(index=False, classes="table table-striped", escape=False), media_type="text/html")
    else:
        return Response(content=df.to_json(orient="records"), media_type="application/json")

@router.get("/")
async def render_editable_csv(request: Request):
    return "db hello world"