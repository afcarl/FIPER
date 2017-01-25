# Capture video with OpenCV

import numpy as np
import cv2
import time 

cap = cv2.VideoCapture('serenity.mp4')

while(cap.isOpened()):

	ret, frame = cap.read()

	# time.sleep(.25)

	cv2.rectangle(frame,(384,0),(510,128),(0,255,0),3)
	
	cv2.imshow('frame',frame)
	if cv2.waitKey(5) & 0xFF == ord('q'):
		break
		
		
		
cap.release()
