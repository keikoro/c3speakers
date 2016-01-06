import configparser
import sqlite3
import os
import sys
import json
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
    year = date.today().year

    # get vars from config file
    config = configparser.ConfigParser()
    config.read('config.txt')
    dir_path = config.get('db', 'dir_path')
    db_name = config.get('db', 'db_name')
    table = config.get('db', 'table')

    if dir_path:
        dir_path = os.getcwd() + '/'

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

    count = 0
    exists = 0

    t = Twitter(auth=OAuth(atoken, atoken_secret, ckey, ckey_secret))

    try:
        result = t.lists.list(screen_name=username, reversed='true')
    # TODO less broad exceptions
    except Exception as err:
        raise err

    with open(output_file, 'a', encoding='utf8') as outfile:
        for twitter_list in result:
            # check slugs of all lists
            slug = result[count]['slug']
            # check if requested list exists
            if slug == list_slug:
                exists = 1
                json.dump(twitter_list, outfile)
            count += 1
        # if requested list does not exist, create it
        # and make it a private list for now
        if exists == 0:
            try:
                t.lists.create(name=list_slug, mode='private')
                print("Created Twitter list {}!".format(list_slug))
            # TODO less broad exceptions
            except Exception as err:
                raise err


if __name__ == "__main__":
    main()
