from src.bots.base_bot import *
from src.common.adb_manager import AdbManager
from src.common.template_matcher import Template_Types
from src.common.window_capture import WindowCapture

class GearType(Enum):
    UNKNOWN = auto()
    GLOVES = auto()
    HAT = auto()
    SCARF = auto()
    SHOES = auto()

class GearRarity(Enum):
    UNKNOWN = auto()
    COMMON = auto()
    UNCOMMON = auto()
    RARE = auto()
    EPIC = auto()
    LEGENDARY = auto()

TEMPLATE_TO_GEAR_TYPE_MAP = {
    Template_Types.HAT_COMMON: GearType.HAT,
    Template_Types.HAT_UNCOMMON: GearType.HAT,
    Template_Types.HAT_RARE: GearType.HAT,
    Template_Types.HAT_EPIC: GearType.HAT,
    Template_Types.HAT_LEGENDARY: GearType.HAT,
    Template_Types.GLOVES_COMMON: GearType.GLOVES,
    Template_Types.GLOVES_UNCOMMON: GearType.GLOVES,
    Template_Types.GLOVES_RARE: GearType.GLOVES,
    Template_Types.GLOVES_EPIC: GearType.GLOVES,
    Template_Types.GLOVES_LEGENDARY: GearType.GLOVES,
    Template_Types.SCARF_COMMON: GearType.SCARF,
    Template_Types.SCARF_UNCOMMON: GearType.SCARF,
    Template_Types.SCARF_RARE: GearType.SCARF,
    Template_Types.SCARF_EPIC: GearType.SCARF,
    Template_Types.SCARF_LEGENDARY: GearType.SCARF,
    Template_Types.SHOE_COMMON: GearType.SHOES,
    Template_Types.SHOE_UNCOMMON: GearType.SHOES,
    Template_Types.SHOE_RARE: GearType.SHOES,
    Template_Types.SHOE_EPIC: GearType.SHOES,
    Template_Types.SHOE_LEGENDARY: GearType.SHOES,
}

TEMPLATE_TO_RARITY_MAP = {
    Template_Types.HAT_COMMON: GearRarity.COMMON,
    Template_Types.SCARF_COMMON: GearRarity.COMMON,
    Template_Types.GLOVES_COMMON: GearRarity.COMMON,
    Template_Types.SHOE_COMMON: GearRarity.COMMON,
    Template_Types.HAT_UNCOMMON: GearRarity.UNCOMMON,
    Template_Types.SCARF_UNCOMMON: GearRarity.UNCOMMON,
    Template_Types.GLOVES_UNCOMMON: GearRarity.UNCOMMON,
    Template_Types.SHOE_UNCOMMON: GearRarity.UNCOMMON,
    Template_Types.HAT_RARE: GearRarity.RARE,
    Template_Types.SCARF_RARE: GearRarity.RARE,
    Template_Types.GLOVES_RARE: GearRarity.RARE,
    Template_Types.SHOE_RARE: GearRarity.RARE,
    Template_Types.HAT_EPIC: GearRarity.EPIC,
    Template_Types.SCARF_EPIC: GearRarity.EPIC,
    Template_Types.GLOVES_EPIC: GearRarity.EPIC,
    Template_Types.SHOE_EPIC: GearRarity.EPIC,
    Template_Types.HAT_LEGENDARY: GearRarity.LEGENDARY,
    Template_Types.SCARF_LEGENDARY: GearRarity.LEGENDARY,
    Template_Types.GLOVES_LEGENDARY: GearRarity.LEGENDARY,
    Template_Types.SHOE_LEGENDARY: GearRarity.LEGENDARY,
}

class MARKET_BOT_STATES(Enum):
    IDLE = auto()
    CHECK_IF_IN_EXCHANGE_PAGE = auto()

    REFRESH = auto()
    SCAN = auto()
    PARSE_DATA = auto()

class MarketData:

    def __init__(self, gearType:GearType, gearRarity:GearRarity, tradeCounts:int, price:int, enhancement:int=0, durability:int=1) -> None:
        self.gearType = gearType
        self.gearRarity = gearRarity
        self.tradeCount = tradeCounts
        self.price = price
        self.enhancement = enhancement
        self.durability = durability

    def __repr__(self) -> str:
        return f"({self.gearRarity.name}) {self.gearType.name} +{self.enhancement} - {self.price} BD | Trades Left: {self.tradeCount}"

