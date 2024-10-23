from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    When used on a function, requires the user to be logged in.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            print(session.get("user_id"))
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function
