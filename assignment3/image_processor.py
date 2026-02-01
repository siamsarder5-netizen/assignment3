import cv2
import numpy as np

class ImageProcessor:
    def __init__(self, image):
        self.image = image

    def grayscale(self):
        return cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def blur(self, intensity):
        k = intensity * 2 + 1
        return cv2.GaussianBlur(self.image, (k, k), 0)

    def edge_detect(self):
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        return cv2.Canny(gray, 100, 200)

    def adjust_brightness(self, value):
        return cv2.convertScaleAbs(self.image, alpha=1, beta=value)

    def adjust_contrast(self, value):
        return cv2.convertScaleAbs(self.image, alpha=value, beta=0)

    def rotate(self, angle):
        if angle == 90:
            return cv2.rotate(self.image, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(self.image, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(self.image, cv2.ROTATE_90_COUNTERCLOCKWISE)

    def flip(self, mode):
        return cv2.flip(self.image, 1 if mode == "horizontal" else 0)

    def resize(self, scale):
        h, w = self.image.shape[:2]
        return cv2.resize(self.image, (int(w*scale), int(h*scale)))
