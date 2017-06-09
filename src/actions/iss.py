"""International Space Station Plugin

Author: Eric Duncan (@eduncan911)
        http://eduncan911.com/stem/iss-plugin.html

This plugin enables functionality around the International Space Station.
Full source code and documentaiton is located at:

    https://github.com/eduncan911/iss/cmd/iss-monitor

Examples:

    > "Hey Google, is there a space station showing tonight?"
    > "Hey Google, where is the space station right now?"
    > "Hey Google, when is the next space station fly [pass] over?"

This plugin will not work without setting a few things up first.  You must
configure your system or an error will be spoken.

Setup:

    Install the background service that receives the Weather and ISS
    details required for the module.  The commands below will:

        * install Golang, if not already installed.
        * download and build a background utility
        * run a script that creates a background service (under "pi" user)
        * enable the background service
        * start the background service

    $ sudo apt-get install golang
    $ go install github.com/eduncan911/iss/cmd/iss-monitor
    $ ~/go/src/github.com/eduncan911/iss/cmd/iss-monitor/setup.sh
    $ systemctl enable pi@iss-monitor.service
    $ systemctl start pi@iss-monitor.service

Below we will need to configure the service.  To enable Worldwide adoption
of this plugin, we need to get two custom URLs that the service will use.
Yes, I could have automated this; but, it would have only been for the US
or UK and maybe Canada.  Making you go get the URLs manually, by finding
your locations around the world, ensures complete coverage Worldwide.

Get an RSS Feed from NASA for the International Space Station:

    You will need to figure out the Feed URL used by NASA to determine
    the location to reference.  They do not make this simple but instead
    require you to open a web browser and use their plugin.  Follow the
    steps below to "get the URL", which we will use later below in the
    iss-monitor.ini file.

        * https://spotthestation.nasa.gov/
        * Use the Interactive Map and find your exact location and click it.
        * On the next page, find the "RSS" button.
        * Keep that URL of the RSS link to use below.

Get an RSS Feed for your Weather Forecast:

    You will need another URL for your Weather Forecast.  

        * https://www.yr.no/ (language selector at top-right)
        * Type your location and view the weather. 
        * Keep that URL to use below.

Configuring the RSS Feeds:

    Finally, you will need to configure the service.  You will use the two
    URLs you found earlier in this file.  One for the ISS feed, and one for
    the Weather forecast for your area.

    $ nano ~/.config/iss-monitor.ini

    And follow the directions.

Todo:
"""

import logging

def Register(say, actor):
    """Register takes an actionbase.actor and creates actors for triggers."""
    
    actor.add_keyword(_('where is the space station'), SpotTheStation(say, 'where'))
    actor.add_keyword(_('when space station'), SpotTheStation(say, 'where'))
    actor.add_keyword(_('is there space station'), SpotTheStation(say, 'where'))
    actor.add_keyword(_('space station fly'), SpotTheStation(say, 'where'))
    actor.add_keyword(_('space station pass'), SpotTheStation(say, 'where'))


class SpotTheStation(object):
    """Spot the ISS"""
    def __init__(self, say, command):
        self.say = say
        self.command = command

    def run(self, voice_command):
        if self.command == "where":
            self.say("It looks like the next viewings are tonight at 9:02 PM and tomorrow at 10:01 PM")

        else:
            logging.error("ISS: could not determine command.")
            self.say("Sorry I couldn't look that up for the Space Station")

