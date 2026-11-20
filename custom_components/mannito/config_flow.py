"""Config flow of the Mannito integration: cloud address and API token of one board."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_TOKEN, CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
import probatio

from .api import BoardSnapshot, MannitoAuthError, MannitoClient, MannitoConnectionError, MannitoError
from .const import DEFAULT_URL, DOMAIN, LOGGER

URL_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.URL))
TOKEN_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


class MannitoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Adds a Mannito board with an API token from the Mannito cloud."""

    VERSION = 1
    MINOR_VERSION = 1

    async def _async_validate(self, url: str, token: str) -> tuple[BoardSnapshot | None, dict[str, str]]:
        """Read the board with the token; the errors for the form."""
        client = MannitoClient(async_get_clientsession(self.hass), url, token)
        try:
            return await client.async_get_board(), {}
        except MannitoAuthError:
            return None, {"base": "invalid_auth"}
        except MannitoConnectionError:
            return None, {"base": "cannot_connect"}
        except MannitoError:
            return None, {"base": "cannot_connect"}
        except Exception:
            LOGGER.exception("Unexpected error while checking the token")
            return None, {"base": "unknown"}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for the cloud address and the token."""
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            token = user_input[CONF_API_TOKEN].strip()
            snapshot, errors = await self._async_validate(url, token)
            if snapshot is not None:
                await self.async_set_unique_id(snapshot.board.id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=snapshot.board.name, data={CONF_URL: url, CONF_API_TOKEN: token})
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                probatio.Schema(
                    {
                        probatio.Required(CONF_URL): URL_SELECTOR,
                        probatio.Required(CONF_API_TOKEN): TOKEN_SELECTOR,
                    }
                ),
                user_input or {CONF_URL: DEFAULT_URL},
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """The token stopped working (revoked or expired)."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for a new token of the same board."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            token = user_input[CONF_API_TOKEN].strip()
            snapshot, errors = await self._async_validate(entry.data[CONF_URL], token)
            if snapshot is not None:
                await self.async_set_unique_id(snapshot.board.id)
                self._abort_if_unique_id_mismatch(reason="wrong_board")
                return self.async_update_reload_and_abort(entry, data_updates={CONF_API_TOKEN: token})
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=probatio.Schema({probatio.Required(CONF_API_TOKEN): TOKEN_SELECTOR}),
            description_placeholders={"name": entry.title},
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Change the cloud address or the token of the board."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            token = user_input[CONF_API_TOKEN].strip()
            snapshot, errors = await self._async_validate(url, token)
            if snapshot is not None:
                await self.async_set_unique_id(snapshot.board.id)
                self._abort_if_unique_id_mismatch(reason="wrong_board")
                old_url, old_token = entry.data[CONF_URL], entry.data[CONF_API_TOKEN]
                result = self.async_update_reload_and_abort(entry, data_updates={CONF_URL: url, CONF_API_TOKEN: token})
                if token != old_token:
                    # the replaced token would keep working: revoke it (the board reloads with the new one meanwhile)
                    old = MannitoClient(async_get_clientsession(self.hass), old_url, old_token)
                    if not await old.async_revoke_token():
                        LOGGER.warning("The replaced API token could not be revoked; revoke it in the Mannito cloud")
                return result
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                probatio.Schema(
                    {
                        probatio.Required(CONF_URL): URL_SELECTOR,
                        probatio.Required(CONF_API_TOKEN): TOKEN_SELECTOR,
                    }
                ),
                {CONF_URL: entry.data[CONF_URL]},
            ),
            errors=errors,
        )
