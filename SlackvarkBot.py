import sys
import configparser
import json
import requests
from slackclient import SlackClient

import MessageConstants

class Conversation:
    def __init__(self, name, ID):
        self.username = name
        self.userID = ID
        self.status = 0 # 0 = init, 1 = user has typed 'hello', 2 = question, 3 = tag, 4 = confirmed
        self.question = ""
        self.tags = []

    def setStatus(self, num):
        self.status = num

    def setQuestion(self, quest):
        self.question = quest

    def setTags(self, tags):
        self.tags = tags

    def getStatus(self):
        return self.status

    def getQuestion(self):
        return self.question

    def getUsername(self):
        return self.username

    def getUserID(self):
        return self.userID


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
        self.inLegalSlack = inLegalSlack
        self.directChannelList = []
        self.conversationList= []

    def connect(self, inLegalSlack):
        """
        Connects to the Slack Real Time Messaging (RTM) API.
        """
        if inLegalSlack:
            self.client = SlackClient(self.human_token)
        else:
            self.client = SlackClient(self.bot_token)
        self.client.rtm_connect()
        self.username = self.client.server.username

        response = self.client.api_call(method="im.list").decode("utf-8")
        response = json.loads(response)
        # debug
        directIDList = []
        for imObj in response["ims"]:
            directIDList.append(imObj["id"])
        self.directChannelList = directIDList

        userObjects = self.client.api_call(method="users.list").decode("utf-8") # list all users in slack w/API call
        userObjects = json.loads(userObjects)

        if userObjects["ok"]:
            for user in userObjects["members"]:
                self.conversationList.append(Conversation(user["name"], user["id"]))
  
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
                if "type" in action and "subtype" not in action and \
                        action["type"] == "message":
                    response = self.processMessage(action)
                elif "type" in action and action["type"] == "team_join":
                    newDirectChannel = self.openDirectChannel(action["user"]["id"])
                    self.connect(False) # need this reconnect to update internal list
                    self.post(newDirectChannel, MessageConstants.JOIN_CHANNEL)
                    self.in_menu = False
                elif "type" in action and action["type"] == "group_joined":
                    self.connect(False)
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

    def readMessage(self, lower=True, strip=True):
        """
        Waits for a response and returns the text of the message

        Parameters:
        ***(username)*** (str) -- username to listen to (not implemented yet)
        lower (bool) -- specifies if the string is to be set to lowercase
        strip (bool) -- specifies if the string is to be stripped

        Returns:
        answer (str) -- the input submitted by users
        """
        answer = ""
        while True:
            response = self.client.rtm_read()
            for item in response:
                if "type" in item and item["type"] == "message":
                    answer = item["text"]
                    if lower:
                      answer = answer.lower()
                    if strip:
                      answer = answer.strip()
                    return answer

    def readMenuSelection(self):
        """
        Gives a menu and waits for a response from the user

        Returns:
        answer (int) -- int representation of user response
        """
        while True:
            response = self.client.rtm_read()
            for item in response:
                if "type" in item and item["type"] == "message":
                    answer = item["text"]
                    if answer.isdigit():
                        return int(answer)
                    else: return None

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
        userObjects = self.client.api_call(method="users.list").decode("utf-8") # list all users in slack w/API call
        userObjects = json.loads(userObjects)

        if userObjects["ok"]:
            for user in userObjects["members"]:
                # print(user["name"], "vs.", username)
                if user["name"] == username:  # if found user
                    return user["id"]  # return user ID
            else:
                print("Couldn't find that username in the list of users")
        else:
            print("Bad Response from users.list")
        return None

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
        groupObjects = self.client.api_call(method = "groups.list") # list all groups in slack w/API call
        # may have to comment this out on other OS's, need to figure a better
        # way to do this with flags maybe
        groupObjects = groupObjects.decode("utf-8")
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

    def getConversationObject(self, user):
        for objct in self.conversationList:
            #print(type(objct))
            if objct.getUserID() == user:
                return objct
    

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

        self.connect(True)  # switch to human token
        groupObject = self.client.api_call(
            method="groups.create", token=human_token, name=groupName)  # create group

        # decode group object to resolve ID (needed to add users)
        groupObject = groupObject.decode("utf-8")
        groupObject = json.loads(groupObject)
        # print(json.dumps(groupObject, sort_keys=False, indent=4), end='\n\n')

        if groupObject["ok"]:
            groupId = groupObject["group"]["id"]
        elif groupObject["error"] == 'name_taken':
            self.connect(False) # switch back to bot token
            groupID = self.getGroupID(groupName)
            self.connect(True) # switch back to human token

            groupObject = self.client.api_call(method = "groups.unarchive", token=self.human_token, channel=groupID)
            groupObject = groupObject.decode("utf-8")
            groupObject = json.loads(groupObject)
            print(json.dumps(groupObject, sort_keys=False, indent=4), end='\n\n')
            if not groupObject["ok"]:
                # print("Bad response from groups.unarchive")
                if groupObject["error"] == "not_archived":
                    groupId = groupID
            else:
                groupId = groupID
                if "group" in groupObject:
                    groupId = groupObject["group"]["id"]

        for userName in users:
            userName = userName.rstrip(":")
            # print(userName) #DEBUG
            self.client.api_call(method="groups.invite", token=human_token,
                                 channel=groupId, user=self.getUserID(userName))  # invite to group

        self.client.api_call(method="groups.invite", token=human_token,
                             channel=groupId, user=self.getUserID(botName))  # invite self

        self.connect(False)  # switch back to bot token
        return groupId

    def webhookPost(self, payload, url=None):
        """
        Sends a POST into Slack webhook

        Parameters:
        payload (JSON Object) -- Payload to post through webhook, encoded with JSON library
        """
        if not url:
            url = "https://hooks.slack.com/services/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"
        return requests.post(url, payload)

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
        message = action["text"].lower().strip()  # retrieve actual text of message
        userID = action["user"]
        conversation = self.getConversationObject(userID)

        if (conversation.getStatus() == 0) and (action["channel"] == self.getDirectChannelID(action["user"])):
            if message == "hello":
                conversation.setStatus(1)
                self.post(action["channel"], MessageConstants.MENU_OPTION_2a)
                return

        #if command == "hello" and action["channel"] in self.directChannelList:  # bot listens for "hello"
        if (conversation.getStatus() == 1) and (action["channel"] == self.getDirectChannelID(action["user"])):
            # self.post(action["channel"], MessageConstants.MENU)
            question = ""
            if message.endswith("?"):
                self.post(action["channel"], MessageConstants.MENU_OPTION_2b)
                conversation.setQuestion(message)
                conversation.setStatus(2)
                return
            else:
                self.post(action["channel"], "Didn't get that - try again?")
                return

                
        if (conversation.getStatus() == 2) and (action["channel"] == self.getDirectChannelID(action["user"])):
            # question = self.readMessage(False, True)
            # self.post(action["channel"], MessageConstants.MENU_OPTION_2b)
            tagList = message.split()
            conversation.setTags(tagList)
            submitResponses = "\n*Question:* " + conversation.getQuestion() + "\n*Tags:* "
            for tag in tagList:
                submitResponses += tag + " "
            self.post(action["channel"], MessageConstants.MENU_OPTION_2_CONFIRMa + submitResponses)
            self.post(action["channel"], MessageConstants.MENU_OPTION_2_CONFIRMb)
            conversation.setStatus(3)
            return

        if (conversation.getStatus() == 3) and (action["channel"] == self.getDirectChannelID(action["user"])):
            if message == "yes":
                userName = self.getUserName(action["user"])
                channelName = "question_channel_" + userName
                self.post(self.createNewGroup([userName], channelName), MessageConstants.CREATED_Q_CHANNEL)
                conversation.setStatus(4)
            return

            # elif userSelection == 3:
            #     self.post(action["channel"], MessageConstants.MENU_OPTION_3)
            #     usernameList = self.readMessage().split()
            #     self.post(action["channel"], MessageConstants.PROMPT_CHANNEL)
            #     channelName = self.readMessage()
            #     # post to newly-created channel
            #     self.post(self.createNewGroup(usernameList, channelName),
            #             MessageConstants.CREATED_CHANNEL)
            # elif userSelection == 4:
            #     self.post(action["channel"], MessageConstants.PROMPT_CHANNEL)
            #     channelName = self.readMessage()
            #     userList = []
            #     userList.append(self.getUserName(action["user"]))
            #     createdGroupID = self.createNewGroup(userList, channelName)
            #     if not createdGroupID:
            #         return
            #     self.post(createdGroupID, MessageConstants.CREATED_CHANNEL)

            #     payload = {
            #             "text" : self.getUserName(action["user"]) + " " +\
            #             channelName + " " + "T0K6H0Q8N/B0NCLNQNQ/1W8CAOsVNkZwMtq1gmWyhBfy",
            #             "channel" : "@aaron",
            #             "username" : "temp"
            #             }
            #     payload = json.JSONEncoder().encode(payload)
            #     r = self.webhookPost(payload)

            #     to_send = ""
            #     while True:
            #         response = self.client.rtm_read()
            #         for item in response:
            #             print(json.dumps(item, sort_keys=False, indent=4), end='\n\n')
            #             if "type" in item and item["type"] == "message" and \
            #                     "user" in item and item["user"] != self.getUserID("slackvark_bot") and \
            #                     item["channel"] == self.getGroupID(channelName):
            #                 to_send = item["text"].lower().strip()
            #                 payload = {
            #                         "text" : to_send,
            #                         "channel" : "#" + channelName,
            #                         "username" : self.getUserName(item["user"]),
            #                         "icon_emoji" : ":electric_plug:"
            #                         }
            #                 payload = json.JSONEncoder().encode(payload)
            #                 r = self.webhookPost(payload)

            # else:
            #     self.post(action["channel"], "Invalid Selection.")

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
        self.createNewGroup([commandList[0].lower()], commandList[1].lower())

        hookURL = 'https://hooks.slack.com/services/' + commandList[2]
        to_send = ""
        while True:
            response = self.client.rtm_read()
            for item in response:
                if ("type" in item and item["type"] == "message") and \
                        ("user" in item and item["user"] != self.getUserID("aaron")): #and item["channel"] == self.getGroupID(commandList[1]):
                    to_send = item["text"].lower().strip()
                    payload = {
                            "text" : item["text"],
                            "channel" : "#" + commandList[1],
                            "username" : commandList[0],
                            "icon_emoji" : ":electric_plug:"
                            }
                    payload = json.JSONEncoder().encode(payload)
                    r = requests.post(hookURL, data=payload)        
        return

if __name__ == "__main__":
    inLegalSlack = False
    if len(sys.argv) > 1 and sys.argv[1] == "legal":
        inLegalSlack = True
    config = configparser.ConfigParser()
    config.read("creds.cfg") # read creds file
    if not inLegalSlack:
        bot_token = config["SLACK"]["token"] # retrieve bot token from creds file
        human_token = config["PERSON1"]["token"] # retrieve human token from creds file

    else:
        bot_token = config["AARON"]["token"]
        human_token = config["PERSON2"]["token"] # retrieve human token from creds file

    slackvark_bot = SlackvarkBot(bot_token, human_token, inLegalSlack)
    slackvark_bot.connect(False)

    slackvark_bot.listen() # call listener
