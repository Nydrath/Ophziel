from __future__ import print_function, division

import sys
import os
import time
import random
import socket
import string
import urllib2

from PIL import Image
from imgurpython import ImgurClient

import decks

def parsemsg(s):
    # Stolen from Twisted. Parses a message to it's prefix, command and arguments.
    prefix = ''
    trailing = []
    if s == "":
        print("Empty line.")
    if s[0] == ':':
        prefix, s = s[1:].split(' ', 1)
    if s.find(' :') != -1:
        s, trailing = s.split(' :', 1)
        args = s.split()
        args.append(trailing)
    else:
        args = s.split()
    command = args.pop(0)
    return prefix, command, args


class Bot:
    def __init__(self, host='eu.sorcery.net', port=9000):
        self.host = host
        self.port = port

        self.nickname = self.ident = self.realname = "Ophziel"

        self.receiveBuffer = ""

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client_id = '05c4e4c8869eb82'
        client_secret =  '711339dbcc785ad5d2da165e9bf6b22f0f4b8136'
        self.imgurclient = ImgurClient(client_id, client_secret)

        self.runeworker = None

    def connect(self):
        self.socket.connect((self.host, self.port))
        self.send("NICK {0}".format(self.nickname))
        self.send("USER {0} 0 * :{1}".format(self.ident, self.realname))

    def send(self, msg):
        self.socket.send('{0}\r\n'.format(msg).encode())

    def sendmsg(self, chan, msg):
        self.send("PRIVMSG "+chan+" :"+msg)

    def receive(self):
        self.receiveBuffer = ""
        try:
            self.receiveBuffer=self.socket.recv(1024)
        except socket.error, e:
            if e.args[0] != 11:
                # We don't just have a "no data received" error
                with open("errors", "w") as f:
                    print(e, file=f)
                sys.exit(1)
        temp=string.split(self.receiveBuffer, "\n")
        for line in temp:
            try:
                line=string.rstrip(line)
                line=string.split(line)
            
                if(line[0]=="PING"):
                    self.socket.send("PONG %s\r\n" % line[1])
            except:
                pass

    def join(self, channel):
        self.send("JOIN {0}".format(channel))

    def handleinput(self):
        if len(self.receiveBuffer) > 0:
            alwaysTalk = False
            prefix, command, args = parsemsg(self.receiveBuffer)

            if command == "PRIVMSG":
                name = prefix[:prefix.index("!")]
                name = name.replace("Chirobot", "C.")
                name = name.replace("Deltabot", "D.")

                channel = args[0]
                if channel == self.nickname:
                    # Someone sent a private message, to send a private message back we have to use their name as a channel
                    channel = name
                    alwaysTalk = True

                inputstring = args[1]
                inputstring = inputstring[:-2]
                if self.nickname.lower() in inputstring.lower() or alwaysTalk:
                    time.sleep(0.8)
#                    if "website" in inputstring.lower():
                    if False:
                        card = urllib2.urlopen("http://www.randomwebsite.com/cgi-bin/random.pl").geturl()
                    else:
                        if "rw" in inputstring.lower():
                            deck = decks.RW_DECK
                        elif "rune" in inputstring.lower():
                            deck = decks.RUNES
                        else:
                            deck = decks.THOTH
                        if "spread" in inputstring.lower():
                            card = ' / '.join(random.sample(deck, 3))
                        else:
                            card = random.choice(deck)
                    self.sendmsg(channel, name+": "+card)

    def checkrunes(self):
        if self.runeworker != None:
            if not self.runeworker.done:
                self.runeworker.work()
            else:
                upload = self.imgurclient.upload_from_path(os.getcwd()+"/runethrow.png")
                self.sendmsg(self.runeworker.channel, self.runeworker.querent+": "+upload['link'])
                self.runeworker = None

class RuneWorker:
    RUNEWIDTH = 149
    RUNEHEIGHT = 197
    IMAGE_WIDTH = RUNEWIDTH*5
    IMAGE_HEIGHT = RUNEHEIGHT*2

    # This class relies on each function happening fast enough that the IRC won't disconnect the bot, to simulate nonblocking.
    # As such, it isn't guaranteed portable anymore. Ugly, but only way I know of without using subprocess.

    def __init__(self, channel, querent, runes):
        self.done = False
        self.channel = channel
        self.querent = querent
        self.images = []
        self.runenames = runes
        self.positions = []
        self.background = Image.new('RGB', (self.IMAGE_WIDTH, self.IMAGE_HEIGHT), (0,0,0))

    def work(self):
        if len(self.runenames) > 0:
            # We're not done opening all the runes yet, unpack the next one
            rune = self.runenames.pop(0)
            index = decks.RUNES.index(rune)
            name = "[{0}] ".format(index+1) + rune.split()[0] + ".png"
            self.images.append(Image.open("Runes/"+name))
        elif len(self.images) > 0:
            # We're not done pasting all the images yet, paste the next one
            while True:
                x, y = random.randint(1, self.IMAGE_WIDTH-self.RUNEWIDTH), random.randint(1, self.IMAGE_HEIGHT-self.RUNEHEIGHT)
                colliding = False
                for otherx, othery in self.positions:
                    if x in range(otherx-self.RUNEWIDTH-1, otherx+self.RUNEWIDTH+1) and y in range(othery-self.RUNEHEIGHT-1, othery+self.RUNEHEIGHT+1):
                        colliding = True
                        break
                if not colliding:
                    break
            # We have the future position of this rune
            self.positions.append((x, y))
            self.background.paste(self.images.pop(0), (x, y))
        else:
            self.background.save("runethrow.png")
            self.done = True
            

radika = Bot()
radika.connect()
time.sleep(2)
radika.join("#/div/ination")
radika.join("#ophziel")
radika.socket.setblocking(False)
t = time.time()
while True:
    radika.receive()
    radika.handleinput()
    dt = t + 1/30.0 - time.time()
    if dt > 0: time.sleep(dt)
