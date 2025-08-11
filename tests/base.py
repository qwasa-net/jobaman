import jobaman.logger


class BaseTestCase:

    def setUp(self):
        jobaman.logger.configure()
        self.log = jobaman.logger.get_logger()
