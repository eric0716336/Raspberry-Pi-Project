import multiprocessing
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import json
import http.client,urllib
import socket
import smbus
import requests
import lineTool
from datetime import datetime
import sys
import signal
from datetime import datetime

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
reader = SimpleMFRC522()
GPIO.setup(38, GPIO.IN, pull_up_down=GPIO.PUD_UP)#Button to GPIO20
PIR=8
GPIO.setup(PIR,GPIO.IN)

deviceKey = "insert device key"
deviceId = "insert device id"

token = "insert token"
run =1
def get_to_mcs(id):
    host = "http://api.mediatek.com"
    endpoint = "/mcs/v2/devices/" + deviceId + "/datachannels/"+str(id)+"/datapoints"
    url = host + endpoint
    headers = {"Content-type": "application/json", "deviceKey": deviceKey}
    r = requests.get(url,headers=headers)
    if(r.json()["dataChannels"][0]["dataPoints"]==[]):
        return ""
    value = (r.json()["dataChannels"][0]["dataPoints"][0]["values"]["value"])
    return value

def post_to_mcs(idd, item):
    payload = {"datapoints":[{"dataChnId": str(idd),"values":{"value":item}}]}
    print(json.dumps(payload))
    headers = {"Content-type": "application/json", "deviceKey": deviceKey}
    not_connected = 1
    while (not_connected):
        try:
            conn = http.client.HTTPConnection("api.mediatek.com")
            conn.connect()
            not_connected = 0
        except (http.client.HTTPException, socket.error) as ex:
            print ("Error: %s" % ex)
            time.sleep(10) # sleep 10 seconds
    conn.request("POST", "/mcs/v2/devices/" + deviceId + "/datapoints", json.dumps(payload), headers)
    response = conn.getresponse()
    print(response.status, response.reason, json.dumps(payload), time.strftime("%c"))
    data = response.read()
    conn.close()

def linenotify(a,b):
    lineTool.lineNotify(a,b)
    print("NOTIF SEND")

def target1():
    while True:
        try:
            id,text=reader.read()
            print("ID: ",id);
            print("TEXT: ",text);
            listt= get_to_mcs(1)
            listt= listt.split(',')
            if listt[0]!="":
                for i in range(0,len(listt),2):
                    if(listt[i]==str(id)):
                        s= get_to_mcs(6)
                        now= datetime.now()
                        date_time= now.strftime("%m/%d/%Y, %H:%M:%S")
                        s=s+"Exit,"+listt[i+1]+","+date_time+","
                        time.sleep(0.1)
                        post_to_mcs(6,s)
                        msg=listt[i+1]+" Exit"
                        linenotify(token,msg)
            print("people in the room : ",get_to_mcs(4))
            people_in = int(get_to_mcs(4))
            people_in = people_in-1
            if(people_in<=0): people_in=0
            post_to_mcs(4,str(people_in))
            print("people in the room -1 : ",get_to_mcs(4))
            time.sleep(5)#original 0.2
            post_to_mcs(5,"1")
            time.sleep(5)
            post_to_mcs(5,"0")
            time.sleep(0.1)
        except KeyboardInterrupt:
            pass

def target2():
    count =0
    while True:
        button_state = GPIO.input(38)
        if button_state == False:
            count+=1
            print('Button Pressed...',count)
            print("people in the room : ",get_to_mcs(4))
            people_in = int(get_to_mcs(4))
            people_in = people_in-1
            if(people_in<=0): people_in=0
            post_to_mcs(4,str(people_in))
            print("people in the room -1 : ",get_to_mcs(4))
            msg="logout detected by button"
            s= get_to_mcs(6)
            now= datetime.now()
            date_time= now.strftime("%m/%d/%Y, %H:%M:%S")
            s=s+"Exit,Button,"+date_time+","
            time.sleep(0.1)
            post_to_mcs(6,s)
            linenotify(token,msg)
            time.sleep(5)#original 0.1
            post_to_mcs(5,"1") 
            time.sleep(5)
            post_to_mcs(5,"0")
            time.sleep(0.1)
        else:
            pass

post_to_mcs(4,"0")
p1= multiprocessing.Process(target=target1)
p2= multiprocessing.Process(target=target2)
p1.start()
p2.start()

def join_and_exit():
    print('Join Process and exit system')
    p1.join()
    p2.join()
    quit()
post_to_mcs(9,"")
while True:
    try:
        i=GPIO.input(PIR)
        people_in = int(get_to_mcs(4))
        print("people inside now ",people_in)
        if(i==0):
            print('safe')
            time.sleep(2)
        elif(i):
            people_in = int(get_to_mcs(4))
            if(people_in==0):
                print('intruder enter')
                msg='intruder enter an empty house'
                linenotify(token,msg)
                intruder_history=""
                intruder_history=get_to_mcs(9)
                now=datetime.now()
                date_time= now.strftime("%m/%d/%Y, %H:%M:%S")
                intruder_history=intruder_history+"intruder at "+date_time+','
                print(intruder_history)
                post_to_mcs(9,intruder_history)
                time.sleep(2)
    except KeyboardInterrupt:
        print("End Program")
        join_and_exit()





