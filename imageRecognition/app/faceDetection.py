
#By Ria Bhatia
#Helpful sources: OpenCV tutorials
#For use by Microsoft and other parties to demo
#Azure Container Service, Azure Container Instances
#and the experimental ACI-connector

import sys
import numpy as np
import cv2
from PIL import Image
import glob
import os
import time
import requests
import time

from dbAzureBlob import DbAzureBlob

start_time = time.time()                        # Start the timer

def detect(img, cascade):                       # Figure out if the image has a face
    rects = cascade.detectMultiScale(img, scaleFactor=1.3,
    minNeighbors=4, minSize=(30, 30),flags=cv2.CASCADE_SCALE_IMAGE)
    if len(rects) == 0:                         # No face found
        return []
    rects[:,2:] += rects[:,:2]                  # Face found
    return rects

image_list=[]

def draw_rects(img, rects, color):              # Draw a rectangle around the face (Not being used)
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

def getFilename(url):
    sys.stderr.write('get url')
    try:
        r = requests.get(url)
    except:
        sys.stderr.write('url is false')
        return False


    if(r == None):
        sys.stderr.write('no request')
        return False

    if(r.status_code != 200):
        sys.stderr.write('status code not 200')
        return False

    return r.json()

#grab the filename request
def sendRes(url, filename, detected):
    r = requests.get(url + "/processed", params={
            "detected":detected,
            "filename":filename
        })

#make a request
jobserver_url = "http://" + os.getenv('IP_JOB_SERVER', "localhost")
print("JOB SERVER URL: ", jobserver_url)


counter = 0

dbHelper = DbAzureBlob()

while True:
    response = getFilename(jobserver_url)

    if(response == False):
        print("Failed to get response from jobserver")
        time.sleep(1)
        continue

    if(response['processed'] == 1):
        time.sleep(1)

    filename = response['filename']
    realFilename = filename

    if(filename[:2] == "._"):
        filename = filename[2:]

    if(not dbHelper.getImageFromAzureBlob(filename,"/app/Pics/" + filename)):
        continue
    
    print("Got image: ",filename," from blob")
    img = cv2.imread("/app/Pics/" + filename)

    cascade = cv2.CascadeClassifier('/app/haarcascade_frontalface_default.xml')

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.equalizeHist(gray)
    rects = detect(gray, cascade)

    if rects != []:
        sys.stderr.write('\ntrue rect')          # Count the number of images with faces
        sendRes(jobserver_url,realFilename,"true")

    else:
        sys.stderr.write('\nfalse rect')
        sendRes(jobserver_url,realFilename,"false")
