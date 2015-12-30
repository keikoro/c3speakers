import sys
import getopt
import requests
import re
from urllib.request import urlopen
from datetime import date
from bs4 import BeautifulSoup, SoupStrainer
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


def find_speakers(html):
    """
    Find URLs to speakers pages in speakers.html
    :param html: the html object to parse with Beautiful Soup
    """

    # only look for URLs
    # which contain '/speakers/'
    # and which contain no other tags
    parse_links = SoupStrainer('a')
    filter_links = re.compile("(/speakers/)")
    filter_contents = re.compile(".*")
    soup = BeautifulSoup(html, 'html.parser', parse_only=parse_links)

    # print out all valid URLs
    for item in soup.find_all('a', href=filter_links, string=filter_contents):
        # filter_id = re.compile("/speakers/([0-9]+).html")
        regex = ".+/speakers/([0-9]+).html"
        href = item['href']
        speaker_id = re.match(regex, href).group(1)
        value = item.get_text()
        print(href)
        print(str(speaker_id) + " - " + value)


def parse_speaker_profile(id):
    """
    """
    pass



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
    urls = (testurl_offnon,
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
                find_speakers(html_obj)
                break
        except ValueError as err:
            print(err)


if __name__ == "__main__":
    main()
