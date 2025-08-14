from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from accounts.models import User
from lessons.models import Classroom


class GoalRedirectTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.binary_location = "/usr/bin/chromium-browser"
            service = Service(ChromeDriverManager().install())
            cls.selenium = webdriver.Chrome(service=service, options=options)
            cls.selenium.implicitly_wait(10)
        except Exception:
            cls.selenium = None

    @classmethod
    def tearDownClass(cls):
        if cls.selenium:
            cls.selenium.quit()
        super().tearDownClass()

    def _login(self, user):
        self.client.force_login(user)
        cookie = self.client.cookies['sessionid']
        self.selenium.get(self.live_server_url + reverse('login'))
        self.selenium.add_cookie({'name': 'sessionid', 'value': cookie.value, 'path': '/'})

    def test_goal_kg_redirect(self):
        if not self.selenium:
            self.skipTest("Webdriver not available")
        classroom = Classroom.objects.create(name="10A")
        user = User.objects.create_user(pseudonym="kg1", gruppe=User.KG, classroom=classroom)
        self._login(user)
        self.selenium.get(self.live_server_url + reverse('goal_kg'))
        textarea = self.selenium.find_element(By.NAME, "raw_text")
        textarea.send_keys("Testziel")
        self.selenium.find_element(By.CSS_SELECTOR, "form button").click()
        WebDriverWait(self.selenium, 5).until(lambda d: d.current_url.endswith('/dashboard/'))

    def test_goal_vg_redirect(self):
        if not self.selenium:
            self.skipTest("Webdriver not available")
        classroom = Classroom.objects.create(name="10A", use_ai=True)
        user = User.objects.create_user(pseudonym="vg1", gruppe=User.VG, classroom=classroom)
        self._login(user)
        self.selenium.get(self.live_server_url + reverse('goal_vg'))
        textarea = self.selenium.find_element(By.TAG_NAME, "textarea")
        textarea.send_keys("Test")
        self.selenium.find_element(By.CSS_SELECTOR, "form button").click()
        WebDriverWait(self.selenium, 5).until(lambda d: d.execute_script("return document.querySelector('[x-data]').__x.$data.goalId !== null"))
        self.selenium.execute_script("document.querySelector('[x-data]').__x.$data.handleResponse({detail:{xhr:{responseText:'{\"message_type\":\"ready_to_finalize\"}'}}});")
        WebDriverWait(self.selenium, 5).until(lambda d: d.current_url.endswith('/dashboard/'))
