import RPi.GPIO as GPIO
import time
from gpiozero import Servo
import requests
from mfrc522 import SimpleMFRC522
import smbus
import http.client, urllib
import json
import socket
import lineTool
from datetime import datetime
#from picamera import PiCamera
import base64
import urllib.parse
import sys
import argparse
import pickle
import cv2
import face_recognition
import imutils
from imutils.video import VideoStream

msg="login detected"
token = "insert token"
deviceKey = "device key"
deviceId = "device id"

# Set the LED PIN
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
ledPin = 12
buzzer=16
GPIO.setup(ledPin,GPIO.OUT)
GPIO.setup(buzzer,GPIO.OUT)

reader= SimpleMFRC522()

print("[INFO] starting video stream...")
vs = VideoStream(0).start()

# Set MediaTek Cloud Sandbox (MCS) Connection
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
    print("Notification send")

def line_and_photo():
    line_url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': 'Bearer ' + token}
    payload = {'message': 'intruder'}
    files = {'imageFile': open('wrong_card.jpg', 'rb')} 
    r = requests.post(line_url, headers=headers, params=payload, files=files)
    if files:
        files['imageFile'].close()
    return r.status_code

def capture_photo():
    frame = vs.read()
    cv2.imwrite("wrong_card.jpg",frame)
    with open("wrong_card.jpg","rb") as img_file:
        EncodeBytes = base64.b64encode(img_file.read())
    
    EncodeStr=str(EncodeBytes,"utf-8")
    post_to_mcs(8,EncodeStr)
    #print("ENCODE:" ,EncodeStr)
    time.sleep(10)
    line_and_photo()
    
def lcd_display(mode, id):
    
    I2C_ADDR  = 0x27 # I2C device address, if any error, change this address to 0x3f
    LCD_WIDTH = 20   # Maximum characters per line

    # Define some device constants
    LCD_CHR = 1 # Mode - Sending data
    LCD_CMD = 0 # Mode - Sending command

    LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
    LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
    LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
    LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

    LCD_BACKLIGHT  = 0x08  # On
    #LCD_BACKLIGHT = 0x00  # Off

    ENABLE = 0b00000100 # Enable bit

    # Timing constants
    E_PULSE = 0.0005
    E_DELAY = 0.0005

    #Open I2C interface
    #bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
    bus = smbus.SMBus(1) # Rev 2 Pi uses 1

    def lcd_init():
        # Initialise display
        lcd_byte(0x33,LCD_CMD) # 110011 Initialise
        lcd_byte(0x32,LCD_CMD) # 110010 Initialise
        lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
        lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
        lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
        lcd_byte(0x01,LCD_CMD) # 000001 Clear display
        time.sleep(E_DELAY)

    def lcd_byte(bits, mode):
        # Send byte to data pins
        # bits = the data
        # mode = 1 for data
        #        0 for command
        bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
        bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT
        # High bits
        bus.write_byte(I2C_ADDR, bits_high)
        lcd_toggle_enable(bits_high)
        # Low bits
        bus.write_byte(I2C_ADDR, bits_low)
        lcd_toggle_enable(bits_low)

    def lcd_toggle_enable(bits):
        # Toggle enable
        time.sleep(E_DELAY)
        bus.write_byte(I2C_ADDR, (bits | ENABLE))
        time.sleep(E_PULSE)
        bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
        time.sleep(E_DELAY)

    def lcd_string(message,line):
        # Send string to display
        message = message.ljust(LCD_WIDTH," ")
        lcd_byte(line, LCD_CMD)
        for i in range(LCD_WIDTH):
            lcd_byte(ord(message[i]),LCD_CHR)

    def main(id):
        # Main program block
        # Initialise display
        lcd_init()
        time.sleep(0.5)
        # Send some test
        lcd_string("      Welcome      ",LCD_LINE_1)
        lcd_string("       "+str(id)+"    ",LCD_LINE_2)
    
    def wrong_pass():
        # Main program block
        # Initialise display
        lcd_init()
        time.sleep(0.5)
        # Send some test
        lcd_string("   Wrong ID CARD   ",LCD_LINE_2)
    
    def wrong_key():
        # Main program block
        # Initialise display
        lcd_init()
        time.sleep(0.5)
        # Send some test
        lcd_string("   Wrong PIN   ",LCD_LINE_2)
        lcd_string("Please Repeat Again", LCD_LINE_3)
        capture_photo()
    
    def usecard():
        # Main program block
        # Initialise display
        lcd_init()
        time.sleep(0.5)
        # Send some test
        lcd_string("   Welcome  ",LCD_LINE_1)
        lcd_string("   Tap your ID Card  ",LCD_LINE_2)
    
    def welcome(id):
        lcd_init()
        time.sleep(0.5)
        # Send some test
        lcd_string("    Welcome...     ",LCD_LINE_1)
        lcd_string("  Hold # on keypad ",LCD_LINE_2)
        lcd_string("  to use  ",LCD_LINE_3)
        lcd_string("  Face Recognition ",LCD_LINE_4)
    
    def welcome_key():
        lcd_init()
        time.sleep(0.5)
        # Send some test
        lcd_string("  Welcome... ",LCD_LINE_2)
        
    def welcome_face(name):
        lcd_init()
        time.sleep(0.5)
        # Send some test
        lcd_string("  Face Recognized ",LCD_LINE_2)
        lcd_string("  "+name,LCD_LINE_3)
    def face_recog_mode():
        lcd_init()
        time.sleep(0.5)
        lcd_string("    Welcome...     ",LCD_LINE_1)
        lcd_string(" Please Face Camera",LCD_LINE_2)
        lcd_string("  Hold # for RFID ",LCD_LINE_3)
    
    if(mode=="display"):
        main(id)
    elif(mode=="clear"):
        time.sleep(0.0005)
        lcd_byte(0x01, 0)
        time.sleep(0.0005)
        lcd_byte(0x01, 0)
        time.sleep(0.0005)
    elif(mode=="wrong"):
        wrong_pass()
    elif(mode=="welcome"):
        welcome(id)
    elif(mode=="usecard"):
        usecard()
    elif(mode=="wrongkey"):
        wrong_key()
    elif(mode=="welcomekey"):
        welcome_key()
    elif(mode=="face"):
        welcome_face(id)
    elif(mode=="face_mode"):
        face_recog_mode()

