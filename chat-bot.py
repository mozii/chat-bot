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
        payload = text.replace("\\","").rstrip()

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

