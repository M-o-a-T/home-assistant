"""Test the bootstrapping."""
# pylint: disable=protected-access
import pytest
import os
from unittest.mock import Mock, patch
import logging
import trio_asyncio

import homeassistant.config as config_util
from homeassistant import bootstrap, core
import homeassistant.util.dt as dt_util

from tests.common import patch_yaml_files, get_test_config_dir

ORIG_TIMEZONE = dt_util.DEFAULT_TIME_ZONE
VERSION_PATH = os.path.join(get_test_config_dir(), config_util.VERSION_FILE)

_LOGGER = logging.getLogger(__name__)


# prevent .HA_VERSION file from being written
@pytest.mark.trio
@patch(
    'homeassistant.bootstrap.conf_util.process_ha_config_upgrade', Mock())
@patch('homeassistant.util.location.detect_location_info',
       Mock(return_value=None))
@patch('homeassistant.bootstrap.async_register_signal_handling', Mock())
@patch('os.path.isfile', Mock(return_value=True))
@patch('os.access', Mock(return_value=True))
@patch('homeassistant.bootstrap.async_enable_logging',
       Mock(return_value=True))
def test_from_config_file():
    trio_asyncio.run(_test_from_config_file)
async def _test_from_config_file():
    """Test with configuration file."""
    components = set(['browser', 'conversation', 'script'])
    files = {
        'config.yaml': ''.join('{}:\n'.format(comp) for comp in components)
    }

    hass = core.HomeAssistant()
    with patch_yaml_files(files, True):
        await bootstrap.async_from_config_file('config.yaml', hass)

    assert components.issubset(hass.config.components)


@patch('homeassistant.bootstrap.async_enable_logging', Mock())
@patch('homeassistant.bootstrap.async_register_signal_handling', Mock())
def test_home_assistant_core_config_validation(hass):
    trio_asyncio.run(_test_home_assistant_core_config_validation, hass)
async def _test_home_assistant_core_config_validation(hass):
    """Test if we pass in wrong information for HA conf."""
    # Extensive HA conf validation testing is done
    hass = core.HomeAssistant()
    result = await bootstrap.async_from_config_dict({
        'homeassistant': {
            'latitude': 'some string'
        }
    }, hass)
    assert result is None
