import sys
import configparser
import json
from slackclient import SlackClient

class SlackvarkBot:

    def __init__(self, bot_token, human_token):
        self.client = None
        self.username = None
        self.bot_token = bot_token
        self.human_token = human_token
        self.in_menu = False

    # inititalize client and open connection
    def connect(self, token):
        self.client = SlackClient(token)
        self.client.rtm_connect()
        self.username = self.client.server.username

    # starts listener for server
    def listen(self):
        while True:
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

    # Creates a new private channel (group) using human token. Automatically invites itself and any users specified in arguments
    # params users - list; users to be added, groupName - string; name of group
    # returns ID number of newly-created group
    def createNewChannel(self, users, groupName):
        self.connect(self.human_token)  # switch to human token
        groupObject = self.client.api_call(
            method="groups.create", token=human_token, name=groupName)  # create group

        # decode group object to resolve ID (needed to add users)
        groupObject = groupObject.decode("utf-8")
        groupObject = json.loads(groupObject)
        # as of now, function will fail if given a groupName that has already been used. Plan to address this when implementing code
        # to programatically determine private channel name
        if(groupObject["ok"]):
            groupId = groupObject["group"]["id"]

        # for each user in the input list
        for userName in users:
            if(userName[-1] == ":"):
                userName = userName[
                    :-1]  # strip the colon that Slack automatically adds
                # print(userName) #DEBUG
            self.client.api_call(method="groups.invite", token=human_token,
                                 channel=groupId, user=self.getUserID(userName))  # invite to group

        self.client.api_call(method="groups.invite", token=human_token,
                             channel=groupId, user=self.getUserID("slackvark_bot"))  # invite self

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
                      3. Create a new channel")
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
            self.post(self.createNewChannel(usernameList, channelName),
                      "Hello again! I've created this channel for you.\n")
        #This will stop the invalid selection bug where it keeps saying it in chat
        elif self.in_menu:
            self.post(action["channel"], "invalid selection.")
            print("\n\n\n\n" + command + "\n\n\n\n")

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("creds.cfg")  # read creds file
    bot_token = config["SLACK"]["token"]  # retrieve bot token from creds file
    human_token = config["PERSON"]["token"]
        # retrieve human token from creds file

    slackvark_bot = SlackvarkBot(bot_token, human_token)
    slackvark_bot.connect(bot_token)

    slackvark_bot.listen()  # call listener
