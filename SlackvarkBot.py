import sys
import configparser
import json
import requests
from slackclient import SlackClient


class SlackvarkBot:

    def __init__(self, bot_token, human_token, inLegalSlack):
        """
        Initializes the bot using the given credentials.

        Parameters:
        bot_token (str), human_token (str)-- credentials for the bot to connect with
        inLegalSlack (bool) -- flag indicating whether bot is in Legal Slack
        """
        self.client = None
        self.username = None
        self.bot_token = bot_token
        self.human_token = human_token
        self.in_menu = False
        self.inLegalSlack = inLegalSlack


    def connect(self):
        """
        Connects to the Slack Real Time Messaging (RTM) API.
        """
        self.client = SlackClient(self.bot_token)
        self.client.rtm_connect()
        self.username = self.client.server.username


    # Suggested separating listener into a separate class to handle actions
    def listen(self):
        """
        Starts the listener within the Slack that the bot is part of.
        """
        while not self.inLegalSlack:
            response = self.client.rtm_read()
            for action in response:
                # debug pretty print
                print(json.dumps(action, sort_keys=False, indent=4), end='\n\n')
                if "type" in action and action["type"] == "message":
                    response = self.processMessage(action)
                    if response:
                        exit()
                elif "type" in action and action["type"] == "team_join":
                    newDirectChannel = self.openDirectChannel(action["user"]["id"])
                    self.connect()
                    # Change message to post on new team member join
                    self.post(newDirectChannel, "Hello there, welcome to the channel")
                    self.in_menu = False
        while self.inLegalSlack:
            response = self.client.rtm_read()
            for action in response:
                # debug pretty print
                print(json.dumps(action, sort_keys=False, indent=4), end='\n\n')
                if "type" in action and action["type"] == "message":
                    self.processDMLegal(action)


    def post(self, channel, message):
        """
        Posts a message to a channel.

        Parameters:
        channel (str) -- channel to post in
            ex: "#testchannel" or "#Cxxxxxxxx"
        message (str) -- message to post
        """
        channel = channel.lstrip('#')
        chanObj = self.client.server.channels.find(channel)
        if not chanObj:
            raise Exception("%s not found in list of available channels." %
                            channel)
        chanObj.send_message(message)


    def openDirectChannel(self, username):
        """
        Opens a direct message channel

        Parameters:
        username (str) -- username to open a channel between
            ex: "slackuser1" or "Uxxxxxxxx"

        Returns:
        channelID (str) -- channel id of opened direct message channel
            ex: "Cxxxxxxxx"
        """
        response = self.client.api_call(method="im.open",user=username).decode("utf-8")
        response = json.loads(response)
        # debug
        # print(json.dumps(response, sort_keys=False, indent=4), end="\n\n")
        if response["ok"]:
            channelID = response["channel"]["id"]
            # debug
            # print("Direct Message ChannelID Open:", channelID)
            return channelID
        else:
            print("Bad response from im.open")
            return None


    def getDirectChannelID(self, username):
        """
        Gets direct message channel ID given username

        Parameters:
        username (str) -- username to open a channel between
            ex: "slackuser1" or "Uxxxxxxxx"

        Returns:
        channelID (str) -- channel id of direct message channel of user
            ex: "Cxxxxxxxx"
        """
        imObjects = self.client.api_call(method="im.list").decode("utf-8")
        imObjects = json.loads(imObjects)
        if imObjects["ok"]:
            for im in imObjects["ims"]:
                if im["user"] == username:  # if found user
                    return im["id"]  # return direct message channel ID
            else:
                print("Couldn't find that username in the"
                      "list of open direct message channels")
        else:
            print("Bad Response from im.list")
        return None

    def getUserID(self, username):
        """
        Gets user ID given username

        Parameters:
        username (str) -- username to look up id of
            ex: "slackuser1"

        Returns:
        userID (str) -- user id belonging to param username
            ex: "Uxxxxxxxx"
        """
        userObjects = self.client.api_call(method="users.list").decode(
            "utf-8")  # list all users in slack w/API call
        userObjects = json.loads(userObjects)

        if userObjects["ok"]:
            for user in userObjects["members"]:
                if user["name"] == username:  # if found user
                    return user["id"]  # return user ID
            else:
                print("Couldn't find that username in the list of users")
        else:
            print("Bad Response from users.list")
        return None

    # resolve username given user ID
    # params userID - string; user ID to look up
    # returns string of username if successful, none otherwise
    def getUserName(self, userID):
        """
        Gets username given user ID

        Parameters:
        userID (str) -- user ID to look up name of
            ex: "Uxxxxxxxx"

        Returns:
        username (str) -- username belonging to param userID
            ex: "slackuser1"
        """
        userObjects = self.client.api_call(method = "users.list").decode("utf-8") # list all users in slack w/API call
        userObjects = json.loads(userObjects)

        if userObjects["ok"]:
            for user in userObjects["members"]:
                if user["id"] == userID: # if found user
                    return user["name"] # return username
            else:
                print("Couldn't find that user in the list of users")
        else:
            print("Bad response from users.list")
        return None

    def getGroupID(self, groupName):
        """
        Gets groupID given channel name

        Parameters:
        groupName (str) -- groupName to look up group ID of
            ex: #slackchannel1
        
        Returns:
        groupID (str) -- groupID belonging to param groupName
        """
        groupObjects = self.client.api_call(method = "groups.list").decode("utf-8") # list all groups in slack w/API call
        groupObjects = json.loads(groupObjects)

        if groupObjects["ok"]:
            for group in groupObjects["groups"]:
                if group["name"] == groupName: # if found group
                    return group["id"] # return group ID
            else:
                print("Couldn't find that group in the list of groups")
        else:
            print("Bad response from groups.list")
        return None


    def createNewGroup(self, users, groupName):
        """
        Creates a new private channel (group) using human token.
        Bot automatically invites itself and any users specified in arguments

        Parameters:
        users (list) -- users to be added
        groupName (str) -- name of group (channel)

        Returns:
        groupId (str) -- ID number of newly-created group
        """
        groupId = ""
        if self.inLegalSlack: botName = "aaron"
        else: botName = "slackvark_bot"
        
        self.connect(self.human_token)  # switch to human token
        groupObject = self.client.api_call(
            method="groups.create", token=human_token, name=groupName)  # create group

        # decode group object to resolve ID (needed to add users)
        groupObject = groupObject.decode("utf-8")
        groupObject = json.loads(groupObject)
  
        if groupObject["ok"]:
            groupId = groupObject["group"]["id"]
        elif groupObject["error"] == 'name_taken':
            self.connect(self.bot_token) # switch back to bot token
            groupID = self.getGroupID(groupName)
            self.connect(self.human_token) # switch back to human token

            groupObject = self.client.api_call(method = "groups.unarchive", token=self.human_token, name=groupID)
            groupObject = groupObject.decode("utf-8")
            groupObject = json.loads(groupObject)
            if not groupObject["ok"]:
                print("Bad response from groups.unarchive")
                return None
            groupId = groupObject["group"]["id"]

        for userName in users:
            if(userName[-1] == ":"):
                userName = userName[:-1]  # strip the colon that Slack automatically adds
                # print(userName) #DEBUG
            self.client.api_call(method="groups.invite", token=human_token,
                                 channel=groupId, user=self.getUserID(userName))  # invite to group

        self.client.api_call(method="groups.invite", token=human_token,
                             channel=groupId, user=self.getUserID(botName))  # invite self

        self.connect(self.bot_token)  # switch back to bot token
        return groupId


    # Handler could also be a separate class
    def processMessage(self, action):
        """
        Handles actions passed from listener

        Parameters:
        action (dict) -- response from RTM listener
            ex: {
                    "type": "presence_change",
                    "user": "Uxxxxxxxx",
                    "presence": "active"
                }
        """
        command = action["text"].lower().strip()  # retrieve actual text of message
        # inintialize variables for private channel creation
        usernameList = []
        channelName = ""

        # rudimentary menu follows. will likely be scrapped as bot developes
        if command == "hello":  # bot listens for "hello"
            self.in_menu = True
            # post main options
            self.post(action["channel"],"Hi! I am a test build of Slackvark. Please choose from these options:\n \
                      1. Exit menu\n \
                      2. Send a direct message\n \
                      3. Create a new group\n \
                      4. Message the Legal Slack")
        elif self.in_menu and command == "1":
            return 1  # signals listener to quit program
        elif self.in_menu and command == "2":
            self.post(self.getDirectChannelID(
                action["user"]), "hello")  # messages "hello" via DM
        elif self.in_menu and command == "3":
            self.post(
                action["channel"], "Awesome. Who would you like to invite?")
                      # prompts for list of users
            condition = True
            while condition:  # wait for response from user
                # begin code repeated from listener. This may be a good
                # candidate for a function. ##
                response1 = self.client.rtm_read()
                for item in response1:
                    if "type" in item and item["type"] == "message":
                        usernameList = item["text"].strip().split(
                            " ")  # split on spaces
                        condition = False
                # --------------------------- end repeated code --------------------------------- ##
            self.post(
                action["channel"], "What would you like to call this channel?")
            condition = True
            while condition:
                # another repeat of above. Nuri has suggested we split the listener into a separate class. \
                    # perhaps this can be a member function #
                response2 = self.client.rtm_read()
                for item in response2:
                    if "type" in item and item["type"] == "message":
                        channelName = item["text"].lower().strip()
                        condition = False
                # --------------------------- end repeated code --------------------------------- ##
            # post to newly-created channel
            self.post(self.createNewGroup(usernameList, channelName),
                      "Hello again! I've created this channel for you.\n")
        elif self.in_menu and command == "4":
            self.post(action["channel"], "Please give a channel name.")
            condition = True
            while condition:
                response2 = self.client.rtm_read()
                for item in response2:
                    if "type" in item and item["type"] == "message":
                        channelName = item["text"].lower().strip()
                        condition = False
            self.post(self.createNewGroup([], channelName), "Hello again! I've created this channel for you.\n")
            
            payload = {"text" : self.getUserName(item["user"]) + " " + channelName + " " + "T0K6H0Q8N/B0NCLNQNQ/1W8CAOsVNkZwMtq1gmWyhBfy", "channel" : "@aaron", "username" : "temp"}
            payload = json.JSONEncoder().encode(payload)
            r = requests.post("https://hooks.slack.com/services/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", data=payload)
            
            to_send = ""
            while True:
                response3 = self.client.rtm_read()
                for item in response3:
                    if "type" in item and item["type"] == "message" and "user" in item and item["user"] != self.getUserID("slackvark_bot") and item["channel"] == self.getGroupID(channelName):
                        to_send = item["text"].lower().strip()
                        payload = {"text" : to_send, "channel" : "#" + channelName, "username" : self.getUserName(item["user"]), "icon_emoji" : ":electric_plug:"}
                        payload = json.JSONEncoder().encode(payload)
                        r = requests.post("https://hooks.slack.com/services/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", data=payload)
        #This will stop the invalid selection bug
        elif self.in_menu:
            self.post(action["channel"], "Invalid Selection.")

    def processDMLegal(self, action):
        """
        Handles actions specific to the legal slack passed from the listener

        Parameters:
        action (dict) -- response from RTM listener
            ex: {
                    "type": "presence_change",
                    "user": "Uxxxxxxxx",
                    "presence": "active"
                }
        """
        commandList = action["text"].strip().split() # retrieve actual text of message
        self.createNewGroup(commandList[0].lower(), commandList[1].lower())

        hookURL = 'https://hooks.slack.com/services/' + commandList[2]
        to_send = ""
        while True:
            response = self.client.rtm_read()
            for item in response:
                if ("type" in item and item["type"] == "message") and ("user" in item and item["user"] != self.getUserID("aaron")): #and item["channel"] == self.getGroupID(commandList[1]):
                    to_send = item["text"].lower().strip()
                    payload = {"text" : item["text"], "channel" : "#" + commandList[1], "username" : commandList[0], "icon_emoji" : ":electric_plug:"}
                    payload = json.JSONEncoder().encode(payload)
                    r = requests.post(hookURL, data=payload)        
        return

if __name__ == "__main__":
    inLegalSlack = False
    config = configparser.ConfigParser()
    config.read("creds.cfg") # read creds file
    if not inLegalSlack:
        bot_token = config["SLACK"]["token"] # retrieve bot token from creds file
        human_token = config["PERSON"]["token"] # retrieve human token from creds file

    else:
        bot_token = config["AARON"]["token"]
        human_token = config["PERSON2"]["token"] # retrieve human token from creds file
    
    slackvark_bot = SlackvarkBot(bot_token, human_token, inLegalSlack)
    slackvark_bot.connect()

    slackvark_bot.listen() # call listener
