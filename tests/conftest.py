"""Pytest configuration for NetBox ZPL Labels tests.

This conftest.py mocks NetBox dependencies so that the ZPL module tests
can run without a full NetBox installation.
"""

import sys
from unittest.mock import MagicMock

# Mock netbox module before any imports
netbox_mock = MagicMock()
netbox_mock.plugins = MagicMock()
netbox_mock.plugins.PluginConfig = type("PluginConfig", (), {})
netbox_mock.models = MagicMock()
netbox_mock.models.NetBoxModel = type("NetBoxModel", (), {})
netbox_mock.api = MagicMock()
netbox_mock.api.routers = MagicMock()
netbox_mock.api.serializers = MagicMock()
netbox_mock.api.viewsets = MagicMock()
netbox_mock.filtersets = MagicMock()
netbox_mock.forms = MagicMock()
netbox_mock.tables = MagicMock()
netbox_mock.views = MagicMock()
netbox_mock.search = MagicMock()

sys.modules["netbox"] = netbox_mock
sys.modules["netbox.plugins"] = netbox_mock.plugins
sys.modules["netbox.models"] = netbox_mock.models
sys.modules["netbox.api"] = netbox_mock.api
sys.modules["netbox.api.routers"] = netbox_mock.api.routers
sys.modules["netbox.api.serializers"] = netbox_mock.api.serializers
sys.modules["netbox.api.viewsets"] = netbox_mock.api.viewsets
sys.modules["netbox.filtersets"] = netbox_mock.filtersets
sys.modules["netbox.forms"] = netbox_mock.forms
sys.modules["netbox.tables"] = netbox_mock.tables
sys.modules["netbox.views"] = netbox_mock.views
sys.modules["netbox.views.generic"] = MagicMock()
sys.modules["netbox.search"] = netbox_mock.search

# Mock utilities module
utilities_mock = MagicMock()
utilities_mock.choices = MagicMock()
utilities_mock.choices.ChoiceSet = type("ChoiceSet", (), {"colors": {}})
utilities_mock.forms = MagicMock()
utilities_mock.forms.fields = MagicMock()
utilities_mock.forms.rendering = MagicMock()
utilities_mock.views = MagicMock()

sys.modules["utilities"] = utilities_mock
sys.modules["utilities.choices"] = utilities_mock.choices
sys.modules["utilities.forms"] = utilities_mock.forms
sys.modules["utilities.forms.fields"] = utilities_mock.forms.fields
sys.modules["utilities.forms.rendering"] = utilities_mock.forms.rendering
sys.modules["utilities.views"] = utilities_mock.views

# Mock dcim module
dcim_mock = MagicMock()
dcim_mock.models = MagicMock()
dcim_mock.api = MagicMock()
dcim_mock.api.serializers = MagicMock()

sys.modules["dcim"] = dcim_mock
sys.modules["dcim.models"] = dcim_mock.models
sys.modules["dcim.api"] = dcim_mock.api
sys.modules["dcim.api.serializers"] = dcim_mock.api.serializers

# Mock rest_framework
rf_mock = MagicMock()
sys.modules["rest_framework"] = rf_mock
sys.modules["rest_framework.serializers"] = MagicMock()
sys.modules["rest_framework.views"] = MagicMock()
sys.modules["rest_framework.decorators"] = MagicMock()
sys.modules["rest_framework.response"] = MagicMock()

# Mock django_filters
sys.modules["django_filters"] = MagicMock()

# Mock django_tables2
sys.modules["django_tables2"] = MagicMock()
