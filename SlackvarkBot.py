import sys
import configparser
import json
import requests
from slackclient import SlackClient

class SlackvarkBot:

    def __init__(self, bot_token, human_token, inLegalSlack):
        self.client = None
        self.username = None
        self.bot_token = bot_token
        self.human_token = human_token
        self.in_menu = False
        self.inLegalSlack = inLegalSlack


    # inititalize client and open connection
    def connect(self, token):
        self.client = SlackClient(token)
        self.client.rtm_connect()
        self.username = self.client.server.username

    # starts listener for server
    def listen(self):
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
                    self.post(self.openDirectChannel(action["user"]["id"]),
                            action["user"]["id"])
                    self.in_menu = False
        while self.inLegalSlack:
            response = self.client.rtm_read()
            for action in response:
                # debug pretty print
                print(json.dumps(action, sort_keys=False, indent=4), end='\n\n')
                if "type" in action and action["type"] == "message":
                    self.processDMLegal(action)
                    

    # post message to channel
    # params channel - string; message - string
    def post(self, channel, message):
        channel = channel.lstrip('#')
        chanObj = self.client.server.channels.find(channel)
        if not chanObj:
            raise Exception("%s not found in list of available channels." %
                            channel)
        chanObj.send_message(message)

    # open direct channel
    # params username - string;
    # returns channel id
    def openDirectChannel(self, username):
        response = self.client.api_call(method="im.open",user=username).decode("utf-8")
        response = json.loads(response)
        # debug
        print(json.dumps(response, sort_keys=False, indent=4), end="\n\n")
        if response["ok"]:
            channelID = response["channel"]["id"]
            print("Direct Message ChannelID Open:", channelID)
            return channelID
        else:
            print("openDirectChannel Error")

    # resolve direct channel ID given username
    # params username - string; username to look up
    # returns string of channel ID if successful
    def getDirectChannelID(self, username):
        """Returns direct message channel id given username"""
        imObjects = self.client.api_call(method="im.list").decode(
            "utf-8")  # list all direct message channels
        imObjects = json.loads(imObjects)
        # debug pretty print
        # print(json.dumps(imObjects, sort_keys=False, indent=4))
        if imObjects["ok"]:
            for im in imObjects["ims"]:
                if im["user"] == username:  # if found user
                    return im["id"]  # return direct message  channel ID
        return None

    # resolve user ID given username
    # params username - string; username to look up
    # returns string of user ID if successful, none otherwise
    def getUserID(self, username):
        userObjects = self.client.api_call(method="users.list").decode(
            "utf-8")  # list all users in slack w/API call
        userObjects = json.loads(userObjects)

        if userObjects["ok"]:
            for user in userObjects["members"]:
                if user["name"] == username:  # if found user
                    return user["id"]  # return user ID
        return None

    # resolve username given user ID
    # params userID - string; user ID to look up
    # returns string of username if successful, none otherwise
    def getUserName(self, userID):
        userObjects = self.client.api_call(method = "users.list").decode("utf-8") # list all users in slack w/API call
        userObjects = json.loads(userObjects)

        if userObjects["ok"]:
            for user in userObjects["members"]:
                if user["id"] == userID: # if found user
                    return user["name"] # return username
        return None

    # resolve group ID given channel name
    # params groupName - string; group name to look up
    # returns string of group ID if successful, none otherwise
    def getGroupID(self, groupName):
        groupObjects = self.client.api_call(method = "groups.list").decode("utf-8") # list all groups in slack w/API call
        groupObjects = json.loads(groupObjects)

        if groupObjects["ok"]:
            for group in groupObjects["groups"]:
                if group["name"] == groupName: # if found group
                    return group["id"] # return group ID
        return None


    # Creates a new private channel (group) using human token. Automatically invites itself and any users specified in arguments
    # params users - list; users to be added, groupName - string; name of group
    # returns ID number of newly-created group
    def createNewGroup(self, users, groupName):
        groupId = ""
        if self.inLegalSlack: botName = "aaron"
        else: botName = "slackvark_bot"
        
        self.connect(self.human_token)  # switch to human token
        groupObject = self.client.api_call(
            method="groups.create", token=human_token, name=groupName)  # create group

        # decode group object to resolve ID (needed to add users)
        groupObject = groupObject.decode("utf-8")
        groupObject = json.loads(groupObject)
  
        if(groupObject["ok"]):
            groupId = groupObject["group"]["id"]
        elif groupObject["error"] == 'name_taken':
            self.connect(self.bot_token) # switch back to bot token
            groupID = self.getGroupID(groupName)
            self.connect(self.human_token) # switch back to human token

            groupObject = self.client.api_call(method = "groups.unarchive", token=self.human_token, name=groupID)
            groupObject = groupObject.decode("utf-8")
            groupObject = json.loads(groupObject)
            if not groupObject["ok"]:
                return None
            groupId = groupObject["group"]["id"]

        # for each user in the input list
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

    # handle listener actions
    # params action - dictionary;
    def processMessage(self, action):
        command = action[
            "text"].lower().strip()  # retrieve actual text of message
        # inintialize variables for private channel creation
        usernameList = []
        channelName = ""

        # rudimentary menu follows. will likely be scrapped as bot developes
        if command == "hello":  # bot listens for "hello"
            self.in_menu = True
            # post main options
            self.post(action["channel"], "Hi! I am a test build of Slackvark. Please choose from these options:\n \
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
                # another repeat of above. Nuri has suggested we split the listener into a separate class. \
                    # perhaps this can be a member function #
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
            self.post(action["channel"], "invalid selection.")

    def processDMLegal(self, action):
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
        human_token = config["PERSON1"]["token"] # retrieve human token from creds file

    else:
        bot_token = config["AARON"]["token"]
        human_token = config["PERSON2"]["token"] # retrieve human token from creds file
    
    slackvark_bot = SlackvarkBot(bot_token, human_token, inLegalSlack)
    slackvark_bot.connect(bot_token)

    slackvark_bot.listen() # call listener
