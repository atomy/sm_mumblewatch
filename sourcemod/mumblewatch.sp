#include <sourcemod>
#include <sdktools>
#include <string>

#define STATUSFILE "../mumblequerytools/mumbleusers.txt"
#define MAXCHECKPLAYERS 32
#define PLUGIN_VERSION "1.1"

new String:players[64][32]

public Plugin:myinfo =
{
	name = "MumbleWatch",
        author = "Atomy",
        description = "watch for joining/parting playes in mumble",
        version = PLUGIN_VERSION,
        url = "http://www.losd-clan.com"
};
       
public OnPluginStart()
{
        CreateConVar("sm_mumblewatch_version", PLUGIN_VERSION, "", FCVAR_PLUGIN | FCVAR_REPLICATED | FCVAR_NOTIFY);
	RegAdminCmd("checkmumbleplayers", CheckUsers, ADMFLAG_CHANGEMAP, "none");
}

public UserLeft(String:usa[])
{
        TrimString(usa)
        PrintToChatAll("%s left Mumble.", usa)
}

public UserJoined(String:usa[])
{
        TrimString(usa)
        PrintToChatAll("%s joined Mumble.", usa)
}	

public Action:CheckUsers(client, args)
{
	CreateTimer(2.0, Doit)

	return Plugin_Continue
}

public Action:Doit(Handle:timer)
{
	new String:buf[32]
	new String:fileusers[64][32]
	new Handle:s_file
	new found = 0
	new i = 0
	new k = 0
	new f = 0

	if (!FileExists(STATUSFILE))
		ThrowError("error while locating statusfile")
        
	s_file = OpenFile(STATUSFILE, "r")

	if (s_file == INVALID_HANDLE)
		ThrowError("error while opening statusfile")

	while (s_file != INVALID_HANDLE && !IsEndOfFile(s_file) && ReadFileLine(s_file, buf, sizeof(buf)))
	{
		TrimString(buf)
		strcopy(fileusers[f], 32, buf)
		f++
	}

	CloseHandle(s_file)
	
	for (i=0; i<64; i++)
	{
		found = 0

		for (k=0; k<64; k++)
		{
	                if (strlen(players[i]) == 0 || strlen(fileusers[k]) == 0)
	                        continue
								
			if (StrEqual(fileusers[k], players[i]))
			{
				found = 1
				break
			}
		}

		if (found == 0 && strlen(players[i]) != 0)
		{
			UserLeft(players[i])
		}
	}

        for (i=0; i<64; i++)
        {
                found = 0

                for (k=0; k<64; k++)
                {
                        if (strlen(fileusers[i]) == 0 || strlen(players[k]) == 0)
                                continue

                        if (StrEqual(fileusers[i], players[k]))
                        {
                                found = 1
                                break
                        }

                }

                if (found == 0 && strlen(fileusers[i]) != 0)
                {
                        UserJoined(fileusers[i])
                }
        }


	for (i=0; i<64; i++)
	{
		strcopy(players[i], 32, fileusers[i])
	}
	
	return Plugin_Continue
}
