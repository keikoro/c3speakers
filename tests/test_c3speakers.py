import pytest
from c3speakers import *


def test_helloworld():
    """Example test."""
    x = hello_world()
    assert x == 'Hello, world!'


# TEST CONGRESS DATA

# this year's congress
@pytest.fixture
def this_c3_data():
    year, c3_no = congress_data(date.today().year)
    return year, c3_no


# error on invalid date entered
@pytest.fixture
def err_invalid_date():
    return ("ERROR: Value entered is not a valid year.\n"
            "Only years between 1984 and the current year are allowed.")


# error on invalid congress entered
@pytest.fixture
def err_invalid_congress():
    return ("ERROR: Value entered is not a valid congress.\n"
            "Only congresses between 1C3 and {}C3 are allowed."
            .format(this_c3_data()[1]))


# pass – valid year
def test_congress_1984():
    year = 1984
    this_congress = congress_data(year)
    assert this_congress == (1984, 1)


# pass – valid year (provided as str)
def test_congress_2015():
    year = '2015'
    this_congress = congress_data(year)
    assert this_congress == (2015, 32)


# pass – valid c3 shortcut
def test_congress_1c3():
    congress = '1C3'
    this_congress = congress_data(c3_shortcut=congress)
    assert this_congress == (1984, 1)


# pass – valid c3 shortcut
def test_congress_33c3():
    congress = '33c3'
    this_congress = congress_data(c3_shortcut=congress)
    assert this_congress == (2016, 33)


# pass – no year nor c3 shortcut provided, use current
def test_congress_today():
    this_congress = congress_data()
    assert this_congress == this_c3_data()


# fail – date before very first congress
def test_congress_1983():
    year = '1983'
    with pytest.raises(ValueError) as excinfo:
        congress_data(year)
    assert str(excinfo.value) == err_invalid_date()


# fail – str entered for year (int)
# ValueError
def test_congress_yearblah():
    year = 'blah'
    with pytest.raises(SystemExit) as excinfo:
        congress_data(year)
    assert excinfo.value.code == 1


# fail – results in None value for congress no.
# ValueError
def test_congress_0c2():
    congress = '0c2'
    with pytest.raises(SystemExit) as excinfo:
        congress_data(c3_shortcut=congress)
    assert excinfo.value.code == 1


# fail – results in str for congress no.
# ValueError
def test_congress_abc3():
    congress = 'abC3'
    with pytest.raises(SystemExit) as excinfo:
        congress_data(c3_shortcut=congress)
    assert excinfo.value.code == 1


# fail – int instead of str entered for congress no.
# AttributeError
def test_congress_no55():
    congress = 55
    with pytest.raises(SystemExit) as excinfo:
        congress_data(c3_shortcut=congress)
    assert excinfo.value.code == 1


# fail – future date
def test_congress_2100():
    year = 2100
    with pytest.raises(ValueError) as excinfo:
        congress_data(year)
    assert str(excinfo.value) == err_invalid_date()


# fail – future congress
def test_congress_99c3():
    congress = '99C3'
    with pytest.raises(ValueError) as excinfo:
        congress_data(c3_shortcut=congress)
    assert str(excinfo.value) == err_invalid_congress()


# TEST URLs
def test_url_offline_invalid():
    this_url = testurl_offnon
    this_check = open_website(this_url)
    assert this_check == "ERROR: Not a valid file."


def test_url_online_404():
    this_url = testurl_on404
    this_check = open_website(this_url)
    assert this_check == "404 – page not found"


def test_url_offline_valid():
    this_url = testurl_offtrue
    this_check = open_website(this_url)
    assert this_check[0] is True


def test_url_online_valid():
    this_url = testurl_ontrue
    this_check = open_website(this_url)
    assert this_check[0] is True


def test_url_online_invalid():
    this_url = testurl_offnon2
    this_check = open_website(this_url)
    assert this_check == "ERROR: Not a valid file."


# TEST FOREIGN URLs

# error on invalid foreign URL
@pytest.fixture
def err_invalid_foreign_url():
    return ("ERROR: The provided URL has an unexpected "
            "format and cannot be used.\n"
            "Will try to capture data from the "
            "standard CCC URLs instead...")


# pass - valid url with year
def test_url_foreign_year1():
    url = "http://neato-fahrplan-backup.com/2010/Fahrplan/schedule.html"
    check_url = foreign_url(url)
    assert check_url == (
        "http://neato-fahrplan-backup.com/2010/Fahrplan/", "2010", None,
        ".html")


# pass - valid url with year
def test_url_foreign_year2():
    url = "https://mirror.ccc.de/2012/Fahrplan/speakers.en.html"
    check_url = foreign_url(url)
    assert check_url == (
        "https://mirror.ccc.de/2012/Fahrplan/", "2012", None, ".en.html")


# pass - valid url with c3 shortcut
def test_url_foreign_c3shortcut():
    url = "http://nerds.ninja/31c3/justforyou/Fahrplan/schedule.de.html"
    check_url = foreign_url(url)
    assert check_url == (
        "http://nerds.ninja/31c3/justforyou/Fahrplan/", None, "31c3",
        ".de.html")


# pass - valid url with c3 shortcut
def test_url_foreign_c3shortcut2():
    url = "http://hackfleisch.de/33C3/Fahrplan/speakers.html"
    check_url = foreign_url(url)
    assert check_url == (
        "http://hackfleisch.de/33C3/Fahrplan/", None, "33C3", ".html")


# fails - no valid year or congress shortcut
def test_url_foreign_invalid1():
    url = "http://haxx0rz.com/1337/CCC/Fahrplan/speakers.html"
    with pytest.raises(AttributeError) as excinfo:
        foreign_url(url)
    assert str(excinfo.value) == err_invalid_foreign_url()


# fails - invalid year or congress shortcut
def test_url_foreign_invalid2():
    url = "http://oh-so-leet.de/100C3/Fahrplan/speakers.html"
    with pytest.raises(AttributeError) as excinfo:
        foreign_url(url)
    assert str(excinfo.value) == err_invalid_foreign_url()
