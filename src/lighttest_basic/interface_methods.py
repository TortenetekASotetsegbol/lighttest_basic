import inspect
from dataclasses import dataclass
from enum import Enum, unique
from functools import wraps
from pathlib import Path

from lighttest_supplies import date_methods
from lighttest_supplies.timers import Utimer

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common import exceptions, WebDriverException, TimeoutException
from lighttest_supplies.general import create_logging_structure, create_logging_directory
from faker import Faker
from lighttest_basic.datacollections import CaseStep
from lighttest_basic.light_exceptions import NoneAction
from selenium.webdriver import Chrome

fake = Faker()


class CaseManagement:
    def __init__(self,  driver: Chrome, screenshots_container_directory: str = "C:\Screenshots"):
        self.local_click_xpaths: set[str] = {}
        self.local_field_xpaths: set[str] = {}
        self.teststep_count = 0
        self.testcase_failed: bool = False
        self.error_count: int = 0
        self.screenshots_container_directory: str = screenshots_container_directory
        self.steps_of_reproduction: dict = {}
        self.casebreak = False
        self.combobox_parent_finding_method_by_xpaths: set[str] = {}
        self.error_in_case = False
        self.driver = driver
        self.action_driver = ActionChains(self.driver)

    def set_combobox_parent_finding_method_by_xpath(self, *xpaths: str):
        """
        @param: global_combobox_parent_finding_method_by_xpath the value of this param determinate
                how to find combobox parent webelement
        """
        self.combobox_parent_finding_method_by_xpaths = set(xpaths)

    @staticmethod
    def set_global_field_xpath(*xpaths: str):
        """
        placeholder

        Arguments:
            *xpaths: the value of this param determinate
                    how to find fields in global.

        Format:
            the paramter in the xpath need to be the following: __param__

        Example:
            set_case_field_xpath("//*[text()='__param__']/parent::*/descendant::input",
            "//*[text()='__param__']/parent::*/descendant::textarea")

        """
        MiUsIn.global_field_xpaths = set(xpaths)

    def set_case_field_xpath(self, *xpaths: str):
        """
        placeholder

        Arguments:
            *xpaths: the value of this param determinate
                    how to find fields in the level of testcase.

        Format:
            the paramter in the xpath need to be the following: __param__

        Example:
            set_case_field_xpath("//*[text()='__param__']/parent::*/descendant::input",
            "//*[text()='__param__']/parent::*/descendant::textarea")

        """
        self.local_field_xpaths = set(xpaths)

    @staticmethod
    def set_global_click_xpaths(*xpaths: str):
        """
        placeholder

        Arguments:
            *xpaths: the value of this param determinate
                    how to find clickable webelements in global.

        Format:
            the paramter in the xpath need to be the following: __param__

        Example:
            set_case_field_xpath("//*[text()='__param__']/parent::*/descendant::fa-icon",
            "//*[text()='__param__']/parent::*/descendant::button")

        """
        MiUsIn.global_click_xpaths = set(xpaths)

    def set_case_click_xpaths(self, *xpaths: str):
        """
        placeholder

        Arguments:
            *xpaths: the value of this param determinate
                    how to find clickable webelements in the level of testcase.

        Format:
            the paramter in the xpath need to be the following: __param__

        Example:
            set_case_field_xpath("//*[text()='__param__']/parent::*/descendant::fa-icon",
            "//*[text()='__param__']/parent::*/descendant::button")

        """
        self.local_click_xpaths = set(xpaths)

    @staticmethod
    def set_global_combobox_parent_finding_method_by_xpath(*xpaths: str):
        '''
        field_xpath : it set the global_combobox_parent_finding_method_by_xpath class variable
        '''
        MiUsIn.global_combobox_parent_finding_method_by_xpaths = set(xpaths)


