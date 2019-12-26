#include <sourcemod>
#include <sdktools>

public Plugin:myinfo =
{
	name = "MumbleJoin",
        author = "Atomy",
        description = "open motd with mumble:// url to join it w/o tabbing/leaving game",
        version = "1.2",
        url = "http://www.losd-clan.com"
};
       
public OnPluginStart()
{
       RegConsoleCmd("say", Command_Say)
       RegConsoleCmd("say_team", Command_TeamSay)
}
       
public Action:Command_Say(client, args)
{
	new String:text[192]

	GetCmdArgString(text, sizeof(text))
		 
	new startidx = 0
	
	if (text[0] == '"')
	{
		startidx = 1
		
		new len = strlen(text)
		
		if (text[len-1] == '"')
		{
			text[len-1] = '\0'
		}
	}
																	 
	if (StrEqual(text[startidx], "!joinmumble"))
	   	ShowMotd(client)

	if (StrEqual(text[startidx], "!mumbleusers"))
		ShowMotd2(client)
	
	return Plugin_Continue
}
  
public Action:Command_TeamSay(client, args)
{
        new String:text[192]

        GetCmdArgString(text, sizeof(text))

        new startidx = 0

        if (text[0] == '"')
        {
                startidx = 1

                new len = strlen(text)

                if (text[len-1] == '"')
                {
                        text[len-1] = '\0'
                }
        }

        if (StrEqual(text[startidx], "!joinmumble"))
                ShowMotd(client)

        if (StrEqual(text[startidx], "!mumbleusers"))
                ShowMotd2(client)

        return Plugin_Continue
}

public ShowMotd(client)
{
	new String:url[255]

	Format(url, sizeof(url), "mumble://Guest%i@jackinpoint.net/Dystopia", GetRandomInt(1000, 9999))

	PrintToChat(client, "Opening %s...", url)
        ShowMOTDPanel(client, "Joining Mumble Server...", url, MOTDPANEL_TYPE_URL)
}

public ShowMotd2(client)
{
        new String:url[255]

        Format(url, sizeof(url), "http://jackinpoint.net/cgi-bin/mumbleviewer/viewer.cgi")

        PrintToChat(client, "Opening %s...", url)
        ShowMOTDPanel(client, "Mumble Userstatus...", url, MOTDPANEL_TYPE_URL)
}
