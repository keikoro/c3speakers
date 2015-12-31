import sys
import getopt
import requests
import re
import time
from urllib.request import urlopen
from datetime import date
from bs4 import BeautifulSoup, SoupStrainer
from c3urls import *


def hello_world():
    """Example function."""
    hello = "Hello, world!"
    return hello


def usage():
    howto = "Usage: python3 %s -y YEAR -u URL" % str(sys.argv[0])
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


def open_speakers_file(url):
    """Open the file/website listing all C3 speakers for a given year.
    :param url: website address of C3 Fahrplan speakers info

    previous URLs e.g.:
    https://events.ccc.de/congress/2015/Fahrplan/speakers.html
    https://events.ccc.de/congress/2012/Fahrplan/speakers.en.html
    https://events.ccc.de/congress/2010/Fahrplan/speakers.de.html
    """

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

    return True, html


def find_speakers(html_obj):
    """
    Find URLs to speakers pages in speakers.html
    :param html: the html object to parse with Beautiful Soup
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
        regex = ".+/speakers/([0-9]+).html"
        href = item['href']
        speaker_id = re.match(regex, href).group(1)
        value = item.get_text()
        # debug
        print(str(speaker_id) + ": " + value)
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
    check_url = open_speakers_file(url)
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
            value = twitter_account.get_text()
            # debug
            print(str(speaker_twitter))


def main():
    table = 'speakers'
    year = date.today().year

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'yu:h', ['year=', 'url=', 'help'])
    except getopt.GetoptError as err:
        print(usage())
        print(err)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(usage())
        elif opt in ('-y', '--year'):
            year = arg
        elif opt in ('-u', '--url'):
            url = arg
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

    # possible speaker URLs
    # based on previous congresses

    # TODO
    # let user input alternative URLs
    # (for Fahrplan mirrors)
    urls = (
        "https://events.ccc.de/congress/" + str(
            year) + "/Fahrplan/speakers.html",
        "https://events.ccc.de/congress/" + str(
            year) + "/Fahrplan/speakers.en.html"
    )

    # test urls (on and offline)
    urls = (
            headertest,
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
            check_url = open_speakers_file(url)
            status = check_url[0]
            html_obj = check_url[1]
            if status is True:
                print(url)
                try:
                    # fetch speaker IDs from valid URL
                    speakers = find_speakers(html_obj)
                    print("---")
                    # display the no. of speakers that was found
                    if len(speakers) > 0:
                        print(len(speakers), "speakers, all in all")
                    else:
                        print("No speakers found.")
                except Exception as err:
                    print("ERROR: No speakers found.")
                    sys.exit(1)
                break
        except ValueError as err:
            print("ERROR: Value entered is not a valid URL.")
            print(err)



    speakers = (speaker_test_1,
               speaker_test_2
               )

    # parse speakers profiles
    for speaker in speakers:
        # time delay to appear less bot-like
        time.sleep(2)
        parse_speaker_profile(speaker)




if __name__ == "__main__":
    main()