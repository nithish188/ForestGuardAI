import cv2
import numpy as np

def detect_deforestation(before_path, after_path):
    before = cv2.imread(before_path)
    after = cv2.imread(after_path)

    before = cv2.resize(before, (600, 600))
    after = cv2.resize(after, (600, 600))

    # absolute difference
    diff = cv2.absdiff(before, after)

    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    # highlight major changes
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)

    # color the changes in red
    after_highlight = after.copy()
    after_highlight[thresh == 255] = [0, 0, 255]

    change_percent = (np.sum(thresh == 255) / thresh.size) * 100

    return after_highlight, change_percent