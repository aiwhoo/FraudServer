from fastapi import APIRouter, Request, Form, Response,  HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import uuid
from pydantic import BaseModel,Field, constr, UUID4
from datetime import datetime, date
import os
import csv 
import utils
router = APIRouter(prefix="/db", tags=["scripts"],)
templates = Jinja2Templates(directory="templates")
data_sources = ["fraud", "bank", "credit_card", "demographic", "transaction"]

@router.get("/{secret_id}")
@utils.check_secret_password(secret_id="password")
async def root(request: Request,secret_id: str): #read from the database
    content_html = ""
    for adb in data_sources:
        adb_df = get_adb(adb)

        content_html += "<a href='/db/submit/" + adb + "/password'>" + adb + "</a>" + "<br>\n"
        content_html += adb_df.to_html(index=False, classes="table table-striped", escape=False)
        content_html += "<br>\n"
    return Response(content=content_html, media_type="text/html")

def format_response(df, format_type='html'):
    if format_type == 'html':
        return Response(content=df.to_html(index=False, classes="table table-striped", escape=False), media_type="text/html")
    else:
        return Response(content=df.to_json(orient="records"), media_type="application/json")

@router.post("/transactions/")
#@utils.auth_required(role="all")
async def create_transaction(request: Request):
    df, form_data = await create_adb_entry(request, "transaction")
    df = df[df['credit_card_id'] == form_data["credit_card_id"]] # check for distinct value only
    return format_response(df, format_type="html")

@router.get("/show/transaction/{credit_card_id}/{format_type}")
async def get_transactions(request: Request, credit_card_id: str, format_type:str): #read from the database
    print("^^^accessed get transactions funciton")
    df = get_adb( "transaction")
    if len(df) > 0:
        df = df[df["credit_card_id"] == credit_card_id]
    return format_response(df, format_type)

def get_adb(adb: str):
    csv_file = os.path.join("data", adb + ".csv")
    df = pd.read_csv(csv_file) if os.path.isfile(csv_file) and os.path.getsize(csv_file) > 0 else pd.DataFrame()
    return df

def create_csv_file(adb, form_data, distinct=False, key=None):
    csv_file = os.path.join("data", adb + ".csv")
    existing_df = get_adb(adb)
    print(form_data)
    new_df = pd.DataFrame([form_data], index=[form_data[adb + "_id"]])
    df = pd.concat([existing_df, new_df], ignore_index=True)
    df.to_csv(csv_file, index=False)
    return df

async def create_adb_entry(request, adb):
    form_data = dict(await request.form())
    current_datetime = datetime.now()
    date = str(current_datetime.date())  # Extract the date component
    time = str(current_datetime.time())
    form_data["date"] = date
    form_data["time"] = time
    form_data[adb+ "_id"] = str(uuid.uuid4())
    df = create_csv_file(adb, form_data)
    return df, form_data

@router.post("/{adb}/{secret_id}")
async def insert_adb_entry(request: Request, adb: str):
    df, _ = await create_adb_entry(request, adb)
    return format_response(df)

@router.get("/submit/{adb}/{secret_id}")
@utils.check_secret_password(secret_id="password", exceptions=["transaction"])
async def check_db(request: Request, adb: str, secret_id : str):
    assert adb in data_sources
    return templates.TemplateResponse(adb + ".html.j2", {"request": request})

@router.get("/list/{adb}/{secret_id}/{format_type}")
@utils.check_secret_password(secret_id="password", exceptions=["transaction"])
async def get_adb_data(request: Request, adb:str, secret_id: str, format_type:str): #read from the database
    if not adb in data_sources:
        return adb + " needs to be in " + str(data_sources)
    df = get_adb(adb)
    return format_response(df, format_type)
