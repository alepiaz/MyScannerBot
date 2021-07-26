import cv2
import numpy as np
import matplotlib.pyplot as plt
from croplayer import *
import sys, os

protoPath = "hed/hed_model/deploy.prototxt"
modelPath = "hed/hed_model/hed_pretrained_bsds.caffemodel"
net = cv2.dnn.readNetFromCaffe(protoPath, modelPath)
cv2.dnn_registerLayer("Crop", CropLayer)

def for_point_warp(cnt, orig):

    pts = cnt.reshape(4, 2)
    rect = np.zeros((4, 2), dtype = "float32")
    s = pts.sum(axis = 1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis = 1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype = "float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warp = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))
    return warp

def resize(img, width=None, height=None, interpolation = cv2.INTER_AREA):
    global ratio
    w, h, _ = img.shape

    if width is None and height is None:
        return img
    elif width is None:
        ratio = height/h
        width = int(w*ratio)
        resized = cv2.resize(img, (height, width), interpolation)
        return resized
    else:
        ratio = width/w
        height = int(h*ratio)
        resized = cv2.resize(img, (height, width), interpolation)
        return resized

def scanner(orig):
    try: 

        s = 5
        m = 5
        g = 5
        d = 2
        e = 2



        image = orig.copy()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        (oH,oW) = orig.shape[:2]
        image = resize(image, 500)
        (H, W) = image.shape[:2]

        ratio = (H-(2*s))/oH
    #     orig = img.copy()
        # convert the image to grayscale, blur it, and perform Canny
        # edge detection
        # print("[INFO] performing Canny edge detection...")
        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.medianBlur(image, m)
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        # construct a blob out of the input image for the Holistically-Nested
        # Edge Detector
        blob = cv2.dnn.blobFromImage(blurred, scalefactor=1.0, size=(W, H),
            mean=(104, 117, 124),
            swapRB=False, crop=False)

        # set the blob as the input to the network and perform a forward pass
        # to compute the edges
        # print("[INFO] performing holistically-nested edge detection...")
        net.setInput(blob)
        hed = net.forward()
        hed = cv2.resize(hed[0, 0], (W, H))
        hed = (255 * hed).astype("uint8")

        # show the output edge detection results for Canny and
        # Holistically-Nested Edge Detection

        gauss = cv2.GaussianBlur(hed, (g,g),0)

        canny = cv2.Canny(gauss, 0, 75)

        dialated = cv2.dilate(canny, cv2.getStructuringElement(cv2.MORPH_RECT,(3,3)), iterations = d)

        eroded = cv2.erode(dialated,cv2.getStructuringElement(cv2.MORPH_RECT,(3,3)), iterations = e)

        # thresh = cv2.adaptiveThreshold(eroded,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,2)

        closing = cv2.morphologyEx(eroded, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8),iterations = 1)

        closing = closing[s:-s,s:-s]

        contours, hierarchy = cv2.findContours(closing, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        if contours == []:
            return []
        contours = sorted(contours, key = cv2.contourArea, reverse = True)[:5]


        targets = []

        # print("[INFO] detecting contours...")


        for c in contours:
            p = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.05* p, True)

            if len(approx) == 4:
                target = approx

                target[0] = ((target[0])/ratio)
                target[1] = ((target[1])/ratio)
                target[2] = ((target[2])/ratio)
                target[3] = ((target[3])/ratio)
                # cv2.drawContours(orig, [target], -1, (0, 255, 0), 2)
                targets.append(target)

        if targets == [] :
            return []

        else:
            origs = []
            warps = []
            for target in targets:
                tmp = orig.copy()
                cv2.drawContours(tmp, [target], -1, (67,160,71), 5)
                warp = for_point_warp(target,orig)
                if warp.shape[:2][0] < 200 or warp.shape[:2][1] < 200:
                    return origs,warps
                # gray_warp = cv2.cvtColor(warp, cv2.COLOR_BGR2GRAY)
                # thresh = cv2.adaptiveThreshold(gray_warp, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
                # denoised = cv2.fastNlMeansDenoising(thresh, 11, 31, 9)
                origs.append(tmp)
                warps.append(warp)
            return origs,warps
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)