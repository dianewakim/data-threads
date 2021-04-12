# Example line
# Android formatting
# 09/04/2015, 13:57 - Firstname Lastname: Comme vous voulez!
# iOS formatting
# [15/11/2013 13:44:01] Ziad: ‎image absente

import re
import sys
import json
import emoji
import pprint
from textblob import TextBlob
from textblob_fr import PatternTagger, PatternAnalyzer # for French text
from collections import Counter
from datetime import datetime, timedelta

# open file in argument
with open(sys.argv[1], 'r') as dataFile:
    lines = dataFile.readlines()

# date regex
regex = r"\A\d{2}/\d{2}/\d{4} à \d{1,2}:\d{1,2} - "  # android
regex2 = r"\A\[\d{2}/\d{2}/\d{4} \d{1,2}:\d{1,2}:\d{1,2}\] "  # iOS

# format messages in list of dicts
messagesList = []
groupActivity = {}
senders = {}

# all the info messages we want to ignore
INFOMESSAGES = [
    " changed this group's icon",
    " a changé l'icône de ce groupe",
    "Vous avez changé l'icône de ce groupe",
    "‎Vous avez changé le sujet en ",
    " a changé la description du groupe",
    " changed the subject to ",
    " a modifié le sujet en ",
    " a remplacé le sujet par ",
    "Messages to this group are now secured with end-to-end encryption.",
    "Les messages envoyés dans ce groupe sont désormais protégés avec le chiffrement de bout en bout",
    " left",
    " est parti(e)",
    " a retiré ",
    "Vous avez ajouté ",
    " a ajouté ",
    " a été ajouté(e)",
    " a été retiré(e)",
    "‎Vous êtes désormais admin",
    " a changé de numéro de téléphone. ‎Appuyez pour envoyer un message ou ajouter le nouveau numéro.",
    "Vous avez été ajouté(e)",
    " added",
    "You created group ",
    " est passé à ",
    " a changé de numéro de téléphone. Appuyez pour contacter ou ajouter le nouveau numéro."
]

# Android formatting
# 09/04/2015 à 13:57 - Firstname Lastname: Comme vous voulez!
# iOS formatting
# [15/11/2013 13:44:01] Name: ‎image absente
def getDateAndTime(line):
    date, time = "", ""
    if line[0] == "[":  # iOS formatting
        date = line[1:11]
        time = line[12:17]
    else:  # android formatting
        date = line[0:10]
        time = line[13:18]
    formattedDate = datetime.strptime(date, '%d/%m/%Y')
    return formattedDate.strftime("%Y/%m/%d"), time


def getSenderAndMessage(line):
    senderAndMessage = ""
    if line[0] == "[":  # iOS formatting
        senderAndMessage = line[22:]
    else:
        senderAndMessage = line[21:]
    sender, message = senderAndMessage.split(': ', 1)
    return sender, message


# scanning all the lines of the file
# to construct the messagesList object
# it contains message objects that look like this
# {
#     'date': date,
#     'time': time,
#     'sender': sender,
#     'content': content,
#     'length': len(content)
# }
for line in lines:
    line = line.strip('\u200e')
    # checking if we do not have an empty line
    # if the line starts with a date (any formatting)
    # if the line does not contain one of the info messages
    # or if the line contains one of the info messages
    # but has a : (in this case it is a real message)
    if line != '' and re.match("|".join([regex, regex2]), line) and (not any(x in line for x in INFOMESSAGES) or ': ' in line):
        try:
            # unpacking datetime and message
            date, time = getDateAndTime(line)
            sender, content = getSenderAndMessage(line)
            # creating the message object with all the data
            message = {
                'date': date,
                'time': time,
                'sender': sender,
                'content': content,
                'length': len(content)
            }
            messagesList.append(message)
        except:
            # in case where there was a split problem let's log it
            print("SPLIT PROBLEM", line)
    else:
        # in case the message spans multiple lines
        # we add it to the content of the last message object
        if not re.match("|".join([regex, regex2]), line):
            messagesList[-1]["content"] = messagesList[-1]["content"] + " " + line
        else:
            # here we can track subject changes and people joining/leaving
            if line[0] == '[':  # iOS formatting
                formattedLine = line[1:].split('] ')
                almostAndroidLine = ' - '.join(formattedLine).split(' ', 1)
                line = ' à '.join(almostAndroidLine)

print("TOTAL NUMBER OF MESSAGES:", len(messagesList))

# In our case we want to split the data into 12 parts
# So here are 12 lists ready to be filled with the data
part1, part2, part3, part4, part5, part6, part7, part8, part9, part10, part11, part12 = [], [], [], [], [], [], [], [], [], [], [], []

# scanning the messagesList objects to put it in the correct list
for message in messagesList:

    messageHour = int(message["time"][0:2])

    # this is a very ugly switch
    if 0 <= messageHour < 2:
        part1.append(message)
    elif 2 <= messageHour < 4:
        part2.append(message)
    elif 4 <= messageHour < 6:
        part3.append(message)
    elif 6 <= messageHour < 8:
        part4.append(message)
    elif 8 <= messageHour < 10:
        part5.append(message)
    elif 10 <= messageHour < 12:
        part6.append(message)
    elif 12 <= messageHour < 14:
        part7.append(message)
    elif 14 <= messageHour < 16:
        part8.append(message)
    elif 16 <= messageHour < 18:
        part9.append(message)
    elif 18 <= messageHour < 20:
        part10.append(message)
    elif 20 <= messageHour < 22:
        part11.append(message)
    else:
        part12.append(message)

# We now have a list of all the time-frames
listoflists = [part1, part2, part3, part4, part5, part6, part7, part8, part9, part10, part11, part12]
finalList = []

# getting the data for each of the time-frames
for hourlist in listoflists:
    # get list of unique senders & their number of messages
    sendersCountList = Counter(message['sender'] for message in hourlist)
    sortedSenderList = sorted(sendersCountList)

    family = {}

    for sender in sortedSenderList:
        family[sender] = {
            "nbMessages": sendersCountList[sender],
            "nbChar": 0,
            "nbEmojis": 0,
            "content": "",
            "positivity": 0
        }

    for message in hourlist:
        family[message["sender"]]["nbChar"] += message["length"]
        family[message["sender"]]["content"] += message["content"]

    nbMessagesList = []
    nbCharList = []
    positivityList = []

    for person in family:
        # positivity rate
        blob = TextBlob(family[person]["content"], pos_tagger=PatternTagger(), analyzer=PatternAnalyzer())
        family[person]["positivity"] = int(blob.sentiment[0]*100)

        nbMessagesList.append(family[person]["nbMessages"])
        nbCharList.append(family[person]["nbChar"])
        positivityList.append(family[person]["positivity"])

    finalList.append({
            "names": list(family.keys()),
            "nbMessages": nbMessagesList,
            "nbChar": nbCharList,
            "positivity": positivityList
        })


# pprint.pprint(finalList)

# output as a JSON file
with open(sys.argv[2], 'w') as outfile:
    json.dump(finalList, outfile)
