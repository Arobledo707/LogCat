# Alberto Robledo
# Discord Python Bot
# This is a discord bot that creates logs for certain channels and can be set
# to create logs for them daily.
# It creates a directory for each date and each date will have a directory for
# each channel which will contain a .txt file of the logs
# Creating logs manually is also an option for either a specific date or from a
# starting date to an ending date
import discord
import os
import datetime
import shutil
import asyncio
import re
import distutils.dir_util
import sys
from discord.ext import commands
from datetime import timezone
from pathlib import Path
import time
import xml
import xml.etree.ElementTree as ET
import xml.dom.minidom
import traceback
import logging


logging.basicConfig(filename='./console.txt', filemode='a+', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
# Current version
# keep this up to date
Version = '0.10.1'

#------------------------------------------------Constants-------------------------------------------------------------------------
BotPrefix = []

TOKEN = None

LogLimitPerChannel = sys.maxsize
SecondsInDay = 86400
SecondsInHour = 3600

AutomaticLogging = False

LogTypeInfo = 0
LogTypeWarning = 1
LogTypeError = 2

text_channel_type = 0

ParentDirectory = 'Logs'
ConsoleLogs = 'console.txt'
TempFolder = 'temp'
ConfigFile = 'config.txt'
ConfigXmlFile = 'Config.xml'
URL = 'url'
BadChannelIdOrName = 'Bad Channel ID or Name'
DateFormat = "%Y-%m-%d"
DateTimeFormat = "%Y-%m-%d %H:%M:%S"
#Possible Log Times
# 24 hour clock
# example for adding minutes
# datetime.time(1,30)
# this will try to log from midnight to 1 am
# it will attempt to log during this time period midnight - 1 am
EarlyLogTime = datetime.time(0)
LateLogTime = datetime.time(1)

Error = '```excel\n'
Warning = '```http\n'
Log = '```Elm\n'

#XML element names
XMLToken = 'Token' 
XMLTokenAttribute = 'id'
XMLChannel = 'Channel'
XMLChannelAttribute = 'info'
XMLPrefix = 'Prefix'
XMLPrefixAttribute = 'character'
XMLRole = 'Role'
XMLRoleAttribute = 'name'

#probably should make this an enum
MessageTypeLog = 'Log'
MessageTypeError = 'Error'
MessageTypeWarning = 'Warning'

EndCodeBlock = '```'

ServerID = None

start_time = time.time()
#---------------------------------------------------Constants
#end------------------------------------------------------------------


#---------------------------------------------RegEx----------------------------------------------------------------------------
date_pattern = re.compile(r'(\d\d\d\d)\W(\d\d)\W(\d\d)')

emoji_pattern = re.compile("["u"\U0001F600-\U0001F64F"
                                 u"\U0001F300-\U0001F5FF"
                                 u"\U0001F680-\U0001F6FF"
                                 u"\U0001F1E0-\U0001F1FF"
                                 u"\U00002702-\U000027B0"
                                 u"\U000024C2-\U0001F251" "]+", flags=re.UNICODE)

#---------------------------------------------RegEx---------------------------------------------------------------------------
client = commands.Bot(command_prefix=BotPrefix)


# if we want to add a channel here manually enter it as a string '543553573'
# entering it as an int does not work
# This should be read from a config file and saved when a new channel is added
# to log or removed
channelsToLog = []

parsedChannelInfo = []

commandRoles = []

#------------------------------------------------------check_config_file----------------------------------------------------------
def check_config_file():
    """Checks if config file exists if not it creates one"""
    if not os.path.exists(ConfigXmlFile):
        create_xml_config_file()
    parse_xml_config()

#-----------------------------------------------------parse_xml_config------------------------------------------------------------
def parse_xml_config():
    """Trys to parse xml file into tree. If it fails it creates a default xml file.
Parses the data and assigns prefixes, channelsToLog, Token"""
    try:
        tree = ET.parse(ConfigXmlFile)
    except Exception as e:
        print_and_log(LogTypeError, e)
        print_and_log(LogTypeInfo, 'Creating new xml file')
        create_xml_config_file()
    tree = ET.parse(ConfigXmlFile)
    root = tree.getroot()
    for Element in root:
        if Element.tag == XMLChannel:
            info = Element.get(XMLChannelAttribute)
            print_and_log(LogTypeInfo, 'Adding ' + info + ' to logged channels')
            if info in parsedChannelInfo:
                print_and_log(LogTypeInfo, info + ' was already in channels to log')
            else:
                parsedChannelInfo.append(info)
        if Element.tag == XMLToken:
            global TOKEN
            TOKEN = Element.get(XMLTokenAttribute)
            print_and_log(LogTypeInfo, 'Using this Token: ' + TOKEN)
        if Element.tag == XMLPrefix:
            prefix = Element.get(XMLPrefixAttribute)
            print_and_log(LogTypeInfo, 'Adding ' + prefix + ' to bot prefixes')
            if prefix in BotPrefix:
                 print_and_log(LogTypeInfo, prefix + ' is already a prefix!')
            else:
                BotPrefix.append(Element.get(XMLPrefixAttribute))
        if Element.tag == XMLRole:
            role = Element.get(XMLRoleAttribute)
            print_and_log(LogTypeInfo, 'Adding ' + role + ' to command roles')
            if role in commandRoles:
                print_and_log(LogTypeInfo, role + ' was already in command roles!')
            else:
                commandRoles.append(role)


#-----------------------------------------------------------RemoveFromXML-----------------------------------------------------------
def RemoveFromXML(Element, attribName, attribValue):
    """Removes element with an attrivute of certain value from XML file"""
    tree = ET.parse(ConfigXmlFile)
    root = tree.getroot()
    for element in root.findall(Element):
        if attribValue == element.get(attribName):
            root.remove(element)
    xmlstr = xml.dom.minidom.parseString(ET.tostring(root)).toxml()
    file = open(ConfigXmlFile, 'w')
    file.write(xmlstr)
    file.close()

#-------------------------------------------------------------AddToXML---------------------------------------------------------------
def AddToXML(element, attribName, attribValue):
    """Adds an element of type element that has an attribute with the passed in value"""
    tree = ET.parse(ConfigXmlFile)
    root = tree.getroot()
    ET.SubElement(root, element).set(attribName, attribValue)
    xmlstr = xml.dom.minidom.parseString(ET.tostring(root)).toxml()
    file = open(ConfigXmlFile, 'w')
    file.write(xmlstr)
    file.close()



#--------------------------------------------------------create_xml_config_file------------------------------------------------------
# Creates initial XML config file for the bot
def create_xml_config_file():
    file = open(ConfigXmlFile, 'w+')
    try:
        global TOKEN
        if TOKEN is None:
            TOKEN = "Enter Token Here"
        file.write('''<?xml version="1.0" encoding="UTF-8"?>
<LogCat>
	<Token id="''' + TOKEN + '''"/>
	<Prefix character="$"/>
    <Role name="Admin"/>
</LogCat>''')
    except UnicodeEncodeError as e:
        print_and_log(LogTypeI, 'Failed to write XML file')
        print_and_log(LogTypeError, e)
    file.close()

#----------------------------------------------------------prefixes---------------------------------------------------------------
@client.command(name='Prefixes',
                description='Lists the command prefixes that have been set',
                brief='Lists command prefixes',
                aliases=['prefixes'],
                pass_context=True)
async def prefixes(context):
    """Sends client all prefixes in BotPrefixes"""
    if BotPrefix == 0:
        await context.send(format_message(MessageTypeError, 'Error: no prefixes assigned. Either add a prefix in xml or delete config file and run again'))
        return
    await context.send(format_message(MessageTypeLog, 'Here are all the command prefixes'))
    for prefix in BotPrefix:
        await context.send(format_message(MessageTypeLog, prefix))
    await context.send(format_message(MessageTypeLog, 'Done!'))

#---------------------------------------------------create_logs_for_yesterday---------------------------------------------------------
async def create_logs_for_yesterday():
    """Logs everything that happened yesterday in every channel in ChannelsToLog"""
    info = await yesterday_log_loop()
    if info is not None:
        print(info)

#------------------------------------------------------LogChannel-------------------------------------------------------------------
async def LogChannel(channel, startTime, command=None):
    """Logs a certain channel from a startTime to 24 hours from then
Creates a folder with the logged date as the name and a folder 
with the channels name
Inside of the folder with the channel's name it creates a .txt file that
contains each message along with its author's name
and the time it was sent at.  It also adds the URL of any attachment that 
the author included"""
    midnight = startTime + datetime.timedelta(days=1)
    print_and_log(LogTypeInfo, 'Getting logs for ' + channel.name + ' from ' + startTime.strftime(DateTimeFormat) + ' to ' + midnight.strftime(DateTimeFormat))
    channelNameFix = channel.name.replace('/', '-')
    channelNameFix = channelNameFix.replace(r'\\', '-')
    mainDirectory = channelNameFix
    fileName = channelNameFix + ' ' + startTime.strftime(DateFormat)
    path = ParentDirectory + '/' + mainDirectory
    os.makedirs(path, exist_ok=True)
    file = open(path + '/' + fileName + '.txt', 'w+')
#   For each message in a channel from startTime to midnight ---- From a start
#   time to 24 hours after
    channelMessages = []
    try:
        async for message in channel.history(limit=LogLimitPerChannel, before=midnight, after=startTime):
            messageAuthor = "null"
            # if the author has set a nickname use that else use their discord
            # account name
            if hasattr(message.author, 'nick'):
                if message.author.nick is not None:
                    messageAuthor = message.author.nick
                else:
                    messageAuthor = message.author.name
                # Get the message's timestamp and convert it to local time
                # using GetTimeoffset
                timeZoneTime = message.created_at - datetime.timedelta(hours=GetTimeOffset())
                # save the date, the message's author and the message content
                # without emojis
                newMessage = {}
                newMessage['data'] = timeZoneTime.strftime(DateTimeFormat) + " " + kill_emojis(messageAuthor) + ":" + kill_emojis(message.content) + '\n'
                newMessage['id'] = message.id
                # append the newMessage to the channelMessages list
                channelMessages.append(newMessage)

            # if the message has attachments append the attachment url to
            # channelMessages
            if hasattr(message, 'attachments'):
                if message.attachments:
                    attachments = message.attachments
                    for attachment in attachments:
                        message_url = {'data': attachment.url + '\n', 'id': 0}
                        channelMessages.append(message_url)
    #try to write each message in channelMessages else print the error message
    except Exception as e:
        if command is not None:
            print_and_log(LogTypeInfo, 'Command: ' + command)
        print_and_log(LogTypeError, e)
    for message in reversed(channelMessages):
        try:
            file.write(message['data'])
        except UnicodeEncodeError as e:
            print("UnicodeEncodeError for message with id of:" + str(message['id']))
            print(e)
    file.close()

#-----------------------------------------------------check_time-------------------------------------------------------------------
async def check_time():
    """Checks if the currentTime is in between the times that the bot can 
log at for automatic logging
If the bot is within that time then it createsLogs for yesterday and waits a
full 24 hours before logging again
If it was not in the correct time to log then it checks every hour until it
hits the goal time."""
    while True:
        if EarlyLogTime <= datetime.datetime.now().time() <= LateLogTime:
            print("Logging these channels: ")
            await create_logs_for_yesterday()
            print_and_log(LogTypeInfo, 'Logs created. Sleeping for 24 hours until it is time to log again')
            await asyncio.sleep(SecondsInDay)
        else:
            print("Not correct time to log. Will wait an hour and try again")
            await asyncio.sleep(SecondsInHour)

#---------------------------------------------------------print_and_log---------------------------------------------------------------
def print_and_log(log_type, string):
    """prints string to console and writes string to log file"""
    print(string)
    if log_type == LogTypeInfo:
        logging.info(string, exc_info=True)
    elif log_type == LogTypeWarning:
        logging.warning(string, exc_info=True)
    elif log_type == LogTypeError:
        logging.error(string, exc_info=True)
    else:
        logging.log(string, exc_info=True)
    
#-------------------------------------------------------on_ready------------------------------------------------------------------
@client.event
async def on_ready():
    """This is called when the bot comes is ready
        if channelsToLog is not empty it then calls check_time() which can start the
        autolog process
        printing early log time and late logtime along with timezone"""
    if len(client.guilds) > 1:
        print_and_log(LogTypeWarning,'Connected to more than one server!')
    for server in client.guilds:
        print_and_log(LogTypeInfo,'Connected to: ' + server.name)
        global ServerID
        ServerID = server.id
        break
    
    commands = client.commands
    print_and_log(LogTypeInfo, 'Running version: ' + Version)
    print('Connected and ready to log!\nLogging sometime between these times')
    print(EarlyLogTime)
    print(LateLogTime)
    print(time.tzname)
    
    for channelInfo in parsedChannelInfo:
        channel = get_channel_by_name(channelInfo)
        if channel is None:
            channel = client.get_channel(channelInfo)
        if channel is not None:
            channelsToLog.append(channel.id)
    if len(channelsToLog) > 0:
        global AutomaticLogging
        AutomaticLogging = True
        await check_time()
    else:
        print('Channels to log is empty.\nAdd channels to log then call StartLogging Command')

#-----------------------------------------------------version----------------------------------------------------------------------
@client.command(name='Version',
                description='Sends client version of the bot',
                brief='Version number',
                aliases=['version', 'v'],
                pass_context=True)
async def version(context):
    """sends user bot's version number"""
    async with context.typing():
        await context.send(format_message(MessageTypeLog,'Version: ' + Version))

#-------------------------------------------------------on_message----------------------------------------------------------------
@client.event
async def on_message(message):
    """takes each message that the bot can access and makes it lower case
    this is used so commands can be non case sensitive"""
    if message.author.bot == True:
        return
    for prefix in BotPrefix:
        if message.content[0].lower() == prefix:
            break
    else:
        return
    global ServerID
    server = client.get_guild(ServerID)
    serverMember = server.get_member(message.author.id)
    if serverMember == None:
        print_and_log(LogTypeInfo, 'User: ' + kill_emojis(message.author.name) + ' is not connected to the server')
    else:
        roles = serverMember.roles
        doesBotListen = False
        for role in commandRoles:
            for r in roles:
                if role == r.name:
                    doesBotListen = True
                    break
    if doesBotListen:
        message.content = message.content.lower()
        message.author = serverMember
        await client.process_commands(message)
    else:
        print_and_log(LogTypeInfo, 'User with no permissions trying to run command!')
        if serverMember.nick is not None:
            print_and_log(LogTypeInfo, 'Username: ' + kill_emojis(message.author.name))
            print_and_log(LogTypeInfo, 'Nickname: ' + kill_emojis(serverMember.nick))
        else:
            print_and_log(LogTypeInfo, 'Username: ' + kill_emojis(message.author.name))
        print_and_log(LogTypeInfo, 'Message: ' + kill_emojis(message.content))

#--------------------------------------------------------get_channels-------------------------------------------------------------
@client.command(name='GetChannelIDs',
				description='Gets text channels that the bot can access and prints their names and ids',
				brief='Prints Channel names and ids',
				aliases=['channels', 'listchannelids', 'getchannelids'],
				pass_context=True)
async def get_channels(context):
    """Shows the user the current text channels along with the channel's ID that are
        available to the bot"""
    channels = client.get_guild(ServerID).text_channels
    await context.send('Getting Available Channels...')
    async with context.typing():
        for channel in channels: 
            await context.send(format_message(MessageTypeLog, channel.name + " " + str(channel.id)))
        await context.send('All available channels listed.')


#----------------------------------------------------add_all_channels--------------------------------------------------------------
# adds all channels the bot can access to the logged channels list
@client.command(name='AddAllChannels',
                description='Adds all text channels to logged channels list',
                brief='Adds all channels to log list',
                aliases=['addallchannels', 'aac'],
                pass_context=True)
async def add_all_channels(context):
    async with context.typing():
        channels = client.get_guild(ServerID).text_channels
        for channel in channels:
            if channel.id not in channelsToLog:
                channelsToLog.append(channel.id)
                AddToXML(XMLChannel, XMLChannelAttribute, channel.name)
        LogCommand(context.message)
        await context.send('Added all text channels to be logged')

#--------------------------------------------------remove_all_channels-------------------------------------------------------------
@client.command(name='RemoveAllChannels',
                description='Removes all channels that are currently set to be logged.',
                brief='Removes all channels from logging',
                aliases=['removeallchannels'],
                pass_context=True)
async def remove_all_channels(context):
    """removes all the channels currently in channels to log list"""
    async with context.typing():
        for channelID in channelsToLog:
            channel = client.get_channel(channelID)
            RemoveFromXML(XMLChannel, XMLChannelAttribute, channel.name)
        LogCommand(context.message)
        channelsToLog.clear()
    await context.send('Removed all channels from logging!')

#-------------------------------------------------------log_date--------------------------------------------------------------------
@client.command(name='LogDate',
                description='Logs certain dates depending on dates submitted. \
To log one date enter date in format yyyy/mm/dd. To log a range of dates enter second date in same format. LogDate yyyy/mm/dd or LogDate yyyy/mm/dd yyyy/mm/dd',
                brief='Logs certain dates depending on date(s) submitted.',
                aliases=['LogDates', 'logdate', 'logdates'],
                pass_context=True)
async def log_date(context, date=None, endDate=None):
    """Creates a log for a specific date or from startDate to endDate for each channel in channelsToLog"""
    if len(channelsToLog) == 0:
        await context.send(format_message(MessageTypeWarning, 'Channels to log is empty'))
        return
    #if no date was passed in then return
    if date is None:
        return
    # the first date is set to the checked date and adjusted to local time
    firstDate = check_date(date)
    # if firstDate was an incorrect format let the client know then return
    if firstDate is None:
        await context.send(format_message(MessageTypeWarning, 'Date has an incorrect format'))
        return
    firstDate = firstDate - datetime.timedelta(hours=-GetTimeOffset())
    if endDate is not None:
        # if a second date was passed in set the date to the checked date plus
        # a day and convert to local time
        secondDate = check_date(endDate)
        # if the secondDate is None then return because it was in a bad format
        # or an invalid date
        if secondDate is None:
            await context.send(format_message(MessageTypeWarning, 'Second date has an incorrect format'))
            return
        else:
            secondDate = secondDate - datetime.timedelta(days=-1,hours=-GetTimeOffset())
            initialDate = firstDate
            lastDate = secondDate - datetime.timedelta(days=1)
        # if the second date is a correct format Log each channel in
        # ChannelsToLog and increment the day until
        # firstdate is equal or greater than the secondDate
            while firstDate < secondDate:
                async with context.typing():
                    for channelID in channelsToLog:
                        channel = client.get_channel(channelID)
                        if(channel._type is text_channel_type):
                            await LogChannel(channel, firstDate, 'LogDate')
                        else:
                            await context.send("Channel: " + channel.name + " is not a TextChannel!")
                    firstDate = firstDate + datetime.timedelta(days=1)
            await context.send(format_message(MessageTypeLog, 'Logs for created from:' + initialDate.strftime(DateFormat) + ' to ' + lastDate.strftime(DateFormat)))
            return
    # if no second date was entered
    # create logs for the first date for each channel in ChannelsToLog
    async with context.typing():
        for channelID in channelsToLog:
            channel = client.get_channel(channelID)
            if(channel._type is text_channel_type):
                await LogChannel(channel, firstDate, 'LogDate')
            else:
                await context.send("Channel: " + channel.name + " is not a TextChannel!")
        await context.send('Done!')

#--------------------------------------------------log_yesterday---------------------------------------------------------------------
# Creates logs for each channel in ChannelsToLog for yesterday's date
@client.command(name='LogYesterday',
				description='Logs yesterdays messages',
				brief='Logs yesterdays messages',
				aliases=['ly', 'logy', 'logyes', 'logyesterday'],
                pass_context=True)
async def log_yesterday(context):
    async with context.typing():
        info = await yesterday_log_loop('LogYesterday')
        if info is not None:
            await context.send(info)
        await context.send(format_message(MessageTypeLog, 'Finished logging yesterday'))

#--------------------------------------------------roles----------------------------------------------------------------------------
@client.command(name='Roles',
                description='Sends client the list of roles that the bot will take commands from.',
                brief='Sends client roles bot listens to',
                aliases=['roles'],
                pass_context=True)
async def roles(context):
    """Sends client each role in commandRoles"""
    if len(commandRoles) == 0:
        await context.send(format_message(MessageTypeError, 'Error: No roles have been added. Use AddRole to add a role.'))
        return
    async with context.typing():
        await context.send(format_message(MessageTypeLog, 'These are the roles that the bot will take commands from:'))
        for role in commandRoles:
            await context.send(format_message(MessageTypeLog, role))
        await context.send(format_message(MessageTypeLog, 'Done listing roles.'))

#------------------------------------------------------add_role----------------------------------------------------------------------
@client.command(name='AddRole',
                description='Adds a server role that the bot will take commands from.',
                brief='Add a role that the bot will listen to.',
                aliases=['addrole'],
                pass_context=True)
async def add_role(context, role=None):
    """Adds a role to the list of roles the bot will listen to. Adds a new xml element for the role."""
    if role is None:
        await context.send(format_message(MessageTypeWarning, 'Role not entered'))
        return
    async with context.typing():
        role = role.replace("'", '')
        server = client.get_guild(ServerID)
        added_role = None
        for servRole in server.roles:
            if role.lower() == servRole.name.lower():
                added_role = servRole.name
                break
        else:
            await context.send(format_message(MessageTypeWarning, 'Server does not have this role'))
            return
        LogCommand(context.message)
        commandRoles.append(added_role)
        AddToXML(XMLRole, XMLRoleAttribute, added_role)
        await context.send(format_message(MessageTypeLog, added_role + ' has been added'))

#----------------------------------------------------------remove_role---------------------------------------------------------------
@client.command(name='RemoveRole',
                description='Removes a server role that the bot takes commands from.',
                brief='Remove a role that the bot listens to',
                aliases=['removerole'],
                pass_context=True)
async def remove_role(context, role=None):
    """Removes specified role from list of roles the bot listens to and removes it from the xml config file."""
    if role == None:
        await context.send(format_message(MessageTypeWarning, 'Role not entered'))
    role = role.replace("'", '')
    removeRole = None
    for servRole in commandRoles:
        if servRole.lower() == role:
            removeRole = servRole
            break
    else:
        await context.send(format_message(MessageTypeWarning, 'Role was not in Command Roles'))
        return
    if len(commandRoles) == 1:
        await context.send(format_message(MessageTypeWarning, 'Only one Role can give the bot commands. Add another role to be able to remove this one.'))
        return
    commandRoles.remove(servRole)
    LogCommand(context.message)
    RemoveFromXML(XMLRole, XMLRoleAttribute, servRole)
    await context.send(format_message(MessageTypeLog, servRole + ' has been removed'))
    

#-------------------------------------------------------add_prefix----------------------------------------------------------
@client.command(name='AddPrefix',
                description='Adds a new character as a command prefix.  Can use this character to issue a command.',
                brief='Add new character as command prefix',
                aliases=['addprefix', 'addprfx'],
                pass_context=True)
async def add_prefix(context, prefix=None):
    """Adds a prefix to list of BotPrefixes used for calling commands"""
    if prefix is None:
        await context.send(format_message(MessageTypeWarning, 'Prefix not entered'))
        return
# name and nick
    if len(prefix) == 1:
        BotPrefix.append(prefix)
        AddToXML(XMLPrefix, XMLPrefixAttribute, prefix)
        await context.send(format_message(MessageTypeLog, prefix + ' has been added as a prefix'))
        LogCommand(context.message)
    else:
        await context.send(format_message(MessageTypeWarning, 'Prefix should be one character'))


#-----------------------------------------------------LogCommand--------------------------------------------------------------------
def LogCommand(message):
    """username, nick, and message and printed in console and written to file"""
    print_and_log(LogTypeInfo, 'Username: ' + kill_emojis(message.author.name))
    if message.author.nick is not None:
        print_and_log(LogTypeInfo, 'Nickname: ' + kill_emojis(message.author.nick))
    print_and_log(LogTypeInfo, 'Message: ' + kill_emojis(message.content))

#-------------------------------------------------------remove_prefix----------------------------------------------------------
@client.command(name='RemovePrefix',
                description='Removes a prefix from command prefixes.',
                brief='Remove a character from command prefixes',
                aliases=['removeprefix', 'rmvprfx'],
                pass_context=True)
async def remove_prefix(context, prefix=None):
    """Removes a prefix from BotPrefixes.  Prefixes are used to call commands"""
    if prefix is None:
        await context.send(format_message(MessageTypeWarning, 'No prefix entered'))
        return
    if prefix in BotPrefix and len(prefix) == 1:
        if len(BotPrefix) == 1:
            await context.send(format_message(MessageTypeWarning, 'Only one prefix exists. Add another to be able to remove this one'))
            return
        BotPrefix.remove(prefix)
        RemoveFromXML(XMLPrefix, XMLPrefixAttribute, prefix)
        await context.send(format_message(MessageTypeLog, prefix + ' has been removed from prefixes'))
        LogCommand(context.message)
    else:
        await context.send(format_message(MessageTypeWarning, prefix + ' was not a prefix'))

#---------------------------------------------------add_channel_to_log----------------------------------------------------------------
@client.command(name='AddChannelToLog',
				description='Adds a channel to list of channels to log',
				brief='Adds channel to channel list',
				aliases=['addchannel', 'addchn', 'addchanneltolog'],
				pass_context=True)
async def add_channel_to_log(context, newChannel):
    """Adds Channels to Logging"""
    newChannel = newChannel.replace("'", '')
    channel = get_channel_by_name(newChannel)
    if channel is None:
        channel = client.get_channel(newChannel)
    if channel is None:
        await context.send(format_message(MessageTypeError, BadChannelIdOrName))
        return
    
    for channelID in channelsToLog:
        if channelID == channel.id:
            await context.send(format_message(MessageTypeWarning, 'Channel: ' + channel.name + '\nID:' + str(channel.id) + '\nHas already been added.'))
            return
    if(channel._type is not text_channel_type):
        await context.send(format_message(MessageTypeLog, 'Channel: ' + channel.name + '\nID:' + str(channel.id) + '\nis not a TextChannel and has not been added.'))
        return
    channelsToLog.append(channel.id)
    AddToXML(XMLChannel, XMLChannelAttribute, channel.name)
    LogCommand(context.message)
    await context.send(format_message(MessageTypeLog, 'Channel: ' + channel.name + '\nID:' + str(channel.id) + '\nHas been added to channels to log.'))

#----------------------------------------------------remove_channel_from_log--------------------------------------------------------
@client.command(name='RemoveChannelFromLog',
				description='Removes channel from list of channels to log',
				brief='Removes channel to channel list',
				aliases=['removechannel', 'rmchn', 'removechannelfromlog'],
				pass_context=True)
async def remove_channel_from_log(context, new_channel):
    """Removes channels from logging"""
    new_channel = new_channel.replace("'", '')
    channel = client.get_channel(new_channel)
    if channel is None:
        channel = get_channel_by_name(new_channel)
    if channel is None:
        await context.send(format_message(MessageTypeError, BadChannelIdOrName))
        return
    if channel.id in channelsToLog:
        channelsToLog.remove(channel.id)
        RemoveFromXML(XMLChannel, XMLChannelAttribute, channel.name)
        await context.send(format_message(MessageTypeLog, 'Channel: ' + channel.name + '\nID:' + str(channel.id) + '\nwas removed from Channels To Log'))
        LogCommand(context.message)
    else:
        await context.send(format_message(MessageTypeWarning, 'Channel: ' + channel.name + '\nID:' + str(channel.id) + '\nwas not in Channels To Log'))


#----------------------------------------------------format_date-------------------------------------------------------------
def format_date(date, date_number):
    if date is not None:
        newDate = check_date(date)
        if newDate is None:
            print('Error: ' + date_number + ' is not valid')
            return None
        else:
            return newDate

#-----------------------------------------------------get_logs----------------------------------------------------------------
@client.command(name='GetLogs',
                description='Gets all logs and sends them to user',
                brief='Gets all logs',
                aliases=['getlogs', 'gl', 'getlog'],
                pass_context=True)
async def get_logs(context):
    """Gets all logs and sends them to user"""
    if os.path.exists(ParentDirectory):
        await context.send('Getting all logs...')
        log_name = 'LogCat_logs_All_Logs'
        shutil.make_archive(log_name, 'zip', ParentDirectory)
        try:
            await context.send(file=discord.File(log_name + '.zip', log_name + '.zip'))
            await context.send('Done!')
        except Exception as e:
            print_and_log(LogTypeInfo, 'Command: ' + 'GetLogs')
            print_and_log(LogTypeError, e)
            await context.send(e)
        os.remove(log_name + '.zip')
    else:
        await context.send(format_message(MessageTypeError, 'No Logs Exist'))

#----------------------------------------------get_channel_logs-------------------------------------------------------------------

@client.command(name='GetChannelLogs',
                description='Gets logs from specificed channel name or ID. Can also pass in dates formatted yyyy/mm/dd. Can enter\
 dates in any order. Enter a single date for logs for that day or 2 dates for all logs during that period. GetChannelLogs general yyyy/mm/dd yyyy/mm/dd',
                brief='Gets the logs from the specified channel name',
                aliases=['getchannellogs', 'getchannellog', 'chnlog', 'chnlogs'],
                pass_context=True)
async def get_channel_logs(context, param1=None, param2=None, param3=None):
    """Gets logs from a specific channel that the user passes in.  If no date is
entered all logs are returned for that specific channel.
if a single date is entered then the logs for that channel on that date are returned.
if two dates and a channel are entered then the logs from the earlier date to
the later date are returned from that channel"""
    directoryToCopy = ParentDirectory
    channel = None
    date1 = None
    date2 = None
    filesToCopy = []

    #tries to see what parameter is a channel
    if param1 is not None:
        channel = get_channel_by_name(param1)
    if channel is None and param2 is not None:
        channel = get_channel_by_name(param2)
    if channel is None and param3 is not None:
        channel = get_channel_by_name(param3)
    
    permission_required = await has_permissions(channel)

    if permission_required == False:
        await context.send(format_message(MessageTypeError, "Error: read_channel_history permission is required."))
        return
        

    # if no channel wa found return and send error message
    if channel is None:
        await context.send(format_message(MessageTypeError, 'Error: could not find channel name')) 
        return

    # if the channel's name has any slashes replace them with -
    channelNamePath = channel.name.replace('/', '-')
    channelNamePath = channelNamePath.replace(r'\\', '-')
    
    # if we found a channel set the directoryToCopy to the parent directory +
    # the channels name
    if channel is not None:
        directoryToCopy = ParentDirectory + '/' + channelNamePath
        #check the if another parameter was added and check if it's a date
        if param1 is not channel and param1 is not None:
            date1 = check_date(param1)
        if param2 is not channel and param2 is not None:
            if date1 is None:
                date1 = check_date(param2)
            else:
                date2 = check_date(param2)
        if param3 is not channel and param3 is not None:
            if date1 is None:
                date1 = check_date(param3)
            else:
                if date2 is None:
                    date2 = check_date(param3)
    
        if channel is not None:
            # if channel is none create a temp folder with the channel's name
            await context.send(format_message(MessageTypeLog, 'Attempting to get logs for ' + channel.name))
            path = TempFolder + '/' + channelNamePath
            os.makedirs(path, exist_ok=True)
            if os.path.exists(ParentDirectory + '/' + channelNamePath):
                print('path exists')
            else:
                await context.send(format_message(MessageTypeError,'Error: Logs do not exist'))
                return
        # check if a first date was entered
        if date1 is not None:
            #if second date was entered compare dates and set earlier date to
            #startDate
            # and later date to endDate
            if date2 is not None:
                if date1 >= date2:
                    startDate = date2
                    endDate = date1
                else:
                    startDate = date1
                    endDate = date2
                interDate = startDate
                #copy filenames to filesToCopy for each day until we reach the
                #end date
                while interDate <= endDate:
                    await copy_files(interDate, directoryToCopy, filesToCopy, channel.name)
                    interDate = interDate + datetime.timedelta(days=1)
            # if only a first date was entered copy the filenames to
            # filesToCopy for that day
            else:
                await copy_files(date1, directoryToCopy, filesToCopy, channel.name)

            if len(filesToCopy) > 0:
                for file in filesToCopy:
                    sourcePath = ParentDirectory + '/' + channel.name + '/' + file
                    shutil.copyfile(sourcePath, path + '/' + file)
            else:
                await context.send(format_message(MessageTypeWarning, 'No Logs available. Sending empty folder'))

            fileDate = date1.strftime(DateFormat) 
            if date2 is not None:
                fileDate = startDate.strftime(DateFormat) + ' ' + endDate.strftime(DateFormat)
            
            LogName = 'LogCat_logs_' + channel.name + '_' + fileDate
            shutil.make_archive(LogName, 'zip', TempFolder)

        # if no date was entered send the channel's entire logs
        if date1 is None and date2 is None:
            source_path = ParentDirectory + '/' + channelNamePath
            if os.path.isdir(source_path):
                distutils.dir_util.copy_tree(source_path, path)
                LogName = 'LogCat_logs_' + channelNamePath
                shutil.make_archive(LogName, 'zip', ParentDirectory + '/' + channelNamePath)
            else:
                await context.send(format_message(MessageTypeError, 'No Logs available. Sending empty folder'))
    # send the logs with the channel's name
    try:
        await context.send(file=discord.File(LogName + '.zip', LogName + '.zip'))
        await context.send('Logs Sent!')
    except Exception as e:
        print_and_log(LogTypeInfo, 'Command: ' + 'get_channel_logs')
        print_and_log(LogTypeError, e)
        await context.send(e)

    # delete the temp folder
    if os.path.exists(TempFolder):
        distutils.dir_util.remove_tree(TempFolder)
    if os.path.isfile(LogName + '.zip'):
        os.remove(LogName + '.zip')

#------------------------------------------------------copy_files--------------------------------------------------------------------
async def copy_files(date, directoryToCopy, filesToCopy, channelName):
    """Checks if a file exists and appends its path to filesToCopy
if it does not exist then it attempts to create a log for that day"""
    file = channelName + ' ' + date.strftime(DateFormat) + '.txt'
    if os.path.exists(directoryToCopy + '/' + file):
        print('Found file')
        print(file)
    else:
        channel = get_channel_by_name(channelName)
        check = GetTimeOffset()
        if(channel.type is text_channel_type):
            await LogChannel(channel, date + datetime.timedelta(hours=GetTimeOffset()), 'get_channel_logs')
        else:
            print_and_log(LogTypeError, "Channel: " + channel.name + " is not a TextChannel!")
    filesToCopy.append(file)

#------------------------------------------get_channel_by_name-------------------------------------------------------------------
def get_channel_by_name(channelName):
    """Loops through all channels and returns channel if the channelName was equal to the channel's name"""
    channels = client.get_all_channels()
    for channel in channels:
        if channel.name.lower() == channelName.lower():
            return channel

#------------------------------------------------logged_channels------------------------------------------------------------------
@client.command(name='LoggedChannels',
                description='Tells what channels are set to be logged.',
                brief='What channels are set to be logged',
                aliases=['LoggedChan', 'loggedchannels', 'lc'],
                pass_context=True)
async def logged_channels(context):
    """Tells the client what channels are in channelsToLog list"""
    if len(channelsToLog) == 0:
        await context.send(format_message(MessageTypeWarning,'No channels have been added'))
    else:
        await context.send('These are the channels that are currently set to be logged:')
        async with context.typing():
            for channelID in channelsToLog:
                await context.send(format_message('Log', client.get_channel(channelID).name))
            await context.send('Done listing channels set to be logged.')

#-----------------------------------------------start_logging---------------------------------------------------------------
@client.command(name='StartLogging',
                description='Starts the automated daily logging',
                brief='Starts auto logging',
                aliases=['startlogging', 'strtlog'],
                pass_context=True)
async def start_logging(context):
    """Starts automatic logging
    checks if channelsToLog's size is greater than 0 and if it is then calls
    check_time, and sets AutomaticLogging to True"""
    global AutomaticLogging
    if AutomaticLogging == False:
        if len(channelsToLog) > 0:
            AutomaticLogging = True
            await context.send('Starting AutoLogging')
            await check_time()
        else:
            await context.send(format_message(MessageTypeError, 'Error : No channels added to log list'))
    else:
        await context.send(format_message(MessageTypeWarning, 'Warning : Auto logging is already started'))

#----------------------------------------------------auto_logging----------------------------------------------------------------
@client.command(name="AutoLogging",
                description='Says state of Automatic Logging',
                brief='State of Auto Logging',
                aliases=['autologging','autolog'],
                pass_context=True)
async def auto_logging():
    """Tells client the current state of AutomaticLogging"""
    await context.send('Automatic logging is currently set to: ' + str(AutomaticLogging))

#------------------------------------------------kill_emojis----------------------------------------------------------------------
def kill_emojis(string):
    """Removes emojis from a string.  Writing strings to a file that have emojis
causes an error in write.  So we just remove them"""
    return emoji_pattern.sub(r'', string)


#--------------------------------------------------yesterday_log_loop------------------------------------------------------------
async def yesterday_log_loop(command=None):
    """Loops through each channel ID in channels to log
gets each channel and creates logs for yesterday"""
    for channelID in channelsToLog:
        channel = client.get_channel(channelID)
        if channel is None:
            return('Incorrect Channel ID')
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1, hours=datetime.datetime.now().hour - GetTimeOffset(), minutes=datetime.datetime.now().minute, seconds=datetime.datetime.now().second)
        if(channel._type is text_channel_type):
            await LogChannel(channel, yesterday, command)
        else:
            print_and_log(LogTypeError ,"Channel: " + channel.name + " is not a TextChannel!")

