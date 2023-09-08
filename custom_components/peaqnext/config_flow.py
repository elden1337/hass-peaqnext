"""Config flow for Peaq integration."""
from __future__ import annotations

import logging
from typing import Any, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from custom_components.peaqnext.service.models.consumption_type import (
    CONSUMPTIONTYPE_NAMES,
)
from custom_components.peaqnext.service.models.next_sensor.enums.calculate_by import CalculateBy
from custom_components.peaqnext.service.models.next_sensor.enums.update_by import UpdateBy

from .const import (
    CONF_DEDUCT_PRICE,
    DOMAIN,
    CONF_NAME,
    CONF_SENSORS,
    CONF_CONSUMPTION_TYPE,
    CONF_TOTAL_CONSUMPTION_IN_KWH,
    CONF_TOTAL_DURATION_IN_MINUTES,
    CONF_NONHOURS_START,
    CONF_NONHOURS_END,
    CONF_CLOSEST_CHEAP,
    CONF_CUSTOM_CONSUMPTION_PATTERN,
    CONF_UPDATE_BY,
    CONF_CALCULATE_BY,
)  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)


SENSORS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_CONSUMPTION_TYPE): vol.In(CONSUMPTIONTYPE_NAMES),
        vol.Optional(CONF_CUSTOM_CONSUMPTION_PATTERN): cv.string,
        vol.Required(CONF_TOTAL_CONSUMPTION_IN_KWH): cv.positive_float,
        vol.Required(CONF_TOTAL_DURATION_IN_MINUTES): cv.positive_float,
        vol.Optional(CONF_NONHOURS_START): cv.multi_select(list(range(0, 24))),
        vol.Optional(CONF_NONHOURS_END): cv.multi_select(list(range(0, 24))),
        vol.Optional(CONF_CLOSEST_CHEAP, default=12): cv.positive_float,
        vol.Optional(CONF_DEDUCT_PRICE, default=0): cv.positive_float,
        vol.Optional(
            CONF_UPDATE_BY,
            default=UpdateBy.MINUTE.value,
        ): vol.In([h.value for h in UpdateBy]),
        vol.Optional(
            CONF_CALCULATE_BY,
            default=CalculateBy.STARTTIME.value,
        ): vol.In([h.value for h in CalculateBy]),
        vol.Optional("add_another_sensor"): cv.boolean,
    }
)



class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    OPTIONS = "options"
    data: Optional[dict[str, Any]]
    info: Optional[dict[str, Any]]

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None, initial=True):
        """Second step in config flow to add a repo to watch."""
        if user_input is None and initial:
            self.data = {}
            if CONF_SENSORS not in self.data:
                self.data[CONF_SENSORS] = []
        if user_input is not None:
            self.data[CONF_SENSORS].append(
                {
                    CONF_CONSUMPTION_TYPE: user_input[CONF_CONSUMPTION_TYPE],
                    CONF_CUSTOM_CONSUMPTION_PATTERN: user_input.get(CONF_CUSTOM_CONSUMPTION_PATTERN, None),
                    CONF_NAME: user_input.get(CONF_NAME),
                    CONF_TOTAL_DURATION_IN_MINUTES: user_input.get(CONF_TOTAL_DURATION_IN_MINUTES),
                    CONF_TOTAL_CONSUMPTION_IN_KWH: user_input.get(CONF_TOTAL_CONSUMPTION_IN_KWH),
                    CONF_NONHOURS_START: user_input.get(CONF_NONHOURS_START,[]),
                    CONF_NONHOURS_END: user_input.get(CONF_NONHOURS_END,[]),
                    CONF_CLOSEST_CHEAP: user_input.get(CONF_CLOSEST_CHEAP, 12),
                    CONF_DEDUCT_PRICE: user_input.get(CONF_DEDUCT_PRICE, 0),
                    CONF_UPDATE_BY: user_input.get(CONF_UPDATE_BY, ""),
                    CONF_CALCULATE_BY: user_input.get(CONF_CALCULATE_BY, "")
                }
            )
            if user_input.get("add_another_sensor", False):
                return await self.async_step_user(initial=False)

            # User is done adding repos, create the config entry.
            return self.async_create_entry(title="Peaqnext-sensors", data=self.data)

        return self.async_show_form(
            step_id="user", data_schema=SENSORS_SCHEMA, errors={}
        )


# class OptionsFlowHandler(config_entries.OptionsFlow):
#     def __init__(self, config_entry):
#         """Initialize options flow."""
#         self.config_entry = config_entry
#         self.options = dict(config_entry.options)

#     async def _get_existing_param(self, parameter: str, default_val: any):
#         if parameter in self.config_entry.options.keys():
#             return self.config_entry.options.get(parameter)
#         if parameter in self.config_entry.data.keys():
#             return self.config_entry.data.get(parameter)
#         return default_val

