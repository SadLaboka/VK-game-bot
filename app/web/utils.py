import json
import typing
from hashlib import sha256

from typing import Any, Optional

from aiohttp.web import json_response as aiohttp_json_response
from aiohttp.web_exceptions import HTTPForbidden
from aiohttp.web_response import Response

from app.admin.models import Admin, AdminModel
from app.store.admin.accessor import NotRegistered

if typing.TYPE_CHECKING:
    from app.web.app import Application


def json_response(data: Any = None, status: str = "ok") -> Response:
    if data is None:
        data = {}
    return aiohttp_json_response(
        data={
            "status": status,
            "data": data,
        }
    )


def error_json_response(
    http_status: int,
    status: str = "error",
    message: Optional[str] = None,
    data: Optional[dict] = None,
):
    if data is None:
        data = {}
    return aiohttp_json_response(
        status=http_status,
        data={
            'status': status,
            'message': str(message),
            'data': data,
        })


async def authenticate(email: str, password: str, app: "Application") -> Admin:
    try:
        admin = await app.store.admins.get_by_email(email)
    except NotRegistered:
        raise HTTPForbidden(text='Admin with this email is not registered')

    if admin.is_password_valid(password):
        return admin
    else:
        raise HTTPForbidden(text='Wrong password')


def get_text_from_exception(e: Exception) -> Optional[str]:
    try:
        data = json.loads(e.text)
    except Exception:
        data = e.text
    return data