#--------------------------------------------------------check_date---------------------------------------------------------------
def check_date(date):
    """Checks if a string the user entered can be converted into a datetime object
if it can then a datetime object is made and returned"""
    found_date = date_pattern.match(date)
    if found_date is None:
        return None
    the_date = found_date.group(1) + '-' + found_date.group(2) + '-' + found_date.group(3)
    print(the_date)
    newDateTime = datetime.datetime.strptime(found_date.group(1) + ' ' + found_date.group(2) + ' ' + found_date.group(3),'%Y %m %d')
    return newDateTime

#-------------------------------------------------------GetTimeOffset-------------------------------------------------------------
def GetTimeOffset():
    """Gets the hour difference between local time and GMT
Is used to convert from GMT to Local time
this won't work for some timezones because some change by half an hour during
dst. This works fine for pacific time"""
    hourOffset = time.gmtime().tm_hour - time.localtime().tm_hour
    return hourOffset % 24

#------------------------------------------------------format_message---------------------------------------------------------------
def format_message(message_type, message):
    """Formats a message by adding a color and making them into a code block in discord"""
    formatted_message = None
    if message_type == MessageTypeError:
        formatted_message = Error + message
    elif message_type == MessageTypeLog:
        formatted_message = Log + message
    elif message_type == MessageTypeWarning:
        formatted_message = Warning + message
    formatted_message += EndCodeBlock
    return formatted_message

