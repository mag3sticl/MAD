from aiohttp import web
from aiohttp.abc import Request
from aiohttp_jinja2.helpers import url_for

from mapadroid.madmin.AbstractRootEndpoint import AbstractRootEndpoint


class SettingsEndpoint(AbstractRootEndpoint):
    """
    "/settings"
    """

    def __init__(self, request: Request):
        super().__init__(request)

    # TODO: Auth
    async def get(self):
        await self._redirect(self._url_for("settings_devices"))
