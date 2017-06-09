"""TuneIn Plugin for AIY Projects

Author: 
    busyman96
    https://github.com/gabriel-micle/aiyprojects-raspbian

Basic instructions found at:
    https://www.raspberrypi.org/forums/viewtopic.php?f=114&t=185227#

Usage:

    > "Hey Google, radio <station_name>"

    And press the GPIO Button to stop.

Examples:

    > "Hey Google, radio WNYC"
    < "Now playing wnyc"
    
    > "Hey Google, radio KERA"
    < "Now playing kera"

Setup:

    Note that this will require the main media player VLC installed along
    with Python VLC bindings.  I tried to find just the basic libs, instead
    of the full VLC media app but failed to find all.  Therefore, you must
    install the entire application:

        $ sudo apt-get install vlc
    
    If you have the AIYProjects SD card image, activate your virtualenv
    and install:

        $ source env/bin/activate
        $ pip3 install python-vlc

    If you have a custom image, install however you are managing python
    packages for your install.  virtualenv, "sudo pip3 install python-vlc", 
    etc.

Known errors:

    Upon startup, you may see errors such as this:

        [018ba7a0] pulse audio output error: PulseAudio server connection failure: Connection refused

    This seems to be expected if you are using a different audio device, like
    the Voice HAT by Google's AIYProject.

    Another error, and crash, is related when you ask for a station that has a
    grouping.  I've raised the issue with the author so it may be fixed in the
    future.
"""

import json 
import re
import RPi.GPIO as GPIO
import time
import urllib
import vlc
import logging

def Register(say, actor):
    """Registers this plugin with the AIYProject"""

    actor.add_keyword(_('tunein'), TuneInRadio(say,_('tunein')))

class TuneInRadio(object):
    """Plays a radio stream from TuneIn radio"""
    
    BASE_URL = 'http://tunein.com/'
    FILTER_STATIONS = 'Stations'
    
    def __init__(self, say, keyword):
        self.say = say
        self.keyword = keyword
        self._init_player()
        self._init_gpio(23)
        logging.info("tunein: registered keyword '%s'", self.keyword)
        
    def run(self, voice_command):
        
        search_str = voice_command.lower().replace(self.keyword, '', 1).strip()
     
        if not search_str:
            logging.info("tunein: 'please specify a station'")
            self.say('Please specify a station')
            return
     
        logging.info("tunein: searching for '%s'", search_str)
        stations = self._search(search_str)
        if not stations:
            logging.info("tunein: 'didn't find any stations'")
            self.say("Didn't find any stations")
            return
            
        station = stations[0]
        url = self._get_stream_url(station['Id'])
        if not url:
            logging.info("tunein: 'didn't find any streams'")
            self.say("Didn't find any streams")
            return
        
        logging.debug(url)
        logging.info("tunein: attempting %s", url)
        media = self.instance.media_new(url)
        self.player.set_media(media)
        
        self.now_playing = station['Title']
        logging.info("tunein: 'now playing %s'", self.now_playing)
        self.say('Now playing ' + self.now_playing)
        
        self.player.play()

        self.done = False
        while not self.done:
            time.sleep(1)
            
    def _init_gpio(self, channel, polarity=GPIO.FALLING, pull_up_down=GPIO.PUD_UP):
        self.input_value = polarity == GPIO.RISING
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(channel, GPIO.IN, pull_up_down=pull_up_down)
        try:
            GPIO.add_event_detect(channel, polarity, callback=self._on_input_event)
        except RuntimeError:
            logging.info('Event already added')
            GPIO.add_event_callback(channel, self._on_input_event)
    
    def _init_player(self):
        self.now_playing = None
        self.done = False
        self.instance = vlc.get_default_instance()
        self.player = self.instance.media_player_new()
        events = self.player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_player_event)
        events.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_player_event)
    
    def _on_input_event(self, channel):
        if GPIO.input(channel) == self.input_value:
            self.player.stop()
            self.done = True
            
    def _on_player_event(self, event):
        if event.type == vlc.EventType.MediaPlayerEndReached:
            self.done = True
        elif event.type == vlc.EventType.MediaPlayerEncounteredError:
            self.say("Can't play " + self.now_playing)
            self.done = True

    def _search(self, search_str, search_filter=FILTER_STATIONS):
    
        ret_results= None
        
        url = TuneInRadio.BASE_URL + 'search/?query=' + urllib.parse.quote(search_str)
        logging.debug(url)
        req = urllib.request.Request(url)
        fp = urllib.request.urlopen(req)
        xml_str = fp.read().decode('ascii', 'ignore')
        fp.close()
        
        pattern = r'TuneIn.payload = (\{.*\})'
        result = re.search(pattern, xml_str)
        
        if not result:
            return None
        
        payload = result.group(1)
        result = json.loads(payload)
        
        categories = result['ContainerGuideItems']['containers']
        for category in categories:
            if category['Title'] == search_filter:
                ret_results = category['GuideItems']
                break;
        
        return ret_results
                
    def _get_stream_url(self, station_id):
    
        url = TuneInRadio.BASE_URL + 'station/?stationId=' + str(station_id)
        logging.debug(url)
        req = urllib.request.Request(url)
        fp = urllib.request.urlopen(req)
        xml_str = fp.read().decode('ascii', 'ignore')
        fp.close()
        
        pattern = r'"StreamUrl":"(.*?)"'
        result = re.search(pattern, xml_str)
        
        logging.info("tunein: resulting groups: %s", result)

        if not result:
            return None

        if not result.group(1):
            return None
        
        json_url = 'http:' + result.group(1)
        streams = self._get_stream_list(json_url)
        
        if not streams:
            return None
            
        stream = streams[0]
        return stream['Url']
        
    def _get_stream_list(self, url):
        
        logging.debug(url)
        req = urllib.request.Request(url)
        fp = urllib.request.urlopen(req)
        json_str = fp.read().decode('ascii', 'ignore')
        fp.close()
        
        result = json.loads(json_str)
        return result['Streams']

