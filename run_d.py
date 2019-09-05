#all code written by Jess Fan - DO NOT DISTRIBUTE WITHOUT PERMISSION
import cv2
import os
import pytesseract
import pkgutil
import sys
import plotly as py
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import shutil
import time
import discord
import asyncio
import subprocess
import binascii
import re

#default variables
script_dir = "script/"
submit_dir = "drive/BACCC CTF Submissions (File responses)/Screenshot (File responses)"
team_dir = "teams/"
site_dir = "site/"

graph_title = "CTF Scores"

def load_all_modules_from_dir(dirname):
    module_list = []
    for importer, package_name, _ in pkgutil.iter_modules([dirname]):
        module = importer.find_module(package_name).load_module(package_name)
        module_list.append(module)
    return module_list

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def convertHex(input1):
    color = binascii.hexlify(str.encode(input1))
    color = str(color)
    rep = re.search("'(.*)'", color)
    endres = "#" + str(rep.group(1)[:6])
    return endres

def cl_text(text, title):
    cleanlist = []
    #clean up the results a bit
    for line in text:
        if hasNumbers(line):
            #if title.lower() in line.lower() or "score" in line.lower():
            cleanlist.append(line)
    return cleanlist

def runcheck():
    files = False
    print(os.listdir(submit_dir))
    for filename in os.listdir(submit_dir):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            files = True
            #gather texts
            img = cv2.imread(os.path.join(submit_dir, filename),cv2.IMREAD_GRAYSCALE)
            height,width = img.shape
            img = cv2.medianBlur(cv2.resize(img,(width*2,height*2)),3)
            ex_text = pytesseract.image_to_string(img).split("\n")
            team = filename.split(" - ")[0]
            ex_text = cl_text(ex_text, team)
            print(ex_text)

            #run modular areas
            modules = load_all_modules_from_dir(script_dir)
            RESULT = ["NULL"]
            for module in modules:
                res = module.check(ex_text[0], )
                if not res == "":
                    RESULT = res
            
            #now, check if this is a score that needs to be updated or added
            try:
                f = open("teams/"+team+".txt", "r")
                try:
                    temp = f.readlines()
                except:
                    temp = f.readlines().split("\n")
                for i,x in enumerate(temp):
                    comp, score = x.split(", ")
                    #update a score
                    if comp == RESULT[0]:
                        temp[i] = comp + ", " + RESULT[1]
                    #add a score
                    else:
                        temp.append(comp + ", " + RESULT[1])
                f.close()
                #write scores
                f = open(os.path.join(team_dir,team+".txt"), "w")
                for i,line in enumerate(temp):
                    if i == 0:
                        f.write(line)
                    else:
                        f.write("\n"+line)
                f.close()
            except Exception as e:
                print(e)
                #new team? new file
                try:
                    f = open(os.path.join(team_dir,team+".txt"), "w")
                    f.write(RESULT[0] + ", " + str(RESULT[1]))
                    f.close()
                except:
                    pass
    return files

def listsort(tup):
    lst = len(tup)  
    for i in range(0, lst):    
        for j in range(0, lst-i-1):  
            if (int(tup[j][1]) < int(tup[j + 1][1])):  
                temp = tup[j]  
                tup[j]= tup[j + 1]  
                tup[j + 1]= temp  
    return tup

def graph():
    tscore = []
    temp_chart = []
    for filename in os.listdir(team_dir):
        team_total=0
        f = open(os.path.join(team_dir, filename), "r")
        try:
            temp = f.readlines()
        except:
            temp = f.readlines().split("\n")
        for z in temp:
            #team, comp, score
            team_total = int(z.split(", ")[1]) + team_total
            temp_chart.append((filename[:-4], z.split(", ")[0], z.split(", ")[1]))
        tscore.append((filename[:-4], team_total))
        f.close()

    data = make_subplots(
        rows=2, cols=1,
        vertical_spacing=0.05,
        specs=[[{"type": "bar"}],
            [{"type": "table"}]]
    )

    for item in temp_chart:
        data.add_trace(go.Bar(x=[str(item[0])], y=[int(item[2])], name=str(item[1]), text=[str(item[1])], textposition = 'auto', 
            marker=dict(color=convertHex(item[0]), line=dict(color=convertHex(item[0]), width=1.5)), 
            opacity=0.8),row=1, col=1)

    rankings = []
    if len(tscore)+1 > 16:
        for i in range(1, 16):
            rankings.append(i)
    else:
        for i in range(1, len(tscore)+1):
            rankings.append(i)

    tscore = listsort(tscore)
    scores = []
    teams = []
    for index,item in enumerate(tscore):
        if index <= 16:
            teams.append(item[0])
            scores.append(item[1])

    data.add_trace(go.Table(header=dict(values=["Rank", "Team", "Score"]), cells=dict(values=[rankings, teams, scores])), row=2, col=1)

    data.update_layout(title=graph_title, barmode='stack', xaxis={'categoryorder':'category ascending'}, showlegend=False, height=1000)

    py.offline.plot({
        "data": data
        }, auto_open=False)

    try:
        with open("temp-plot.html", "a") as f:
            f.write('<style type="text/css">\nhtml {\noverflow:hidden;\n}\n</style>"')
        shutil.copy("temp-plot.html", os.path.join(site_dir,"index.html"))
    except:
        pass