class MarketBotTableParser:
    ROW_LEFT_X = 0.05
    ROW_RIGHT_X = 0.95
    ROW_HEIGHT_START = 0.13
    ROW_HEIGHT_Y = 0.09
    ROW_GAP_Y = 0.006
    NUM_ROWS_PER_SCREEN = 7
    NUM_ROWS_PER_PAGE = 10 # this counts the offscreen rows too

    def __init__(self, screenshot, templateStore:TemplateStore, debugMode:bool=False) -> None:
        self.screenshot = screenshot
        self.templateStore = templateStore
        self._debugMode = debugMode
        self.__genRowSliceRatios()

        self._thresh = 255
        st = time.time()
        self._run()
        print(time.time()-st)

    def _run(self):
        if self.screenshot is None:
            return
        screenshot = self.screenshot.copy()

        results = []
        for row in self._rowSlices:
            topLeft = row[0]
            botRight = row[1]
            screenshot, topLeft_px, botRight_px = self._getRowImg(screenshot=screenshot, topLeft=topLeft, botRight=botRight)
            results.append([screenshot, topLeft_px, botRight_px])
            marketData = self._parseRowImg(screenshot[topLeft_px[1]:botRight_px[1], topLeft_px[0]:botRight_px[0]])
            # LOGGER.debug(self.__doOCR(screenshot, topLeft_px, botRight_px))
            LOGGER.debug(marketData)
        cv2.imshow("Market Bot Table Parser", screenshot)
        cv2.waitKey(0)

    def _parseRowImg(self, rowImg):
        """ Parse row image to get gear icon, name, trade counts, dark gem price
        """
        h, w = rowImg.shape[:2]
        priceTL = int(w*0.7), 0
        priceBR = w, h
        price = self.__doOCR(rowImg, topLeft=priceTL, botRight=priceBR)
        tradeCountsTL = int(w*0.59), 0
        tradeCountsBR = int(w*0.65), h
        tradeCounts = self.__doOCR(rowImg, topLeft=tradeCountsTL, botRight=tradeCountsBR)
        # gearInfoTL = int(w*0.18), 0
        # gearInfoBR = int(w*0.45), h
        # gearText = self.__doOCR(rowImg, topLeft=gearInfoTL, botRight=gearInfoBR, digitsOnly=False)
        # gearType, gearRarity, enhancement = self.__getGearFromText(gearText=gearText)
        templateMatcher = TemplateMatcher(rowImg, templateType=Template_Types.HAT_COMMON, templateStore=self.templateStore, 
                                          threshold=0.6, defaultHeight=h, templateHeight=20, heightUp=0, heightDown=10, 
                                          cropX=0.2, cropY=1, cropOffsetX=-140)
        LOGGER.debug(templateMatcher.templateMatchResult)
        templateType = templateMatcher.templateMatchResult.templateType
        gearType = TEMPLATE_TO_GEAR_TYPE_MAP[templateType]
        gearRarity = TEMPLATE_TO_RARITY_MAP[templateType]
        return MarketData(gearType=gearType, gearRarity=GearRarity.COMMON, tradeCounts=tradeCounts, price=price)
    
    def __getGearFromText(self, gearText):
        enhancement = 0
        gearType = GearType.UNKNOWN
        gearRarity = GearRarity.COMMON
        if "+" in gearText:
            enhancement = int(gearText[1])
        if "HAT" in gearText.upper():
            gearType = GearType.HAT
        
        return gearType, gearRarity, enhancement
        

    def __doOCR(self, img, topLeft, botRight, digitsOnly:bool=True):
        """ Key function to return out the ocr text
        """
        img = img.copy()
        img = img[topLeft[1]:botRight[1], topLeft[0]:botRight[0]]
        custom_oem_psm_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789' # psm (page segmentation: 7 for treating img as single line text)
        # By default OpenCV stores images in BGR format and since pytesseract assumes RGB format,
        # we need to convert from BGR to RGB format/mode:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # get outer contours and draw filled ones as white on black background
        if self._debugMode:
            while True:
                thresh = cv2.threshold(img, self._thresh, 255, cv2.THRESH_BINARY)[1]
                thresh = self._image_resize(thresh, height=300)
                cv2.imshow("Thresh", thresh)
                key = cv2.waitKey(0)
                if key == ord("w"):
                    self._thresh +=1
                elif key == ord("s"):
                    self._thresh -= 1
                elif key == ord("q"):
                    break
                self._thresh = max(min(self._thresh, 255), 0)
                print(self._thresh)
        else:
            img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)[1]
            # flood fill
            try:
                cv2.floodFill(img, None, (20,20),0)
            except:
                pass
            img = cv2.bitwise_not(img)
            # sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            # img = cv2.filter2D(img, -1, sharpen_kernel)
            # detectedText = pytesseract.image_to_string(img,config=custom_oem_psm_config)
            tmpFile = tempfile.NamedTemporaryFile(suffix=".png", mode="w", delete_on_close=False)
            tmpFile.close()
            cv2.imwrite(tmpFile.name, img)
            OCR.SetImageFile(tmpFile.name)
            if digitsOnly:
                OCR.SetVariable('tessedit_char_whitelist', digits)
            else:
                OCR.SetVariable('tessedit_char_whitelist', digits+ascii_letters+"+")
            detectedText = OCR.GetUTF8Text()
            if os.path.exists(tmpFile.name):
                os.remove(tmpFile.name)
            # LOGGER.debug(detectedText)
            # cv2.imshow("debug", img)
            # cv2.waitKey(0)
        if digitsOnly:
            return int(detectedText.strip().replace(" ", ""))
        return detectedText.strip()

    def _getRowImg(self, screenshot, topLeft, botRight):
        st = time.time()
        h, w = screenshot.shape[:2]
        topLeft_px = (int(topLeft[0]*w), int(topLeft[1]*h))
        botRight_px = (int(botRight[0]*w), int(botRight[1]*h))
        screenshot = cv2.rectangle(screenshot, topLeft_px, botRight_px, color=(0,255,0), thickness=1)
        return screenshot, topLeft_px, botRight_px
    
    def __genRowSliceRatios(self):
        """ Generate the row slices ratio
        1st row: (0.05, 0.13) to (0.95, 0.22)
        2nd row: (0.05, 0.225) to (0.95, 0.315)
        """
        self._rowSlices = []
        for i in range(self.NUM_ROWS_PER_SCREEN):
            if i == 0:
                # first
                topLeft = (self.ROW_LEFT_X, self.ROW_HEIGHT_START)
            else:
                topLeft = (self.ROW_LEFT_X, self.ROW_HEIGHT_START+i*self.ROW_HEIGHT_Y+(i)*self.ROW_GAP_Y)
            botRight = (self.ROW_RIGHT_X, topLeft[1]+self.ROW_HEIGHT_Y)
            # Apply Rounding
            topLeft = round(topLeft[0],3), round(topLeft[1],3)
            botRight = round(botRight[0],3), round(botRight[1],3)
            self._rowSlices.append((topLeft, botRight))

    def _image_resize(self, image, width = None, height = None, inter = cv2.INTER_AREA):
        if image is None:
            return
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

