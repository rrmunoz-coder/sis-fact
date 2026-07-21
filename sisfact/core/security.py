from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import abort, session


def login_required(view: Callable):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            abort(401)
        return view(*args, **kwargs)
    return wrapper


def roles_required(*roles: str):
    def decorator(view: Callable):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user_roles = set(session.get("roles", []))
            if not user_roles.intersection(set(roles)):
                abort(403)
            return view(*args, **kwargs)
        return wrapper
    return decorator
