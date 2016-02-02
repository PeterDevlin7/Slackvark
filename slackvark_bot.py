import sys
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
                print(action)
                if "type" in action and action["type"] == "message":
                    self.process_message(action["text"])

    def post(self, channel, message):
        channel = channel.lstrip('#')
        chanObj = self.client.server.channels.find(channel)

        if not chanObj:
            raise Exception("#%s not found in list of available channels." %
                    channel)

        chanObj.send_message(message)

    def process_message(self, command):
        if command.lower().strip() == "hello":
            self.post("test", "hello there!")

if __name__ == "__main__":
    bot_token = ""
    slackvark_bot = SlackvarkBot()
    slackvark_bot.connect(bot_token)

    slackvark_bot.listen()