class MarketBot(BaseBot):
    NAME = "MARKET EXCHANGE BOT"
    DATA_HEADERS = ["Time", "Gear Type", "Gear Trade Counts", "Gear Cost", "Match Value"]
    DEFAULT_DATA_FOLDER = os.path.join(ROOT_PATH, "Data", NAME)
    FOLDER_PATH_FOR_SCREENSHOTS = os.path.join(ROOT_PATH, "Data", NAME, "Screenshots")

    def __init__(self, windowCapture: WindowCapture, adbManager: AdbManager, templateTypes: list[Template_Types], folder=DEFAULT_DATA_FOLDER, headers: list[str] = DATA_HEADERS):
        self._state = MARKET_BOT_STATES.IDLE
        self._freshStart = True
        super().__init__(windowCapture, adbManager, templateTypes, folder, headers)

    def _botSpecificActions(self, screenshot):
        if self._state == MARKET_BOT_STATES.IDLE:
            # Move to check if in exchange if its just startup
            if self._freshStart:
                self._freshStart = False
                self._state = MARKET_BOT_STATES.CHECK_IF_IN_EXCHANGE_PAGE
            return screenshot
        elif self._state == MARKET_BOT_STATES.CHECK_IF_IN_EXCHANGE_PAGE:
            templateMatcher = TemplateMatcher(screenshot, templateType=Template_Types.MARKET_HEADER, 
                                              templateStore=self.templateStore, threshold=0.6, cropX=0.95, cropY=0.07, cropOffsetY=-280)
            if templateMatcher.templateMatchResult.matchVal != 0:
                # FOUND Market Exchange Header
                LOGGER.info("Confirmed That Already In Market Exchange")
                self._state = MARKET_BOT_STATES.REFRESH
            return templateMatcher.getMatchedImg()
        elif self._state == MARKET_BOT_STATES.REFRESH:
            # Double Click To Refresh
            LOGGER.info(f"[{self.NAME}]: Refreshing Market")
            self.adbManager.click(TAP_MARKET_PRICE_LABEL_POS_RATIO)
            time.sleep(0.5)
            self.adbManager.click(TAP_MARKET_PRICE_LABEL_POS_RATIO)
            self._state = MARKET_BOT_STATES.SCAN
            return screenshot
        elif self._state == MARKET_BOT_STATES.SCAN:
            return screenshot
        
    def __scan(self, screenshot):
        pass

if __name__ == "__main__":
    # windowCapture = WindowCapture(windowName="Cathero")
    # windowCapture.start()
    # adbManager = AdbManager()
    # a = MarketBot(windowCapture=windowCapture,
    #               adbManager=adbManager,
    #               templateTypes=[])
    # windowCapture.stop()

    MarketBotTableParser(screenshot=cv2.imread(os.path.join(ROOT_PATH, r"Data\MARKET EXCHANGE BOT\Screenshots\20240317_232628772862.png")),
                         templateStore=TemplateStore(),
                         )