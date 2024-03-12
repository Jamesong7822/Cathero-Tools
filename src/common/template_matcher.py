from src.common.utils import *
import cv2

class Template_Types(Enum):
    REWARD_FROM_AD_CART = 0
    FISH_TANK_KIT = auto()
    CANNON_TICKET = auto()
    SKILL_TICKET = auto()
    COMPANION_TICKET = auto()
    RUNE_TICKET = auto()
    DIAMONDS = auto()

class TemplateStore:
    DATA = {
        Template_Types.REWARD_FROM_AD_CART: os.path.join(ROOT_PATH, "src", "Assets", "Templates", "Ad Cart.png"),
        Template_Types.FISH_TANK_KIT: os.path.join(ROOT_PATH, "src", "Assets", "Templates", "Fish Tank Kit 2.png"),
        Template_Types.CANNON_TICKET: os.path.join(ROOT_PATH, "src", "Assets", "Templates", "Cannon Ticket.png"),
        Template_Types.SKILL_TICKET: os.path.join(ROOT_PATH, "src", "Assets", "Templates", "Skill Ticket 2.png"),
        Template_Types.COMPANION_TICKET: os.path.join(ROOT_PATH, "src", "Assets", "Templates", "Companion Ticket 2.png"),
        Template_Types.RUNE_TICKET: os.path.join(ROOT_PATH, "src", "Assets", "Templates", "Rune Ticket.png"),
        Template_Types.DIAMONDS: os.path.join(ROOT_PATH, "src", "Assets", "Templates", "Diamond 2.png"),
        
    }

    def __init__(self):
        self._loadTemplates()

    def _loadTemplates(self):
        self._images = {}
        for key, assetLoc in self.DATA.items():
            self._images[key] = cv2.imread(assetLoc)

    def getTemplateImg(self, templateType:Template_Types):
        assert templateType in self.DATA, f"{templateType} is Invalid!"
        return self._images.get(templateType, None)