def motor_on():
    servoPIN = 11
    GPIO.setup(servoPIN, GPIO.OUT)
    p = GPIO.PWM(servoPIN, 50) # GPIO 17 for PWM with 50Hz
    p.start(2.5) # Initialization
    try:
        p.ChangeDutyCycle(10)
        time.sleep(3)
        p.ChangeDutyCycle(5)
        time.sleep(0.5)
        p.ChangeDutyCycle(2.5)
        time.sleep(0.5)
    except KeyboardInterrupt:
        p.stop()

def pass_key():
    L1 = 29
    L2 = 31
    L3 = 33
    L4 = 35

    C1 = 32
    C2 = 36
    C3 = 38
    C4 = 40

    GPIO.setup(L1, GPIO.OUT)
    GPIO.setup(L2, GPIO.OUT)
    GPIO.setup(L3, GPIO.OUT)
    GPIO.setup(L4, GPIO.OUT)
    GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def readLine(line, characters):
        global liness
        GPIO.output(line, GPIO.HIGH)
        if(GPIO.input(C1) == 1):
            liness= liness+ characters[0]        
        if(GPIO.input(C2) == 1):
            liness= liness+ characters[1]      
        if(GPIO.input(C3) == 1):
            liness= liness+ characters[2]          
        if(GPIO.input(C4) == 1):
            liness= liness+ characters[3]
        GPIO.output(line, GPIO.LOW)
        
    global liness
    liness=""
    
    while True:
        #lcd_display("welcome","")
        if(get_to_mcs(7)==1):
            GPIO.output(ledPin,GPIO.HIGH)
            motor_on()
            time.sleep(1)
            GPIO.output(ledPin,GPIO.LOW)
        
        readLine(L1, ["1","2","3","A"]) 
        readLine(L2, ["4","5","6","B"])
        readLine(L3, ["7","8","9","C"])
        readLine(L4, ["*","0","#","D"])
        time.sleep(0.175)
        print(liness)
        if(liness[0:5]=="####"):
            print("switch to face recognition mode")
            lcd_display("face_mode","")
            print("[INFO] loading encodings + face detector...")
            data = pickle.loads(open("res.pickle", "rb").read())
            detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
            #print("[INFO] starting video stream...")
            #vs = VideoStream(0).start()
            print("AFTER VS")
            time.sleep(2.0)
            liness=""
            user_name=""
            while True:
                readLine(L1, ["1","2","3","A"]) 
                readLine(L2, ["4","5","6","B"])
                readLine(L3, ["7","8","9","C"])
                readLine(L4, ["*","0","#","D"])
                time.sleep(0.175)
                print("HERE:" ,liness)
                
                frame = vs.read()
                frame = imutils.resize(frame, width=500)

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
                    minNeighbors=5, minSize=(30, 30))
                boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]
                
                encodings = face_recognition.face_encodings(rgb, boxes)
                names = []
                det=0
                
                for encoding in encodings:
                    matches = face_recognition.compare_faces(data["encodings"],
                        encoding)
                    name = "Unknown"
                
                    if True in matches:
                        matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                        counts = {}
                        for i in matchedIdxs:
                            name = data["names"][i]
                            counts[name] = counts.get(name, 0) + 1
                        name = max(counts, key=counts.get)
                        user_name=name
                        det=1
                        
                    names.append(name)

                for ((top, right, bottom, left), name) in zip(boxes, names):
                    # draw the predicted face name on the image
                    cv2.rectangle(frame, (left, top), (right, bottom),
                        (0, 255, 0), 2)
                    y = top - 15 if top - 15 > 15 else top + 15
                    cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.75, (0, 255, 0), 2)
                cv2.imshow("Frame", frame)
                key = cv2.waitKey(1) & 0xFF
                
                if(det or liness[0:5]=="####"):
                    cv2.destroyAllWindows()
                    #vs.stop()
                    if(liness[0:5]=="####"):
                        print("switch to rfid mode")
                    elif(det):
                        s=""
                        s=get_to_mcs(6)
                        now=datetime.now()
                        date_time= now.strftime("%m/%d/%Y, %H:%M:%S")
                        s=s+user_name+",Face Recognition,"+date_time+","
                        #time.sleep(0.1)
                        post_to_mcs(6,s)
                        post_to_mcs(7,0)
                        lcd_display("face",user_name)
                        motor_on()
                        print("Face Recognized")
                        msg=name+" Enter Using Face Recognition"
                        linenotify(token,msg)
                        people_in = int(get_to_mcs(4))
                        people_in+=1
                        post_to_mcs(4,people_in)
                        #time.sleep(2)
                        lcd_display("welcome","")
                    break
           
            #print("switch to RFID")
            if(liness[0:5]=="####"):
                break
        
        if len(liness)== 4 and liness[0:5]!="####" :
            if liness==get_to_mcs(2):
                lcd_display("welcomekey","")
                motor_on()
                print("password correct recognized")
                msg="login detected"
                linenotify(token,msg)
                people_in = int(get_to_mcs(4))
                people_in+=1
                post_to_mcs(4,people_in)
                s=""
                s=get_to_mcs(6)
                now=datetime.now()
                date_time= now.strftime("%m/%d/%Y, %H:%M:%S")
                s=s+"Entrance,Button,"+date_time+","
                time.sleep(0.1)
                post_to_mcs(6,s)
                post_to_mcs(7,0)
                liness=""
                time.sleep(2)
                lcd_display("welcome","")
            else:
                lcd_display("wrongkey","")
                print("wrong password")
                liness=""
        
