import clr
import codecs
import ctypes
import json
import os
import sys

clr.AddReference('System.Speech')
from System.Speech.Synthesis import SpeechSynthesizer #  noqa .net system


class FrogTipsReader(object):
    """ 
    Because I hate coding with only functions and using Global variables.
    Here is the FrogTipsReader, the frog tips to TTS reader.
    This will download FrogTips and and playthem with the .net Voice synthetyser.
    """
    config_file = "config.json"
    application_name = 'Frog Tips TTS reader'
    version = '1.0.0'

    def __init__(self):
        self.base_path = os.path.dirname(__file__)
        self.credential_file = "credential.txt"
        self.credential_file_path = os.path.join(self.base_path, self.credential_file)
        self.tips_file = "tips.txt"
        self.tips_file_path = os.path.join(self.base_path, self.tips_file)
        self.settings = {}
        self.allowedUsers = []
        self.commands = []
        self.volume = 0.5
        self.parent = None
        self.spk = SpeechSynthesizer()

    def setParent(self, parent):
        self.parent = parent

    def setConfigs(self):
        self.loadSettings()

        # Set the true volume for streamlabs Chatbot
        self.volume = self.settings["volume"] / 100.0

        self.setupCredentials()
        self.loadTips()

    def setupCredentials(self):
        if not Path(self.credential_file_path).is_file():
            self.init_credentials_file()
            self.register()
 
    def register(self):
        """Register with the API server in order to create an API key.
        Registers the uuid and user name with the API server in order to
        create an API key. Unless force_registration is set to True, will
        return immediately if there's already a secret phrase populated in
        self.phrase (indicating a complete API key),  Saves the key to disk
        upon successful completion."""

        # Prepare request
        url = 'https://' + self.settings['frogTipsDomain'] + '/api/3/auth'
        http_headers = {'Content-type': 'application/json',
                        'Accept': 'application/json'}

        # Post request
        response = requests.post(url=url,
                            data=self.serialize(),
                            headers=http_headers)

        # Decode and save API key
        self.set_phrase(response.json()['phrase'])
        self.save_credentials()

    def init_credentials_file(self):
        """Create credentials file and/or wipe the existing one clean."""
        try:
            file = open(self.settings['frogTipsDomain'], 'w')
        except OSError:
            sys.exit("Couldn't create file %s" % self.settings['frogTipsDomain'])
        file.write('::')
        file.close()

    def loadSettings(self):
        """
            This will parse the config file if present.
            If not present, set the settings to some default values
        """
        try:
            with codecs.open(os.path.join(self.base_path, self.config_file), encoding='utf-8-sig', mode='r') as file:
                self.settings = json.load(file, encoding='utf-8-sig')
        except Exception:
            self.settings = {
                "liveOnly": True,
                "command": "!FrogTTSTips",
                "permission": "Everyone",
                "volume": 50.0,
                "useCooldown": True,
                "useCooldownMessages": True,
                "cooldown": 60,
                "onCooldown": "{user}, {command} is still on cooldown for {cd} minutes!",
                "userCooldown": 180,
                "onUserCooldown": "{user}, {command} is still on user cooldown for {cd} minutes!",
                "frogTipsDomain": "frog.tips"
            }

    def scriptToggled(self, state):
        """
            Do an action if the state change. Like sending an announcement message
        """
        return

    def execute(self, data):
        """
            Parse the data sent from the bot to see if we need to do something.
        """
        # If it's from chat and the live setting correspond to the live status
        if self.canParseData(data):
            # If it's the defined help command
            if data.GetParam(0).lower() == self.settings["command"].lower():
                return self.playFrogTips(data)
        return
    
    def canParseData(self, data):
        return (
            data.IsChatMessage() and
            (
                (self.settings["liveOnly"] and self.parent.IsLive()) or 
                (not self.settings["liveOnly"])
            )
        )
    
    def isOnCoolDown(self, data, command):
        if (
            self.settings["useCooldown"] and
            (self.parent.IsOnCooldown(ScriptName, command) or
            self.parent.IsOnUserCooldown(ScriptName, command, data.User))
        ):
            self.sendOnCoolDownMessage(data, command)
            return True
        else:
            return False
    
    def sendOnCoolDownMessage(self, data, command):
        if self.settings["useCooldownMessages"]:
            commandCoolDownDuration = self.parent.GetCooldownDuration(ScriptName, command)
            userCoolDownDuration = self.parent.GetUserCooldownDuration(ScriptName, command, data.User)

            if commandCoolDownDuration > userCoolDownDuration:
                cdi = commandCoolDownDuration
                message = self.settings["onCooldown"]
            else:
                cdi = userCoolDownDuration
                message = self.settings["onUserCooldown"]
            
            cd = str(cdi / 60) + ":" + str(cdi % 60).zfill(2) 
            self.sendMessage(data, message, command=command, cd=cd)
        

    def helpMessage(self, data):
        # If it's still on cool down
        if not self.isOnCoolDown(data, self.settings["command"]) and self.parent.HasPermission(data.User, self.settings["permission"], ""):
            if data.UserName.lower() in self.allowedUsers:
                self.sendMessage(data, self.settings["permitedResponse"])
            else:
                self.sendMessage(data, self.settings["notPermitedResponse"])
            
            self.setCoolDown(data, self.settings["command"])
    
    def playFrogTips(self, data):
        self.spk.Speak('Hello world!')
        self.setCoolDown(data)

    def setCoolDown(self, data, command):
        if self.settings["useCooldown"]:
            self.parent.AddUserCooldown(ScriptName, command, data.User, self.settings["userCooldown"])
            self.parent.AddCooldown(ScriptName, command, self.settings["cooldown"])


    def sendMessage(self, data, message, command=None, cd="0"):
        if command is None:
            command = self.settings["command"]

        outputMessage = message.format(
            user=data.UserName,
            cost=str(None),  # not used
            currency=self.parent.GetCurrencyName(),
            command=command,
            avail_sound_commands=self.avail_sound_commands,
            cd=cd
        )
        self.parent.SendStreamMessage(outputMessage)

    def tick(self):
        """
        not used, here for maybe future projects.
        """
        return
    
    def openReadMe(self):
        location = os.path.join(os.path.dirname(__file__), "README.txt")
        if sys.platform == "win32":
            os.startfile(location)  # noqa windows only
        else:
            import subprocess
            opener ="open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, location])
        return
