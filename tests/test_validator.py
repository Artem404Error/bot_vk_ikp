import pytest
from core.validator import validate_fio, validate_phone, parse_time

def test_fio_valid():
    res = validate_fio("Иванов Иван Иванович")
    assert res.is_valid
    assert res.value == "Иванов Иван Иванович"

def test_fio_invalid():
    res = validate_fio("Иванов Иван")
    assert not res.is_valid

def test_phone_valid():
    res = validate_phone("+7 (912) 345-67-89")
    assert res.is_valid
    assert "912" in res.value

def test_phone_clean():
    res = validate_phone("89123456789")
    assert res.is_valid

def test_parse_time():
    res = parse_time("завтра в 15:00")
    assert res.is_valid