while(True):    
    lcd_display("welcome","")
    time.sleep(0.1)
    if(get_to_mcs(7)==1):
        GPIO.output(ledPin,GPIO.HIGH)
        time.sleep(1)
        motor_on()
        
        GPIO.output(ledPin,GPIO.LOW)
    pass_key()
    lcd_display("usecard","")
    try:
        id, text= reader.read()
    except:
        print("no")
    print(id)
    if(id>0):
        card_list= get_to_mcs(1).split(',')
        card_name=[]
        card_id=[]
        print(card_list)
        print(len(card_list))
        res= get_to_mcs(1)
        res1= res
        if res=="":
            res=str(id)+",anon"
        else:
            res= res+","+str(id)+",anon"
        print(res)
        post_to_mcs(1,res)
        print(res1)
        post_to_mcs(1,res1)
        if card_list[0]!='':
            for i in range(0, len(card_list),2):
                card_id.append(card_list[i])
                card_name.append(card_list[i+1])
        if(get_to_mcs(7)==1):
            for i in range(0, len(card_id)):
                if str(id) == card_id[i]:
                    print("access granted")
                    msg=card_name[i]+" Enter"
                    linenotify(token,msg)
                    people_in = int(get_to_mcs(4))
                    people_in+=1
                    post_to_mcs(4,people_in)
                    GPIO.output(ledPin,GPIO.HIGH)
                    GPIO.output(buzzer,GPIO.HIGH)
                    print ("Beep")
                    time.sleep(0.2) # Delay in seconds
                    GPIO.output(buzzer,GPIO.LOW)
                    print ("No Beep")
                    time.sleep(0.2)
                    GPIO.output(buzzer,GPIO.HIGH)
                    print ("Beep")
                    time.sleep(0.2) # Delay in seconds
                    GPIO.output(buzzer,GPIO.LOW)
                    lcd_display("display",card_name[i])
                    motor_on()
                    time.sleep(0.2)
                    GPIO.output(ledPin,GPIO.LOW)
                    lcd_display("clear",card_name[i])
                    s=""
                    s=get_to_mcs(6)
                    now=datetime.now()
                    date_time= now.strftime("%m/%d/%Y, %H:%M:%S")
                    s=s+"Entrance,"+card_name[i]+","+date_time+","
                    time.sleep(0.1)
                    post_to_mcs(6,s)
                    time.sleep(3)
                    post_to_mcs(7,0)
        else:
            #wrong card
            s=""
            s=get_to_mcs(6)
            now=datetime.now()
            date_time= now.strftime("%m/%d/%Y, %H:%M:%S")
            s=s+"Wrong card,"+"anon"+","+date_time+","
            time.sleep(0.1)
            post_to_mcs(6,s)
            msg="Unknown card detected, someone try to enter your home"
            linenotify(token,msg)
            #capture photo here
            capture_photo()
            for i in range(2):
                GPIO.output(ledPin,GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(buzzer,GPIO.HIGH)
                print ("Beep")
                time.sleep(0.2) # Delay in seconds
                GPIO.output(buzzer,GPIO.LOW)
                GPIO.output(ledPin,GPIO.LOW)
                
            lcd_display("wrong","")
            print("access denied")
            time.sleep(3)
            post_to_mcs(3, str(id))
            lcd_display("clear","")
    

    #pass_key()
    time.sleep(0.5)

