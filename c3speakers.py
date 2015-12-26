import sys, getopt
import sqlite3 as lite
from datetime import date
from urllib.error import *
from urllib.request import urlopen
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
    except ValueError as err:
        print("ERROR: Value entered is not a valid date.")
        print(err)
        sys.exit(1)

    # only allow congresses between the very first congresses and now
    if year >= 1984 and year <= this_year:
        c3_no = year - first + 1
        c3_id = str(c3_no) + c3
        return year, c3_id
    else:
        raise ValueError("ERROR: Value entered is not a valid year.\n"
                         "Only years between 1984 and the current year are allowed.")


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


if __name__ == "__main__":
    main()
