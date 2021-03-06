#SRCDS.py
#Half-Life 2 and Half-Life Dedicated Server Interface for Python
#Released under the LGPL (http://www.gnu.org/licenses/lgpl.html)
#
#Christopher Munn
#Based off (most code copied from) SRCDS.py by Sean C. Steeg
#


__author__ = 'Christopher Munn'
__license__ = 'http://www.gnu.org/licenses/lgpl.html'
__date__ = '07 Mar 2006'
__version__ = '2.02'
__credits__ = """Sean C. Steeg for SRCDS.py 1.01.
Bryan Gerber, for the original HLDS.py.
The players and staff of TacticalGamer.com, who make us want to do stuff like this."""

import socket, re, xdrlib, string

#Server Query Constants
DETAILS = "TSource Engine Query\x00"
DETAILS_RESP_HL2 = 'I'
DETAILS_RESP_HL1 = 'm'
GETCHALLENGE = 'W'
CHALLENGE = 'A'
PLAYERS = 'U'
PLAYERS_RESP = 'D'
RULES = 'V'
RULES_RESP = 'E'
#HL2 RCON Constants
SERVERDATA_RESPONSE_VALUE = 0
SERVERDATA_AUTH_RESPONSE = 2
SERVERDATA_EXECCOMMAND = 2
SERVERDATA_AUTH = 3
RCON_EMPTY_RESP = (10,0,0,'','')
#HL1 RCON Constants
RCON_CHALLENGE = "challenge rcon\n"

##################################################
# Network data manipulation
def hldsunpack_int(data):
    """
Network traffic is big endian, and xdrlib wants little endian, meaning the
bytes need to be reversed in order for xdrlib to work its magic."""
    s = ""
    for c in data:
        s = c + s
    p = xdrlib.Unpacker(s)
    return p.unpack_int()

def hldsunpack_float(data):
    """
Network traffic is big endian, and xdrlib wants little endian, meaning the
bytes need to be reversed in order for xdrlib to work its magic."""
    s = ""
    for c in data:
        s = c + s
    p = xdrlib.Unpacker(s)
    return p.unpack_float()

def hldspack_int(integer):
    s = ""
    p = xdrlib.Packer()
    p.pack_int(integer)
    data = p.get_buffer()
    for c in data:
        s = c + s
    return s

##################################################
# Functions for reading packets 
def read_byte(data):
    return (ord(data[0]), data[1:])

def read_char(data):
    return (str(data[0]), data[1:])

def read_string(data):
    s = ''
    i = 0
    while 1:
        if str(data[i]) != '\x00':
            s = s + str(data[i])
            i += 1
        else:
            break
    return (s, data[i+1:])

def read_int(data):
    ret = hldsunpack_int(data[0:4])
    return (ret, data[4:])

def read_float(data):
    ret = hldsunpack_float(data[0:4])
    return (ret, data[4:])
    
##################################################
# Exceptions
class SRCDS_Error(Exception):
    """Base error."""
    pass

class RCON_Error(Exception):
    """Raised when a command requiring RCON is given, but the RCON password is missing or incorrect."""
    pass