class TemplateMatcherResult:

    def __init__(self, templateType:Template_Types, matchVal:float, topLeft, width, height, offsetTL, cropW, cropH):
        self.templateType = templateType
        self.templateName = templateType.name
        self.matchVal = matchVal
        self.topLeft = topLeft
        self.width = width
        self.height = height
        self.offsetTL = offsetTL
        self.offsetBR = offsetTL[0]+cropW, offsetTL[1]+cropH
        self.botRight  = (self.topLeft[0] + width, self.topLeft[1] + height)
        self.center = (int(self.topLeft[0]+self.width//2), int(self.topLeft[1]+self.height//2))

    def __repr__(self) -> str:
        return f"Template Matcher - {self.templateName}: Matched With {self.matchVal:.3f}, TL: {self.topLeft}, BR: {self.botRight}, Center: {self.center}"

class TemplateMatcher:
    # FORCE RESIZE
    DEFAULT_HEIGHT = 700 # px
    TEMPLATE_HEIGHT_MAX = 50 #px
    TEMPLATE_HEIGHT_MIN = 15 #px
    TEMPLATE_HEIGHT_STEP = 1 #px
    MIN_MATCH_THRESHOLD = 0.8

    def __init__(self, img, templateType:Template_Types, templateStore:TemplateStore, 
                 threshold:float=MIN_MATCH_THRESHOLD, cropX=0.5, cropY=0.5, cropOffsetY:int=0) -> None:
        self.originalImg = copy.deepcopy(img)
        self.img = self._image_resize(img, height=self.DEFAULT_HEIGHT)
        self.templateType = templateType
        self.threshold = threshold
        self.cropX = cropX
        self.cropY = cropY
        self.cropOffsetY = cropOffsetY
        ## Make some important variables for the image
        self._height, self._width = self.img.shape[0], self.img.shape[1]
        self._imgCenter = (self._height//2, self._width//2)

        if templateType == Template_Types.REWARD_FROM_AD_CART:
            # do nothing
            self.templateImg = templateStore.getTemplateImg(templateType=templateType)
        else:
            self.templateImg = self._image_resize(templateStore.getTemplateImg(templateType=templateType), height=self.TEMPLATE_HEIGHT_MAX)

        self.templateMatchResult = self._matchTemplate()
        if self.templateMatchResult:
            self.matchedImage = self._generateTemplateMatchImg(self.img, templateMatchResult=self.templateMatchResult)
        else:
            self.matchedImage = self.img

    def getMatchedImg(self):
        return self.matchedImage
    
    def _matchTemplate(self) -> TemplateMatcherResult:
        # Reduce region of inerest
        img, offsetTL, cropH, cropW = self._cropImage(self.img, self.cropX, self.cropY, self.cropOffsetY)
        # for i in range(self.TEMPLATE_HEIGHT_MAX, self.TEMPLATE_HEIGHT_MIN, -self.TEMPLATE_HEIGHT_STEP):
        for i in range(10, -20, -1):
            try:
                template = self._image_resize(self.templateImg, height=self.TEMPLATE_HEIGHT_MAX+i)
                w, h = template.shape[1], template.shape[0]
                res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if max_val > self.threshold:
                    topLeft = (max_loc[0] + offsetTL[0], max_loc[1]+offsetTL[1])
                    return TemplateMatcherResult(templateType=self.templateType, matchVal=max_val, topLeft=topLeft, 
                                                 width=w, height=h, offsetTL=offsetTL, cropW=cropW, cropH=cropH)
            except Exception as e:
                # LOGGER.warning(e)
                pass
        return TemplateMatcherResult(templateType=self.templateType, matchVal=0, topLeft=(0,0), width=0, height=0, offsetTL=offsetTL, cropW=cropW, cropH=cropH)

    def _image_resize(self, image, width = None, height = None, inter = cv2.INTER_AREA):
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
    
    def _cropImage(self, img, cropX, cropY, cropOffsetY):
        # ratios of crop
        img = copy.deepcopy(img)
        h, w = img.shape[:2]
        ratioY_1 = 0.5*(1-cropY)
        ratioY_2 = 1-0.5*(1-cropY)
        ratioX_1 = 0.5*(1-cropX)
        ratioX_2 = 1-0.5*(1-cropX)
        img = img[int(h*ratioY_1)+cropOffsetY:int(h*ratioY_2)+cropOffsetY, int(w*ratioX_1):int(w*ratioX_2)]
        # get transposed positions
        offsetTopLeft = [int(w*ratioX_1), int(h*ratioY_1)+cropOffsetY]
        # offsetTopRight = [int(h*ratioY_2), int(w*ratioX_2)]
        # Debug
        # cv2.waitKey(0)
        # cv2.imshow("debug", img)
        cropH, cropW = img.shape[0], img.shape[1]
        return img, offsetTopLeft, cropH, cropW
    
    def _generateTemplateMatchImg(self, img, templateMatchResult:TemplateMatcherResult):
        # Draw the cropped rectangle
        img = cv2.rectangle(img, templateMatchResult.offsetTL, templateMatchResult.offsetBR, color=(0,255,0), thickness=2)
        img = cv2.rectangle(img, templateMatchResult.topLeft, templateMatchResult.botRight, color=(0,0,255), thickness=2)
        value = templateMatchResult.matchVal
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.5
        img = cv2.putText(img, f"Template: {templateMatchResult.templateName}", (10,20), font, fontScale, (0,255,0), 1, cv2.LINE_AA)
        img = cv2.putText(img, f"Match Val: {value:.3f}", (10,40), font , fontScale, (0,255,0), 1, cv2.LINE_AA) 
        return img

if __name__ == "__main__":
    import time
    # Test the sequence
    imgs = [
        (Template_Types.REWARD_FROM_AD_CART, cv2.imread(os.path.join(ROOT_PATH, "src", "Assets", "Sample", "SkillTicket.png")), 0.7, 0.4, 0.15, -120),
        (Template_Types.REWARD_FROM_AD_CART, cv2.imread(os.path.join(ROOT_PATH, "src", "Assets", "Sample", "FishTankKit.png")), 0.7, 0.4, 0.15, -120),
        (Template_Types.REWARD_FROM_AD_CART, cv2.imread(os.path.join(ROOT_PATH, "src", "Assets", "Sample", "Companion_Summon.jpg")), 0.7, 0.4, 0.15, -120),
        (Template_Types.FISH_TANK_KIT, cv2.imread(os.path.join(ROOT_PATH, "src", "Assets", "Sample", "FishTankKit.png")), 0.7, 0.2, 0.10, 0),
        (Template_Types.FISH_TANK_KIT, cv2.imread(os.path.join(ROOT_PATH, "src", "Assets", "Sample", "FishTankKit2.png")), 0.7, 0.2, 0.10, 0),
        (Template_Types.SKILL_TICKET, cv2.imread(os.path.join(ROOT_PATH, "src", "Assets", "Sample", "SkillTicket.png")), 0.7, 0.2, 0.10, 0),
        (Template_Types.COMPANION_TICKET, cv2.imread(os.path.join(ROOT_PATH, "src", "Assets", "Sample", "Companion_Summon.jpg")), 0.7, 0.2, 0.10, 0),
        (Template_Types.DIAMONDS, cv2.imread(os.path.join(ROOT_PATH, "src", "Assets", "Sample", "Diamond.png")), 0.7, 0.2, 0.1, 0),
        (Template_Types.DIAMONDS, cv2.imread(os.path.join(ROOT_PATH, "src", "Assets", "Sample", "Diamond2.png")), 0.7, 0.2, 0.1, 0),
        #(Template_Types.FISH_TANK_KIT, cv2.imread(os.path.join(ROOT_PATH, "Data", "AD CART BOT", "Screenshots", "20240310_111411.png")), 0.7, 0.2, 0.2),
    ]
    for templateType, img, threshold, cropX, cropY, cropOffsetY in imgs:
        st = time.time()
        a = TemplateMatcher(img, templateType=templateType, templateStore=TemplateStore(), threshold=threshold, cropX=cropX, cropY=cropY, cropOffsetY=cropOffsetY)
        et = time.time()
        print(et-st)
        print(a.templateMatchResult)
        cv2.imshow("img", a.matchedImage)
        cv2.waitKey(0)
    cv2.destroyAllWindows()