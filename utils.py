from functools import wraps
from starlette.responses import RedirectResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
faculty_listing = ["ashimaganja98@gmail.com"]
super_users = ["mattsap@udel.edu","ashimaganja98@gmail.com"]
def auth_required(*decorator_args, **decorator_kwargs):
    def inner(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            user = request.session.get('user')
            print("raw, url", str(request.url))
            if user is None:
                request.session["state_prior_to_login"] = str(request.url)
                return RedirectResponse(url='/login')

            authorized_role = False
            email = user["email"]
            # Need to check if username has role type coordinator or superadmin or
            required_role_type = decorator_kwargs.get("role")

            if required_role_type == "faculty":
                authorized_role = authorized_role or (email in faculty_listing)
            authorized_role = authorized_role or (required_role_type == "all") or required_role_type is None or (
                    email in super_users)
            if authorized_role:
                return await func(*args, **kwargs)
            else:
                return RedirectResponse(url='/unauthorized')

        return wrapper

    return inner

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

def get_user_information(request: Request):
    print("json", request.session)
    print("cookies", str(request.cookies))
    user_session = request.session.get('user')
    print(user_session, "is logged in")
    email = user_session.get("email")
    name = user_session.get("name", "unnamed_user")
    return email, name