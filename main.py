from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from routers import (db_access)



app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(SessionMiddleware, secret_key="!secret")




app.include_router(db_access.router)



@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("home.html.j2", {"request": request})



def main(production = False):
    import uvicorn
    if production:
        uvicorn.run(app, host="0.0.0.0", port=8005)
    else:
        uvicorn.run(app, host="localhost", port=8005)


main()
