import configparser
import sqlite3
import os
import sys
import json
import urllib
import c3speakers
from twitter import *
from datetime import date
from twitterconfig import *


def db_query(dir_path, table):
    """Update table in DB.
    :param dir_path:
    :param table: the table that should be modified
    """
    twitters = []

    try:
        # debug
        print(dir_path)
        db = sqlite3.connect(dir_path)
    except sqlite3.OperationalError:
        print("ERROR: Cannot connect to database.")
        return None

    # insert into table
    try:
        cur = db.cursor()
        cur.execute(
            "SELECT count(twitter) FROM {} WHERE twitter != '' ".format(table)
        )
        rows = cur.fetchone()
        print("{} results".format(rows[0]))
        print("---")
        cur.execute("SELECT * FROM {} "
                    "WHERE twitter != '' ".format(table)
                    )
        rows = cur.fetchall()
        db.commit()
        for row in rows:
            print(row[2])
            twitters.append(row[2])
        return twitters
    except sqlite3.OperationalError as err:
        # rollback on problems with db statement
        print(str(err))
        db.rollback()
    finally:
        db.close()


def main():
    c3 = 'C3'
    # TODO switch later
    # year = date.today().year
    year = 2015

    # get vars from config file
    config = configparser.ConfigParser()
    config.read('config.txt')
    dir_path = config.get('db', 'dir_path')
    db_name = config.get('db', 'db_name')
    table = config.get('db', 'table')

    # congress data for specified year
    try:
        year, c3_no = c3speakers.congress_data(year=year)
        c3_shortcut = "{}{}".format(c3_no, c3)
        # debug
        print("{} > {} ... this year".format(year, c3_shortcut))
    except ValueError as err:
        print(err)
        sys.exit(1)

    if not dir_path:
        dir_path = "{}/".format(os.getcwd())

    try:
        # connect to db
        db = c3speakers.db_connect(dir_path, db_name, table, year)
        # query for twitter accounts in db
        twitters = db_query(db, table)
        print(twitters)
    except TypeError as err:
        print(err)
    except ValueError as err:
        print(err)
        sys.exit(1)

    # split Twitter list into smaller lists with max. 100 elements
    # due to Twitter's create_all limit of 100 accounts per call
    # and immediately turn lists into strings
    composite_list = (', '.join(twitters[x:x+4]) for x in range(0, len(twitters), 4))

    # Twitter connection & actions start here
    # list_slug = "CCC-{}-speakers".format(c3_shortcut)
    count = 0
    exists = 0
    # debug
    # print(list_slug)

    # connect to/authenticate with Twitter
    try:
        t = Twitter(auth=OAuth(atoken, atoken_secret, ckey, ckey_secret))
    # TODO less broad exceptions
    except Exception as err:
        print(err)
        sys.exit(1)

    try:
        result = t.lists.list(screen_name=username, reversed='true')
    # raise exception in case we cannot connect to Twitter
    except urllib.error.URLError as err:
        print("ERROR: Cannot connect to Twitter at this time.")
        sys.exit(1)
    # unknown other exception > exit program
    except Exception as err:
        print("An error occurred. Exiting program.")
        print(err)
        sys.exit(1)

    with open(output_file, 'a', encoding='utf8') as outfile:
        for twitter_list in result:
            # check slugs of all lists
            slug = result[count]['slug']
            # check if requested list exists
            if slug == list_slug:
                exists = 1
                print("List {} already exists".format(list_slug))
                json.dump(twitter_list, outfile)
            count += 1
        # if requested list does not exist, create it
        # and make it a private list for now
        if exists == 0:
            try:
                t.lists.create(name=list_slug, mode='private')
                print("Created Twitter list {}".format(list_slug))
            # exception in case we cannot connect to Twitter
            except urllib.error.URLError:
                print("ERROR: Cannot connect to Twitter.\n"
                      "Creation of list {} impossible at this time.".format(list_slug))
            # unknown other exception > exit program
            except Exception as err:
                print("An error occurred. Exiting program.")
                print(err)
                sys.exit(1)

        # update existing twitter list with new list members
        try:
            for sublist in composite_list:
                # use create_all to add up to 100 members at once
                # via comma-delimited string
                t.lists.members.create_all(slug=list_slug, owner_screen_name=username, screen_name=sublist)
                print("Added new members to twitter list {}:\n{}".format(list_slug, sublist))
        # exception in case we cannot connect to Twitter
        except urllib.error.URLError:
            print("ERROR: Cannot connect to Twitter.\n"
                  "Adding new members to list {} impossible at this time.".format(list_slug))
        # unknown other exception > exit program
        except Exception as err:
            print("An error occurred. Exiting program.")
            print(err)
            sys.exit(1)

if __name__ == "__main__":
    main()
