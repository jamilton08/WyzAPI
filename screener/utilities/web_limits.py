import sys
import requests
from bs4 import BeautifulSoup

# -----------------------
# Method 1: Detect using Requests & BeautifulSoup
# -----------------------
def detect_with_requests(url):
    result = {}
    try:
        # Make a GET request and follow redirects.
        r = requests.get(url, allow_redirects=True, timeout=10)
        result['status_code'] = r.status_code
        # Save final URL (may be different if redirected).
        result['final_url'] = r.url

        # Check HTTP status codes.
        if r.status_code in (401, 403):
            result['status_indicator'] = True
        else:
            result['status_indicator'] = False

        # If the final URL contains typical login keywords, mark that as a hint.
        if 'login' in r.url.lower() or 'signin' in r.url.lower():
            result['redirect_indicator'] = True
        else:
            result['redirect_indicator'] = False

        # Parse the returned HTML.
        soup = BeautifulSoup(r.text, 'html.parser')
        # Look for password fields.
        result['password_field'] = bool(soup.find('input', attrs={'type': 'password'}))

        # Check if the content contains phrases that suggest login/authentication.
        lower_text = r.text.lower()
        result['text_indicator'] = ('please log in' in lower_text or 
                                    'sign in' in lower_text or 
                                    'login' in lower_text)
    except Exception as e:
        result['error'] = str(e)
    return result

# -----------------------
# Method 2: Detect using Selenium (headless Chrome)
# -----------------------
def detect_with_selenium(url):
    result = {}
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        result['error'] = "Selenium is not installed. Please run 'pip install selenium'."
        return result

    options = Options()
    options.headless = True
    # Initialize the Chrome WebDriver (ensure chromedriver is in PATH)
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        result['error'] = "Error initializing Selenium WebDriver: " + str(e)
        return result

    try:
        driver.get(url)
        driver.implicitly_wait(5)  # wait for page load
        result['final_url'] = driver.current_url

        # Check for password fields in the page.
        password_elements = driver.find_elements_by_css_selector("input[type='password']")
        result['password_field'] = len(password_elements) > 0

        # Look for login-related keywords in the title.
        result['title_indicator'] = ("login" in driver.title.lower() or "signin" in driver.title.lower())

        # Look for login-related keywords in the page source.
        page_source = driver.page_source.lower()
        result['text_indicator'] = ("login" in page_source or "signin" in page_source)

        driver.quit()
    except Exception as e:
        result['error'] = str(e)
        driver.quit()
    return result

# -----------------------
# Combine the Heuristics to Decide
# -----------------------
def analyze_detection(req_result, selenium_result):
    login_required = False
    reasons = []

    # Check status code from Requests.
    if req_result.get("status_indicator"):
        login_required = True
        reasons.append(f"HTTP status code {req_result.get('status_code')} indicates restricted access.")
    
    # Check the results from the Requests-based analysis.
    if req_result.get("redirect_indicator"):
        login_required = True
        reasons.append("HTTP redirect to a login-related URL: " + req_result.get("final_url", ""))
    if req_result.get("password_field"):
        login_required = True
        reasons.append("Found a password input field in the raw HTML.")
    if req_result.get("text_indicator"):
        login_required = True
        reasons.append("The page content includes login-related words (e.g., 'login', 'sign in').")
    
    # Check the Selenium-based analysis.
    if selenium_result.get("password_field"):
        login_required = True
        reasons.append("Selenium: Detected a password input field on the page.")
    if selenium_result.get("title_indicator"):
        login_required = True
        reasons.append("Selenium: The page title suggests it is a login page.")
    if selenium_result.get("text_indicator"):
        login_required = True
        reasons.append("Selenium: The page content contains login keywords.")

    # Append any errors.
    if req_result.get("error"):
        reasons.append("Requests error: " + req_result.get("error"))
    if selenium_result.get("error"):
        reasons.append("Selenium error: " + selenium_result.get("error"))

    return login_required, reasons


def require_login(url):
    """
    Main function to check if a URL requires login.
    It uses both Requests and Selenium for detection.
    """
    req_result = detect_with_requests(url)
    selenium_result = detect_with_selenium(url)

    login_required, reasons = analyze_detection(req_result, selenium_result)

    return {
        "login_required": login_required,
        "reasons": reasons,
        "requests_result": req_result,
        "selenium_result": selenium_result
    }


