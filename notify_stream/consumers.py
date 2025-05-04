import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class NotifyConsumers(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("loco", self.channel_name)
        await self.channel_layer.group_add(self.scope["user"].username, self.channel_name)
        await self.accept()

    


    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        print(text_data)
        text_as_json = json.loads(text_data)
        message = text_as_json["message"]
        user = text_as_json["user"]
        print(message)
        print(user)

        # IDEA: Implement something such as recieve a code that will identify what kind of actions is recieved and resolve
        # TODO: after implemented what decides we will send to group, it wil be sort or a encrypt and decrypt and then we send to group
        await self.channel_layer.group_send(
            "loco", {"type" : "code.decipher", "message" : message}
        )

        await self.channel_layer.group_send(
            user, {"type" : "code.decipher", "message" : message}
        )


    async def code_decipher(self, event):
        message = event["message"]
        # IDEA: here wil will implement the above comments inside recieve function
        await self.send(text_data = json.dumps({"message": message, "lit" : "bro"}))


    async def receive_json(self, message):
        command = message.get("command")
        if command == "Say hello !":
            print(message["data_string"])
            await self.send_json({
                "command_response": "The command to \
                say hello was received ",
                "data_string_bacK": message.get
              ("data_string", None)
            })
