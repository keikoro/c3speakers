import sys
import getopt
import requests
import re
import time
import os.path
import sqlite3
from urllib.request import urlopen
from datetime import date
from bs4 import BeautifulSoup, SoupStrainer
from c3urls import *


def hello_world():
    """Example function."""
    hello = "Hello, world!"
    return hello


def usage():
    howto = ("Usage: python3 {} "
             "[-y] <year> "
             "[-u] <url> "
             "[-c] <xxC3>".format(sys.argv[0]))
    return howto


def congress_no(c3_year, this_year=date.today().year):
    """Return year and congress shortcut.
    :param c3_year: year of queried congress
    :param this_year: current year
    """
    c3 = 'C3'
    first = 1984

    try:
        year = int(c3_year)

    # TODO allow c3 shortcuts to be entered instead of years, e.g. 30C3
    except ValueError as err:
        print("ERROR: Value entered is not a valid date.")
        print(err)
        sys.exit(1)

    # only allow congresses between the very first congresses and now
    if 1984 <= year <= this_year:
        c3_no = year - first + 1
        c3_id = "{}{}".format(c3_no, c3)
        return year, c3_id
    else:
        raise ValueError("ERROR: Value entered is not a valid year.\n"
                         "Only years between 1984 and the current year are "
                         "allowed.")


def custom_headers():
    """
    Custom headers for http(s) request.
    """
    headers = {"User-Agent":
                   "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0",
               "Accept":
                   "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Accept-Encoding": "gzip,deflate",
               "Accept-Language": "en-US,en;q=0.8"}
    return headers


def open_website(url):
    """Open the file/website listing all C3 speakers for a given year.
    :param url: website address of C3 Fahrplan speakers info

    previous URLs e.g.:
    https://events.ccc.de/congress/2015/Fahrplan/speakers.html
    https://events.ccc.de/congress/2012/Fahrplan/speakers.en.html
    https://events.ccc.de/congress/2010/Fahrplan/speakers.de.html
    """

    session = requests.Session()
    headers = custom_headers()

    try:
        r = session.get(url, headers=headers, verify=False, timeout=5)
        if not r.status_code // 100 == 2:
            if r.status_code == 404:
                return "404 – page not found"
            return "ERROR: Unexpected response {}".format(r)
        html = r.text
    # connection timeout
    except requests.exceptions.ConnectTimeout:
        return "ERROR: The connection timed out."
    # ambiguous exceptions
    except requests.exceptions.RequestException as err:
        if "No connection adapters were found for" not in str(err):
            return ("ERROR: Invalid request.\n{}".format(err))
        # offline use – try opening file with urllib
        else:
            # noinspection PyBroadException,PyBroadException
            try:
                html = urlopen(url)
            except Exception:
                return "ERROR: Not a valid file."

    return True, html


def find_speakers(html_obj):
    """
    Find URLs to speakers pages in speakers.html
    :param html_obj: the html object to parse with Beautiful Soup
    """
    speakers = {}

    # only look for URLs
    # which contain '/speakers/'
    # and which contain no other tags
    parse_links = SoupStrainer('a')
    filter_links = re.compile("(/speakers/)")
    filter_contents = re.compile(".*")
    soup = BeautifulSoup(html_obj, 'html.parser', parse_only=parse_links)

    # print out all valid URLs
    for item in soup.find_all('a', href=filter_links, string=filter_contents):
        regex = ".+/speakers/([0-9]+)(\..*[.html])"
        href = item['href']
        speaker_id = re.match(regex, href).group(1)
        value = item.get_text()
        # debug
        # print("{} : {}".format(speaker_id, value))
        speakers[speaker_id] = value

    return speakers


def parse_speaker_profile(url):
    """
    :param url: url to an individual speaker profile

    Typical speaker URLs:
    https://events.ccc.de/congress/2015/Fahrplan/speakers/6238.html
    https://events.ccc.de/congress/2009/Fahrplan/speakers/2650.en.html
    https://events.ccc.de/congress/2012/Fahrplan/speakers/3943.de.html
    """

    # try to open speaker's profile page/file
    check_url = open_website(url)
    status = check_url[0]
    html_obj = check_url[1]
    if status is True:
        # look for Twitter links
        parse_links = SoupStrainer('a')
        filter_links = re.compile("(twitter.com)")
        soup = BeautifulSoup(html_obj, 'html.parser', parse_only=parse_links)

        # print out all valid URLs
        for twitter_account in soup.find_all('a', href=filter_links):
            regex = ".+/twitter.com/([@_A-Za-z0-9]+)"
            href = twitter_account['href']
            speaker_twitter = re.match(regex, href).group(1)
            twitter_handle = twitter_account.get_text()
            return twitter_handle


