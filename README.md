# c3speakers

A programm to find all [CCC](https://en.wikipedia.org/wiki/Chaos_Communication_Congress) (Chaos Communication Congress) [speakers](https://events.ccc.de/congress/2015/Fahrplan/speakers.html) for a given year, store their names and Twitter handles (where applicable)
into an SQLite database and to add all found Twitter handles to a Twitter list.

## Files & dependencies
**c3speakers.py**, the script for finding speakers and storing their data works independently of **twittering.py**.

**twittering.py**, which is used to create a Twitter list and add speakers' Twitter handles to it, on the other hand, needs **c3speakers.py** to work. To use the Twitter script, you also need to create a [Twitter app](https://apps.twitter.com/) and add your Twitter credentials (consumer key + secret, access token + secret, user name) to **config_twitter.py** (which is provided in the form of a template **config_twitter.py.template**).

Both scripts depend on the existence of **config.txt**, which contains variables for setting the path to the preferred directory for saving the database(s), as well as default names for the database and table. These variables can be changed by the user at any time without having to dig through the actual program code, or they can be used as-is.