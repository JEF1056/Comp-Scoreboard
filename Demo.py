import cv2
import numpy as np
import pytesseract
import subprocess
import os

#the next two functions are depreciated, they DO NOT produce good results.
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
    all_boxes=open(eval_path, 'r').readlines()
    img_path=all_boxes[0]
    img = cv2.imread("input/picoctf scores.JPG")

    #writer=open(out_path, 'w')

    #loop through all written boxes
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

subprocess.call("python3 eval.py --test_data_path=input/ --checkpoint_path=pretrained/ --output_dir=output/", shell=True)
directory = "input/"
for filename in os.listdir(directory):
    filename=filename.lower()
    if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".jpeg"): 
        cleanme = pytesseract.image_to_string(cv2.imread(os.path.join(directory, filename))).split("\n")
        print("\n\n\n\n")
        for line in cleanme:
                if line == "" or line == " ":
                        continue
                else:
                        print(line)