#----------------------------------------------check_if_roles_assigned----------------------------------------------------------------
def check_if_roles_assigned():
    global commandRoles
    if len(commandRoles) == 0:
        print_and_log(LogTypeError, 'No roles assigned. Either generate a new file or add\n<Role name="Fake Role"/> in config.xml')

#-----------------------------------------------get_console_logs------------------------------------------------------------------
@client.command(name='GetConsoleLogs',
                description='Sends the debug text file to the client. console.txt contains a list of the add and remove commands that were sent to the bot along with the sender info',
                brief='Sends console.txt to client',
                aliases=['getconsolelogs'],
                pass_context=True)
async def get_console_logs(context):
    """Sends the console.txt file to the client"""
    try:
        await context.send(file=discord.File(ConsoleLogs, ConsoleLogs))
        await context.send('Done sending console logs')
    except Exception as e:
        print_and_log(LogTypeInfo, 'Command: ' + 'GetConsoleLogs')
        print_and_log(LogTypeError, e)
        await context.send(e)

#-----------------------------------------------get_runtime-----------------------------------------------------------------------
@client.command(name='GetRuntime',
                description='Gets the runtime of the bot',
                brief='Returns runtime',
                aliases=['getruntime', 'runtime'],
                pass_context=True)
async def get_runtime(context):
    """Returns the runtime of the script"""
    total_time = time.time() - start_time
    seconds = int(total_time)
    minutes = 0
    hours = 0
    days = 0
    if total_time >= 60:
        minutes = int(seconds / 60)
        seconds = seconds % 60
    if minutes >= 60:
        hours = int(minutes / 60)
        minutes = minutes % 60
    if hours > 24:
        days = int(hours/24)
        hours = hours % 24
    await context.send(str(days) + " Days, " + str(hours) + ' Hours, ' + str(minutes) + ' Minutes, ' + str(seconds) + " Seconds")
#------------------------------------------------on_error--------------------------------------------------------------------------
@client.event
async def on_error(event, *args, **kwargs):
    print_and_log(LogTypeError, sys.exc_info())

#------------------------------------------------has_permissions----------------------------------------------------------------
async def has_permissions(channel):
    """Returns read message history permissions for the specified channel"""
    server = client.get_guild(ServerID)
    permissions = channel.permissions_for(server.me)
    return permissions.read_message_history
    

#-------------------------------------------------run_client-----------------------------------------------------------------------
def run_client(client):
    """Try to run the bot and if it fails wait a minute and try again"""
    bot_loop = asyncio.get_event_loop()
    while True:
        try:
            #Check config file and apply settings
            check_config_file()
            check_if_roles_assigned()
            global TOKEN
            bot_loop.run_until_complete(client.start(TOKEN))
        except Exception as e:
            if e is not IOError:
                print_and_log(LogTypeError, e)
        print_and_log(LogTypeInfo, 'Waiting 60 seconds then restarting')
        time.sleep(60)
    
run_client(client)
