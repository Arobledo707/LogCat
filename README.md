# LogCat --- Discord Bot
Requirements:
Python 3.5.3 or higher  
Discord.py
https://discordpy.readthedocs.io/en/latest/intro.html#installing

--- LogCat Guide Version: 0.10.0 ---
If this is your first time using LogCat, run the script to create the xml
It should create this xml file for you:

```xml<?xml version="1.0" encoding="UTF-8"?>
<LogCat>
	<Token id="Enter Token Here"/>
	<Prefix character="$"/>
    <Role name="Admin"/>
</LogCat>
```

--- Add a Bot Token ---
Get your bot token from here
https://discordapp.com/developers/applications

--- Seeing available Channels ---
Once the script is running type $channels in a direct message to the bot
The bot will list the channel's name along with their ID's

--- Adding a channel ---
Use "$addchannel general" to add the general channel to the loggedList
Channel names with spaces in them such as Concept Art Support require their ID's instead of the names
Use the $channels command (above) to get IDs in this case.
You can also set Discord to developer mode to get channel IDs.
Adding a channel with spaces in its name would look like this "$addchannel <ID>" where <ID> is the channel's ID.
These channels will be saved in the xml and will be automatically added next time the bot runs

--- Starting Automatic Logging ---
Once the bot has at least one channel added we can call $startlogging
The bot will log between the time of 0:00 to 1:00
If the xml file already has channels added when the bot loads we do not need to call this


--- Removing a channel ---
"$removechannel general" ---> this would remove the general channel from automatic logging
It is also possible to remove channels by their ID


--- Creating logs manually ---
To create logs there still needs to be at least one channel added with $addchannel
Once that has been done we can call $logdate
logdate can take either one date or two dates depending if we want to log a specific day or a start date and end date
The format for the dates is yyyy/mm/dd
"$logdate 2018/07/15" would log the 15th of july 2018
"$logdate 2018/07/01 2018/07/30" would log from the 2018/07/01 to 2018/07/30
Order for the dates matters as of 7/30/2018 for this command

We can also log yesterday with the LogYesterday Command
$ly or $logyesterday

--- Getting logs ---
If we want to get all of the logs that the bot has created we can use
$getlogs -->> this would have the bot send you all of the logs that it has created in a zip file

--- Logs from a specific channel ---
$GetChannelLogs
Let's get logs for general chat:
"$getchannellogs general"
This would return all of the logs the bot has made for general chat

--- Getting logs from a specific date and channel ---
"$getchannellogs general 2018/07/14" 
"$getchannellogs 2018/07/14 general"
These both get logs for only the general channel on July 14 2018.
Order does not matter here

--- Getting logs from a channel from a certain date to an end date ---
"$getchannellogs general 2018/07/14 2018/07/25"
"$getchannellogs 2018/07/14 2018/07/25 general"
These both get logs for only the general channel from July 14 to July 25.
Order also does not matter here

--- Console.txt Debug Info----
Errors, Warning, Bot Information is stored in console.txt
The following commands are logged upon success. 
The user's discord username, nickname and entire message are logged
add commands: AddPrefix, AddChannel, AddRole
remove commands: RemovePrefix, RemoveChannel, RemoveRole

If a user does not have access to the bot but knows it's prefix and sends a message with the prefix,
will have their message and user info logged.

--- Additional Info ---
use the $help command to list all the commands along with info about them
To see more info about a certain command type "$help commandName"
"$help GetLogs" would show additional info about GetLogs
