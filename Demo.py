# -*- coding: utf-8 -*-

import matplotlib
matplotlib.use('GTK3Agg')

from PIL import Image
import numpy as np
import pytesseract
import subprocess
import os
import plotly as py
import plotly.graph_objs as go
import time
import shutil
import threading
#import tkinter as tk

t1 = time.time()

# the next two functions are depreciated, they DO NOT produce good results.
# using the bounding boxes has been directly shifted to the tessaract functions.

#these are important variables, can be changed using commands
global max_score, directory, amountoftime, gtitle

scores_list = []
max_score = 19000
directory = "input/"
amountoftime = 2.5
gtitle = "MEOW GRR *real cat moment*"
out_path = ""

def runcommand():
    global max_score, directory, amountoftime, gtitle
    command_inp = e1.get()
    print("")
    command_inp = command_inp.lower()
    if command_inp == "-r":
        #run check operations agaon
        task()
    elif command_inp.startswith("-s"):
        #set commands
        args = command_inp.split(" ")
        if args[1] == "s" or args[1] == "score":
            max_score = int(args[2])
            print("Set the max. score to " + str(max_score))
        elif args[1] == "t" or args[1] == "time":
            amountoftime = int(args[2])
            print("Set the polling time to " + str(amountoftime))
        elif args[1] == "d" or args[1] == "directory":
            directory = args[2]
            print("Set input directory to " + directory)
        elif args[1] == "n" or args[1] == "name":
            gtitle = args[2]
            print("Set graph title to " + gtitle)

#add user input for the introduction
max_score = input("What's the max. score of the CTF? (assumed 19000 if blank or 0)\n>>> ")
if max_score=="0" or max_score=="":
    max_score = 19000
else:
    max_score=int(max_score)
directory = input("What's the directory of the input folder, realative to the launch location of this script?\n>>> ")
amountoftime = input("What amount of time (in seconds) should the program poll the input folder?\n>>> ")
amountoftime=int(amountoftime)
gtitle = input("Name the resulting graph\n>>> ")
out_path = input("Output path\n>>> ")
print("\n READY!")

#window = tk.Tk()
meow=True
global draw_line
draw_line = "█"
subprocess.call("clear")
print("\033[1;32;40m" + draw_line)
f = '{0:>12}:  {1}\033[1;37;40m'
print("\033[2;37;40m")
print(f.format("Team", "Points"))
print("\033[1;30;40m")
print(f.format("Null", "Null"))

#def task(): #oof solved the looping problem!!!!!!!!!!
def update_graph(firstrun):
    global draw_line
    if meow == True:
        subprocess.call("clear")
        print("\033[1;32;40m" + draw_line)
        draw_line = draw_line+"█"
        if len(draw_line) == 168:
            draw_line=="█"
        print("\033[1;37;40mCheck cycles: " + str(len(draw_line)) +"\n")
        temp_dir=directory
        if firstrun == True:
            temp_dir=directory[:-1]+"_archive/"
        else:
            temp_dir=directory
        for filename in os.listdir(temp_dir):
            if filename.endswith(".jpg") or filename.endswith(".png"):
                #run tessaract operations
                cleanme = pytesseract.image_to_string(Image.open(os.path.join(temp_dir, filename))).split("\n")
                filename = filename.lower()
                cleanlist = []
                #clean up the results a bit
                for line in cleanme:
                    if line == "" or line == " ":
                        continue
                    else:
                        cleanlist.append(line)
                #find and eval the score
                for line in cleanlist:
                    #there's some that work directly, but others (they're evil) who didn't do it on the score page
                    #luckily, there's a redundancy fix here
                    if "Score:" in line or str(filename[:-4].split(" - ")[0]).lower() in line.lower():
                        findint = line.split(" ")
                        foundint = -100
                        for possibleint in findint:
                            try:
                                foundint = int(possibleint)
                            except:
                                continue
                        #add all the culminated scores as tuples to a list
                            #one character, the thunderbolt, is commonly misinterpreted as a "4" or a "$"
                            #the easiest fix is to compare it to the max. score, when it's passed through that type of operation.
                        if foundint > 0 and foundint < max_score:
                            score_tuple = str(filename[:-4].split(" - ")[0]) , str(foundint)
                            scores_list.append(score_tuple)
                        elif foundint > 0 and foundint > max_score:
                            score_tuple = str(filename[:-4].split(" - ")[0]) , str(foundint)[1:]
                            scores_list.append(score_tuple)
                        elif foundint < 0:
                            print("\n\033[1;31;40m Please contact team " + str(filename[:-4].split(" - ")[0]) + ", their screenshot could not be read.")
                            print("\033[1;37;40m")

        #so while our list is now pretty clean, there are still problems (wow, totally unexpected)
        #clean up repeats by selecting the higher score
        seen_names = []
        final_list = []
        #aw yeah look at those nested for statements (i'm great at coding, i swear)
        for index, arg in enumerate(scores_list):
            icu = False
            for sni, vis in enumerate(seen_names):
                icu = False
                if arg[0] == vis[0]:
                    icu=True
                    if int(scores_list[vis[1]][1]) > int(arg[1]):
                        pass
                    elif int(scores_list[vis[1]][1]) == int(arg[1]):
                        pass
                    else:
                        del final_list[sni]
                        final_list.append(arg)
            if icu==False:
                temp= arg[0], index
                seen_names.append(temp)
                final_list.append(arg)

        f = '{0:>12}:  {1}\033[1;37;40m'
        print("\033[2;37;40m")
        print(f.format("Team", "Points"))
        print("")
        for team in final_list:
            print("\033[1;30;40m")
            print(f.format(team[0], team[1]))
        x=[]
        y=[]
        #graph with plotly
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
            "layout": go.Layout(title=gtitle)
            }, auto_open=False)

        try:
            shutil.copy("temp-plot.html", os.path.join(out_path, "temp-plot.html"))
        except:
            pass

        #ok, now clean out the folder
        for filename in os.listdir(directory):
            shutil.move(os.path.join(directory, filename), os.path.join(directory[:-1]+"_archive/", filename))

        #window.after(int(amountoftime*1000), task)

update_graph(True)

while True:
    update_graph(False)
    time.sleep(amountoftime)