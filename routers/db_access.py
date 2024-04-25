from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import uuid
from pydantic import BaseModel,Field, constr
from datetime import datetime
import os
import csv 

router = APIRouter(prefix="/db", tags=["scripts"],)
#templates = Jinja2Templates(directory="templates")


class Transaction(BaseModel):
    credit_card_id: str | constr(min_length=10, max_length=10)
    zip_code: str | constr(min_length=5, max_length=5)
    vendor_name: str
    amount: float


def write_transaction_to_csv(transaction: Transaction, csv_file: str):
    fieldnames = ['Transaction ID', 'Date', 'Time', 'Credit Card ID', 'Zip Code', 'Vendor Name', 'Amount']
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'Transaction ID': str(uuid.uuid4()),
            'Date': str(datetime.now().date()),
            'Time': str(datetime.now().time()),
            'Credit Card ID': transaction.credit_card_id,
            'Zip Code': transaction.zip_code,
            'Vendor Name': transaction.vendor_name,
            'Amount': transaction.amount
        })

@router.get("/transactions/",  response_class=HTMLResponse)
async def transaction_form(request: Request):
    html_content = """
    <html>
    <head>
        <title>Transaction Form</title>
    </head>
    <body>
        <h1>Create a New Transaction</h1>
        <form method="post" action="/db/transactions/">
            <label for="credit_card_id">Credit Card ID (10 characters):</label>
            <input type="text" id="credit_card_id" name="credit_card_id" minlength="10" maxlength="10" required><br><br>
            
            <label for="zip_code">Zip Code (5 characters):</label>
            <input type="text" id="zip_code" name="zip_code" minlength="5" maxlength="5" required><br><br>
            
            <label for="vendor_name">Vendor Name:</label>
            <input type="text" id="vendor_name" name="vendor_name" required><br><br>
            
            <label for="amount">Amount:</label>
            <input type="number" id="amount" name="amount" min="0" step="0.01" required><br><br>
            
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@router.post("/transactions/")
async def create_transaction( request: Request, 
    credit_card_id: str = Form(...),
    zip_code: str = Form(...),
    vendor_name: str = Form(...),
    amount: float = Form(...),
):

    transaction = Transaction(
        credit_card_id=credit_card_id,
        zip_code=zip_code,
        vendor_name=vendor_name,
        amount=amount
    )
    
    # Write transaction to CSV file
    csv_file = 'data/transactions.csv'
    write_transaction_to_csv(transaction, csv_file)

    return " Transaction succeessful"


def format_response(df, format_type):
    if format_type == 'html':
        return Response(content=df.to_html(index=False, classes="table table-striped", escape=False), media_type="text/html")
    else:
        return Response(content=df.to_json(orient="records"), media_type="application/json")

@router.get("/transactions/{credit_card_id}/{format_type}/")
async def get_transactions(request: Request, credit_card_id: str, format_type:str): #read from the database
    df = pd.read_csv("data/transactions.csv", dtype={"Credit Card ID": str})

    df = df[df["Credit Card ID"] == credit_card_id]
    return format_response(df, format_type)


