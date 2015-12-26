import sqlite3 as lite
from datetime import date
from urllib.error import *
from urllib.request import urlopen

from c3urls import *


def hello_world():
    """Example function."""
    hello = "Hello, world!"
    return hello


def read_html():
    """Open site that contains info on C3 speakers."""
    try:
        html = urlopen('file:///' + parent)
    except HTTPError as err:
        print("404 - The requested website is not available.")
        print(err)
        return
    get_speakers(html)


def congress_no(year=date.today().year):
    """Return current year and congress shortcut.
    :param year: year YYYY
    """
    c3 = 'C3'
    first = 1984
    this_year = int(year)

    if this_year >= 1984:
        c3_no = this_year - first + 1
        c3_id = str(c3_no) + c3
        return this_year, c3_id
    else:
        raise ValueError("Value entered is not a valid date.")


def db_connect(table, year=date.today().year):
    """Create / connect to SQLite database.
    :param year: year YYYY
    """
    db_name = 'c3speakers' + str(year) + '.sqlite'

    # create table for speakers
    try:
        db = lite.connect(db_name)
        cur = db.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS
                    %s(id INTEGER PRIMARY KEY, name TEXT, twitter TEXT)
                    """  % table)
        cur.execute("SELECT Count(*) FROM %s" % table)
        rows = cur.fetchone()
        print("Table rows: %s" % rows)
        db.commit()
    except lite.OperationalError as err:
        # rollback on problems with db statement
        print(str(err))
        raise err
        db.rollback()
    finally:
        db.close()

    return db_name


def get_speakers(html):
    pass



table = 'speakers'

# test function
print(hello_world())

# get congress data
try:
    congress_data = congress_no()
    print(congress_data)
except ValueError as err:
    print(err.args[0])

# connect to/create db and create first table
try:
    table_data = db_connect(table, congress_data[0])
    print(table_data)
    db = table_data[0]
except NameError as err:
    print("Cannot create DB, no congress no. specified.")
