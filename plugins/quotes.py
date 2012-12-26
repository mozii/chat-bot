#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# Copyright (C) 2012  Jamie Duncan (jamie.e.duncan@gmail.com)

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

'''
Chat-Bot Quotes Plugin
Operation: takes a list of quotes and responds with a random one when requested.
'''

class QuotePlugin:

    def __init__(self):
        self.quote_file = 'quotes.txt'

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

