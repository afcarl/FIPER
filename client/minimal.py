from __future__ import unicode_literals, print_function, absolute_import

import time

import cv2

from FIPER.client.direct import DirectConnection


dc = DirectConnection("127.0.0.1")
dc.connect("127.0.0.1")
time.sleep(3)
for frame in dc.get_stream(bytestream=False):
    cv2.imshow("Da Stream!", frame)
    key = cv2.waitKey(1)
    if key == 27:
        break
    print(key)

dc.teardown()
