from __future__ import print_function, division

import sys
import os
import time
import random
import socket
import string
import urllib2

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

                channel = args[0]
                if channel == self.nickname:
                    # Someone sent a private message, to send a private message back we have to use their name as a channel
                    channel = name
                    alwaysTalk = True

                inputstring = args[1]
                inputstring = inputstring[:-2]
                if self.nickname.lower() in inputstring.lower() or alwaysTalk:
                    time.sleep(0.8)
                    if "website" in inputstring.lower():
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

radika = Bot()
radika.connect()
time.sleep(2)
radika.join("#/div/ination")
radika.socket.setblocking(False)
while True:
    radika.receive()
    radika.handleinput()