#     async def async_step_init(self, user_input=None):
#         """Priceaware"""
#         if user_input is not None:
#             self.options.update(user_input)
#             if self.options["priceaware"] is False:
#                 return await self.async_step_hours()
#             return await self.async_step_months()

#         _priceaware = await self._get_existing_param("priceaware", False)
#         _topprice = await self._get_existing_param("absolute_top_price", 0)
#         _minprice = await self._get_existing_param("min_priceaware_threshold_price", 0)
#         _hourtype = await self._get_existing_param("cautionhour_type", CautionHourType.INTERMEDIATE.value)
#         _dynamic_top_price = await self._get_existing_param("dynamic_top_price", False)
#         _max_charge = await self._get_existing_param("max_charge", 0)

#         return self.async_show_form(
#             step_id="init",
#             last_step=False,
#             data_schema=vol.Schema(
#                 {
#                     vol.Optional("priceaware", default=_priceaware): cv.boolean,
#                     vol.Optional("dynamic_top_price", default=_dynamic_top_price): cv.boolean,
#                     vol.Optional("absolute_top_price", default=_topprice): cv.positive_float,
#                     vol.Optional("min_priceaware_threshold_price", default=_minprice): cv.positive_float,
#                     vol.Optional(
#                         "cautionhour_type",
#                         default=_hourtype,
#                     ): vol.In(CAUTIONHOURTYPE_NAMES),
#                     vol.Optional("max_charge", default=_max_charge): cv.positive_float,
#                 }
#             ),
#         )

#     async def async_step_hours(self, user_input=None):
#         """Hours"""
#         if user_input is not None:
#             self.options.update(user_input)
#             return await self.async_step_months()

#         _nonhours = await self._get_existing_param("nonhours", list(range(0, 24)))
#         _cautionhours = await self._get_existing_param("cautionhours", list(range(0, 24)))

#         return self.async_show_form(
#             step_id="hours",
#             last_step=False,
#             data_schema=vol.Schema(
#                 {
#                     vol.Optional("nonhours", default=_nonhours): cv.multi_select(list(range(0, 24))),
#                     vol.Optional("cautionhours", default=_cautionhours): cv.multi_select(list(range(0, 24))),
#                 }
#             ),
#         )

#     async def async_step_months(self, user_input=None):
#         """Months"""
#         if user_input is not None:
#             months_dict = await async_set_startpeak_dict(user_input)
#             self.options["startpeaks"] = months_dict
#             return await self.async_step_misc()

#         _defaultvalues = self.config_entry.options.get("startpeaks", self.config_entry.data.get("startpeaks"))
#         defaultvalues = {float(k): v for (k, v) in _defaultvalues.items()}

#         return self.async_show_form(
#             step_id="months",
#             last_step=False,
#             data_schema=vol.Schema(
#                 {
#                     vol.Optional("jan", default=defaultvalues[1]): cv.positive_float,
#                     vol.Optional("feb", default=defaultvalues[2]): cv.positive_float,
#                     vol.Optional("mar", default=defaultvalues[3]): cv.positive_float,
#                     vol.Optional("apr", default=defaultvalues[4]): cv.positive_float,
#                     vol.Optional("may", default=defaultvalues[5]): cv.positive_float,
#                     vol.Optional("jun", default=defaultvalues[6]): cv.positive_float,
#                     vol.Optional("jul", default=defaultvalues[7]): cv.positive_float,
#                     vol.Optional("aug", default=defaultvalues[8]): cv.positive_float,
#                     vol.Optional("sep", default=defaultvalues[9]): cv.positive_float,
#                     vol.Optional("oct", default=defaultvalues[10]): cv.positive_float,
#                     vol.Optional("nov", default=defaultvalues[11]): cv.positive_float,
#                     vol.Optional("dec", default=defaultvalues[12]): cv.positive_float,
#                 }
#             ),
#         )

#     async def async_step_misc(self, user_input=None):
#         """Misc options"""
#         if user_input is not None:
#             self.options["mains"] = user_input["mains"]
#             self.options["blocknocturnal"] = user_input["blocknocturnal"]
#             self.options["gainloss"] = user_input["gainloss"]
#             return self.async_create_entry(title="", data=self.options)

#         mainsvalue = await self._get_existing_param("mains", "")
#         blocknocturnal = await self._get_existing_param("blocknocturnal", False)
#         gainloss = await self._get_existing_param("gainloss", True)

#         schema = vol.Schema(
#             {
#                 vol.Optional(
#                     "mains",
#                     default=mainsvalue,
#                 ): vol.In(FUSES_LIST),
#                 vol.Optional("blocknocturnal", default=blocknocturnal): cv.boolean,
#                 vol.Optional("gainloss", default=gainloss): cv.boolean,
#             }
#         )

#         return self.async_show_form(step_id="misc", last_step=True, data_schema=schema)
