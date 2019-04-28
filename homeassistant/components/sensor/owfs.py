"""
Support for OWFS sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.owfs/
"""

from datetime import timedelta

from homeassistant.components.owfs import (OWFSDevice, init_devices,
                                           DEVICE_SCHEMA, SubDevice_)
from homeassistant.components.sensor import PLATFORM_SCHEMA

DEPENDENCIES = ['owfs']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(DEVICE_SCHEMA.schema)

SCAN_INTERVAL = timedelta(
    minutes=5)  # default; don't do it too often, may be expensive


async def async_setup_platform(hass,
                               config,
                               async_add_entities,
                               discovery_info=None):
    """Set up sensor(s) for OWFS platform."""

    await init_devices(hass, 'sensor', config, discovery_info,
                       async_add_entities, CLASSES)


class TemperatureSensor(OWFSDevice):
    """Representation of an OWFS DS18b20 temperature sensor."""

    _attr = "temperature"
    temperature = None

    async def _init(self, without_config: bool):
        """Async part of device initialization."""
        await super()._init(without_config)
        if without_config:
            await self.dev.set_polling_interval("temperature", 30)

    async def process_event(self, event):
        from trio_owfs.event import DeviceValue

        if isinstance(event, DeviceValue) and \
                event.attribute in {'temperature', 'latesttemp'}:
            self.temperature = event.value
            self.async_schedule_update_ha_state()

        await super().process_event(event)

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return "°C"


class VoltageSensor(OWFSDevice):
    """Representation of an OWFS DS2450 A/D converter.

    This sensor is a proxy for reading all voltages
    via simultaneous conversion.
    """

    _attr = "voltage"
    voltages = None

    async def _init(self, without_config: bool):
        """Async part of device initialization."""
        await super()._init(without_config)
        if without_config:
            await self.dev.set_polling_interval("voltage", 30)

    async def process_event(self, event):
        from trio_owfs.event import DeviceValue

        if isinstance(event, DeviceValue) and \
                event.attribute == "volt_all":
            self.voltage = event.value

            devs = self.dev._OWFSDevice__objects
            for i in range(4):
                subdev = devs.get('volt_'+str(i), None)
                if subdev is not None:
                    await subdev.polled_value(self.voltage[i])
        await super().process_event(event)

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return "°C"

    @classmethod
    def cls_for(cls, attr):
        if attr in {'volt.0','volt.1','volt.2','volt.3'}:
            return SubDevice_("Voltage_"+attr[-1], attr)
        return super(cls).cls_for(attr)

CLASSES = {
    0x10: TemperatureSensor,
    0x20: VoltageSensor
}

