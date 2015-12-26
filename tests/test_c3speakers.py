import pytest
from c3speakers import *


def test_helloworld():
    """Example test."""
    x = hello_world()
    assert x == 'Hello, world!'


def test_congressno_1964():
    this_year = '1964'
    with pytest.raises(ValueError) as excinfo:
        congress_no(this_year)
    # assert 'Value entered is not a valid date.' in str(excinfo.value)
    assert str(excinfo.value) == 'Value entered is not a valid date.'


def test_congressno_2023():
    this_year = '2023'
    this_congress = congress_no(this_year)
    assert this_congress == (2023, '40C3')


def test_congressno_2015():
    this_year = 2015
    this_congress = congress_no(this_year)
    assert this_congress == (2015, '32C3')


def test_congressno_1984():
    this_year = 1984
    this_congress = congress_no(this_year)
    assert this_congress == (1984, '1C3')


def test_congressno_1983():
    this_year = '1983'
    with pytest.raises(ValueError) as excinfo:
        congress_no(this_year)
    assert str(excinfo.value) == 'Value entered is not a valid date.'