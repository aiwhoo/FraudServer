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


#password = "password"

# bank network
class Network(BaseModel):
    bank_id: str
    date: str


# transaction Schema
class Transaction(BaseModel):
    transaction_id : UUID4
    date: str 
    time: str
    credit_card_id: str
    zip_code: str
    vendor_name: str
    amount: float

# Schema for credit card
class CreditCard(BaseModel):
    customer_id : str 
    credit_card_id: str
    transaction_id : str

#Schema for Customer
class Customer(BaseModel):
    customer_id : str
    credit_card_id: str
    credit_card_list : int
    amount : float

#Schema for Fradulent transaction
class Fraud(BaseModel):
    credit_card_id: str
    transaction_id : str
    issuer : str

#Schema for bank 
class Bank(BaseModel):
    bank_id : str
    customer_id: str 
    credit_card_id: str


def search_df(df, item_id, index): #search df
    if item_id in df[index].values:
        return True
    else:
        return False

def format_response(df, format_type):
    if format_type == 'html':
        return Response(content=df.to_html(index=False, classes="table table-striped", escape=False), media_type="text/html")
    else:
        return Response(content=df.to_json(orient="records"), media_type="application/json")

def create_csv_file(csv_file, base, distinct=False, key=None):
    existing_df = pd.read_csv(csv_file) if os.path.isfile(csv_file) and os.path.getsize(csv_file) > 0 else pd.DataFrame()
    # Create a DataFrame from the new transaction data  
    new_df = pd.DataFrame([base.model_dump()])

    # Concatenate existing data with new data or use new data directly
    df = pd.concat([existing_df, new_df], ignore_index=True)
    df.to_csv(csv_file, index=False)

    #return format_response(df, format_type='html')
    return df



@router.get("/transactions/")
async def transaction_form(request: Request):
  return templates.TemplateResponse("transaction.html.j2", {"request": request})


@router.post("/transactions/")
#@utils.auth_required(role="all")
async def create_transaction(
    credit_card_id: str = Form(...),
    zip_code: str = Form(...),
    vendor_name: str = Form(...),
    amount: float = Form(...),
):
    current_datetime = datetime.now()
    date = str(current_datetime.date())  # Extract the date component
    time = str(current_datetime.time())  # Extract the time component
    transaction_id = uuid.uuid4()
   
    transaction = Transaction(
        transaction_id=transaction_id,
        date = date, time = time,credit_card_id=credit_card_id,
        zip_code=zip_code,
        vendor_name=vendor_name, 
        amount=amount)
    
    csv_file = "data/transactions.csv"
    df = create_csv_file(csv_file, transaction)
    df = df[df['credit_card_id'] == credit_card_id] # check for distinct value only
       
    return format_response(df, format_type="html")




@router.get("/transactions/{credit_card_id}/{format_type}/")
#@utils.auth_required(role="all")

async def get_transactions(request: Request, credit_card_id: str, format_type:str): #read from the database
    #print(utils.get_user_information(request))
    print("^^^accessed get transactions funciton")
    df = pd.read_csv("data/transactions.csv", dtype={"credit_card_id": str})
    df = df[df["credit_card_id"] == credit_card_id]
    return format_response(df, format_type)


  
@router.get("/customer/{secret_id}")
@utils.check_secret_password(secret_id="password")
async def get_customer_info( request: Request, secret_id : str ):
    
    return templates.TemplateResponse("customer.html.j2", {"request": request})
    

@router.post("/customer/{secret_id}")
async def insert_customer_info(
    request:Request,
    customer_id: str = Form(...),
    credit_card_id: str = Form(...),
    amount: float = Form(...)
):
    

    csv_file = "data/customer.csv"

    # ---------------- To DO ----
    # create a list of credit cards based on the customer id 
    # count the number of cards that customer has length of the list and then add it to the credit card list.

    
    
    customer = Customer(customer_id=customer_id, credit_card_id= credit_card_id, amount = amount)
    
    return create_csv_file(csv_file, customer)




# create a bank network of banks
@router.get("/network/{secret_id}")
#@utils.auth_required(role="faculty")
@utils.check_secret_password(secret_id="password")
async def get_network_info(request: Request, secret_id = str ):
    return templates.TemplateResponse("network.html.j2", {"request": request})


@router.post("/network/{secret_id}")
async def create_network(bank_id: str = Form(...)):

    current_datetime = datetime.now()
    date = str(current_datetime.date())  # Extract the date component
    network = Network(bank_id=bank_id, date=date)


    csv_file = "data/network.csv" 

    if os.path.isfile(csv_file):
        df = pd.read_csv(csv_file)
        filtered_df =  df[df['bank_id'] == bank_id]
        if filtered_df.empty: # check for distinct value only
            df = create_csv_file(csv_file, network)
        else:
            return "Bank ID exists"

    else:
        df = create_csv_file(csv_file, network)

    return format_response(df, format_type="html")


#using @utils.check_secret_password is the better way to use password.

@router.get("/bank/{secret_id}/")
#@utils.auth_required(role="faculty")
@utils.check_secret_password(secret_id="password")
async def create_bank(request: Request, secret_id : str ):
    return templates.TemplateResponse("bank.html.j2", {"request": request})

@router.post("/bank/{secret_id}/")
async def create_bank_customer(request: Request, 
    bank_id: str = Form(...),                           
    customer_id: str = Form(...),
    credit_card_id: str = Form(...),
  
):
    bank = Bank(bank_id=bank_id, customer_id=customer_id, credit_card_id=credit_card_id)
    csv_file = "data/bank.csv"
    
    df = create_csv_file(csv_file, bank)

    return df



@router.get("/fraud/{secret_id}/")
@utils.check_secret_password(secret_id="password")
async def fraud_transaction(request: Request, secret_id : str):
    return templates.TemplateResponse("fraud.html.j2", {"request": request})
    
