# coding=utf-8

import cv2
import numpy as np

speedin = cv2.imread("speedin.jpg")  # type: np.ndarray
speedout = cv2.imread("speedout.jpg")  # type: np.ndarray

ishx, ishy, ishz = speedin.shape
oshx, oshy, oshz = speedout.shape
trX, trY = (oshx - ishx) // 2, (oshy - ishy) // 2


def kmph_stream():
    velocity = 0.
    while 1:
        velocity *= 0.95
        velocity += np.random.uniform(0.0, 10.0)
        yield int(velocity)


def cam_stream():
    # noinspection PyArgumentList
    dev = cv2.VideoCapture(0)
    while 1:
        succes, frame = dev.read()
        if succes:
            yield frame
        else:
            print("Frameskip!")


def get_speedometer(kmph):
    if kmph >= 240:
        kmph = 240
    deg = 30 - kmph
    rotM = cv2.getRotationMatrix2D((ishx//2, ishy//2), deg, 1)
    rotIn = cv2.warpAffine(speedin, rotM, (ishx, ishy))
    mat = speedout.copy()
    mat[trX:trX+ishx, trY:trY+ishy] = rotIn
    return mat


def decorate_frame(frame, kmph):
    speedometer = get_speedometer(kmph)
    output = frame.copy()
    output[-oshx:, :oshy] += speedometer
    cv2.putText(output, "{} km/h".format(kmph), (20, 20), 1, 1, (255, 255, 255))
    return np.clip(output, 0, 255)


def main():
    speeds = kmph_stream()
    camframes = cam_stream()
    frame = next(camframes)
    fourcc = cv2.VideoWriter_fourcc(*"DIVX")
    vw = cv2.VideoWriter("speedometer.avi", fourcc, 20.0, frame.shape[:2][::-1])  # type: cv2.VideoWriter
    for i in range(300):
        print "\r", i,
        deco = decorate_frame(next(camframes), next(speeds))
        vw.write(deco)
    vw.release()

if __name__ == '__main__':
    main()
    raw_input("LÉCCI NE PUSHOLD FEL A VIDEÓT GITRE!!! KÖSZI :)")
