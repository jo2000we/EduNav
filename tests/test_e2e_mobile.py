from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException


class MobileSmokeTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--window-size=375,812")
        try:
            cls.browser = webdriver.Chrome(options=options)
        except WebDriverException:
            cls.browser = None

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "browser", None):
            cls.browser.quit()
        super().tearDownClass()

    def test_login_page_mobile_viewport(self):
        if not getattr(self, "browser", None):
            self.skipTest("webdriver not available")
        self.browser.get(f"{self.live_server_url}/")
        assert "Login" in self.browser.title
