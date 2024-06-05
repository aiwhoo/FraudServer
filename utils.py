from functools import wraps
from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def check_secret_password(*decorator_args, **decorator_kwargs):
    def inner(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            print("deckwargs",decorator_kwargs)
            print("decargs",decorator_args)
            print("args",args)
            print("kwargs", kwargs)
            if kwargs["secret_id"] == decorator_kwargs["secret_id"] or kwargs["adb"] in decorator_kwargs["exceptions"]:
                return await func(*args, **kwargs)
            else:
                #return "Secret ID does not match"
                return templates.TemplateResponse("wrongPass.html.j2", {"request": request})


        return wrapper

    return inner
