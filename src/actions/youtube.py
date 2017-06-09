"""YouTube Plugin for AIY Projects

Author: 
    busyman96
    https://github.com/gabriel-micle/aiyprojects-raspbian

This is my (eduncan911) modifications to get it working with a plugin approach.

Usage:

    > "Hey Google, youtube <track name>"

    And press the GPIO button to stop.

Examples:

    > "Hey Google, youtube Baby Songs"
    < "Now playing Baby Songs"
    
    > "Hey Google, youtube Humble"
    < "Now playing Kendrick Lamar HUMBLE"

Setup:

    Note that this will require the main media player VLC installed along
    with Python VLC bindings.  I tried to find just the basic libs, instead
    of the full VLC media app but failed to find all.  Therefore, you must
    install the entire application:

        $ sudo apt-get install vlc
    
    If you have the AIYProjects SD card image, activate your virtualenv
    and install:

        $ source env/bin/activate
        $ pip3 install python-vlc youtube_dl

    If you have a custom image, install however you are managing python
    packages for your install.  virtualenv, 
    "sudo pip3 install python-vlc youtube_dl", etc.

Known errors:

    Upon startup, you may see errors such as this:

        [018ba7a0] pulse audio output error: PulseAudio server connection failure: Connection refused

    This seems to be expected if you are using a different audio device, like
    the Voice HAT by Google's AIYProject.

    Another error, and crash, is related when you ask for a station that has a
    grouping.  I've raised the issue with the author so it may be fixed in the
    future.
"""""

import youtube_dl
import json 
import re
import RPi.GPIO as GPIO
import time
import urllib
import vlc
import logging

def Register(say, actor):
    """Registers the YouTube plugin"""
    
    actor.add_keyword(_('youtube'), YouTubePlayer(say,_('youtube')))


class YouTubePlayer(object):
    """Plays song from YouTube."""
    
    def __init__(self, say, keyword):
        self.say = say
        self.keyword = keyword
        self._init_player()
        self._init_gpio(23)
        logging.info("youtube: registered keyword '%s'", self.keyword)
        
    def run(self, voice_command):
    
        track = voice_command.lower().replace(self.keyword, '', 1).strip()
        
        if not track:
            self.say('Please specify a song')
            return
        
        logging.info("youtube: track '%s'", track)
        ydl_opts = {
            'default_search': 'ytsearch1:',
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
        }
        
        meta = None
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                meta = ydl.extract_info(track, download=False)
        except Exception as e:
            logging.error("youtube: 'failed to find %s' %s", track, e)
            self.say('Failed to find ' + track)
            return
        
        if not meta:
            logging.info("youtube: 'failed to find %s', meta is None", track)
            self.say('Failed to find ' + track)
            return
            
        track_info = meta['entries'][0]
        if not track_info:
            logging.info("youtube: 'failed to find %s', track_info is None", track)
            self.say('Failed to find ' + track)
            return
   
        url = track_info['url']
        logging.info("youtube: opening url %s", url)
        media = self.instance.media_new(url)
        self.player.set_media(media)
   
        # Keep only words and use negative lookahead and lookbehind to remove '_'
        pattern = r'(?!_)\w+(?<!_)'
        self.now_playing = ' '.join(re.findall(pattern, track_info['title']))
        logging.info("youtube: 'now playing %s'", self.now_playing)
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
