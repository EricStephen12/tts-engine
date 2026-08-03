
from config.settings import Settings


def test_api_key_list_parses_csv():
    settings = Settings(api_keys="key1, key2 ,key3")
    assert settings.api_key_list == ["key1", "key2", "key3"]


def test_cors_origin_list_parses_csv():
    settings = Settings(cors_origins="http://a.com, http://b.com")
    assert settings.cors_origin_list == ["http://a.com", "http://b.com"]


def test_invalid_device_raises():
    import pytest

    with pytest.raises(Exception):
        Settings(device="tpu")


def test_default_device_is_auto():
    settings = Settings()
    assert settings.device == "auto"
