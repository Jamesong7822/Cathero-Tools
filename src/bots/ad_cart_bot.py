from src.bots.base_bot import *
from src.common.template_matcher import Template_Types
from src.common.window_capture import WindowCapture

class AD_CART_BOT_STATES(Enum):
    IDLE = auto()
    LOOK_FOR_AD_CART = auto()
    DETERMINE_REWARD_TYPE = auto()

class AdCartBot(BaseBot):
    NAME = "AD CART BOT"
    DATA_HEADERS = ["Time", "Ad Cart Type", "Match Value"]
    DEFAULT_DATA_FOLDER = os.path.join(ROOT_PATH, "Data", NAME)
    FOLDER_PATH_FOR_SCREENSHOTS = os.path.join(ROOT_PATH, "Data", NAME, "Screenshots")

    def __init__(self, windowCapture: WindowCapture, templateTypes: list[Template_Types], folder=DEFAULT_DATA_FOLDER, headers: list[str] = DATA_HEADERS):
        self.lastRewardTime = datetime.now()
        self.lastAdCartTime = datetime.now()
        self.detectedAdCartFlag = False
        self._state = AD_CART_BOT_STATES.LOOK_FOR_AD_CART
        self.startIdleTime = datetime.now()
        super().__init__(windowCapture, templateTypes, folder, headers)
        
    def _botSpecificActions(self, screenshot):
        if self._state == AD_CART_BOT_STATES.IDLE:
            # Use this state as a cooldown to prevent multiple matches
            if (datetime.now() - self.startIdleTime).total_seconds() > 30: # 30 seconds
                # Move back to look for ad cart state
                self._state = AD_CART_BOT_STATES.LOOK_FOR_AD_CART
            return screenshot

        elif self._state == AD_CART_BOT_STATES.LOOK_FOR_AD_CART:
            templateMatcher = TemplateMatcher(screenshot, templateType=Template_Types.REWARD_FROM_AD_CART, 
                                            templateStore=self.templateStore, threshold=0.7, cropX=0.4, cropY=0.15, cropOffsetY=-120)
            if templateMatcher.templateMatchResult.matchVal != 0:
                # FOUND AD CART
                self._state = AD_CART_BOT_STATES.DETERMINE_REWARD_TYPE
                LOGGER.info("Ad Cart Found!")
                self.lastAdCartTime = datetime.now()
                # Save a screenshot!
                self._takeScreenshot(screenshot=templateMatcher.getMatchedImg())
                self.startDetermineRewardTime = datetime.now()
            return templateMatcher.getMatchedImg()

        elif self._state == AD_CART_BOT_STATES.DETERMINE_REWARD_TYPE:
            templateMatchers:list[TemplateMatcher] = []
            for templateType in self._templateTypes:
                templateMatcher = TemplateMatcher(screenshot, templateType=templateType, templateStore=self.templateStore, 
                                                threshold=0.6, cropX=0.2, cropY=0.1)
                templateMatchers.append(templateMatcher)
                LOGGER.debug(templateMatcher.templateMatchResult)
            # Check for max match value - sort
            templateMatchers = sorted(templateMatchers, key=lambda x: x.templateMatchResult.matchVal, reverse=True)
            bestMatch:TemplateMatcher = templateMatchers[0]
            LOGGER.info(f"Found Best Match: {bestMatch.templateMatchResult}")
            if bestMatch.templateMatchResult.matchVal > 0:
                self.lastRewardTime = datetime.now()
                self._takeScreenshot(screenshot=bestMatch.getMatchedImg())
                self.dataLogger.writeLog(datetime.now().isoformat(), bestMatch.templateType, bestMatch.templateMatchResult.matchVal)
                self._state = AD_CART_BOT_STATES.IDLE
                self.startIdleTime = datetime.now()
            elif (datetime.now() - self.startDetermineRewardTime).total_seconds() > 20:
                # FORCE move to idle state
                self._state = AD_CART_BOT_STATES.IDLE
                self.startIdleTime = datetime.now()
                LOGGER.warning(f"Unable To Determine Reward - FORCED TIMEOUT")
            return templateMatcher.getMatchedImg()

if __name__ == "__main__":
    windowCapture = WindowCapture(windowName="Cathero")
    windowCapture.start()
    a = AdCartBot(windowCapture=windowCapture, 
                  templateTypes=[Template_Types.FISH_TANK_KIT, Template_Types.CANNON_TICKET, 
                                 Template_Types.SKILL_TICKET, Template_Types.COMPANION_TICKET, 
                                 Template_Types.RUNE_TICKET, Template_Types.DIAMONDS])
    windowCapture.stop()