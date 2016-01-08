#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Find Chaos Communication Congress (C3) speakers for a given year
and store their names and Twitter handles (where applicable)
into an SQLite database.

Copyright (c) 2016 K Kollmann <code∆k.kollmann·moe>

License: http://opensource.org/licenses/MIT The MIT License (MIT)

Usage:
Use -h or --help for help on how to use the program.

Users can specify the year or congress for which they want to
query speakers, or provide their own URL or filename to parse
speaker information from.
By default the current year and the CCC's official speakers listing
– https://events.ccc.de/congress/YYYY/Fahrplan/speakers.html –
are used.

For more information on what C3 is about see e.g.
https://en.wikipedia.org/wiki/Chaos_Communication_Congress
"""

import sys
import getopt
import requests
import re
import os.path
import sqlite3
import configparser
from urllib.request import urlopen
import urllib.error
import time
from datetime import date
from bs4 import BeautifulSoup, SoupStrainer


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

    # check if correct URL was provided:
    # URL/file needs to:
    # - contain a year YYYY or C3 shortcut
    # - contain the folder /Fahrplan/
    # - end in .html
    fahrplan_regex = "(.+/)((((19|20)([0-9]{2}))|(([1-9][0-9]){1}[Cc]3))" \
                     ".*/Fahrplan.*/)[A-Za-z]+(\.[A-Za-z.]*html)"
    try:
        fahrplan_data = re.match(fahrplan_regex, url)
        speakers_base_url = fahrplan_data.group(1) + fahrplan_data.group(2)
        year = fahrplan_data.group(4)
        c3_no = fahrplan_data.group(7)
        # account for different file endings (.html, .en.html, .de.html)
        # -> language-dependent pages used for previous c3s
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

    # validate provided c3 shortcut
    if c3_shortcut:
        try:
            c3_no_find = c3_shortcut.lower().rpartition('c3')
            c3_no = c3_no_find[0]
            c3_no = int(c3_no)
        # invalid string entered
        except ValueError as err:
            print("ERROR: Value entered is not a valid congress.")
            print(err)
            sys.exit(1)
        # integer value entered (needs to be string)
        except AttributeError as err:
            print("ERROR: Value entered is not a valid congress.")
            print(err)
            sys.exit(1)

        # if a potential c3 shortcut was found, check if it's for a valid c3
        # only congresses between 1c3 and this year's c3 can be queried
        if first_c3_no <= c3_no <= this_c3_no:
            year = this_year - (this_c3_no - c3_no)
            return year, c3_no
        else:
            raise ValueError("ERROR: Value entered is not a valid "
                             "congress.\nOnly congresses between 1C3 and "
                             "{}C3 are allowed.".format(this_c3_no))
    # validate provided year
    # check if string can be converted to int
    if year:
        try:
            year = int(year)
        # string that cannot be converted to int
        except ValueError:
            print("ERROR: Value entered is not a valid year:\n"
                  "{}".format(year))
            sys.exit(1)

        # if a year was found, check if it's a valid year
        # only congresses between 1984 and this year can be queried
        if first_year <= year <= this_year:
            c3_no = year - first_year + 1
            return year, c3_no
        else:
            raise ValueError("ERROR: Value entered is not a valid year:\n"
                             "{}\n"
                             "Only years between 1984 and the current year are "
                             "allowed.".format(year))

    # return c3 data for this year if no year or c3 shortcut were user-provided
    if not year and not c3_shortcut:
        return this_year, this_c3_no


def custom_headers():
    """
    Custom headers for http(s) request.

    Create headers to make requests look less bot-like.
    """

    headers = {"User-Agent":
                   "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0",
               "Accept":
                   "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Accept-Encoding": "gzip,deflate",
               "Accept-Language": "en-US,en;q=0.8"}
    return headers


def open_website(url):
    """Open a website or file and return its HTML contents.
    :param url: the website/file to be opened
    """

    session = requests.Session()
    headers = custom_headers()

    # connect to the (assumed) website
    try:
        r = session.get(url, headers=headers, verify=True, timeout=5)
        # check the status code returned by the web request
        # only status 200 (OK) signifies the request was successful
        if not r.status_code // 100 == 2:
            # output a separate message for 404 errors
            if r.status_code == 404:
                print(u"\u2717 404 – page not found: {}".format(url))
                return None
            # output for all errors that are not 404
            print("ERROR: Unexpected response {}".format(r))
            return None
        else:
            print(u"\u2713 Opening {}".format(url))
            r.encoding = r.apparent_encoding
            html = r.text
            return html
    # connection timeout
    except requests.exceptions.ConnectTimeout:
        return "ERROR: The connection timed out."
    # ambiguous exceptions on trying to connect to website
    except requests.exceptions.RequestException as err:
        # when there is a problem with reading the file
        # check if it's a local file (requests lib does not work with those)
        if "No connection adapters were found for" not in str(err):
            file_path = "file:///{}".format(url)
            # check if url is actually a local file
            try:
                html = urlopen(file_path)
                print(u"\u2713 Opening {}".format(file_path))
                return html
            # if the local file cannot be opened/does not exist
            except urllib.error.URLError:
                print(u"\u2717 Not a valid file: {}".format(url))
            # unforseen exception
            except Exception as err:
                print("An unexpected error occurred on line {}:".format(
                    sys.exc_info()[-1].tb_lineno))
                print(err)
                sys.exit(1)
        # if the url is NOT a local file, sth. else went wrong with the request
        else:
            print(url)
            print("ERROR: Invalid request. Cannot open website:\n"
                  "{}".format(url))
            sys.exit(1)
    # unforseen exception
    except Exception as err:
        print("An unexpected error occurred on line {}:".format(
            sys.exc_info()[-1].tb_lineno))
        print(err)


def find_speakers(html_obj):
    """
    Find URLs to individual speakers pages in speakers.html
    :param html_obj: the html object to parse with Beautiful Soup
    """
    speakers = {}

    # only look for <a> tags
    parse_links = SoupStrainer('a')
    # look for the string /speakers/
    filter_links = re.compile("(/speakers/)")
    # match any text – except tags! (tags won't get matched by this)
    filter_contents = re.compile(".*")
    soup = BeautifulSoup(html_obj, 'html.parser', parse_only=parse_links)

    # find all URLs that match the defined criteria
    for item in soup.find_all('a', href=filter_links, string=filter_contents):
        # filter out speaker IDs from all valid URLs
        # speaker files are called .../speakers/1234.html etc.
        # where 1234 is the speaker ID
        regex = ".+/speakers/([0-9]+)(\..*[.html])"
        href = item['href']

        # try to match speaker URL
        try:
            speaker_id = re.match(regex, href).group(1)
            value = item.get_text()
            # debug
            # print("{} : {}".format(speaker_id, value))
            # save all speaker IDs and speaker names into a dictionary
            speakers[speaker_id] = value
        # account for malformed speaker URLs
        except Exception as err:
            print("Faulty URL for speaker: {}".format(href))
            print(err)
            return None


    return speakers


def parse_speaker_profile(url):
    """
    Parse a C3 speaker profile for a link to a Twitter account.
    :param url: url to an individual speaker profile
    """

    # try to open a speaker's profile page/file
    html_obj = open_website(url)
    if html_obj:
        # look for <a> tags
        parse_links = SoupStrainer('a')
        # look for the string twitter.com
        filter_links = re.compile("(twitter.com)")
        soup = BeautifulSoup(html_obj, 'html.parser', parse_only=parse_links)

        # find all URLs that match the defined criteria
        for twitter_account in soup.find_all('a', href=filter_links):
            # filter out twitter handles from all valid URLs
            # twitter handles are formatted http(s)://twitter.com/the_name
            regex = ".*twitter.com/([@_A-Za-z0-9]+)"
            href = twitter_account['href']
            # try to find proper Twitter accounts
            try:
                twitter_handle = re.match(regex, href).group(1)
                return twitter_handle
            # account for malformed Twitter URLs
            except Exception as err:
                print("Faulty URL for Twitter account: {}".format(href))
                print(err)
                return None


def db_connect(dir_path, db_name, table, year):
    """Create / connect to SQLite database.
    :param dir_path: path to the directory containing the sqlite db
    :param db_name: name of the DB to connect to
    :param table: name of the table to create for speakers' data
    :param year: year YYYY
    """
    db_file = "{}{}.sqlite".format(db_name, year)

    # try to connect to the sqlite database;
    # if the path is writeable and the file doesn't exist yet,
    # a sqlite db with the requested name be created
    try:
        db = sqlite3.connect(dir_path + db_file)
    except sqlite3.OperationalError:
        print("ERROR: Cannot connect to database.")
        return None

    # create table for speakers if there is none yet
    try:
        cur = db.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS {} "
                    "(id INTEGER PRIMARY KEY, name TEXT, twitter TEXT)"
                    .format(table))
        cur.execute("SELECT Count(*) FROM {}".format(table))
        db.commit()
    except sqlite3.OperationalError as err:
        # rollback on problems with db statement
        print("Could not query the database as requested.")
        print(str(err))
        db.rollback()
    finally:
        db.close()

    return db_file


def db_query(dir_path, db_name, table, column=None):
    """Query table in DB.
    :param dir_path: path to the directory containing the sqlite db
    :param db_name: name of the DB to operate on
    :param table: name of the to-be-modified table holding speakers' data
    :param column: table column to query
    """
    results = {}

    # try to connect to the sqlite database;
    # as the connect was already checked, this should not result in a new file
    try:
        db = sqlite3.connect(dir_path + db_name)
    except sqlite3.OperationalError:
        print("ERROR: Cannot connect to database.")
        return None

    # check for validity of table column provided by user
    if not column:
        select = '*'
        column = 'id'
    elif column == 'name' or column == 'twitter':
        select = "id, {}".format(column)
    else:
        print("ERROR: The provided table column is not valid. Exiting.")
        sys.exit(1)

    # query table for provided column
    try:
        cur = db.cursor()
        cur.execute(
            "SELECT count(id) FROM {} WHERE {} != '' ".format(table, column)
        )
        rows = cur.fetchone()
        # if there are any results, put them into a dictionary and return it
        if rows[0] > 0:
            cur.execute("SELECT {} FROM {} "
                        "WHERE {} != '' ".format(select, table, column)
                        )
            rows = cur.fetchall()
            # ids have to be converted to str as parsed vals are strings
            for row in rows:
                speaker_id = str(row[0])
                results[speaker_id] = row[1]
            db.commit()
            return results
    except sqlite3.OperationalError as err:
        # rollback on problems with db statement
        print("Could not query the database as requested.")
        print(str(err))
        db.rollback()
    finally:
        db.close()


def db_write(dir_path, db_name, table, speakers=None, twitter=None):
    """Update table in DB.
    :param dir_path: path to the directory containing the sqlite db
    :param db_name: name of the DB to operate on
    :param table: name of the to-be-modified table holding speakers' data
    :param speakers: dictionary containing speakers IDs and names
    :param twitter: dictionary containing speakers IDs and twitter handles
    """

    # try to connect to the sqlite database;
    # as the connect was already checked, this should not result in a new file
    try:
        db = sqlite3.connect(dir_path + db_name)
    except sqlite3.OperationalError:
        print("ERROR: Cannot connect to database.")
        return None

    # insert data into table for speakers
    # -> existing speakers and twitter handles are not auto-removed!!
    # but they are printed out
    try:
        cur = db.cursor()
        # if speakers dict was provided, insert IDs and names of speakers
        # if speaker already exists, their name isn't updated/reinserted
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
        # if twitter dict was provided, insert IDs and twitter handles of speakers
        # if speaker already has a witter handle, it doesn't get updated/reinserted
        elif twitter:
            for speaker_id, twitter in twitter.items():
                cur.execute("UPDATE {} SET twitter=? "
                            "WHERE id=? AND twitter is NULL".format(table),
                            (twitter, int(speaker_id))
                            )
            cur.execute(
                "SELECT Count(twitter) FROM {} WHERE twitter is not NULL".format(
                    table))
            db.commit()
    except sqlite3.OperationalError as err:
        # rollback on problems with db statement
        print("Could not query the database as requested.")
        print(str(err))
        db.rollback()
    finally:
        db.close()


def compare_values(db_values, new_values):
    """
    Compare DB values with new values.
    :param db_values: values in the database
    :param new_values: new values retrieved by (re)parsing website
    :return: list with all changed values + list with all deleted values
    """

    changed = {}
    deleted = {}
    try:
        compare_sets = set(db_values.items()) - set(new_values.items())
        if len(compare_sets) > 0:
            for item in compare_sets:
                key = item[0]
                value_db = item[1]

                # DB values that differ from retrieved values
                # (applies to name changes, Twitter handle changes)
                try:
                    value = new_values[key]
                    changed[key] = value

                # IDs in DB that are
                # - not listed in the Fahrplan anymore
                # - which used to have a Twitter handle but don't anymore
                except KeyError:
                    # save all affected (removed) IDs into a dictionary
                    # so there is only one warning per ID
                    # to avoid duplicate msgs for missing Twitter handles
                    # of speakers who were removed from Fahrplan
                    deleted[key] = value_db

                    # if key not in removed:
                    #     removed.append(key)
        return changed, deleted
    # NoneType on empty dictionaries
    except AttributeError:
        return changed, deleted
    # unforseen exception
    except Exception as err:
        print("An unexpected error occurred on line {}:".format(
            sys.exc_info()[-1].tb_lineno))
        print(err)
        sys.exit(1)


def main():
    """
    main function
    """
    c3 = 'C3'
    urls = []
    speakers = {}
    twitters = {}
    # default URL to use for CCC Fahrplan requests
    base_url = "https://events.ccc.de/congress/"
    speakers_base_url = None
    file_ending = None
    # file endings used for prev. c3 websites (.html being the most common)
    file_endings = ('.html', '.en.html', '.de.html')

    # get (user-provided, user-editable) vars from config file
    # -> db name, db path, table name for speaker data
    config = configparser.ConfigParser()
    config.read('config.txt')
    dir_path = config.get('db', 'dir_path')
    db_name = config.get('db', 'db_name')
    table = config.get('db', 'table')

    # use the current working directory to query DBs if no path was provided
    if not dir_path:
        dir_path = "{}/".format(os.getcwd())

    # get congress data for current year (in any case)
    try:
        year, c3_no = congress_data()
    # unforseen exception
    except Exception as err:
        print("An unexpected error occurred on line {}:".format(
            sys.exc_info()[-1].tb_lineno))
        print(err)
        sys.exit(1)

    # check if any command line arguments were provided by user
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'y:c:u:h',
                                   ['year=', 'congress=', 'url=', 'help'])
    except getopt.GetoptError as err:
        print(usage())
        print(err)
        sys.exit(2)

    for opt, arg in opts:
        # help menu requested
        if opt in ('-h', '--help'):
            print(usage())
            sys.exit(1)
        # separate URL provided for speakers file
        elif opt in ('-u', '--url'):
            url = arg
            try:
                speakers_base_url, foreign_year, foreign_c3_no, file_ending = foreign_url(
                    url)
                try:
                    year, c3_no = congress_data(year=foreign_year,
                                                c3_shortcut=foreign_c3_no)
                    print("{}: {}{} ... requested".format(year, c3_no, c3))
                    break
                except ValueError as err:
                    print(err)
                    sys.exit(1)
            except AttributeError as err:
                print(err)
                sys.exit(1)
        # particular date (year) provided by user
        elif opt in ('-y', '--year'):
            # check for validity of user-provided year
            # and break (no further checks of flags)
            try:
                year, c3_no = congress_data(year=arg)
                print("{}: {}{} ... requested".format(year, c3_no, c3))
                break
            except ValueError as err:
                print(err)
                sys.exit(1)
        # particular congress shortcut (xyC3) provided by user
        elif opt in ('-c', '--congress'):
            # check for validity of user-provided c3 shortcut
            # and break (no further checks of flags)
            try:
                year, c3_no = congress_data(c3_shortcut=arg)
                print("{} > {}{} ... requested".format(year, c3_no, c3))
                break
            except ValueError as err:
                print(err)
                sys.exit(1)

    # debug
    print("{}: {}{} ... this year".format(year, c3_no, c3))

    # create base URL for Fahrplan page (which contains speaker page)
    if not speakers_base_url:
        speakers_base_url = "{}{}/Fahrplan/".format(base_url, year)

    # make sure to account for possible different file endings
    # used for previous congresses
    if file_ending:
        urls.append("{}speakers{}".format(speakers_base_url, file_ending))
    else:
        for ending in file_endings:
            urls.append("{}speakers{}".format(speakers_base_url, ending))

    # loop through possible URLs for speakers site until a match is found
    loop_filendings = 0
    for url in urls:
        try:
            # try to open speakers file/website
            html_obj = open_website(url)
            # time delay to appear less bot-like (3 is a good number)
            time.sleep(3)
            if html_obj:
                # fetch speaker IDs from valid URL
                try:
                    speakers = find_speakers(html_obj)
                    # determine file ending if it's not yet known
                    if not file_ending:
                        file_ending = file_endings[loop_filendings]
                        print(file_ending)
                # unforseen exception
                except Exception as err:
                    print("ERROR: Cannot fetch speakers from file.")
                    print("An unexpected error occurred on line {}:".format(
                        sys.exc_info()[-1].tb_lineno))
                    print(err)
                    sys.exit(1)
                break
            loop_filendings += 1
        except ValueError as err:
            print("ERROR: Value entered is not a valid URL.")
            print(err)
        except TypeError as err:
            print(err)
            sys.exit(1)

    # print("---")

    # variables for speakers/twitters before any inserts
    count_s_b4 = 0
    count_t_b4 = 0

    # total no. of speakers
    total_speakers = len(speakers)
    # start counting up speakers
    count_speakers = 1

    # DB – SPEAKERS BLOCK
    if total_speakers > 0:
        # display no. of speakers found
        print("{} speaker(s) found".format(total_speakers))
        print("---")

        # connect to the DB / create it if doesn't exist
        try:
            # connect to the DB / create it if doesn't exist
            db = db_connect(dir_path, db_name, table, year)

            # get current speaker values from DB
            try:
                # get speaker IDs + names
                db_speakers_b4 = db_query(dir_path, db, table, column='name')
            # unforseen exception
            except Exception as err:
                print("An unexpected error occurred on line {}:".format(
                    sys.exc_info()[-1].tb_lineno))
                print(err)

           # try to update db with new values
            try:
                # fill table for speakers with IDs + name
                db_write(dir_path, db, table, speakers=speakers)
            # unforseen exception
            except Exception as err:
                print("An unexpected error occurred on line {}:".format(
                    sys.exc_info()[-1].tb_lineno))
                print(err)
                sys.exit(1)

            # get new speaker values from DB after write
            try:
                db_speakers_after = db_query(dir_path, db, table, column='name')
            # unforseen exception
            except Exception as err:
                print("An unexpected error occurred on line {}:".format(
                    sys.exc_info()[-1].tb_lineno))
                print(err)
                sys.exit(1)

        # unforseen exception
        except Exception as err:
            print("An unexpected error occurred on line {}:".format(
                sys.exc_info()[-1].tb_lineno))
            print(err)
            sys.exit(1)

    # parse individual speaker pages
    if total_speakers > 0:
        # parse all speakers' profiles
        for speaker_id, name in speakers.items():
            # display the how-many-th speaker is queried
            print("Speaker #{} of {}".format(count_speakers, total_speakers))
            # time delay to appear less bot-like (3 is a good number)
            time.sleep(3)
            speaker_url = "{}speakers/{}{}".format(speakers_base_url,
                                                   speaker_id, file_ending)
            # return speaker's twitter handle if applicable
            twitter_handle = parse_speaker_profile(speaker_url)
            # and add it to the twitters dictionary
            if twitter_handle:
                print("Twitter: {}".format(twitter_handle))
                twitters[speaker_id] = twitter_handle
            count_speakers += 1

        # display the no. of twitter handles provided;
        # not the same as twitter handles inserted!
        print("---")
        if twitters:
            print("{} Twitter handle(s) detected:".format(len(twitters)))
            for speaker_id, twitter in twitters.items():
                print("@{}\t".format(twitter), end='')
            print('')
        else:
            print("Found no Twitter handles in Fahrplan.")
    else:
        print("Found no speakers in Fahrplan.")

    # DB – TWITTER BLOCK
    # DB – STATUS MESSAGES

    # start printing status messages now
    print("---")
    print("DB status: ", end='')

    if db_speakers_b4:
        count_s_b4 = len(db_speakers_b4)
        print("{} speaker(s) currently saved.".format(count_s_b4))

        # get current twitter values from DB
        # this query only makes sense if there are speakers to begin with
        try:
            db_twitter_before = db_query(dir_path, db, table, column='twitter')
        # unforseen exception
        except Exception as err:
            print("An unexpected error occurred on line {}:".format(
                sys.exc_info()[-1].tb_lineno))
            print(err)

        if db_twitter_before:
            count_t_b4 = len(db_twitter_before)
    else:
        print("The database contains no speakers so far.")

    # try to update db with new values
    try:
        # update table for speakers with twitter handles where applicable
        db_write(dir_path, db, table, twitter=twitters)

        # if there are entries for speakers in the DB after speakers write, get them
        if db_speakers_after:
            count_s_aft = len(db_speakers_after)
            # update speakers count if there are more DB entries now than before
            if count_s_aft > count_s_b4:
                print("Updating...")
                print("DB status: {} speaker(s) now saved.".format(
                    count_s_aft))
            else:
                print("No new speakers retrieved.")

            # compare values in DB with values obtained via request
            s_changed, s_deleted = compare_values(db_speakers_after,
                                                  speakers)

            # get new twitter values from DB after write
            try:
                db_twitter_after = db_query(dir_path, db, table,
                                            column='twitter')
            # unforseen exception
            except Exception as err:
                print("An unexpected error occurred on line {}:".format(
                    sys.exc_info()[-1].tb_lineno))
                print(err)

            # if there are Twitter handles in the DB, get them
            if db_twitter_after:
                count_t_aft = len(db_twitter_after)
                # print count if there are more Twitter handles now than before
                if (count_t_aft > count_t_b4) and (count_t_b4 != 0):
                    print(
                        "DB status: {} new Twitter handle(s) saved.".format(
                            count_t_aft - count_t_b4))

            # compare Twitter values currently in DB with new values
            t_changed, t_deleted = compare_values(db_twitter_after,
                                                  twitters)

            if s_changed or s_deleted or t_changed or t_deleted:
                print("---")
                print("ATTENTION:")
                for key, value in s_deleted.items():
                    print(
                        u"\u2717 Speaker {} (id {}) is not listed in the Fahrplan anymore.".format(
                            value, key))
                for key, value in s_changed.items():
                    print(
                        u"\u2717 Speaker {} (id {}) has changed to {} in the current Fahrplan.".format(
                            db_speakers_after[key], key, value))
                for key, value in t_deleted.items():
                    if key not in s_deleted:
                        print(
                            u"\u2717 Twitter @{} (id {}) is not listed in the Fahrplan anymore.".format(
                                value, key))
                for key, value in t_changed.items():
                    print(
                        u"\u2717 Twitter @{} (id {}) has changed to @{} in the current Fahrplan.".format(
                            db_twitter_after[key], key, value))
                print(
                    "You might want to look into these changes and fix them manually.")

    # unforseen exception
    except Exception as err:
        print("An unexpected error occurred on line {}:".format(
            sys.exc_info()[-1].tb_lineno))
        print(err)


if __name__ == "__main__":
    main()
