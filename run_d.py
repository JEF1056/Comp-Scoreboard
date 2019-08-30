import cv2
import os
import pytesseract
import pkgutil
import sys
import plotly as py
import plotly.graph_objs as go
import shutil
import time
import discord
import asyncio

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

def cl_text(text, title):
    cleanlist = []
    #clean up the results a bit
    for line in text:
        if hasNumbers(line):
            if title.lower() in line.lower() or "score" in line.lower():
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
                res = module.check(ex_text[0])
                if not res == ["NULL"]:
                    RESULT = res
            
            #now, check if this is a score that needs to be updated or added
            try:
                f = open("teams/"+team+".txt", "r")
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
            except:
                #new team? new file
                try:
                    f = open(os.path.join(team_dir,team+".txt"), "w")
                    f.write(RESULT[0] + ", " + str(RESULT[1]))
                    f.close()
                except:
                    pass
    return files
        
def graph():
    final_list = []
    for filename in os.listdir(team_dir):
        f = open(os.path.join(team_dir, filename), "r")
        try:
            temp = f.readlines()
        except:
            temp = f.readlines().split("\n")
        end_score = 0
        for x in temp:
            end_score = end_score+int(x.split(", ")[1])
        f.close()
        final_list.append([filename[:-4], end_score])
    x=[]
    y=[]
    for team in final_list:
        x.append(team[0])
        y.append(team[1])

    data = [go.Bar(
                x=x,
                y=y,
                text=y,
                textposition = 'auto',
                marker=dict(
                    color='rgb(158,202,225)',
                    line=dict(
                        color='rgb(8,48,107)',
                        width=1.5),
                ),
                opacity=0.6
            )]

    py.offline.plot({
        "data": data,
        "layout": go.Layout(title=graph_title)
        }, auto_open=False)

    try:
        shutil.copy("temp-plot.html", os.path.join(site_dir,"index.html"))
    except:
        pass

client = discord.Client()

async def loop_bg():
    need_graph = runcheck()
    if need_graph:
        graph()
        print("UPDATED")
        for filename in os.listdir(submit_dir):
            shutil.move(os.path.join(submit_dir, filename), os.path.join(submit_dir[:-1]+"_archive/", filename))
    await asyncio.sleep(30)

client.loop.create_task(loop_bg())

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

token = ""
with open("token.txt", "r") as fp:
    token=fp.readline().replace("\n", "")
client.run(token)