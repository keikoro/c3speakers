from urllib.request import urlopen
from urllib.error import *
from c3urls import *
from dateutil.parser import parse
from datetime import date


def hello_world():
    """Example function."""
    hello = "Hello, world!"
    return hello


def read_html():
    """Open website that contains info on speakers."""
    try:
        html = urlopen('file:///' + parent)
    except HTTPError as e:
        print("404 - The requested website is not available.")
        print(e)
        return
    get_speakers(html)
    return


def congress_no(get_year=date.today().year):
    """Return current year and congress shortcut."""
    c3 = 'C3'
    first = 1984
    this_year = int(get_year)

    if (this_year >= 1984):
        c3_no = this_year - first + 1
        c3_id = str(c3_no) + c3
        return this_year, c3_id
    else:
        raise ValueError("Value entered is not a valid date.")


def get_speakers(html):
    pass


print(hello_world())
print(read_html())

try:
    print(congress_no())
except ValueError as err:
    print(err.args[0])