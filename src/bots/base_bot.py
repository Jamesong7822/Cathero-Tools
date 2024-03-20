from src.common.utils import *
from src.common.window_capture import *
from src.common.template_matcher import *
from abc import abstractmethod
from src.common.data_logger import *
from src.common.adb_manager import AdbManager
        
class BaseBot:
    NAME = "BASE BOT"
    FOLDER_PATH_FOR_SCREENSHOTS = os.path.join(ROOT_PATH, "Data", NAME, "Screenshots")
    DEFAULT_DATA_FOLDER = os.path.join(ROOT_PATH, "Data", NAME)
    DATA_HEADERS = []
    def __init__(self, windowCapture:WindowCapture, adbManager:AdbManager,
                 templateTypes:list[Template_Types], folder:str=DEFAULT_DATA_FOLDER, headers:list[str]=DATA_HEADERS):
        self.templateStore = TemplateStore()
        self.dataLogger = DataLogger(folder=folder, headers=headers)
        self._hasTakenScreenshot = False
        self._isRunning = True
        self._templateTypes = templateTypes
        self.windowCapture = windowCapture
        self.adbManager = adbManager
        self._run()

    def _run(self):
        while self._isRunning:
            screenshot = self.windowCapture.getWindowScreen()
            if screenshot is None:
                continue
            # Run bot specific actions
            templateMatchedImg = self._botSpecificActions(screenshot=screenshot)
            # Display
            cv2.imshow("img", templateMatchedImg)
            key = cv2.waitKey(50)
            if key == ord("q"):
                self._isRunning = False
            elif key == ord("s"):
                self._takeScreenshot(screenshot=screenshot)

        cv2.destroyAllWindows()

    @abstractmethod
    def _botSpecificActions(self, screenshot):
        for templateType in self._templateTypes:
            templateMatcher = TemplateMatcher(screenshot, templateType=templateType, templateStore=self.templateStore)
            templateMatchedImg = templateMatcher.getMatchedImg()
        if templateMatcher.templateMatchResult:
            if not self._hasTakenScreenshot:
                self._hasTakenScreenshot = True
                self._takeScreenshot(screenshot=templateMatchedImg)
        else:
            self._hasTakenScreenshot = False

        return templateMatchedImg

    def _takeScreenshot(self, screenshot):
        if screenshot is None:
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
        if not os.path.exists(self.FOLDER_PATH_FOR_SCREENSHOTS):
            os.makedirs(self.FOLDER_PATH_FOR_SCREENSHOTS)
        screenshotFp = os.path.join(self.FOLDER_PATH_FOR_SCREENSHOTS, f"{timestamp}.png")
        LOGGER.info(f"Saving Screenshot To {screenshotFp}")
        cv2.imwrite(screenshotFp, screenshot)

    def _checkForTemplate(self, screenshot, template) -> TemplateMatcher:
        pass

if __name__ == "__main__":
    windowCapture = WindowCapture(windowName="Cathero")
    windowCapture.start()
    a = BaseBot(windowCapture=windowCapture, adbManager=AdbManager(), templateTypes=[])
    windowCapture.stop()