import logging.config
import random
import string
import time
from apscheduler.schedulers.background import BackgroundScheduler
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, Request, Response, BackgroundTasks

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse

from routers import (db_access)


import os
#logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get root logger
#logger = logging.getLogger(__name__)  # the __name__ resolve to "main" since we are at the root of the project.
# This will get the root logger since no logger in the configuration has this name.

app = FastAPI()
templates = Jinja2Templates(directory="templates")
#app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(SessionMiddleware, secret_key="!secret")

config = Config('.env')
oauth = OAuth(config)

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)
app.include_router(db_access.router)



@app.get("/")
async def root(request: Request):
    return "Hello world"




@app.get('/login')
async def login(request: Request):
    redirect_uri = str(request.url_for('auth'))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get('/auth')
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user = token.get('userinfo')
    redirect_url = "/"
    if user:
        request.session['user'] = dict(user)
        redirect_url = request.session["state_prior_to_login"]
        request.session.pop("state_prior_to_login", None)
    return RedirectResponse(url=redirect_url)
@app.get('/shutdown')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@app.get('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')


@app.get("/unauthorized")
async def unauthorized(request: Request):
    return "You are authorized to view this page."

def shutdown_server():
    import os
    os.kill(os.getpid(), 9)

@app.get("/shutdown")
async def shutdown(background_tasks: BackgroundTasks):
    background_tasks.add_task(shutdown_server)
    print("shutdown")
    return "Server is shutting down"

"""
1) schedule a cron job that checks a csv file, and sends out any emails on the csv file
2) mechanism to add scheduled emails to ^^ csv
"""


def main(production = False):
    import uvicorn
    if production:
        uvicorn.run(app, host="0.0.0.0", port=8005)
    else:
        uvicorn.run(app, host="localhost", port=8005)


main()
