#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# Purpose: an all-purpose IRC bot
# Maintainer: Jamie Duncan
#
# Based on original concept by Karl Abbot (kabbott@redhat.com)

import socket
import random
import sys
import os
import re
import time
import ConfigParser
from optparse import OptionParser

class ChatBot:

    def _loadConfigFile(self, config_file):
        '''
        loads the configuration file to read in the settings
        returns the ConfigParser object
        '''
        try:
            #load the config file
            config=ConfigParser.RawConfigParser()
            config.read(config_file)

            return config

        except:
            print "Cannot read config information", sys.exc_info()[0]
            raise


    def _connect(self):
        '''
        Will connect to a given IRC server
        '''

        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        irc.connect((self.server, self.port))
        irc.send("USER "+ self.nick +" "+ self.nick +" "+ self.nick +" :This is a fun ChatBot!\n") #user authentication
        irc.send("NICK "+ self.nick +"\n")                            #sets nick
        irc.send("PRIVMSG nickserv :iNOOPE\r\n")    #auth
        irc.send("JOIN "+ self.channel +"\n")        #join the chan
        irc.send("PRIVMSG " + self.channel +" :"+"This is "+self.nick+". I live to serve the good people of "+ str(self.channel) +".\r\n")

        return irc

    def _encodePayload(self, text):
        '''
        This will take a string, strip off the first word, and return the rest as a string with all special characters escaped.
        '''
        raw = text.split(':')[2].split(' ')[1:] #this strips the first word and returns the rest as a list. now we convert the list to a string

        payload = ''
        for i in range(0,len(raw)):
            payload += " %s" % raw[i]

        payload = re.escape(payload.lstrip())
        payload = "%s\n" % payload

        return payload

    def _cleanPayload(self, text):
        '''
        This will take an encoded string (like from a file) and clean it up for presentation
        '''
        payload = text.replace("\","").rstrip()

        return payload


    def _appendQuoteList(self, quote):
        '''
        adds a quote to the quote list file, escaping out any special characters
        '''
        try:
            f = open(self.quote_file,"a")
            new_line = self._encodePayload(quote)
            f.write(new_line)
            f.close()

            line = "Your quote has been added!"
            response = "PRIVMSG %s :%s\r\n" % (self.channel, line)

            return True

        except:
            print "Cannot add to Quote List", sys.exc_info()[0]
            raise

    def _retrieveQuote(self):
        '''
        retrieves a random quote from the quote list
        '''
        try:
            f = open(self.quote_file, "r")
            line = next(f)
            for num, aline in enumerate(f):
                if random.randrange(num + 2): continue
                line = aline
                line = self._cleanPayload(line)

            prep_line = "PRIVMSG %s :Prepping the Quote Engine...\r\n" % self.channel
            response = "PRIVMSG %s :%s\r\n" % (self.channel, line)

            self.conn.send(prep_line)
            self.conn.send(response)

            return True

        except IOError:
            self.conn.send("PRIVMSG " + self.channel +" :I'm sorry. I don't have any quotes right now.\r\n")

            return False

        except:
            print "Cannot Retrieve Random Quote", sys.exc_info()[0]
            raise

    def __init__(self, options):
        '''
        override the default config file if it's passed on the command line
        it returns the connected socket object, registered to a given channel
        '''

        self.config_file = options.config_file if options.config_file else os.path.expanduser('~/.chat_bot')

        config = self._loadConfigFile(self.config_file)

        #load some config parameters, giving preference to any command-line parameters passed
        self.server = options.server if options.server else config.get('server','server')
        self.port = int(options.port) if options.port else int(config.get('server','port'))
        self.nick = options.nick if options.nick else config.get('server','nick')
        channel = options.channel if options.channel else config.get('server','channel')
        self.channel = "#%s" % channel
        self.quote_file = options.quote_file if options.quote_file else config.get('plugins','quote_file')

        self.conn = self._connect()

    def _processPRIVMSG(self, text):
        '''
        takes the raw input from the socket and processes it to return just the stuff we want to evaluate
        this will in turn be processed and acted upon by the default functions and plugins
        '''
        #a few simple functions
        if text.find('.help') > -1:
            help_string = "ChatBot version %s: made by Jamie Duncan. 2012\r\n" % '0.1'
            self.conn.send("PRIVMSG " + self.channel +" :" + help_string)
        if text.find('.quote') > -1 and text.find('.quote-add') == -1:
            self._retrieveQuote()
        if text.find('.quote-add') > -1:
            self._appendQuoteList(text)
            self.conn.send("PRIVMSG " + self.channel +" :quote added!\r\n")


    def _sendPINGKeepAlive(self, response):
        '''
        this keeps the bot happy and alive within a channel by
        responding to the PING keep-alive requests from the chat server
        '''

        return_string = "PONG %s \r\n" % response.split()[1]
        self.conn.send(return_string)

    def handleChannel(self):
        '''
        This is the function that runs within the while loop.
        It essentially evaluates what type of message is coming by creating a while look and calls the proper processing function to act on it.
        PRIVMSG (comments into the channel) are handled by another function that includes (or will include) any future plugins
        '''
        while 1:
            text=self.conn.recv(4096)
            print text

            if text.find('PRIVMSG') > -1:
                self._processPRIVMSG(text)

            if text.find('PING') > -1:
                self._sendPINGKeepAlive(text)

def main():
    '''
    the primary function
    '''
    ver_string = '0.1'

    #the primary function that is called when this app is invoked.
    parser = OptionParser(usage="%prog [-c]", version="%prog " + ver_string)
    parser.add_option("-c", "--config", dest="config_file", help="config file, overriding default of ~/.chat-bot", metavar="CONFIG_FILE")
    parser.add_option("-C", "--channel", dest="channel", help="channel to join", metavar="CHANNEL")
    parser.add_option("-s", "--server", dest="server", help="server to connect to", metavar="SERVER")
    parser.add_option("-p", "--port", dest="port", help="server port", metavar="PORT")
    parser.add_option("-n", "--nick", dest="nick", help="nickname for IRC channel", metavar="NICK")
    parser.add_option("-q", "--file", dest="quote_file", help="quote file to save quotes", metavar="QUOTE_FILE")

    (options, args) = parser.parse_args()

    server = ChatBot(options)
    server.handleChannel()

if __name__ == '__main__':
    main()

'''
********************************************************************
'''


'''
    def process_text(text,bigX,dontsay):
        if len(text.split(":"))>=3:
            address=text.split(":")[2]
                fromnick=text.split(":")[1].split("!")[0]
                if len(text.split(":"))>=4:
                    command=text.split(":")[3].lstrip(" ")
                if len(fromnick.split(" "))==1 and (not address==self.nick):
                    if address.lower().find("nothing")>-1:
                        irc.send("PRIVMSG " + channel+" :"+fromnick+", could you make clear for me: "+address+" ?\r\n")
                    if address.lower().find("what")>-1 or address.lower().find("wat")>-1:
                        irc.send("PRIVMSG " + channel+" :"+fromnick+", a bag of cheetos. thats wat!\r\n")
                    if text.lower().find("has joined this channel")>-1:
                        name=text.lower().split(">")[1].split(" ")[0]
                        irc.send("PRIVMSG " + channel+" :Hi there "+name+"! Welcome to "+channel+"!\r\n")
                    if address.lower().find(self.nick)>-1:
                        time.sleep(int((random.random()*10)))
                        a_quote=random.choice(quote)
                        while dontsay.has_key(quote.index(a_quote)):
                            a_quote=random.choice(quote)
                            dontsay[quote.index(a_quote)]=quote.index(a_quote)
                    if len(dontsay)==len(quote)-2:
                        dontsay={}
                    if bigX==1 or bigX==8:
                        irc.send("PRIVMSG " +channel+" :ma word, yalls talking about me agin!\r\n")
                    if bigX==2 or bigX==5:
                        irc.send("PRIVMSG " +channel+" :Remember when I used to say: "+a_quote+"\r\n")
                    if bigX==0 or bigX==4 or bigX==7 or bigX==9:
                        irc.send("PRIVMSG " + channel + " :here's one you've never heard before: " +a_quote+"\r\n")
                    if bigX==1 or bigX==3:
                        irc.send("PRIVMSG " + channel + " :Let it be written in the Great Book of Konglish: " + a_quote+"\r\n")
                    if bigX==3 or bigX==9:
                        time.sleep(int((random.random()*10)))
                        irc.send("PRIVMSG " + channel+" :lulz...i crack myself up\r\n")
                    if bigX==6:
                        irc.send("PRIVMSG " + channel+" :could you be more boring?\r\n")
                    if bigX==8:
                        irc.send("PRIVMSG " + channel+" :book of konglish blah blah blah....get back to work.\r\n")
                    if address.lower().find("fighTING")>-1:
                        irc.send("PRIVMSG " + channel+" :"+fromnick+", fighTING!!\r\n")
                    if address.lower().find("define")>-1:
                        defstring=text.split("define")[1].split(" ")[1].rstrip("\n").rstrip(" ").rstrip("\r")
                        think=0
                        irc.send("PRIVMSG " + channel+" :"+fromnick+", you are making me think!\r\n")
                        deflist=[]
                        for item in quote:
                            if item.lower().find(defstring.lower())>-1:
                                deflist.append(item)
                                think=think+1
                            if len(deflist)>0:
                                irc.send("PRIVMSG " +channel+" :"+fromnick+": "+random.choice(deflist)+"\r\n")
                            if think==0:
                                irc.send("PRIVMSG " + channel+" :" + fromnick+": and thinking is too hard!\r\n")
                    if address.lower().find("ping")>-1:
                        irc.send("PRIVMSG " + channel+" :pongzer "+fromnick+"\r\n")
                        time.sleep(int((random.random()*10)))
                        irc.send("PRIVMSG " + channel+" :lulz...\r\n")
                    if address.lower().find("redken")>-1 or text.lower().find("redken")>-1:
                        irc.send("PRIVMSG " + channel+" :redken: i'm the new bot in town!\r\n")
                    if address.lower().find("fuck")>-1 or address.lower().find("shit")>-1 or address.lower().find("damn")>-1:
                        irc.send("PRIVMSG " + channel+" :"+fromnick + ": that will be five dollars.\r\n")
                    if address.lower().find("gummels")>-1:
                        if bigX==4 or bigX==8:
                            irc.send("PRIVMSG " + channel+" :"+fromnick+": he's not going to respond to you....\r\n")
                bigX=bigX+1
                if bigX==10:
                    bigX=0
                if address==self.nick:
                    command=command.lower().rstrip()
                    com_fw=command.split(" ")[0]
                    command_run=0
                    if com_fw=="ping":
                        time.sleep(1)
                        irc.send("PRIVMSG "+channel+" :pongzer " + fromnick+" \r\n")
                        command_run=1
                    if com_fw=="tell":
                        time.sleep(int((random.random()*10)+(random.random()*10)))
                        irc.send("PRIVMSG " + channel+" :"+command.split(com_fw)[1].lstrip()+"\r\n")
                        command_run=1
                    if command_run==0:
                        time.sleep(int((random.random()*10)))
                        a_quote=random.choice(quote)
                        while dontsay.has_key(quote.index(a_quote)):
                            a_quote=random.choice(quote)
                        dontsay[quote.index(a_quote)]=quote.index(a_quote)
                                if len(dontsay)==len(quote)-2:
                                        dontsay={}
                                irc.send("PRIVMSG " + channel+" :"+fromnick+", I really don't get what you're saying. Why don't you ponder this:\r\n")
                                irc.send("PRIVMSG " +channel+" :"+a_quote+"\r\n")
        else:
                pass
        return bigX,dontsay


def connect(irc,init):
        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #defines the socket
        print "connecting to:"+server
        irc.connect((server, 6667))                                                         #co
        irc.send("USER "+ self.nick +" "+ self.nick +" "+ self.nick +" :This is a fun ChatBot!\n") #user authentication
        irc.send("NICK "+ self.nick +"\n")                            #sets nick
        irc.send("PRIVMSG nickserv :iNOOPE\r\n")    #auth
        irc.send("JOIN "+ channel +"\n")        #join the chan
        if init==1:
                irc.send("PRIVMSG " + channel +" :"+"This is "+self.nick+". I live to serve the good people of "+channel+".\r\n")
        return irc

load_quotes()

x=0

irc=None

irc=connect(irc,1)

while 1:    #puts it in a loop
   try:
           text=irc.recv(2040)  #receive the text
           x=x+1
           bigX,dontsay=process_text(text,bigX,dontsay)
           if x==40:
                irc.send("PRIVMSG " + channel+" :yawn....\r\n")
                x=0
   except:
           print "dead on arrival"
           print "we died"
           irc=connect(irc,0)
           sys.exit(1)
'''
