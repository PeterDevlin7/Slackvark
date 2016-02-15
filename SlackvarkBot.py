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

    def connect(self, token):
        self.client = SlackClient(token)
        self.client.rtm_connect()
        self.username = self.client.server.username

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

    def post(self, channel, message):
        channel = channel.lstrip('#')
        chanObj = self.client.server.channels.find(channel)
        if not chanObj:
            raise Exception("#%s not found in list of available channels." %
                            channel)
        chanObj.send_message(message)

    def getDirectChannelID(self, username):
        """Returns direct message channel id given username"""
        imObjects = self.client.api_call(method="im.list").decode("utf-8")
        imObjects = json.loads(imObjects)
        # debug pretty print
        # print(json.dumps(imObjects, sort_keys=False, indent=4))
        if imObjects["ok"]:
            for im in imObjects["ims"]:
                if im["user"] == username:
                    return im["id"]
    
    def getUserID(self, username):
        userObjects = self.client.api_call(method = "users.list").decode("utf-8")
        userObjects  = json.loads(userObjects)

        if userObjects["ok"]:
            for user in userObjects["members"]:
                if user["name"] == username:
                    return user["id"]
        return None

    def createNewChannel(self, users, groupName):
        self.connect(self.human_token)
        groupObject = self.client.api_call(method = "groups.create", token=human_token, name=groupName)

        groupObject = groupObject.decode("utf-8")
        groupObject = json.loads(groupObject)

        if(groupObject["ok"]): groupId = groupObject["group"]["id"]
        
        for userName in users:
            if(userName[-1] == ":"):
                userName = userName[:-1]
                print(userName)
            self.client.api_call(method = "groups.invite", token=human_token, channel=groupId, user=self.getUserID(userName))

        self.client.api_call(method = "groups.invite", token=human_token, channel=groupId, user=self.getUserID("slackvark_bot"))
        
        self.connect(self.bot_token) 
        return groupId

    def processMessage(self, action):
        command = action["text"].lower().strip()
        usernameList = []
        channelName = ""
        if command == "hello":
            self.post(action["channel"], "Hi! I am a test build of Slackvark. Please choose from these options:\n \
                      1. Stop Listening\n \
                      2. Send a direct message\n \
                      3. Create a new channel")
        elif command == "1":
            return 1
        elif command == "2":
            self.post(self.getDirectChannelID(action["user"]), "hello")
        elif command == "3":
            self.post(action["channel"], "Awesome. Who would you like to invite?")
            condition = True
            while condition:
                response1 = self.client.rtm_read()
                for item in response1:
                    if "type" in item and item["type"] == "message":
                        usernameList = item["text"].strip().split(" ")
                        condition = False
                    
            self.post(action["channel"], "What would you like to call this channel?")
            condition = True
            while condition:
                response2 = self.client.rtm_read()
                for item in response2:
                    if "type" in item and item["type"] == "message":
                        channelName = item["text"].lower().strip()
                        condition = False
            self.post(self.createNewChannel(usernameList, channelName), "Hello again! I've created this channel for you.\n")
                                                                                       

        else:
            self.post(action["channel"], "Invalid selection.")

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("creds.cfg")
    bot_token = config["SLACK"]["token"]
    human_token = config["PERSON"]["token"]
    
    slackvark_bot = SlackvarkBot(bot_token, human_token)
    slackvark_bot.connect(bot_token)

    slackvark_bot.listen()
