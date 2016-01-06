import sys
import getopt
import requests
import re
import time
import os.path
import sqlite3
import configparser
from urllib.request import urlopen
from datetime import date
from bs4 import BeautifulSoup, SoupStrainer
# TODO remove later (only for testing)
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


def foreign_url(url):
    """
    :param url: the Fahrplan URL provided by the user

    Fahrplan format e.g.
    http://abc.de/congress/2000/Fahrplan/schedule.en.html
    https://xyz.co.uk/congress/2015/Fahrplan/speakers.html

    schedule.html ... Fahrplan main page
    speakers.html ... speakers page
    """

    # check if speakers URL was provided
    fahrplan_regex = "(.+/)((((19|20)([0-9]{2}))|(([1-9][0-9]){1}[Cc]3))" \
                     ".*/Fahrplan.*/)[A-Za-z]+(\.[A-Za-z.]*html)"

    try:
        fahrplan_data = re.match(fahrplan_regex, url)
        speakers_base_url = fahrplan_data.group(1) + fahrplan_data.group(2)
        year = fahrplan_data.group(4)
        c3_no = fahrplan_data.group(7)
        # account for different file endings (.html, .en.html, .de.html)
        file_ending = fahrplan_data.group(9)
        return speakers_base_url, year, c3_no, file_ending
    except:
        raise AttributeError("ERROR: The provided URL has an unexpected "
                             "format and cannot be used.\n"
                             "Try using a URL that references C3's 'Fahrplan' (schedule).")


