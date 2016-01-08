#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import os
import sys
import urllib
import c3speakers
from twitter import *
from datetime import date
from twitterconfig import *


def main():
    c3 = 'C3'
    # max amount of twitter users to add to one list
    tmax = 100
    year = date.today().year

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
        twitters = c3speakers.db_query(dir_path, db, table, column='twitter')
    except TypeError as err:
        print(err)
        sys.exit(1)
    except ValueError as err:
        print(err)
        sys.exit(1)

    # create list out of dictionary values (for Twitter handles)
    try:
        twitters_list = list(twitters.values())
    # if twitters dictionary is empty
    except AttributeError:
        print("ERROR: No Twitter handles available to add to Twitter list.")
        sys.exit(1)

    # split list into smaller sublists + turn into comma-delimited strings
    # as Twitter only accepts max. 100 elements per create_all call
    composite_list = (', '.join(twitters_list[x:x + tmax]) for x in
                      range(0, len(twitters_list), tmax))

    list_count = 0
    exists = 0
    # Twitter connection & actions start here
    list_slug = "CCC-{}-speakers".format(c3_shortcut)

    # debug
    print("List slug: {}".format(list_slug))

    # connect to/authenticate with Twitter
    try:
        t = Twitter(auth=OAuth(atoken, atoken_secret, ckey, ckey_secret))
    # unforseen exception
    except Exception as err:
        print("An unexpected error occurred on line {}:".format(
            sys.exc_info()[-1].tb_lineno))
        print(err)
        sys.exit(1)

    # retrieve users lists (includes private lists)
    try:
        result = t.lists.list(screen_name=username, reversed='true')
    # raise exception in case connecting to Twitter is impossible
    except urllib.error.URLError:
        print("ERROR: Cannot connect to Twitter at this time.")
        sys.exit(1)
    # unforseen exception
    except Exception as err:
        print("An unexpected error occurred on line {}:".format(
            sys.exc_info()[-1].tb_lineno))
        print(err)
        print("Exiting program.")
        sys.exit(1)

    # iterate over all retrieved lists
    # to see if the new list to create/fill already exists
    for each_list in result:
        # check and try to match slugs of all retrieved lists
        # with slug for the new list
        slug = each_list['slug']
        if slug == list_slug:
            exists = 1
            print("Twitter list {} already exists".format(list_slug))
        list_count += 1

    # if the list does not exist yet, create it
    # and make it a private list for now
    if exists == 0:
        try:
            t.lists.create(name=list_slug, mode='private')
            print("Created Twitter list {}".format(list_slug))
        # raise exception in case connecting to Twitter is impossible
        except urllib.error.URLError:
            print("ERROR: Cannot connect to Twitter.\n"
                  "Creation of list {} impossible at this time.".format(list_slug))
        # unforseen exception
        except Exception as err:
            print("An unexpected error occurred on line {}:".format(
                sys.exc_info()[-1].tb_lineno))
            print(err)
            print("Exiting program.")
            sys.exit(1)

    print("---")

    # update the list with new list members
    # (non-existent Twitter accounts will be ignored)
    try:
        for sublist in composite_list:
            # use create_all to add up to 100 members at once
            # via comma-delimited string
            t.lists.members.create_all(slug=list_slug,
                                       owner_screen_name=username,
                                       screen_name=sublist)
            print(
                "Added new members to twitter list {}:\n{}".format(list_slug,
                                                                   sublist))
    # raise exception in case connecting to Twitter is impossible
    except urllib.error.URLError:
        print("ERROR: Cannot connect to Twitter at this time.")
        sys.exit(1)
    # unforseen exception
    except Exception as err:
        print("An unexpected error occurred on line {}:".format(
            sys.exc_info()[-1].tb_lineno))
        print(err)
        print("Exiting program.")
        sys.exit(1)


if __name__ == "__main__":
    main()
