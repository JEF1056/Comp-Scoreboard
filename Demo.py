import cv2
import numpy as np
import pytesseract
import subprocess
import os
import plotly as py
import plotly.graph_objs as go
import time
import shutil

t1 = time.time()

# the next two functions are depreciated, they DO NOT produce good results.
# using the bounding boxes has been directly shifted to the tessaract functions.

def crop_rect(img, rect):
    # get the parameter of the small rectangle
    center, size, angle = rect[0], rect[1], rect[2]
    center, size = tuple(map(int, center)), tuple(map(int, size))

    # get row and col num in img
    height, width = img.shape[0], img.shape[1]

    # calculate the rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1)
    # rotate the original image
    img_rot = cv2.warpAffine(img, M, (width, height))

    # now rotated rectangle becomes vertical and we crop it
    img_crop = cv2.getRectSubPix(img_rot, size, center)

    return img_crop, img_rot


def set_crop(eval_path):
    all_boxes = open(eval_path, 'r').readlines()
    img_path = all_boxes[0]
    img = cv2.imread("img_path")

    #writer=open(out_path, 'w')

    # loop through all written boxes
    for index, line in enumerate(all_boxes):
        if index > 0:
            line = line.split(",")
            cnt = np.array([
                [int(line[0]), int(line[1])],
                [int(line[2]), int(line[3])],
                [int(line[4]), int(line[5])],
                [int(line[6]), int(line[7])]
            ])
            rect = cv2.minAreaRect(cnt)
            #print("rect: {}".format(rect))

            box = cv2.boxPoints(rect)
            box = np.int0(box)

            # print("bounding box: {}".format(box))
            cv2.drawContours(img, [box], 0, (0, 0, 255), 2)

            # img_crop will the cropped rectangle, img_rot is the rotated image
            img_crop, img_rot = crop_rect(img, rect)
            print(pytesseract.image_to_string(img_crop))


scores_list = []
max_score = 19000
directory = "input/"
amountoftime = 2.5
gtitle = "MEOW GRR *real cat moment*"
#add user input
max_score = input("What's the max. score of the CTF? (assumed 19000 if blank or 0)\n>>> ")
if max_score=="0" or max_score=="":
    max_score = 19000
else:
    max_score=int(max_score)
directory = input("What's the directory of the input folder, realative to the launch location of this script?\n>>> ")
amountoftime = input("What amount of time (in minutes) should the program poll the input folder?\n>>> ")
amountoftime=int(amountoftime)
gtitle = input("Name the resulting graph\n>>> ")
print("\n READY!")

draw_line = "█"
subprocess.call("clear")
print("\033[1;32;40m" + draw_line)
f = '{0:>12}:  {1}\033[1;37;40m'
print("\033[2;37;40m")
print(f.format("Team", "Points"))
print("")

while True: #oof solved the looping problem!!!!!!!!!!
    #wait for a cpecified amount of time
    if int(time.time()-t1) % int(amountoftime*60) == 0:
        #the line below is no longer needed, all of the algorithms have been incorporated into one.
        #subprocess.call("python3 eval.py --test_data_path=input/ --checkpoint_path=pretrained/ --output_dir=output/", shell=True)
        #print("running!")
        subprocess.call("clear")
        print("\033[1;32;40m" + draw_line)
        draw_line = draw_line+"█"
        if len(draw_line) == 168:
            draw_line=="█"
        print("\033[1;37;40mCheck cycles: " + str(len(draw_line)) +"\n")
        for filename in os.listdir(directory):
            filename = filename.lower()
            if filename.endswith(".jpg") or filename.endswith(".png"):
                #run tessaract operations
                cleanme = pytesseract.image_to_string(cv2.imread(os.path.join(directory, filename))).split("\n")
                cleanlist = []
                ##print("\n\n")
                #clean up the results a bit
                for line in cleanme:
                    if line == "" or line == " ":
                        continue
                    else:
                        ##print(line)
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
        #aw yeah look at those neste for statements (i'm great at coding, i swear)
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

        ##print(scores_list)
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

        #ok, now clean out the folder
        for filename in os.listdir(directory):
            shutil.move(os.path.join(directory, filename), os.path.join(directory[:-1]+"_archive/", filename))
                        