@unique
class Values(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


@unique
class InnerStatics(Enum):
    PARAM: str = "__param__"
    FIND_LABEL_BY_PARAM: str = "//*[text()='__param__']"
    IN_PARENT_FIND_LABEL_BY_PARAM: str = ".//*[contains(text(), '__param__')]"


@dataclass(kw_only=True)
class TestStep:
    case_object: CaseStep
    xpath: str
    step_data: str = ""


class ClickMethods:
    global_click_xpaths: set[str] = {}

    def __init__(self):
        pass

    def click(self, xpath: str = None, identifier: str = None, contains: bool = True) -> WebElement:
        """
        Mimic a mouse click event as a case-step.

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        Arguments:
            xpath: a clickable webelement's xpath expression
            identifier: a visible static text(label) on the website
            contains: if true and  the identifier field is used,
                than it accept any webelement which is contains the identifier

        examples:

        """
        match (identifier is not None, contains):
            case (True, False):
                xpath = f"//*[text()='{identifier}']"
            case (True, True):
                xpath = f"//*[contains(text(),'{identifier}')]"
        clickable_webelement: WebElement = self.driver.find_element(by=By.XPATH, value=xpath)
        clickable_webelement.click()
        return clickable_webelement

    def click_by_param(self, identifier: str, xpath: str = None) -> WebElement:
        """
        Mimic a mouse click.

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.


        Arguments:
            xpath: a clickable webelement's parametric xpath expression
            identifier: the paramteric indetifier in the click_xpath expression


        examples:

        """
        created_click_xpath: str = self._create_click_xpath(identifier)
        if xpath is not None:
            created_click_xpath = xpath.replace(InnerStatics.PARAM.value, identifier)
        elif created_click_xpath == "" and xpath is None:
            raise TypeError("None value in argument: 'parametric_xpath'")
        clickable_webelement = self.driver.find_element(by=By.XPATH, value=created_click_xpath)
        clickable_webelement.click()
        return clickable_webelement

    def click_by_webelement(self, webelement: WebElement, identifier: str = "") -> WebElement:
        """
        Mimic a mouse click.

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.


        Arguments:
            webelement: a webelement object
            identifier: an optional name of the webelement.


        examples:

        """
        if webelement is None:
            raise WebDriverException("expected a webelement object, received None type object")
        webelement.click()

        return webelement

    def double_click(self, xpath: str = None, identifier: str = None) -> WebElement:
        """
        Mimic a mouse click event as a case-step.

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        Arguments:
            xpath: a clickable webelement's xpath
            identifier: a visible static text(label) on the website


        examples:

        """

        if identifier is not None:
            xpath = f"//*[text()='{identifier}']"
        clickable_webelement = self.driver.find_element(by=By.XPATH, value=xpath)
        MiUsIn.action_driver.double_click(on_element=clickable_webelement).perform()

        return clickable_webelement

    def _create_click_xpath(self, param: str):
        if len(self.local_click_xpaths) != 0:
            field_xpaths: set[str] = set(
                parametric_xpath.replace(InnerStatics.PARAM.value, param) for parametric_xpath in
                self.local_click_xpaths)
            return "|".join(field_xpaths)

        elif len(MiUsIn.global_click_xpaths) != 0:
            field_xpaths: set[str] = set(
                parametric_xpath.replace(InnerStatics.PARAM.value, param) for parametric_xpath in
                MiUsIn.global_click_xpaths)
            return "|".join(field_xpaths)

        else:
            return ""


class FieldMethods:
    global_field_xpaths: set[str] = {}

    def __init__(self):
        pass

    def fill_field(self, xpath: str, data: str) -> WebElement:
        """
        Mimic the event of filling a field on a webpage.

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        Arguments:
            xpath: The field webelement's xpath
            data: the string you want to put into the specified field.
        """

        if data is None:
            raise NoneAction
        field = self.driver.find_element(by=By.XPATH, value=xpath)
        field.click()
        field.clear()
        field.send_keys(data)

        return field

    def fill_field_by_param(self, identifier: str, xpath: str = None, data="") -> WebElement:
        """
        Mimic the event of filling a field on a webpage.

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        Arguments:
            xpath: The field webelement's parametric xpath
            data: the string you want to put into the specified field.
            identifier: the paramteric indetifier in the field_xpath expression
        """
        if data is None:
            raise NoneAction
        created_field_xpath: str = self._create_field_xpath(identifier)
        if xpath is not None:
            created_field_xpath = xpath.replace(InnerStatics.PARAM.value, identifier)
        elif created_field_xpath == "" and xpath is None:
            raise TypeError("None value in field: 'field_xpath'")
        field = self.driver.find_element(by=By.XPATH, value=created_field_xpath)
        field.click()
        field.clear()
        field.send_keys(data)

        return field

    def fill_form(self, **kwargs):
        """
        this function is useful when want to comletea form with many input fields.
        Just add kw names as fieldnames and kw values as input datas.
        if the field's name contains spaces, replace those with '_'

        Example:
            fill_form(Name='John Doe', Date_of_birth='1992.01.20')
        """
        for key, value in kwargs.items():
            self.fill_field_by_param(identifier=str(key).replace("_", " "), data=value)
        return kwargs

    def _create_field_xpath(self, param: str):
        if len(self.local_field_xpaths) != 0:
            field_xpaths = [field_findig_method.replace(InnerStatics.PARAM.value, param) for field_findig_method in
                            self.local_field_xpaths]
            return "|".join(field_xpaths)

        elif len(MiUsIn.global_field_xpaths) != 0:
            field_xpaths = [field_findig_method.replace(InnerStatics.PARAM.value, param) for field_findig_method in
                            MiUsIn.global_field_xpaths]
            return "|".join(field_xpaths)
        else:
            return ""

    def insert_file_path(self, data: str, xpath: str = "//input[@type='file']"):
        """
        Mimic the event of filling a field on a webpage.

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        Arguments:
            xpath: The field wehre you wnt to put the file-path
            data: the file-path you want to put into the specified field.
        """

        if data is None:
            raise NoneAction
        file_path: str = str(Path(data).absolute())
        file_path_field: WebElement = self.driver.find_element(by=By.XPATH, value=xpath)
        self.driver.execute_script('arguments[0].style.display = "block";', file_path_field)
        file_path_field.send_keys(file_path)


class ValueValidation(FieldMethods):
    global_webalert_xpath: str = None

    def __init__(self):
        pass

    @staticmethod
    def _create_alert_xpath(alert_message: str):
        if MiUsIn.global_webalert_xpath is None:
            created_alert_xpath = f"//*[contains(text(),'{alert_message}')]"
        else:
            created_alert_xpath = MiUsIn.global_webalert_xpath

        return created_alert_xpath

    def expected_condition(self, timeout_in_seconds: float, expected_condition: expected_conditions = None,
                           until_not: bool = False, webelement_is_visible=False, webelement_is_clickable=False,
                           alert: str = None, xpath=None):
        """

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        Arguments:
           timeout_in_seconds: Set the timer. If the expected condition is not happening under that timeperiod,
                               the test-step failed
           expected_condition: the condition, you waiting for.
           until_not: it negate the condition. for example: if you were waited for the appearence of an element,
                       with the until_not = true setting you wait for the disappearence of the element
           webelement_is_visible: set the expected condition for the visibility of an element.
                                   if the webelement described by the field_xpath is not appearing before the timeout,
                                   the step failed
           webelement_is_clickable: set the expected condition to clickability of an element.
                                   if the webelement described by the field_xpath is not became clickable before the timeout,
                                   the step failed
           expected_condition: It can be anything. It is a unique condition
                                bordered by the webdriver expected_conditions options

       """

        chosen_expected_condition = None

        if expected_condition is not None:
            chosen_expected_condition = expected_condition
        elif webelement_is_visible:
            chosen_expected_condition = expected_conditions.visibility_of_element_located((By.XPATH, xpath))
        elif webelement_is_clickable:
            chosen_expected_condition = expected_conditions.element_to_be_clickable((By.XPATH, xpath))
        elif alert is not None:
            xpath = MiUsIn._create_alert_xpath(alert)
            chosen_expected_condition = expected_conditions.visibility_of_element_located((By.XPATH, xpath))

        try:
            if not until_not:
                return WebDriverWait(driver=self.driver, timeout=timeout_in_seconds).until(chosen_expected_condition)

            elif until_not:
                return WebDriverWait(driver=self.driver, timeout=timeout_in_seconds).until_not(
                    chosen_expected_condition)

        except TimeoutException:
            return False

    def get_css_attribute(self, xpath: str, attribute: str) -> str:
        """
        return a selected attribute of a webelement

        Arguments:
            xpath: the webelement's xpath
            attribute: teh attribute of the webelement you want to get
        """
        atr_value = None

        webelement = self.driver.find_element(By.XPATH, value=xpath)
        atr_value = webelement.value_of_css_property(attribute)

        return atr_value

    def match_style(self, xpath: str, identifier: str, data: str) -> object:
        """
        check a style param like color, font type, style, etc.

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        Arguments:
            xpath: the visible website element's xpath expresion
            data: the expected style parameter's value
            identifier: the style attribute's name in the css
        """
        actual_value: str = MiUsIn.get_css_attribute(xpath=xpath, attribute=identifier)
        if actual_value != data:
            raise ValueError({"Expected_value": data, "actual_value": actual_value})

    def check_style(self, xpath: str, attribute: str, expected_value: str):
        if self.casebreak:
            return None
        try:
            actual_value: str = MiUsIn.get_css_attribute(xpath=xpath, attribute=attribute)
            if actual_value != expected_value:
                raise ValueError
        except (exceptions.WebDriverException, ValueError):
            return False

        if actual_value == expected_value:
            return True

    def get_static_text(self, xpath: str = None, by_label: str = None) -> str:

        if by_label is not None:
            xpath = f"//*[text()='{by_label}']"

        text: str = self.driver.find_element(By.XPATH, value=xpath).text

        return text

    def get_field_text(self, xpath: str = None, by_label: str = None) -> str:

        if by_label is not None:
            xpath = f"//*[text()='{by_label}']"

        text: str = self.driver.find_element(By.XPATH, value=xpath).get_property("value")

        return text

    def check_text(self, expected_value: str, xpath: str = None, by_label: str = None) -> bool:
        if self.casebreak:
            return None
        try:
            actual_value = self.get_static_text(xpath=xpath, by_label=by_label)
            if actual_value != expected_value:
                raise ValueError
        except (exceptions.WebDriverException, ValueError):
            return False

        return True

    def match_text(self, data: str, xpath: str = None, identifier: str = None) -> bool:
        """
        check a style param like color, font type, style, etc.

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        Arguments:
            xpath: a label or an inputfield's xpath expresion
            data: the expected text value
            identifier: if it is a static text (a label) can use only the label instead of the full xpath expression

        Return:
            True, if the actual text and the expected test matched
        """
        actual_value: str = MiUsIn.get_static_text(xpath=xpath, by_label=identifier)
        if data is None:
            data = ""
        if actual_value == data:
            return True
        else:
            return False

    def parametric_field_value_match(self, data: str, identifier: str, xpath: str = None) -> bool:
        """

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        """
        created_field_xpath: str = self._create_field_xpath(identifier)
        if xpath is not None:
            created_field_xpath = xpath.replace(InnerStatics.PARAM.value, identifier)
        elif created_field_xpath == "" and xpath is None:
            raise TypeError("None value in field: 'field_xpath'")
        actual_value: str = MiUsIn.get_field_text(xpath=created_field_xpath, by_label=None)
        if data is None:
            data = ""
        if actual_value == data:
            return True
        else:
            return False

    def match_form_field_values(self, **kwargs) -> dict[str:bool]:
        """
        this function is useful when want to check a full form with loaded inputfield values.
        Just add kw names as fieldnames and kw values as expexted values.
        if the field's name contains spaces, replace those with '_'

        Example:
            match_form_field_values(Name='John Doe', Date_of_birth='1992.01.20')
        """
        result: dict[str:bool] = dict()
        for key, value in kwargs.items():
            result.update({key: self.parametric_field_value_match(identifier=str(key).replace("_", " "), data=value)})

        return result

    def wait_till_website_ready(self, timeout: float = 10, identifier: str = "Not specified"):

        """
        Wait till the website is fully loaded. It use the readyState document.
        If the website doesn't load under the timeout parameter, it recognised and logged as an error.

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, this the method return without any action.

        Arguments:
            timeout: maximum accepted loading time. Above this recognised as an error.
            identifier: you can describe the website or website part that you check the loading time.
        """

        @Utimer.bomb(timeout_in_seconds=timeout)
        def get_ready_state():
            state: bool = self.driver.execute_script("return document.readyState") == "complete"
            return state

        try:
            get_ready_state()
        except TimeoutError:
            raise WebDriverException("Website not fully loaded within the specified timeout period")


class DropDownMethods:
    global_combobox_parent_finding_method_by_xpaths: set[str] = {}

    def _find_combobox_list_element(self, input_field_xpath: str, dropdown_element_text: str):
        if len(self.combobox_parent_finding_method_by_xpaths) > 0:
            parent_webelement_xpaths: set = self.combobox_parent_finding_method_by_xpaths
        elif len(MiUsIn.global_combobox_parent_finding_method_by_xpaths) > 0:
            parent_webelement_xpaths: set = MiUsIn.global_combobox_parent_finding_method_by_xpaths

        parent_webelement = self.driver.find_element(by=By.XPATH,
                                                     value=self._combobox_parent_xpath(input_field_xpath,
                                                                                       parent_webelement_xpaths))
        list_element = parent_webelement.find_element(by=By.XPATH,
                                                      value=InnerStatics.IN_PARENT_FIND_LABEL_BY_PARAM.value.replace(
                                                          InnerStatics.PARAM.value, dropdown_element_text))

        return list_element

    def select_combobox_element(self, xpath: str, data: str = "") -> WebElement:
        """
        click on a combobox elements.


        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        Arguments:
            xpath: the combobox's input-field xpath expression
            data: an element in the dropdown you want to click
        """

        self.fill_field(xpath=xpath, data=data)

        list_element = self._find_combobox_list_element(xpath, data)
        list_element.click()

        return list_element

    def select_combobox_element_by_param(self, identifier: str, xpath: str = None,
                                         data: str = "") -> WebElement:
        """
        use the combobox_parent_finding_method to click on a combobox elements

        Special Keywords:
            critical_step: if true and this case-step fail, the remain case-steps will be skipped

            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful

            step_description: optional. You can write a description, what about this step.

            skip: if true, the method return without any action.

        Arguments:
            data: an element in the dropdown you want to click
            identifier: the paramteric indetifier in the field_xpath expression
            xpath: the paramteric parametric representation of the input-field xpath.
                    It can use only with the identifier argument.
        """

        self.fill_field_by_param(xpath=xpath, data=data, identifier=identifier)

        if xpath is None:
            xpath = self._create_field_xpath(identifier)

        list_element = self._find_combobox_list_element(xpath, data)
        list_element.click()
        return list_element

    def _combobox_parent_xpath(self, input_field_xpath: str, parent_webelement_xpaths: list):
        field_list: list = input_field_xpath.split("|")
        all_parent_xpaths: set = set()
        for field_xpath in field_list:
            new_parent_webelement_xpaths: set = {
                f"{field_xpath}{find_parent_parameter}" for find_parent_parameter in parent_webelement_xpaths}

            all_parent_xpaths.update(new_parent_webelement_xpaths)
        combobox_parent_xpath: str = "|".join(all_parent_xpaths)
        return combobox_parent_xpath


class NavigationMethods:
    bomb_timeout: float = 1

    def __init__(self):
        pass

    def jump_webpage(self, url: str) -> None:
        """
        the browser navigate to the desired url.
        """
        self.driver.get(url)

    @staticmethod
    def set_bomb_timeout(timeout: float) -> None:
        """
        Set the timeout value for the bomb decorator.
        """
        MiUsIn.bomb_timeout = timeout

    @Utimer.bomb(timeout_in_seconds=bomb_timeout)
    def jump_to_recent_window_base(self) -> bool:
        if self.casebreak:
            return

        current_window_handle = self.driver.current_window_handle
        recent_window = self.driver.window_handles[-1]
        if current_window_handle != recent_window:
            self.driver.switch_to.window(recent_window)

            return True
        return False

    def jump_to_recent_window(self, timeout: float = 1) -> None:
        if self.casebreak:
            return

        if timeout != 1:
            MiUsIn.set_bomb_timeout(timeout)
        try:
            self.jump_to_recent_window_base()
            print("switched to the recent window")
        except TimeoutError:
            print("failed to switch to the recent windows")

        if timeout != 1:
            MiUsIn.set_bomb_timeout(1)


class DriverManagement:

    def __init__(self, driver: Chrome):
        self.driver: Chrome = driver
        self.action_driver: ActionChains = ActionChains(driver=self.driver)

    def set_implicitly_wait(self, time_to_wait: float) -> None:
        """
        for every event (example: find a webelement), the webdriver will wait till maximum the value of the time_to_wait
        """
        self.driver.implicitly_wait(time_to_wait=time_to_wait)


class MiUsIn(CaseManagement, ValueValidation, ClickMethods, DropDownMethods, NavigationMethods, DriverManagement):
    """
    MiUsIn stand for Mimic User interactions.
    Variables:
        driver: this is the google chrome's webdriver. Every browser interaction use this particular driver.
        bomb_timeout: Its defining how much time need the @bomb decorator to raise timeout error
        global_combobox_parent_finding_method_by_xpath: the value of this param determinate
                how to find combobox parent webelement
    """

    def __init__(self, driver: Chrome, fullsize_windows=True,
                 screenshots_container_directory: str = "C:\Screenshots"):
        """
        placeholder

        Arguments:
            fullsize_windows: If true, the browser's windows will b full-sized
            screenshots_container_directory: If during a testcase it find an error
                    the screenshot taken of the error will be stored and catalogised in that directory
        """
        super().__init__(screenshots_container_directory=screenshots_container_directory, driver=driver)
        self.driver.implicitly_wait(time_to_wait=5)

        if fullsize_windows:
            self.driver.maximize_window()

    def __del__(self):
        pass

    def stack_dict_item(self, updater: dict, current_dict: dict):

        if list(updater.keys())[0] not in list(current_dict.keys()):
            current_dict.update(updater)
        else:
            current_dict[list(updater.keys())[0]] += updater[list(updater.keys())[0]]

    def _take_a_screenshot(self):
        """
        Take a screenshot and save it in a directory structure.

        directory structure:
            C:/screenshots/automatically generated project directory from the webpage URL/
            generated date directory/generated hour directory/screenshot.png
        """
        project_name = self.driver.current_url \
            .split("//")[-1] \
            .split("/")[0] \
            .replace(".", "_") \
            .replace("www_", "")

        file_name: str = f'{date_methods.get_current_time()}.png'
        create_logging_directory(self.screenshots_container_directory, project_name)
        screenshot_path = create_logging_structure(self.screenshots_container_directory, project_name)
        self.driver.save_screenshot(f"{screenshot_path.absolute()}/{file_name}")

    def casebreak_alarm(self, critical_step: bool):
        if critical_step:
            self.casebreak = True

    def __add_default_field_xpaths(self, label: str, xpaths: list) -> None:
        """
        extend the received list with the default field xpaths.
        These xpaths containing the currently searched field's param

        Arguments:
            label: the currently searched field's param
            xpaths: a list of field_xpaths

        Examples:

        """
        default_filed_xpaths: [str] = [f"//*[@*='{label}']"]
        xpaths.extend(default_filed_xpaths)

    def _get_input_field_xpath(self, find_by_label: str):
        return f"//*[text()='{find_by_label}']{self._create_field_xpath()}"

    def press_key(self, identifier: str) -> None:
        """
        Mimic a key peress.

        Arguments:
            identifier: a key-code whics is identifie a key
            critical_step: if true and this case-step fail, the remain case-steps will be skipped
            step_positivity: determine what is the expected outcome of the step. If positive, it must be successful
            step_description: optional. You can write a description, what about this step.

        Identifiers:
            ENTER: 'enter',
            TAB: 'tab',
            ESCAPE: 'esc'

        Examples:

        """
        match identifier:
            case "enter":
                self.action_driver.send_keys(Keys.ENTER).perform()
            case "tab":
                self.action_driver.send_keys(Keys.TAB).perform()
            case "esc":
                self.action_driver.send_keys(Keys.ESCAPE).perform()
            case _:
                raise KeyError(f"Unknown key: '{identifier}'")
