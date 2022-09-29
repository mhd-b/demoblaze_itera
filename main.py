import json
import string
import time
import allure
import random
import pytest
from assertpy.assertpy import assert_that
from datetime import datetime
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


class TestDemoBlazer:

    @classmethod
    def setup_class(cls) -> None:
        def _config_file():
            with open("config.json") as json_data_file:
                data = json.load(json_data_file)
            return data

        cls.username = _config_file().get("username")
        cls.password = _config_file().get("password")
        cls.categories = _config_file().get("categories")
        assert cls.password, " Please specify password in config file !"
        if not cls.username:
            letters = string.ascii_letters
            cls.username = ''.join(random.choice(letters) for i in range(10))
        cls.driver = webdriver.Chrome('./webdriver/chromedriver')
        cls.driver.implicitly_wait(5)
        cls.driver_wait = WebDriverWait(cls.driver, 10)
        # Wish list/ expected Shopping cart items
        cls.wish_cart = []
        cls.logged_in = False

    @classmethod
    def teardown_class(cls) -> None:
        cls.driver.quit()

    def test_01_homepage(self):
        """
        Open home page and assert correct site is loaded.
        """
        self.driver.get("https://www.demoblaze.com/")
        assert_that("STORE",
                    "Error Check homepage !"
                    ).is_equal_to(self.driver.title)



    @allure.step("Signup new random user")
    def test_02_signup(self):
        """
        Sign up a new generic user using random/hardcoded username and
        password from config file.
        """
        try:
            signup_btn = self.driver.find_element(By.XPATH, "//a[@id='signin2']")
            signup_btn.click()
            # Username input field
            self.driver_wait.until(ec.visibility_of_element_located(
                (By.XPATH, "//input[@id='sign-username']")
            )).send_keys(self.username, Keys.ENTER)
            # Password input field
            self.driver_wait.until(ec.visibility_of_element_located(
                (By.XPATH, "//input[@id='sign-password']")
            )).send_keys(self.password, Keys.ENTER)
            # Register button
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Sign up']")
            )).click()
            self._handle_alert("successful")
            allure.attach(f"User:{self.username} "
                          f"|Password{self.password}",
                          "signed up user info",
                          allure.attachment_type.TEXT)
        except (TimeoutException, NoSuchElementException, AssertionError):
            allure.attach(self.driver.get_screenshot_as_png(),
                          "signup_failed.png",
                          attachment_type=allure.attachment_type.PNG)
            raise

    @allure.step("login with the created random user")
    def test_03_login(self):
        """
        Login and check that the correct user is logged in
         using the created user from previous test
        """
        try:
            self.driver.switch_to.default_content()
            # Open login popup
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//a[@id='login2']")
            )).click()
            # Login details username
            self.driver_wait.until(ec.visibility_of_element_located(
                (By.XPATH, "//input[@id='loginusername']")
            )).send_keys(self.username, Keys.ENTER)
            # Login details password
            self.driver_wait.until(ec.visibility_of_element_located(
                (By.XPATH, "//input[@id='loginpassword']")
            )).send_keys(self.password, Keys.ENTER)
            # submit login button
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Log in']")
            )).click()
            time.sleep(2)
            # Check that logout button is visible
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//a[@id='logout2']")
            ))
            login_btn = self.driver.find_element(By.XPATH, "//a[@id='nameofuser']")

            assert_that(login_btn.text,
                        "Wrong username was displayed, check user details"
                        ).contains(self.username)
            self.__class__.logged_in = True
        except (TimeoutException, NoSuchElementException, AssertionError) as e:
            allure.attach(self.driver.get_screenshot_as_png(),
                          "login_failed.png",
                          attachment_type=allure.attachment_type.PNG)
            raise

    @allure.step("Select products and add to cart")
    def test_04_select_products_add_to_cart(self):
        """
        Select multiple products from different categories
        and add them to a wishing list cart.
        """
        if not self.logged_in:
            raise EnvironmentError("Client is not logged in.")
        try:
            for category in self.categories:
                # start always at Home screen.
                self.driver_wait.until(ec.element_to_be_clickable(
                    (By.XPATH, "(//a[@class='nav-link'])[1]")
                )).click()
                # Open product category
                self.driver_wait.until(ec.element_to_be_clickable(
                    (By.XPATH, f"//a[normalize-space()='{category}'][1]")
                )).click()
                # table of products
                time.sleep(2)
                products_table = self.driver.find_element(By.XPATH,
                                                          "//div[@id='tbodyid']")
                # Fetch all children
                all_children = products_table.find_elements(By.XPATH, './/a')
                # Only select 2 products
                products = [product.text for product in all_children
                            if product.accessible_name != ""][:2]
                self._add_to_cart(category, products)
                self.wish_cart.extend(products)
        except (NoSuchElementException, TimeoutException):
            allure.attach(self.driver.get_screenshot_as_png(),
                          "select_products.png",
                          attachment_type=allure.attachment_type.PNG)
            raise


    @allure.step("Check added items in cart and place order")
    def test_05_check_cart_place_order(self):
        """
        Check that cart got actually same selected products from the wish list cart.
        Place the order and validate the entered details with the order summary.
        """
        try:
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space()='Cart'][1]")
            )).click()
            price_total = self.driver_wait.until(ec.visibility_of_element_located(
                (By.XPATH, "//h3[@id='totalp']")
            )).text

            ordered_products_table = self.driver.find_element(By.ID,
                                                              "tbodyid")
            all_children = ordered_products_table.find_elements(By.XPATH, './/tr/td[2]')
            products_in_cart = set(product.text for product in all_children if product.text != "")

            assert_that(products_in_cart).is_not_none()
            # Compare expected ordered products with
            # actual found products in cart.
            assert_that(set(self.wish_cart)).is_equal_to(products_in_cart)

            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Place Order']")
            )).click()

            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "(//div[@class='modal-header'])[3]")
            ))
            self._fill_order_form_and_validate(price_total)

        except (TimeoutException, NoSuchElementException):
            allure.attach(self.driver.get_screenshot_as_png(),
                          "place_order.png",
                          attachment_type=allure.attachment_type.PNG)
            raise

    @allure.step("Fill place order form and validate results")
    def _fill_order_form_and_validate(self, price_total):
        """
        Open order form, fill it and submit it
        then validate the submitted values match the order summary.

        String:: price_total:Total price as displayed in the shopping cart.
        """
        try:
            today_date = datetime.now().date()
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//input[@id='name']")
            )).send_keys(self.username, Keys.ENTER)
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//input[@id='country']")
            )).send_keys("Norway", Keys.ENTER)
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//input[@id='city']")
            )).send_keys("Oslo", Keys.ENTER)
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//input[@id='card']")
            )).send_keys("12345678910123213", Keys.ENTER)
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//input[@id='card']")
            )).send_keys("12345678910123213", Keys.ENTER)
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//input[@id='month']")
            )).send_keys(today_date.month, Keys.ENTER)
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//input[@id='year']")
            )).send_keys(today_date.year, Keys.ENTER)
            self.driver_wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Purchase']")
            )).click()

            self.driver_wait.until(ec.visibility_of_element_located(
                (By.XPATH, "//h2[normalize-space()"
                           "='Thank you for your purchase!']")
            ))

            summary = self.driver_wait.until(ec.visibility_of_element_located(
                (By.XPATH, "//p[contains(@class,'lead text-muted')]")
            )).text
            summary_values = dict([x.split(":") for x in summary.split("\n")])
            allure.attach(str(summary_values),
                          "Placed order info",
                          allure.attachment_type.TEXT)
            assert_that(summary_values.get('Amount')
                        ).contains(price_total)
            assert_that(summary_values.get('Card Number')
                        ).contains("12345678910123213")
            assert_that(summary_values.get("Name")
                        ).contains(self.username)

            # Commented as website has one month earlier date
            # assert_that(today_date.strftime("%d/%m/%y")).is_in(summary_values.get("Date"))
        except (NoSuchElementException, TimeoutException) :
            allure.attach(self.driver.get_screenshot_as_png(),
                          "order_form.png",
                          attachment_type=allure.attachment_type.PNG)
            raise

    @allure.step("Add products from category to cart")
    def _add_to_cart(self, category, products):
        """
        Iterate through list of products and
         locate every product by text then add it to the cart.

        String ::category: Phone,Laptop
        WebElementList ::products: fetched WebElements from category

        """
        try:
            for product in products:
                assert_that(product,
                            "Product name is empty !"
                            ).is_not_equal_to("")
                self.driver_wait.until(ec.element_to_be_clickable(
                    (By.LINK_TEXT, category)
                )).click()
                time.sleep(1)
                self.driver_wait.until(ec.element_to_be_clickable(
                    (By.LINK_TEXT, product)
                )).click()

                self.driver_wait.until(ec.element_to_be_clickable(
                    (By.XPATH, "//a[normalize-space()='Add to cart']")
                )).click()
                self._handle_alert("added")
                time.sleep(1)
                # Navigate back to Home screen.
                self.driver_wait.until(ec.element_to_be_clickable(
                    (By.XPATH, "(//a[@class='nav-link'])[1]")
                )).click()

        except (TimeoutException, NoSuchElementException):
            allure.attach(self.driver.get_screenshot_as_png(),
                          "shopping_cart_fail.png",
                          attachment_type=allure.attachment_type.PNG)
            ValueError(f"Unable to add product to shopping cart")
            raise

    @allure.step("Check alert and accept it")
    def _handle_alert(self, alert_text):
        """
        Switch to pop up alert and accept it,
        and validate that the intended confirmation message is displayed in the alert.

        String:: alert_text: popup alert text to validate against.
        """
        try:
            self.driver_wait.until(ec.alert_is_present())
            result_txt = self.driver.switch_to.alert.text
            assert_that(result_txt).contains(alert_text)
            self.driver.switch_to.alert.accept()
        except (NoSuchElementException, TimeoutException, AssertionError) as e:
            allure.attach(self.driver.get_screenshot_as_png(),
                          "alert_fail.png",
                          attachment_type=allure.attachment_type.PNG)
            raise ValueError(f"Alert is not visible or provided "
                             f"text not in alert text !, stacktrace {e}")


if __name__ == '__main__':
    # Generate Allure test results.
    # pytest main.py --alluredir=./allure_results
    pytest.main()
