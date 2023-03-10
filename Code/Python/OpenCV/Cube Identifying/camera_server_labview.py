import os
import sys
import cv2
import numpy as np
import time
import math
import rospy
from std_msgs.msg import String

constant_height_pixels = 256
constant_distance = 36
cube_height = 11
delta_x_inches = 'error'
theta = 'error'
distance_target = 'error'

last_command = None

font = cv2.FONT_HERSHEY_SIMPLEX
firstrun = True
capture = cv2.VideoCapture(0)
while(True):
         
    #refresh frame
    ret, frame = capture.read()
    
    #convert to HSV
    hsv_raw = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv = hsv_raw
    hsv = cv2.blur(hsv_raw,(10,10))
    #kernel = np.ones((5,5),np.uint8)
    #hsv = cv2.erode(hsv,kernel,iterations = 1)
    #hsv = cv2.bilateralFilter(hsv,9,75,75)
    #cv2.imshow('hsv',hsv)
    #filter for color
    lower_limit = np.array([0,125,125])
    upper_limit = np.array([103,253,255])

    mask = cv2.inRange(hsv, lower_limit, upper_limit)

    masked_image = cv2.bitwise_and(hsv,hsv, mask= mask)
    #cv2.imshow('Masked',masked_image)

    h, s, v = cv2.split(masked_image)

    #cv2.imshow('gray', v)

    gray = v

    #edged = cv2.Canny(gray,100,200)

    #cv2.imshow('edges',edged)
    
    
    ret,thresh = cv2.threshold(gray,127,255,0)
    im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    #cv2.imshow('threshed',thresh)
    contoured = cv2.drawContours(frame, contours, -1, (0,255,0), 3) 

    #cv2.imshow('contoured',contoured)

    #area = cv2.contourArea(contours[0])
    #print(area)
    
    if firstrun:
        print(contours)
        firstrun = False
        pub = rospy.Publisher('autonomous_directions', String, queue_size=10)
        rospy.init_node('camera_server', anonymous=True)
        rate = rospy.Rate(10) # 10hz

    height, width = frame.shape[:2]
    x_center = int(width/2)
    y_center = int(height/2)
    cv2.line(frame,(0,y_center),(width,y_center),(0,0,255),2)
    cv2.line(frame,(x_center,0),(x_center,height),(0,0,255),2)

    filtered_contours = []
    
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(max(contours, key = cv2.contourArea))
        #cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
        h = float(h)
        w = float(w)
        ratio = (float(h/w))
        if float(0.4) < (ratio) < float(2):
            filtered_contours.append(cnt)
            
    if len(filtered_contours) == 0:
        print('No cubes found!')
        next_command = 'left'

    
    if len(filtered_contours) != 0:
        
        x,y,w,h = cv2.boundingRect(max(filtered_contours, key = cv2.contourArea))
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
        cube_x = int(x+(w/2))
        cube_y = int(y+(h/2))
        cv2.line(frame,(0,int((y+(h/2)))),(width,((y+int(h/2)))),(255,250,0),2)
        cv2.line(frame,((x+int(w/2)),0),((x+int(w/2)),height),(255,250,0),2)

        delta_x = int(x_center-cube_x)

        delta_y = int(y_center-cube_y)
        if int(h/cube_height) != 0:
            p = float(h/cube_height)
            delta_x_inches = float(delta_x/p)
        
        
        target = "(%d,%d)"%(delta_x,delta_y)
        print("Target dimentions: %f x %f"%(h,w))

        focal_length = float(((constant_height_pixels*constant_distance)/cube_height))

        distance_target = float(((cube_height*focal_length)/h))
        
        #print(distance_target)

        cv2.putText(frame, str(distance_target) + ' inches', (50,50), font,1,(0,255,0),5)
        if delta_x < 0:
            cv2.putText(frame, target,(cube_x,cube_y),font,1,(0,255,0),10)

        theta = np.arcsin(delta_x_inches/distance_target)
        theta = math.degrees(theta)
        


    message = []
    if not rospy.is_shutdown():
        message.append(str(delta_x_inches))
        message.append(str(theta))
        message.append(str(distance_target))
        pub.publish(message)
        rospy.loginfo(message)
        rate.sleep()

    if len(filtered_contours) != 0:
        cv2.putText(frame, str(theta) + 'degrees', (50,100), font,1,(0,255,0),5)
    cv2.imshow('Final Output',frame)
    
    if cv2.waitKey(1)& 0xFF == ord('q'):
        break


capture.release()
cv2.destroyAllWindows()     
