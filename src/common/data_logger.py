from src.common.utils import *

class DataLogger:

    def __init__(self, folder, headers:list[str]) -> None:
        self.folder = folder
        self.headers = headers
        timestamp = datetime.now().strftime("%Y%m%d")
        if not os.path.exists(folder):
            os.makedirs(folder)
        self.dataFp = os.path.join(folder, f"{timestamp}.csv")
        LOGGER.info(f"Data Logger Fp: {self.dataFp}")

        self._createDataFile()

    def _createDataFile(self):
        if not os.path.exists(self.dataFp):
            LOGGER.info(f"{self.dataFp} does not exist, creating it!")
            # write headers
            with open(self.dataFp, "w+") as f:
                f.write(",".join(self.headers))
                f.write("\n")

    def writeLog(self, *data):
        assert os.path.exists(self.dataFp)
        # write data
        with open(self.dataFp, "a") as f:
            f.write(",".join([str(d) for d in data]))
            f.write("\n")

if __name__ == "__main__":
    a = DataLogger(folder=os.path.join(ROOT_PATH, "src", "test"), headers=["Time", "Ad Cart Type"])
    a.writeLog(datetime.now().isoformat(), 1)