client = discord.Client()

async def loop_bg(loop):
    need_graph = runcheck()
    if need_graph or loop:
        graph()
        print("UPDATED")
        for filename in os.listdir(submit_dir):
            shutil.move(os.path.join(submit_dir, filename), os.path.join(submit_dir[:-1]+"_archive/", filename))
    if loop:
        await asyncio.sleep(30)

client.loop.create_task(loop_bg(True))

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    ModMessage = message.content[3:].lower()
    if message.content.lower().startswith("bs "):
        try:
            role = discord.utils.get(message.guild.roles, name="admins")
        except:
            await message.channel.send('No "admins" role. Please add one.')
        if ModMessage == "update" and role in message.author.roles:
            await loop_bg(True)
            await message.add_reaction("👌")
        elif ModMessage.startswith("change ") and role in message.author.roles:
            ModMessage = ModMessage.replace("change ", "")
            ModMessage = ModMessage.split(" ")
            if not len(ModMessage) == 3:
                await message.channel.send('The "change" argument only accepts 3 arguments formatted as "[Team] [CTF] [Score]"')
            else:
                try:
                    f = open(os.path.join(team_dir,ModMessage[0]+".txt"), "r")
                    temp = ""
                    try:
                        temp = f.readlines()
                        append = True
                        if ModMessage[1] in temp:
                            append = False
                        else:
                            append = True
                        f.close()
                        if append==True:
                            with open(os.path.join(team_dir,ModMessage[0]+".txt"), "w") as b:
                                b.write(temp)
                                b.write("\n"+ModMessage[1] + ", " + str(ModMessage[2]))
                        else:
                            with open(os.path.join(team_dir,ModMessage[0]+".txt"), "w") as b:
                                b.write(ModMessage[1] + ", " + str(ModMessage[2]))
                        await message.add_reaction("👌")
                    except Exception as e:
                        print(e)
                        temp = f.readlines().split("\n")
                        append = True
                        for i,l in enumerate(temp):
                            if ModMessage[1] in l:
                                temp[i] = ModMessage[1] + ", " + str(ModMessage[2])
                                append = False
                        if append:
                            temp.append(ModMessage[1] + ", " + str(ModMessage[2]))
                        f = open(os.path.join(team_dir,ModMessage[0]+".txt"), "w")
                        for i,line in enumerate(temp):
                            if i == 0:
                                f.write(line)
                            else:
                                f.write("\n"+line)
                        f.close()
                        await message.add_reaction("👌")
                except Exception as x:
                    print(x)
                    try:
                        f = open(os.path.join(team_dir,ModMessage[0]+".txt"), "w")
                        f.write(ModMessage[1] + ", " + str(ModMessage[2]))
                        f.close()
                        await message.add_reaction("👌")
                    except:
                        pass
        elif ModMessage.startswith("view "):
            ModMessage = message.content.replace("view ", "").replace("bs ", "")
            try:
                f = open(os.path.join(team_dir, ModMessage+".txt"), "r")
                team_scores = f.readlines()
                await message.channel.send("```"+str(team_scores)+"```")
                f.close()
            except Exception as e:
                print(e)
                await message.channel.send("Cannot find a team by the name of " + ModMessage + " (check capitalization)\nTeams: "+ str(os.listdir(team_dir)).replace(".txt", ""))
        elif ModMessage.startswith("reset ") and role in message.author.roles:
            ModMessage = ModMessage.replace("reset ", "")
            if ModMessage == "all":
                for filename in os.listdir(submit_dir):
                    os.remove(os.path.join(submit_dir,filename))
                graph()
        elif not role in message.author.roles:
            await message.channel.send("Cannot excecute that command - you are not an admin.")
        else:
            await message.channel.send('Could not find command ' + ModMessage)

token = ""
with open("token.txt", "r") as fp:
    token=fp.readline().replace("\n", "")
client.run(token)