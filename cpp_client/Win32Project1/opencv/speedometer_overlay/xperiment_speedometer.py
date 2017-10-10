# coding=utf-8

import cv2
import numpy as np

# Speedometer pointer
speedin = cv2.imread("speedin.jpg")  # type: np.ndarray
# Speedometer outer part
speedout = cv2.imread("speedout.jpg")  # type: np.ndarray

# Shapes
ishx, ishy, ishz = speedin.shape
oshx, oshy, oshz = speedout.shape

# Appropriate translation for the pointer part
trX, trY = (oshx - ishx) // 2, (oshy - ishy) // 2


def kmph_stream():
    """Generates random velocity values"""
    velocity = 0.
    while 1:
        velocity *= 0.95
        velocity += np.random.uniform(0.0, 10.0)
        yield int(velocity)


def cam_stream():
    """Reads the webcam for video frames"""
    # noinspection PyArgumentList
    dev = cv2.VideoCapture(0)
    while 1:
        succes, frame = dev.read()
        if succes:
            yield frame
        else:
            print("Frameskip!")


def get_speedometer(kmph):
    """Constructs a speedometer with the pointer set to the appropriate kmph value"""
    if kmph >= 240:
        kmph = 240
    deg = 30 - kmph
    rotM = cv2.getRotationMatrix2D((ishx // 2, ishy // 2), deg, 1)
    rotIn = cv2.warpAffine(speedin, rotM, (ishx, ishy))  # Rotated pointer
    mat = speedout.copy()
    # Replace speedout's appropriate part with the rotated speedin image
    mat[trX:trX + ishx, trY:trY + ishy] = rotIn
    return mat


def decorate_frame(frame, kmph):
    """Decorates a video frame with a speedometer and a text message"""
    speedometer = get_speedometer(kmph)
    output = frame.copy()
    # Addition below ensures that [0, 0, 0] pixels are transparent
    output[-oshx:, :oshy] += speedometer
    text_bottom_left = (20, 20)
    font_face = 1
    font_scale = 1
    font_color = (255, 255, 255)
    cv2.putText(output, "{} km/h".format(kmph), text_bottom_left,
                font_face, font_scale, font_color)
    return np.clip(output, 0, 255)  # to stay in valid pixel value range


def main():
    speeds = kmph_stream()
    camframes = cam_stream()
    frame = next(camframes)  # Get a single frame for shape info
    fourcc = cv2.VideoWriter_fourcc(*"DIVX")  # Select codec
    vidshape = frame.shape[:2][::-1]  # Drop 3rd dimension and reverse x - y
    vw = cv2.VideoWriter("speedometer.avi", fourcc, 20.0, vidshape)
    for i in range(300):
        print "\r", i,
        deco = decorate_frame(next(camframes), next(speeds))
        vw.write(deco)
    vw.release()


if __name__ == '__main__':
    main()
    raw_input("LÉCCI NE PUSHOLD FEL A VIDEÓT GITRE!!! KÖSZI :)")
