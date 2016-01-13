# c3speakers

A command line-based Python3 programm to find all [CCC](https://en.wikipedia.org/wiki/Chaos_Communication_Congress) (Chaos Communication Congress) [speakers](https://events.ccc.de/congress/2015/Fahrplan/speakers.html) for a given year, store their names and Twitter handles (where applicable)
into an SQLite database and to add all found Twitter handles to a Twitter list.


* [Setup](#setup)
* [Usage](#usage)
  * [Main script: c3speakers\.py](#main-script-c3speakerspy)
    * [Options](#options)
      * [Help](#help)
      * [Find speakers by year](#find-speakers-by-year)
      * [Find speakers by congress shortcut](#find-speakers-by-congress-shortcut)
      * [Use Fahrplan mirrors or local files](#use-fahrplan-mirrors-or-local-files)
  * [Twitter script: twittering\.py](#twitter-script-twitteringpy)
* [License](#license)

## Setup

To prepare your Python virtual environment for running the c3speakers scripts, run ```setup.py``` to download all necessary libraries from PyPI:

    $ python3 setup.py install

You can then remove some unneeded files introduced by the setup process, with:

    $ python3 setup.py clean

Next, you might want to review the variables defined for default paths and names in `config.txt`, and possibly change them to suit your needs.

To use the Twitter-based script `twittering.py`, you will also need to create a [Twitter app](https://apps.twitter.com/) and add your Twitter credentials (consumer key & secret, access token & secret, and user name) to `config_twitter.py` (for which the template  `config_twitter.py.template` is provided).


## Usage

### Main script: c3speakers.py

To find all C3 speakers for the current year – *if* a *Fahrplan* (schedule) has already been made publicly available –, run:

    $ python3 c3speakers.py

This will query all speaker data on the speakers overview page of the official C3 Fahrplan (usually <a href="https://events.ccc.de/congress/YYYY/Fahrplan/speakers.html">https://events.ccc.de/congress/YYYY/Fahrplan/speakers.html</a>) and look for Twitter links on all individual speaker profiles.

Every found speaker's ID, name and Twitter handle (where applicable) will subsequently be saved into an SQLite database for the queried congress. The default filename for the db is ```speakersYYYY.sqlite```, the default save location is the current working directory.

#### Options

##### Help
Run the script with the ```-h``` flag set to be shown all possible command line arguments:

    $ python3 c3speakers.py -h

##### Find speakers by year
If you want to find all speakers for a particular year, you can specify that year by starting the script with the ```-y``` argument set:

    $ python3 c3speakers.py -y 2010


##### Find speakers by congress shortcut
You can also look up all speakers for a particular congress by providing its typical shortcut (e.g. 30C3 for the 30th CCC) with the ```-c``` option:

    $ python3 c3speakers.py -c 28C3


##### Use Fahrplan mirrors or local files
To query a different website than the official Fahrplan page provided by Chaos Communication Club, or a local file, use ```-u``` and the URL or file path to ```speakers.html```:

    $ python3 c3speakers.py -u /Users/JarJar/Desktop/CCC/2010/Fahrplan/speakers.html

Note that currently, Fahrplan mirrors and local files need to contain the directory structure ```/YYYY/Fahrplan/``` or ```/XXC3/Fahrplan/``` and end in ```speakers(...).html``` to be accepted.

### Twitter script: twittering.py

The file ```twittering.py``` is a script with which you can add all speakers' Twitter accounts collected with ```c3speakers.py``` to a (private) Twitter list attached to your Twitter account.

Please refer to the **Setup** section above to make sure you have properly configured the variables the script depends on.

The script is run by entering:

    $ python3 twittering.py

Note that currently, ```twittering.py``` only works for the current year and creates a list with the fixed name/slug ```CCC-XXC3-speakers``` (where ```XXC3``` is the congress shortcut) based on the assumption that equivalent Twitter lists for previous years have already been created.

## License

c3speakers is released under the [MIT License](LICENSE).