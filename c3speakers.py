import sys
import getopt
import requests
from urllib.request import urlopen
from urllib.error import *
import sqlite3 as lite
from datetime import date
from bs4 import BeautifulSoup, SoupStrainer
from c3urls import *


def hello_world():
    """Example function."""
    hello = "Hello, world!"
    return hello


def usage():
    howto = "Usage: python3 %s -y YEAR" % str(sys.argv[0])
    return howto


def congress_no(year, this_year=date.today().year):
    """Return year and congress shortcut.
    :param year: year of queried congress
    :param this_year: this year
    """
    c3 = 'C3'
    first = 1984

    try:
        year = int(year)

    # TODO
    # allow c3 shortcuts to be entered instead of years, e.g. 30C3
    except ValueError as err:
        print("ERROR: Value entered is not a valid date.")
        print(err)
        sys.exit(1)

    # only allow congresses between the very first congresses and now
    if 1984 <= year <= this_year:
        c3_no = year - first + 1
        c3_id = str(c3_no) + c3
        return year, c3_id
    else:
        raise ValueError("ERROR: Value entered is not a valid year.\n"
                         "Only years between 1984 and the current year are allowed.")


def open_speakers_file(year):
    """Open the file/website listing all C3 speakers for a given year.
    :param year: the year for which to get the speakers file

    URLs:   https://events.ccc.de/congress/2015/Fahrplan/speakers.html
            https://events.ccc.de/congress/2012/Fahrplan/speakers.en.html
            https://events.ccc.de/congress/2010/Fahrplan/speakers.de.html

    """

    urls = ("https://events.ccc.de/congress/" + str(year) + "/Fahrplan/speakers.html",
            "https://events.ccc.de/congress/" + str(year) + "/Fahrplan/speakers.en.html"
            )

    if offline:
        url = "file:///" + offline

    try:
        r = requests.get(url, verify=False, timeout=5)
        if not r.status_code // 100 == 2:
            if r.status_code == 404:
                return "404 – page not found"
            return "ERROR: Unexpected response %s" % r
        html = r.text
    # connection timeout
    except requests.exceptions.ConnectTimeout as err:
        return "ERROR: The connection timed out."
    # ambiguous exceptions
    except requests.exceptions.RequestException as err:
        if "No connection adapters were found for" not in str(err):
            return ("ERROR: Invalid request.\n"
                "%s" % str(err))
        # offline use – try opening file with urllib
        else:
            try:
                html = urlopen(url)
            except Exception as err:
                return "ERROR: Not a valid file."

    return url

def main():
    table = 'speakers'
    year = date.today().year

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'y:h', ['year=', 'help'])
    except getopt.GetoptError as err:
        print(usage())
        print(err)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(usage())
        elif opt in ('-y', '--year'):
            year = arg

    # test function
    print(hello_world())

    # get congress data:
    # year of congress + c3 shortcut
    try:
        congress_data = congress_no(year)
        print(congress_data)
    except ValueError as err:
        print(err)
        sys.exit(1)

    # open speakers file/website
    try:
        get_speakers = open_speakers_file(year)
        print(get_speakers)
    except ValueError as err:
        print(err)


if __name__ == "__main__":
    main()