##################################################
# SRCDS class
class SRCDS:
    """
HL2DS/HLDS Interface class. Supports HL2 and HL servers.

Initialization: OBJ = SRCDS(host, [port=27015], [rconpass=''], [timeout=2.0])
Note: timeout is in seconds. host may be ip or hostname
    """

    def __init__(self, host, port=27015, rconpass='', timeout=10.0):
        self.ip, self.port, self.rconpass, self.timeout = socket.gethostbyname(host), port, rconpass, timeout
        self.udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udpsock.settimeout(self.timeout)
        self.tcpsock.settimeout(self.timeout)
        self.udpsock.connect((self.ip, self.port))
        self.challenge, self.rcon_challenege, self.req_id, self.hl = -1, 0, 0, 0
        if self.rconpass: 
            self._authenticate_rcon()

    ##################################################
    # RCON Packet functions
    def send_packet(self, command, string1, string2=''):
        """Crafts and sends a packet to the server."""
        #Increment self.req_id, so all commands have unique id
        self.req_id += 1
        #Make the packet from the end going backwards
        packet = string1 + '\x00' + string2 + '\x00'
        #Add command
        packet = hldspack_int(command) + packet
        #Add request_id
        packet = hldspack_int(self.req_id) + packet
        #Add an int of the packet length
        packet = hldspack_int(len(packet)) + packet
        #Send packet to server
        self.tcpsock.send(packet)
        #Return req_id of packet
        return self.req_id
        
    def read_packet(self):
        """Parses a single response packet from the server."""
        raw_packetlen = self.tcpsock.recv(4)
        packetlen = hldsunpack_int(raw_packetlen)
        raw_packet = self.tcpsock.recv(packetlen)
        req_id = hldsunpack_int(raw_packet[0:4])
        command = hldsunpack_int(raw_packet[4:8])
        raw_packet = str(raw_packet[8:])
        if len(raw_packet) == 2:
            strs = ['', '']
        else:
            strs = re.split('[\000]', raw_packet[:-1], 1)
        return (packetlen, req_id, command, strs[0], strs[1])    
    
    def _authenticate_rcon(self):
        if not self.rconpass: raise RCON_Error, 'Empty RCON password.'
        if self.hl == 0:
            self.details()
        if self.hl == 1:
            self._authenticate_rcon_hl1()
        else:
            self._authenticate_rcon_hl2()

    def _authenticate_rcon_hl1(self):
        self.rcon_challenge =  self._any_response(RCON_CHALLENGE)[15:-2]
        response = self._any_rcon_response_hl1('say')
        if response == 'Bad rcon_password.':
            raise RCON_Error, 'Invalid RCON password.'
        
    def _authenticate_rcon_hl2(self):
        self.tcpsock.connect((self.ip, self.port))
        req_id = self.send_packet(SERVERDATA_AUTH, self.rconpass, '')
        i = 0
        result = RCON_EMPTY_RESP
        while result != (10,req_id,SERVERDATA_AUTH_RESPONSE,'',''):
            result = self.read_packet()
            if result[1] == -1:
                raise RCON_Error, 'Invalid RCON password.'

    def _any_rcon_response(self, command):
        """
This function returns the raw response for commands requiring RCON.
No parsing is done by this function.
        """
        if self.hl == 1:
            return self._any_rcon_response_hl1(command)
        else:
            return self._any_rcon_response_hl2(command)[3]
    
    def _any_rcon_response_hl1(self, command):
        query = "rcon " + self.rcon_challenge + ' "' + self.rconpass + '" ' + command
        return self._any_response(query)[1:]

    def _any_rcon_response_hl2(self, command):
        req_id = self.send_packet(SERVERDATA_EXECCOMMAND, command)
        result = RCON_EMPTY_RESP
        while result[1] != req_id:
            result = self.read_packet()
        return result                

    ##################################################
    # RCON functions
    def set_rconpass(self, password):
        self.rconpass = password
        self._authenticate_rcon()
        
    def rcon_command(self, command):
        return self._any_rcon_response(command)

    def changelevel(self, map):
        self._any_rcon_response('changelevel %s' %map)

    def say(self, statement):
        self._any_rcon_response('say %s' %statement)

    def quit(self):
        self._any_rcon_response('quit')

    def status(self):
        '''
Returns a list of dictionaries.  Each dictionary is the status info on a player.
        '''
        if not self.players(): return []
        raw_status = self._any_rcon_response('status')
        lines = re.split("\n",raw_status)
        line = lines.pop(0)
        while (line == '' or line[0] != '#') and len(lines) != 0:
            line = lines.pop(0)
        keys = re.split(' +', line)
        keys.pop(0)
        if self.hl == 1:
            temp = keys[0]
            keys[0] = keys[1]
            keys[1] = temp
        players = []
        while line != '' and line[0] == '#':
            player = {}
            line = re.split('"', lines[0], 3)
            player[keys[0]] = re.split(' +', line[0])[1]
            player[keys[1]] = line[1]
            values = re.split(" +", line[2])
            if self.hl == 1:
                values.pop(0)
            for i, key in enumerate(keys[2:]):
                player[key] = values[i+1]
            players.append(player)
            line = lines.pop(0)
        return players

    ##################################################
    # Query packet functions
    def _any_response(self, query):
        """
This assembles mult-packet responses and returns the raw response (sans the four \xFF's).  No parsing is done by this function.
        """
        self.udpsock.send('\xFF\xFF\xFF\xFF' + query)
        data = self.udpsock.recv(4096)
        if data[0] == '\xFE':
            num_packets = ord(data[8]) & 15
            packets = [' ' for i in range(num_packets)]
            for i in range(num_packets):
                if i != 0:
                    data = self.udpsock.recv(4096)
                index = ord(data[8]) >> 4
                packets[index] = data[9:]
            data = ''
            for i, packet in enumerate(packets):
                data = data + packet
        return data[4:]
        
    ##################################################
    # Queries
    def getchallenge(self):
        raw_challenge = self._any_response(GETCHALLENGE)
        if raw_challenge[0] != CHALLENGE: 
            raise SRCDS_Error, 'GetChallenge Query Error: Unknown response type'
        data = raw_challenge[1:]
        self.challenge, data = read_int(data)
        return self.challenge
    
    def details(self):
        raw_details = self._any_response(DETAILS)
        if raw_details[0] == DETAILS_RESP_HL2:
            self.hl = 2
            return self.details_hl2(raw_details[1:])
        elif raw_details[0] == DETAILS_RESP_HL1:
            self.hl = 1
            return self.details_hl1(raw_details[1:])
        else:
            raise SRCDS_Error, 'Detail Query Error: Unknown response type'
    
    
    def details_hl2(self, data):
        detaildict = {}
        detaildict['hl_version'] = 2
        detaildict['protocol_version'], data = read_byte(data)
        detaildict['server_name'], data = read_string(data)
        detaildict['current_map'], data = read_string(data)
        detaildict['game_directory'], data = read_string(data)
        detaildict['game_description'], data = read_string(data)
        aid1, data = read_byte(data)
        aid2, data = read_byte(data)
        detaildict['app_id'] = (aid1 * 0x100) + aid2
        detaildict['current_playercount'], data = read_byte(data)
        detaildict['max_players'], data = read_byte(data)
        detaildict['current_botcount'], data = read_byte(data)
        ded, data = read_char(data)
        if ded == 'd':
            detaildict['server_type'] = 'Dedicated'
        else:
            detaildict['server_type'] = 'Listen'
        os, data = read_char(data)
        if os == 'w':
            detaildict['server_os'] = 'Windows'
        else:
            detaildict['server_os'] = 'Linux'
        pworded, data = read_byte(data)
        detaildict['passworded'] = bool(int(pworded))
        secured, data = read_byte(data)
        detaildict['secure'] = bool(int(secured))
        detaildict['exe_version'], data = read_string(data)
        
        return detaildict

    def details_hl1(self, data):
        detaildict = {}
        detaildict['hl_version'] = 1
        detaildict['game_ip'], data = read_string(data)
        detaildict['server_name'], data = read_string(data)
        detaildict['current_map'], data = read_string(data)
        detaildict['game_directory'], data = read_string(data)
        detaildict['game_description'], data = read_string(data)
        detaildict['current_playercount'], data = read_byte(data)
        detaildict['max_players'], data = read_byte(data)
        detaildict['protocol_version'], data = read_byte(data)
        ded, data = read_char(data)
        if ded == 'd':
            detaildict['server_type'] = 'Dedicated'
        else:
            detaildict['server_type'] = 'Listen'
        os, data = read_char(data)
        if os == 'w':
            detaildict['server_os'] = 'Windows'
        else:
            detaildict['server_os'] = 'Linux'
        pworded, data = read_byte(data)
        detaildict['passworded'] = bool(int(pworded))
        detaildict['ismod'], data = read_byte(data)
        if detaildict['ismod'] == 1:
            detaildict['mod_url_info'], data = read_string(data)
            detaildict['mod_url_dl'], data = read_string(data)
            detaildict['mod_unused'], data = read_string(data)
            detaildict['mod_version'], data = read_int(data)
            detaildict['mod_size'], data = read_int(data)
            mod_svonly, data = read_byte(data)
            detaildict['mod_svonly'] = bool(int(mod_svonly))
            mod_cldll, data = read_byte(data)
            detaildict['mod_cldll'] = bool(int(mod_cldll))
        secured, data = read_byte(data)
        detaildict['secure'] = bool(int(secured))
        detaildict['current_botcount'], data = read_byte(data)
        
        return detaildict
        
    def players(self):
        if self.challenge == -1:
            self.getchallenge()
        raw_players = self._any_response(PLAYERS + hldspack_int(self.challenge))
        if raw_players[0] != PLAYERS_RESP: raise SRCDS_Error, 'Player Query Error'
        data = raw_players[1:]
        playerlist = []
        playercount, data = read_byte(data)
        playercount = int(playercount)
        while len(data) != 0:
            currentplayer = {}
            cn, data = read_byte(data)
            currentplayer['index'] = int(cn)
            currentplayer['name'], data = read_string(data)
            currentplayer['frags'], data = read_int(data)
            currentplayer['time_on'], data = read_float(data)
            playerlist.append(currentplayer)
        return playerlist
        
    def rules(self):
        if self.challenge == -1:
            self.getchallenge()
        raw_rules = self._any_response(RULES + hldspack_int(self.challenge))
        if raw_rules[0] != RULES_RESP: raise SRCDS_Error, 'Rules Query Error'
        data = raw_rules[1:]
        rulescount, data = read_byte(data)
        rulescount = int(rulescount)
        nada, data = read_byte(data)    #placeholder to move up one byte
        ruleslist = string.split(str(data), '\x00')
        ruleslist.pop()
        rulesdict =  {}
        for everyother in ruleslist[::2]:
            rulesdict[everyother] = ruleslist[ruleslist.index(everyother) + 1]
        return rulesdict

    def disconnect(self):
        self.udpsock.close()
        
##################################################
# HLDS class (for backwards compatibility with HLDS.py)
class HLDS(SRCDS):
    def close(self):
        self.disconnect()
