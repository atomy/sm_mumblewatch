#!/usr/bin/python
#

import sys
import SRCDS
import math

def MAIN():
        players = 0
        bots = 0
        humans = 0
        try:
                c = SRCDS.SRCDS('jackinpoint.net', 27045, 'rconpw')
		c.rcon_command('checkmumbleplayers')
                c.disconnect()
        except:
                print 'fail'

        print 'done'

if __name__ == "__main__":
        MAIN()