def db_connect(base_path, table, year):
    """Create / connect to SQLite database.
    :param base_path: path to directory of sqlite db
    :param table: name of the table for speakers' data
    :param year: year YYYY
    """
    db_name = "c3speakers{}.sqlite".format(year)

    try:
        db = sqlite3.connect(base_path + db_name)
    except sqlite3.OperationalError:
        print("ERROR: Cannot connect to database.")
        return None

    # create table for speakers
    try:
        cur = db.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS {} "
                    "(id INTEGER PRIMARY KEY, name TEXT, twitter TEXT)"
                    .format(table))
        cur.execute("SELECT Count(*) FROM {}".format(table))
        db.commit()
    except sqlite3.OperationalError as err:
        # rollback on problems with db statement
        print(str(err))
        db.rollback()
    finally:
        db.close()

    return db_name


def db_write(base_path, db_name, table, speakers):
    """Update table in DB.
    :param base_path:
    :param db_name: name of the DB to operate on
    :param table: the table that should be modified
    :param speakers: dictionary containing speakers data
    """

    try:
        db = sqlite3.connect(base_path + db_name)
    except sqlite3.OperationalError:
        print("ERROR: Cannot connect to database.")
        return None

    # insert into table
    try:
        cur = db.cursor()
        for speaker_id, speaker_name in speakers.items():
            cur.execute("INSERT INTO speakers (id, name) "
                        "SELECT ?, ? WHERE NOT EXISTS "
                        "(SELECT * FROM {} WHERE id = ?)".format(table),
                        (int(speaker_id), speaker_name, int(speaker_id)))
        cur.execute("SELECT Count(*) FROM {}".format(table))
        rows = cur.fetchone()
        db.commit()
        print("Table rows: {}".format(rows[0]))
    except sqlite3.OperationalError as err:
        # rollback on problems with db statement
        print(str(err))
        db.rollback()
    finally:
        db.close()


def main():
    """
    main function
    """
    table = 'speakers'
    year = date.today().year
    base_path = os.getcwd() + "/"

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'yu:h',
                                   ['year=', 'url=', 'help'])
    except getopt.GetoptError as err:
        print(usage())
        print(err)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(usage())
            sys.exit(1)
        elif opt in ('-y', '--year'):
            year = arg
        elif opt in ('-u', '--url'):
            # TODO use url
            url = arg
    # test function
    print(hello_world())

    # get congress data:
    # year of congress + c3 shortcut
    try:
        c3_data = congress_no(year)
        c3_year = c3_data[0]
        c3_shortcut = c3_data[1]
        print("{} : {}".format(c3_year, c3_shortcut))
    except ValueError as err:
        print(err)
        sys.exit(1)

    # possible speaker URLs
    # based on previous congresses

    # TODO let user input alternative URLs (for Fahrplan mirrors)
    urls = (
        "https://events.ccc.de/congress/{}/Fahrplan/speakers.html".format(year),
        "https://events.ccc.de/congress/{}/Fahrplan/speakers.en.html".format(year)
    )

    # test urls (on and offline)
    urls = (
        # headertest,
        testurl_offnon,
        testurl_on404,
        testurl_offtrue,
        testurl_ontrue,
        testurl_offnon2
    )

    # loop through possible URLs for speakers site
    for url in urls:
        try:
            # try to open speakers file/website
            check_url = open_website(url)
            status = check_url[0]
            html_obj = check_url[1]
            if status is True:
                print(url)
                try:
                    # fetch speaker IDs from valid URL
                    speakers = find_speakers(html_obj)
                except Exception as err:
                    print("ERROR: Cannot fetch speakers from file.")
                    # TODO remove raise
                    # debug
                    raise err
                    sys.exit(1)
                break
            else:
                print("ERROR: Value entered is not a valid URL:\n{}".format(url))
        except ValueError as err:
            print("ERROR: Value entered is not a valid URL.")
            print(err)

    # debug
    # for testing only
    speakers = {
        testsp_1_id: testsp_1_name,
        testsp_2_id: testsp_2_name,
        testsp_3_id: testsp_3_name,
        testsp_4_id: testsp_4_name,
    }

    # display the no. of speakers that was found
    print("---")
    if len(speakers) > 0:
        print("{} speakers, all in all".format(len(speakers)))

        # parse speakers profiles
        for speaker_url in speakers:
            # time delay to appear less bot-like
            # TODO change to 3
            time.sleep(0.1)
            twitter = parse_speaker_profile(speaker_url)
            if twitter is True:
                # twitter_profiles = {}
                # twitter_profiles[speaker_id] = value
                print(twitter)
    else:
        print("No speakers found.")

    # database connection
    try:
        db_name = db_connect(base_path, table, c3_year)
        db_write(base_path, db_name, table, speakers)
    except:
        pass


if __name__ == "__main__":
    main()
