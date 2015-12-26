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
    return


def congress_no(get_year=date.today().year):
    """Return current year and congress shortcut.
    :param get_year: year YYYY
    """
    c3 = 'C3'
    first = 1984
    this_year = int(get_year)

    if this_year >= 1984:
        c3_no = this_year - first + 1
        c3_id = str(c3_no) + c3
        return this_year, c3_id
    else:
        raise ValueError("Value entered is not a valid date.")


def db_connect(year=date.today().year):
    """Create / connect to SQLite database.
    :param year:
    """
    db_name = 'c3speakers' + str(year) + '.sqlite'
    db = lite.connect(db_name)

    # get SQLite version
    cur = db.cursor()
    cur.execute('SELECT SQLITE_VERSION()')
    data = cur.fetchone()
    print("SQLite version: %s" % data)

    return db_name


def db_write(db_name):
    """Update SQLite database.
    :param db_name: name of the DB to operate on
    """
    db = lite.connect(db_name)

    try:
        cur = db.cursor()
        # create table for speakers
        cur.execute("""CREATE TABLE IF NOT EXISTS
                        speakers(id INTEGER PRIMARY KEY, name TEXT, twitter TEXT)
                    """)
        db.commit()
    except lite.OperationalError as err:
        # rollback on problems with db statement
        print(str(err))
        db.rollback()
    finally:
        db.close()


def get_speakers(html):
    pass


print(hello_world())
print(read_html())

try:
    congress_data = congress_no()
except ValueError as err:
    print(err.args[0])

try:
    # noinspection PyUnboundLocalVariable
    db_file = db_connect(congress_data[0])
    print(db_file)
except NameError as err:
    print("Cannot create DB, no congress specified.")

try:
    # noinspection PyUnboundLocalVariable
    print(db_write(db_file))
except NameError as err:
    print("Database with the provided name does not exist.")
