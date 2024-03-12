import win32gui, win32ui, win32con

from src.common.utils import *
from threading import Thread, Lock
import cv2

class WindowCapture:
    DEFAULT_BORDER_PIXELS = 0
    DEFAULT_TITLE_PIXELS = 40

    def __init__(self, windowName:str|None=None):
        # Capture entire screen if windowName is None
        if windowName is None:
            self.hwnd = win32gui.GetDesktopWindow()
        else:
            self.hwnd = win32gui.FindWindow(None, windowName)
            if not self.hwnd:
                raise Exception('Window not found: {}'.format(windowName))
            else:
                LOGGER.info(f"Successfully Found Window: '{windowName}'")
            
        windowRect = win32gui.GetWindowRect(self.hwnd)
        LOGGER.info(windowRect)

        self.w = int((windowRect[2] - windowRect[0])*1.25)
        self.h = int((windowRect[3] - windowRect[1])*1.25)
        self.w = self.w - (self.DEFAULT_BORDER_PIXELS * 2)
        self.h = self.h - self.DEFAULT_TITLE_PIXELS - self.DEFAULT_BORDER_PIXELS

        self.cropped_x = 0
        self.cropped_y = self.DEFAULT_TITLE_PIXELS

        # create a thread lock object
        self.lock = Lock()

     # threading methods

    def start(self):
        self.stopped = False
        t = Thread(target=self.run, daemon=True)
        t.start()

    def stop(self):
        self.stopped = True

    def run(self):
        while not self.stopped:
            # get an updated image of the game
            screenshot = self.get_screenshot()
            # resize the image
            screenshot = self.image_resize(screenshot, height=700)
            # lock the thread while updating the results
            self.lock.acquire()
            self.screenshot = screenshot
            self.lock.release()

    def getWindowScreen(self):
        if not hasattr(self, "screenshot"):
            return
        return self.screenshot

    def get_screenshot(self):
        # get the window image data
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

        # convert the raw data into a format opencv can read
        #dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype='uint8')
        img.shape = (self.h, self.w, 4)

        # free resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # drop the alpha channel, or cv.matchTemplate() will throw an error like:
        #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type() 
        #   && _img.dims() <= 2 in function 'cv::matchTemplate'
        img = img[...,:3]

        # make image C_CONTIGUOUS to avoid errors that look like:
        #   File ... in draw_rectangles
        #   TypeError: an integer is required (got type tuple)
        # see the discussion here:
        # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
        img = np.ascontiguousarray(img)

        return img
    
    def image_resize(self, image, width = None, height = None, inter = cv2.INTER_AREA):
        # initialize the dimensions of the image to be resized and
        # grab the image size
        dim = None
        (h, w) = image.shape[:2]

        # if both the width and height are None, then return the
        # original image
        if width is None and height is None:
            return image

        # check to see if the width is None
        if width is None:
            # calculate the ratio of the height and construct the
            # dimensions
            r = height / float(h)
            dim = (int(w * r), height)

        # otherwise, the height is None
        else:
            # calculate the ratio of the width and construct the
            # dimensions
            r = width / float(w)
            dim = (width, int(h * r))

        # resize the image
        resized = cv2.resize(image, dim, interpolation = inter)

        # return the resized image
        return resized

if __name__ == "__main__":
    a = WindowCapture(windowName="Cathero")
    a.start()
    # a.stop()
    cv2.namedWindow('img', cv2.WINDOW_NORMAL)
    while True:
        screenshot = a.screenshot
        screenshotResized = a.image_resize(screenshot, height=700)
        cv2.imshow("img", screenshotResized)
        key = cv2.waitKey(1)
        if key == ord("q"):
            cv2.destroyAllWindows()
            break
        elif key == ord("s"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            LOGGER.info(f"{timestamp}.png")
            cv2.imwrite(f"{timestamp}.png", screenshot)
    a.stop()