from fastapi import APIRouter, Request, Form, Response,  HTTPException
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



password = "password"

# bank network
class Network(BaseModel):
    bank_id: str


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
    credit_card_list : list[str]
    transaction_id_list : int
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
    customer_id_list : list[str]


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



@router.get("/transactions/")
async def transaction_form(request: Request):
  return templates.TemplateResponse("transaction.html.j2", {"request": request})


@router.post("/transactions/")
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
   
    transaction = Transaction(transaction_id=transaction_id, date = date, time = time,credit_card_id=credit_card_id, zip_code=zip_code, vendor_name=vendor_name, amount=amount)

    csv_file = "data/transactions.csv"

     # Check if the CSV file exists and is not empty
    existing_df = pd.read_csv(csv_file) if os.path.isfile(csv_file) and os.path.getsize(csv_file) > 0 else pd.DataFrame()

    # Create a DataFrame from the new transaction data  
    new_df = pd.DataFrame([transaction.dict()])

    # Concatenate existing data with new data or use new data directly
    df = pd.concat([existing_df, new_df], ignore_index=True)
    df.to_csv(csv_file, index=False)

    return format_response(df, format_type='html')




@router.get("/transactions/{credit_card_id}/{format_type}/")
@utils.auth_required(role="all")
async def get_transactions(request: Request, credit_card_id: str, format_type:str): #read from the database
    print(utils.get_user_information(request))
    print("^^^accessed get transactions funciton")
    df = pd.read_csv("data/transactions.csv", dtype={"Credit Card ID": str})
    df = df[df["Credit Card ID"] == credit_card_id]
    return format_response(df, format_type)





@router.get("/network/{secret_id}" , response_class=HTMLResponse)
@utils.auth_required(role="faculty")
async def network(request: Request, secret_id = str ):
    html_content = """
        <html>
        <head>
            <title>Network of Banks</title>
        </head>
        <body>
        <h1>Create a New Bank</h1>
        <form method="post" action="/db/network/{secret_id}">
            <label for="bank_id">Create a New Bank ID:</label>
            <input type="text" id="bank_id" name="bank_id" minlength="5" required ><br><br>
            
            <button type="submit">Submit</button>
                
        </form>
        </body>
        </html>

    """

    return HTMLResponse(content=html_content, status_code=200)

@router.get("/bank/{secret_id}/")
@utils.auth_required(role="faculty")
@utils.check_secret_password(secret_id="password")
async def create_bank(request: Request, secret_id : str ):
    html_content = """
     <html>
        <head>
            <title>Bank Profile</title>
        </head>
        <body>
        <h1>Create a Customer</h1>
        <form method="post" action="/db/bank/{secret_id}">
            <label for= "bank_id"> Your Bank ID: </label>
            <input type ="text" id="bank_id" name="bank_id" minlength="5" required> <br> </br>

            <label for="customer_id">Create a Customer:</label>
            <input type="text" id="cutomer_id" name="customer_id" minlength="5" required ><br><br>
        
            <label for="credit_card_id">Create a Credit Card:</label>
            <input type="text" id="credit_card_id" name="credit_card_id" minlength="5" maxlength="10" required ><br><br>    
            
            <button type="submit">Submit</button>
                
        </form>
        </body>
        </html>
    """
    
    return HTMLResponse(content=html_content, status_code=200)

@router.post("/bank/{secret_id}/")
async def create_bank_customer(request: Request, 
    bank_id: str = Form(...),                           
    customer_id: str = Form(...),
    credit_card_id: str = Form(...),
    secret_id = str
):
    
    
    df = pd.read_csv("data/network.csv", dtype={"Bank ID": str})  # check to see if the id for bank exists

    if search_df(df, bank_id ,"Bank ID"):
        
    
        # bank = Bank (
        #     bank_id= bank_id,
        #     customer_id = customer_id,
        #     credit_card_id = credit_card_id
        # )
     
        
        csv_file = 'data/bank.csv'
        fieldnames = ['Bank ID', 'Customer ID', 'Credit Card ID' ,'Date', 'Time']
        file_exists = os.path.isfile(csv_file)
        if file_exists:
            df = pd.read_csv("data/bank.csv", dtype={"Customer ID": str})

            if len(df[df['Customer ID'] == customer_id]) > 0:
                return "This Customer ID already exists! "

            if len(df[df['Credit Card ID'] == customer_id]) > 0:
                return "One Credit Card ID cannot be assigned to more than one Customer "
       
        with open(csv_file, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
    
            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'Bank ID': bank_id,
                'Customer ID' : customer_id,
                'Credit Card ID' : credit_card_id,
                'Date': str(datetime.now().date()),
                'Time': str(datetime.now().time()),
            })
        
        
        df = pd.read_csv("data/bank.csv", dtype={"Bank ID": str})
        return  format_response(df, format_type="html")
    else:
        return "The Bank does not exist"


@router.get("/customer/{secret_id}")
async def get_customer_info(request: Request, secret_id : str ):
    if secret_id != password:
        raise HTTPException(status_code=401, detail="Invalid secret ID")
    
    html_content = """
        <html>
        <head>
            <title>Bank Profile</title>
        </head>
        <body>
        <h1>Add Customer information</h1>
        <form method="post" action="/db/customer/{secret_id}">
            <label for= "customer_id"> Customer ID: </label>
            <input type ="text" id="customer_id" name="customer_id" minlength="5" required> <br> </br>

            <label for="credit_card_id">Credit Card ID:</label>
            <input type="text" id="credit_card_id" name="credit_card_id" minlength="5" maxlength= "10" required ><br><br>
        
            <label for="amount">Amount of money:</label>
            <input type="text" id="amount" name="amount" required ><br><br>    
            
            <button type="submit">Submit</button>
                
        </form>
        </body>
        </html> 
    """
    return HTMLResponse(content=html_content, status_code=200)

@router.post("/customer/{secret_id}")
async def insert_customer_info(
    request:Request,
    customer_id: str = Form(...),
    credit_card_id: str = Form(...),
    amount: float = Form(...)
):

    fieldnames = ['Customer ID', 'Credit Card ID', 'Amount']

    csv_file = "data/customer.csv"
    file_exists = os.path.isfile(csv_file)
    if file_exists:
        df = pd.read_csv("data/bank.csv", dtype={"Customer ID": str})
        df2 = pd.read_csv("data/bank.csv", dtype={"Credit Card ID": str})

        for item in df['Customer ID']: 
            if item != customer_id:
                return "This Customer ID does not exists! "
            
        for item in df2['Credit Card ID']:
            if item == credit_card_id:
                return "This credit card id has already been assigned"

    with open(csv_file, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames= fieldnames)
    
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            
            'Customer ID' : customer_id,
            'Credit Card ID' : credit_card_id,
            'Amount':amount
            })

    df = pd.read_csv("data/customer.csv", dtype={"Customer ID": str})
    return  format_response(df, format_type="html")