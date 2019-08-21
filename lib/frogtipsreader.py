import clr # pylint: disable=all; noqa .net system
import codecs
import json
import os
import sys
import uuid
import base64

clr.AddReference('System.Speech')
from System.Speech.Synthesis import SpeechSynthesizer, VoiceGender # pylint: disable=all; noqa .net system


class FrogTipsReader(object):
    """ 
    Because I hate coding with only functions and using Global variables.
    Here is the FrogTipsReader, the frog tips to TTS reader.
    This will download FrogTips and and playthem with the .net Voice synthetyser.
    """
    script_name = "Frog TTS Tips"
    config_file = "config.json"
    application_name = 'Frog Tips TTS reader'
    version = '1.0.0'

    def __init__(self):
        self.base_path = os.path.dirname(__file__)
        # self.credential_file = "credential.txt"
        # self.credential_file_path = os.path.join(self.base_path, self.credential_file)
        # self.tips_file = "tips.txt"
        # self.tips_file_path = os.path.join(self.base_path, self.tips_file)
        self.settings = {}
        self.parent = None
        self.spk = SpeechSynthesizer()
        self.uuid = str(uuid.uuid4())
        self.phrase = ''
        self.tips = []

    def setParent(self, parent):
        self.parent = parent

    def setConfigs(self):
        self.loadSettings()

        #Set the voice
        gender_id = getattr(VoiceGender, self.settings['voiceGender'])
        self.spk.SelectVoiceByHints(gender_id)
        self.spk.Volume = self.settings["volume"]

        self.setupCredentials()

    def setupCredentials(self):
        # Make this persistant
        self.register()
    
    def get_auth_data(self):
        return {
            'uuid': self.uuid,
            'comment':  '{} {}'.format(
                self.application_name,
                self.version
            )
        }
 
    def register(self):
        # Prepare request
        url = 'https://' + self.settings['frogTipsDomain'] + '/api/3/auth'
        headers = {'Content-type': 'application/json',
                        'Accept': 'application/json'}
        data = self.get_auth_data()

        # Post request
        result = self.parent.PostRequest(url, headers, data, True)
        # Decode and save API key
        response = json.loads(json.loads(result)['response'])
        self.phrase = response['phrase']
    
    def get_http_auth(self):
        return base64.standard_b64encode('{}:{}'.format(self.uuid, self.phrase))
    
    def download_tips(self):
        url = 'https://' + self.settings['frogTipsDomain'] + '/api/3/tips'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Basic {}'.format(self.get_http_auth()),
        }
        result = self.parent.GetRequest(url,headers)
        self.tips = json.loads(json.loads(result)['response'])

    def loadSettings(self):
        """
            This will parse the config file if present.
            If not present, set the settings to some default values
        """
        try:
            with codecs.open(os.path.join(self.base_path, '..', self.config_file), encoding='utf-8-sig', mode='r') as file:
                self.settings = json.load(file, encoding='utf-8-sig')
        except Exception:
            self.settings = {
                "liveOnly": True,
                "command": "!FrogTTSTips",
                "permission": "Everyone",
                "volume": 50.0,
			    "costs": 100,
                'voiceGender': 'Neutral',
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
            command = self.settings["command"].lower()
            if data.GetParam(0).lower() == command:
                if self.hasPoints(data) and not self.isOnCoolDown(data, command):
                    return self.playFrogTips(data, command)
        return
    
    def canParseData(self, data):
        return (
            data.IsChatMessage() and
            (
                (self.settings["liveOnly"] and self.parent.IsLive()) or 
                (not self.settings["liveOnly"])
            )
        )
    
    def hasPoints(self, data):
        points = self.parent.GetPoints(data.User)
        return (points > self.settings['costs'])
    
    def isOnCoolDown(self, data, command):
        if (
            self.settings["useCooldown"] and
            (self.parent.IsOnCooldown(self.script_name, command) or
            self.parent.IsOnUserCooldown(self.script_name, command, data.User))
        ):
            self.sendOnCoolDownMessage(data, command)
            return True
        else:
            return False
    
    def sendOnCoolDownMessage(self, data, command):
        if self.settings["useCooldownMessages"]:
            commandCoolDownDuration = self.parent.GetCooldownDuration(self.script_name, command)
            userCoolDownDuration = self.parent.GetUserCooldownDuration(self.script_name, command, data.User)

            if commandCoolDownDuration > userCoolDownDuration:
                cdi = commandCoolDownDuration
                message = self.settings["onCooldown"]
            else:
                cdi = userCoolDownDuration
                message = self.settings["onUserCooldown"]
            
            cd = str(cdi / 60) + ":" + str(cdi % 60).zfill(2) 
            self.sendMessage(data, message, command=command, cd=cd)
    
    def playFrogTips(self, data, command):
        if not self.tips:
            self.download_tips()
        tip = self.tips.pop()
        self.spk.Speak(tip['tip'])
        self.setCoolDown(data, command)

    def setCoolDown(self, data, command):
        if self.settings["useCooldown"]:
            self.parent.AddUserCooldown(self.script_name, command, data.User, self.settings["userCooldown"])
            self.parent.AddCooldown(self.script_name, command, self.settings["cooldown"])


    def sendMessage(self, data, message, command=None, cd="0"):
        if command is None:
            command = self.settings["command"]

        outputMessage = message.format(
            user=data.UserName,
            cost=str(None),  # not used
            currency=self.parent.GetCurrencyName(),
            command=command,
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
