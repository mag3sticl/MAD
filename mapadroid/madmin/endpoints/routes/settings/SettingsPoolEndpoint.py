from typing import Dict, Optional

import aiohttp_jinja2
from aiohttp import web
from aiohttp.abc import Request
from aiohttp_jinja2.helpers import url_for

from mapadroid.db.helper.SettingsDevicepoolHelper import SettingsDevicepoolHelper
from mapadroid.db.model import SettingsDevicepool
from mapadroid.db.resource_definitions.Devicepool import Devicepool
from mapadroid.madmin.AbstractRootEndpoint import AbstractRootEndpoint


class SettingsPoolEndpoint(AbstractRootEndpoint):
    """
    "/settings/shared"
    """

    def __init__(self, request: Request):
        super().__init__(request)

    # TODO: Auth
    async def get(self):
        identifier: Optional[str] = self.request.query.get("id")
        if identifier:
            return await self._render_single_element(identifier=identifier)
        else:
            return await self._render_overview()

    # TODO: Verify working
    @aiohttp_jinja2.template('settings_singlesharedsetting.html')
    async def _render_single_element(self, identifier: str):
        # Parse the mode to send the correct settings-resource definition accordingly
        device_pool: Optional[SettingsDevicepool] = None
        if identifier == "new":
            pass
        else:
            device_pool: SettingsDevicepool = await SettingsDevicepoolHelper.get(self._session, int(identifier))
            if not device_pool:
                raise web.HTTPFound(self._url_for("settings_pools"))

        settings_vars: Optional[Dict] = self._get_settings_vars()

        template_data: Dict = {
            'identifier': identifier,
            'base_uri': self._url_for('api_devicepool'),
            'redirect': self._url_for('settings_pools'),
            'subtab': 'devicepool',
            'element': device_pool,
            'settings_vars': settings_vars,
            'method': 'POST' if not device_pool else 'PATCH',
            'uri': self._url_for('api_devicepool') if not device_pool else '%s/%s' % (self._url_for('api_devicepool'), identifier),
            # TODO: Above is pretty generic in theory...
        }
        return template_data

    @aiohttp_jinja2.template('settings_sharedsettings.html')
    async def _render_overview(self):
        template_data: Dict = {
            'base_uri': self._url_for('api_devicepool'),
            'redirect': self._url_for('settings_pools'),
            'subtab': 'devicepool',
            'section': await SettingsDevicepoolHelper.get_all_mapped(self._session, self._get_instance_id()),
        }
        return template_data

    def _get_settings_vars(self) -> Optional[Dict]:
        return Devicepool.configuration
