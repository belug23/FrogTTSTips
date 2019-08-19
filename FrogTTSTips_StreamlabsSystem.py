#---------------------------
#   Import Libraries
#---------------------------
import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), "lib")) #point at lib folder for classes / references

from frogtipsreader import FrogTipsReader # pylint: disable=all; noqa
#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "Frog TTS Tips"
Website = "https://github.com/belug23/"
Description = "Use you currency to make the bot read frog tips in tts"
Creator = "Belug"
Version = FrogTipsReader.version


chad_bot = FrogTipsReader()
# Ugly StreamLab part, just map functions to the class
def ScriptToggled(state):
    return chad_bot.scriptToggled(state)

def Init():
    chad_bot.setParent(Parent)  #  noqa injected by streamlabs chatbot
    return chad_bot.setConfigs()

def Execute(data):
    return chad_bot.execute(data)

def ReloadSettings(jsonData):
    return chad_bot.setConfigs()

def OpenReadMe():
    return chad_bot.openReadMe()

def Tick():
    return chad_bot.tick()
