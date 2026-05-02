"""Test botgateway package"""

import botgateway


def test_package_version():
    """Test that version is properly set"""
    assert hasattr(botgateway, '__version__')
    assert botgateway.__version__ == '0.2.0'
