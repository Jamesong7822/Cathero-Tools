from src.common.utils import *

class AdbManager:

    def __init__(self, port:int=5555) -> None:
        self._port = port
        self.__connect()

    def __connect(self):
        # try to connect to port
        try:
            adb.connect(f"127.0.0.1:{self._port}", timeout=3)
        except AdbTimeout as e:
            LOGGER.error(e)
        # Find devices
        devices = adb.device_list()
        LOGGER.info(devices)
        try:
            self.device = adb.device(serial=devices[0].serial)
            LOGGER.info(f"Successfully Connected To {self.device}")
            self._deviceWinSize = self.device.window_size()
            # LOGGER.info(self.device.window_size())
        except AdbTimeout as e:
            LOGGER.error(e)

    def click(self, clickPos):
        """ Handy function for clicking
        clickPos is a tuple / list of actual positions: (100,100), or float (0.5, 0.5) for clicking center
        """
        if all([type(clickPos[0])==float, type(clickPos[1])==float]):
            # this is a ratio so we convert for debug printing
            clickPosDebug = (self._deviceWinSize[0]*clickPos[0], self._deviceWinSize[1]*clickPos[1])
        else:
            clickPosDebug = clickPos
        LOGGER.debug(f"Clicking Screen Position: {clickPosDebug}")
        self.device.click(*clickPos)

    def swipe(self, swipeStartPos, swipeEndPos, swipeDuration):
        """ Handy function for swiping
        """
        if all([type(swipeStartPos[0])==float, type(swipeStartPos[1])==float, type(swipeEndPos[0])==float, type(swipeEndPos[1])==float]):
            # this is a ratio so we convert for debug printing
            swipeStartDebug = (self._deviceWinSize[0]*swipeStartPos[0], self._deviceWinSize[1]*swipeStartPos[1])
            swipeEndDebug = (self._deviceWinSize[0]*swipeEndPos[0], self._deviceWinSize[1]*swipeEndPos[1])
        else:
            swipeStartDebug = swipeStartPos
            swipeEndDebug = swipeEndPos
        LOGGER.debug(f"Swiping From {swipeStartDebug} To {swipeEndDebug} Over {swipeDuration}s")
        self.device.swipe(*swipeStartPos, *swipeEndPos, swipeDuration)

if __name__ == "__main__":
    a = AdbManager()
    # a.click(TAP_MENU_POS_RATIO)
    a.swipe((0.5, 0.1,), (0.5, 0.8), 0.5)