def congress_data(year=None, c3_shortcut=None):
    """Return year and shortcut for queried congress.
    :param year: current year or year of queried congress
    :param c3_shortcut: abbreviation for nth congress, e.g. 30c3 for 30th
    """
    first_year = 1984
    first_c3_no = 1
    this_year = date.today().year
    this_c3_no = this_year - first_year + 1

    if c3_shortcut:
        # validate provided c3 shortcut
        try:
            c3_no_find = c3_shortcut.lower().rpartition('c3')
            c3_no = c3_no_find[0]
            c3_no = int(c3_no)
        # invalid string entered
        except ValueError as err:
            print("ERROR: Value entered is not a valid congress.")
            print(err)
            sys.exit(1)
        # integer value entered
        except AttributeError as err:
            print("ERROR: Value entered is not a valid congress.")
            print(err)
            sys.exit(1)
        if first_c3_no <= c3_no <= this_c3_no:
            year = this_year - (this_c3_no - c3_no)
            return year, c3_no
        else:
            raise ValueError("ERROR: Value entered is not a valid "
                             "congress.\nOnly congresses between 1C3 and "
                             "{}C3 are allowed.".format(this_c3_no))

    if year:
        #  validate provided year
        try:
            year = int(year)
        # string entered
        except ValueError as err:
            print("ERROR: Value entered is not a valid year:\n"
                  "{}".format(year))
            sys.exit(1)
        # only allow congresses between the very first congresses and now
        if first_year <= year <= this_year:
            c3_no = year - first_year + 1
            return year, c3_no
        else:
            raise ValueError("ERROR: Value entered is not a valid year:\n"
                             "{}\n"
                             "Only years between 1984 and the current year are "
                             "allowed.".format(year))

    if not year and not c3_shortcut:
        return this_year, this_c3_no


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
                print("404 – page not found")
            print("ERROR: Unexpected response {}".format(r))
        else:
            print("status: 200")
        html = r.text
        return html
    # connection timeout
    except requests.exceptions.ConnectTimeout:
        return "ERROR: The connection timed out."
    # ambiguous exceptions
    except requests.exceptions.RequestException as err:
        if "No connection adapters were found for" not in str(err):
            # check if url is a local file
            file_path = "file:///{}".format(url)
            try:
                html = urlopen(file_path)
                return html
            # exception while opening the provided file
            except Exception as err:
                print("ERROR: Not a valid file:")
                print(u"\u2717 {}".format(url))
            else:
                print("ERROR: Invalid request. Cannot open website:\n"
                "{}".format(url))
                sys.exit(1)
    except Exception as err:
        print(err)
        print("An unexpected error occurred.")


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
    Parse a C3 speaker profile for a link to a Twitter account.
    :param url: url to an individual speaker profile

    Typical speaker URLs:
    https://events.ccc.de/congress/2015/Fahrplan/speakers/6238.html
    https://events.ccc.de/congress/2009/Fahrplan/speakers/2650.en.html
    https://events.ccc.de/congress/2012/Fahrplan/speakers/3943.de.html
    """

    # try to open speaker's profile page/file
    html_obj = open_website(url)
    if html_obj:
        # look for Twitter links
        parse_links = SoupStrainer('a')
        filter_links = re.compile("(twitter.com)")
        soup = BeautifulSoup(html_obj, 'html.parser', parse_only=parse_links)

        # print out all valid URLs
        for twitter_account in soup.find_all('a', href=filter_links):
            regex = ".+/twitter.com/([@_A-Za-z0-9]+)"
            href = twitter_account['href']
            twitter_handle = re.match(regex, href).group(1)
            return twitter_handle


def db_connect(dir_path, db_name, table, year):
    """Create / connect to SQLite database.
    :param dir_path: path to directory of sqlite db
    :param db_name: name of the db to connect to
    :param table: name of the table for speakers' data
    :param year: year YYYY
    """
    db_file = "{}{}.sqlite".format(db_name, year)

    try:
        db = sqlite3.connect(dir_path + db_file)
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

    return db_file


def db_write(dir_path, db_name, table, speakers=None, twitter=None):
    """Update table in DB.
    :param twitter:
    :param dir_path:
    :param db_name: name of the DB to operate on
    :param table: the table that should be modified
    :param speakers: dictionary containing speakers data
    """

    try:
        db = sqlite3.connect(dir_path + db_name)
    except sqlite3.OperationalError:
        print("ERROR: Cannot connect to database.")
        return None

    # insert into table
    try:
        cur = db.cursor()
        if speakers:
            for speaker_id, speaker_name in speakers.items():
                cur.execute("INSERT INTO {} (id, name) "
                            "SELECT ?, ? WHERE NOT EXISTS "
                            "(SELECT * FROM {} WHERE id = ?)".format(table,
                                                                     table),
                            (int(speaker_id), speaker_name, int(speaker_id))
                            )
            cur.execute("SELECT Count(*) FROM {}".format(table))
            db.commit()
        elif twitter:
            for speaker_id, twitter in twitter.items():
                cur.execute("UPDATE {} SET twitter=? "
                            "WHERE id=? AND twitter is NULL".format(table),
                            (twitter, int(speaker_id))
                            )
            cur.execute(
                "SELECT Count(twitter) FROM {} WHERE twitter is not NULL".format(
                    table))
            rows = cur.fetchone()
            db.commit()
            print("{} Twitter handles identified".format(rows[0]))
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
    c3 = 'C3'
    urls = []
    twitters = {}
    # TODO switch later
    # base_url = "https://events.ccc.de/congress/"
    base_url = test_base
    speakers_base_url = None
    file_ending = None
    # file endings used for prev. c3 websites (.html being the most common)
    file_endings = ('.html', '.en.html', '.de.html')

    # get vars from config file
    config = configparser.ConfigParser()
    config.read('config.txt')
    dir_path = config.get('db', 'dir_path')
    db_name = config.get('db', 'db_name')
    table = config.get('db', 'table')

    if dir_path:
        dir_path = os.getcwd() + '/'

    # congress data for current year
    try:
        year, c3_no = congress_data()
        # debug
        print("{} > {}{} ... this year".format(year, c3_no, c3))
    # unforseen exception
    except ValueError as err:
        print(err)
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'y:c:u:h',
                                   ['year=', 'congress=', 'url=', 'help'])
    except getopt.GetoptError as err:
        print(usage())
        print(err)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(usage())
            sys.exit(1)
        # check for user-provided URL
        elif opt in ('-u', '--url'):
            url = arg
            try:
                speakers_base_url, foreign_year, foreign_c3_no, file_ending = foreign_url(
                    url)
                try:
                    year, c3_no = congress_data(year=foreign_year,
                                                c3_shortcut=foreign_c3_no)
                    print("{} > {}{} ... requested".format(year, c3_no, c3))
                    break
                except ValueError as err:
                    print(err)
                    sys.exit(1)
            except AttributeError as err:
                print(err)
                sys.exit(1)
        # check for user-provided year
        # break when valid input found
        elif opt in ('-y', '--year'):
            try:
                year, c3_no = congress_data(year=arg)
                print("{} > {}{} ... requested".format(year, c3_no, c3))
                break
            except ValueError as err:
                print(err)
                sys.exit(1)
        # check for user-provided congress shortcut
        # break when valid input found
        elif opt in ('-c', '--congress'):
            try:
                year, c3_no = congress_data(c3_shortcut=arg)
                print("{} > {}{} ... requested".format(year, c3_no, c3))
                break
            except ValueError as err:
                print(err)
                sys.exit(1)

    # base URL for Fahrplan page (= basis for speakers page)
    if not speakers_base_url:
        speakers_base_url = "{}{}/Fahrplan/".format(base_url, year)

    # make sure to account for possible different file endings
    if file_ending:
        urls.append("{}speakers{}".format(speakers_base_url, file_ending))
    else:
        for ending in file_endings:
            urls.append("{}speakers{}".format(speakers_base_url, ending))

    # debug
    # print(urls)

    # loop through possible URLs for speakers site
    loop_filendings = 0
    for url in urls:
        try:
            # try to open speakers file/website
            html_obj = open_website(url)
            if html_obj:
                print("Opening speakers file:\n{}".format(url))
                try:
                    # fetch speaker IDs from valid URL
                    speakers = find_speakers(html_obj)
                    # determine file ending
                    if not file_ending:
                        file_ending = file_endings[loop_filendings]
                        print(file_ending)
                except Exception as err:
                    print("ERROR: Cannot fetch speakers from file.")
                    # TODO remove raise
                    # debug
                    raise err
                    sys.exit(1)
                break
            loop_filendings += 1
        except ValueError as err:
            print("ERROR: Value entered is not a valid URL.")
            print(err)
        except TypeError as err:
            print(err)
            sys.exit(1)

    # for testing only
    # TODO remove late
    speakers = {
        testsp_1_id: testsp_1_name,
        testsp_2_id: testsp_2_name,
        testsp_3_id: testsp_3_name,
        testsp_4_id: testsp_4_name,
        testsp_5_id: testsp_5_name
    }

    # display the no. of speakers that was found
    print("---")
    if len(speakers) > 0:
        print("{} speakers, all in all".format(len(speakers)))
        # parse speakers profiles
        # TODO switch later
        # for speaker_id in speakers:
        for speaker_id, name in speakers.items():
            # time delay to appear less bot-like
            time.sleep(3)
            # TODO switch later
            # speaker_url = "{}{}/Fahrplan/speakers/{}{}".format(speakers_base_url, year, speaker_id, file_ending)
            file_ending = '.html'
            speaker_url = "{}speakers/{}{}".format(speakers_base_url,
                                                   speaker_id, file_ending)
            print(u"\u2713 {}".format(speaker_url))
            twitter_handle = parse_speaker_profile(speaker_url)
            if twitter_handle:
                print("Twitter: {}".format(twitter_handle))
                twitters[speaker_id] = twitter_handle
    else:
        print("No speakers found.")

    # database connection
    try:
        # create db if not exists
        db = db_connect(dir_path, db_name, table, year)
        # fill with speaker data
        db_write(dir_path, db, table, speakers=speakers)
        db_write(dir_path, db, table, twitter=twitters)
    except TypeError as err:
        print(err)


if __name__ == "__main__":
    main()
