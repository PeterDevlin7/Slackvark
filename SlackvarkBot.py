import sys
import configparser
import json
from slackclient import SlackClient


class SlackvarkBot:
    def __init__(self):
        self.client = None
        self.username = None

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

    def processMessage(self, action):
        command = action["text"].lower().strip()
        if command == "stop":
            self.post(action["channel"], "I will stop listening now.")
            return 1
        elif command == "hello":
            self.post(action["channel"], "hello there!")
        elif command == "slackvark":
            self.post(self.getDirectChannelID(action["user"]), "hello")

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("creds.cfg")
    bot_token = config["SLACK"]["token"]

    slackvark_bot = SlackvarkBot()
    slackvark_bot.connect(bot_token)

    slackvark_bot.listen()
