import random
import subprocess
import time
import json
import webbrowser
import requests
import io
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains

def random_sleep(min_seconds=1, max_seconds=3):
    """Sleep for a random amount of time between min_seconds and max_seconds."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def get_captcha2_apikey():
    """Retrieve the 2Captcha API key."""
    with open('captcha2_apikey.txt', 'r') as file:
        return file.read().strip()

def get_redbubble_username():
    """Retrieve the Redbubble username."""
    with open('redbubble_username.txt', 'r') as file:
        return file.read().strip()
        
def get_redbubble_password():
    """Retrieve the Redbubble password."""
    with open('redbubble_password.txt', 'r') as file:
        return file.read().strip()

def move_mouse_to_element(driver, element):
    """Move the mouse to the element with human-like behavior."""
    action = ActionChains(driver)
    action.move_to_element(element)
    
    # Adding some randomness to the movement
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    
    action.move_by_offset(offset_x, offset_y)
    action.perform()
    
    # Add a random sleep to mimic human behavior
    time.sleep(random.uniform(0.5, 1.5))

def start_docker_container(image_name, container_name, port_mapping, vnc_port):
    """Run a docker container from the image."""
    try:
        subprocess.check_call([
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{port_mapping}:4444",
            "-p", f"{vnc_port}:7900",  # Expose VNC port to watch the test
            "--shm-size=2g",
            image_name
        ])
        print("Docker container started.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start Docker container: {str(e)}")
        return False
    return True

def stop_docker_container(container_name):
    """Stop and remove the docker container."""
    try:
        subprocess.check_call(["docker", "stop", container_name])
        subprocess.check_call(["docker", "rm", container_name])
        print("Docker container stopped and removed.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to stop/remove Docker container: {str(e)}")

def save_cookies(driver):
    """Save cookies to a file."""
    cookies = driver.get_cookies()
    with open("cookies.json", "w") as outfile:
        json.dump(cookies, outfile)
    print("Cookies saved.")

def load_cookies(driver):
    """Load cookies from a file."""
    with open("cookies.json", "r") as infile:
        cookies = json.load(infile)
    for cookie in cookies:
        driver.add_cookie(cookie)
    print("Cookies loaded.")

def solve_captcha(api_key, site_key, url):
    """Send captcha solving request to 2Captcha."""
    response = requests.post(
        'http://2captcha.com/in.php',
        data={
            'key': api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': url
        }
    ).text
    
    if 'ERROR' in response:
        raise Exception('CAPTCHA solving request error: ' + response)
    
    captcha_id = response.split('|')[1]

    # Wait for 2Captcha to solve the captcha
    for _ in range(40):
        time.sleep(5)
        response = requests.get(
            'http://2captcha.com/res.php',
            params={
                'key': api_key,
                'action': 'get',
                'id': captcha_id
            }
        ).text
        if response == 'CAPCHA_NOT_READY':
            continue
        if 'ERROR' in response:
            raise Exception('CAPTCHA solving error: ' + response)
        return response.split('|')[1]

    raise Exception('CAPTCHA solving timeout.')

def solve_grid_captcha(api_key, driver):
    """Solve grid CAPTCHA using 2Captcha."""
    captcha_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='recaptcha challenge']")))
    driver.switch_to.frame(captcha_element)
    captcha_image = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.rc-imageselect-table")))
    location = captcha_image.location
    size = captcha_image.size
    screenshot = driver.get_screenshot_as_png()
    screenshot = Image.open(io.BytesIO(screenshot))
    captcha_screenshot = screenshot.crop((location['x'], location['y'], location['x'] + size['width'], location['y'] + size['height']))
    captcha_screenshot.save('captcha.png')

    with open('captcha.png', 'rb') as captcha_file:
        response = requests.post(
            'http://2captcha.com/in.php',
            files={'file': captcha_file},
            data={'key': api_key, 'method': 'post'}
        ).text

    if 'ERROR' in response:
        raise Exception('CAPTCHA solving request error: ' + response)
    
    captcha_id = response.split('|')[1]

    for _ in range(40):
        time.sleep(5)
        response = requests.get(
            'http://2captcha.com/res.php',
            params={
                'key': api_key,
                'action': 'get',
                'id': captcha_id
            }
        ).text
        if response == 'CAPCHA_NOT_READY':
            continue
        if 'ERROR' in response:
            raise Exception('CAPTCHA solving error: ' + response)
        return response.split('|')[1]

    raise Exception('CAPTCHA solving timeout.')

def login(driver):
    """Perform the login process."""
    driver.get("https://www.redbubble.com/auth/login")
    print("Navigated to login page.")
    random_sleep()

    redbubble_username = get_redbubble_username()
    username_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "ReduxFormInput1")))
    for char in redbubble_username:
        username_field.send_keys(char)
        random_sleep(0.1, 0.3)
    print("Entered username.")
    random_sleep()
    
    redbubble_password = get_redbubble_password()
    password_field = driver.find_element(By.ID, "ReduxFormInput2")
    for char in redbubble_password:
        password_field.send_keys(char)
        random_sleep(0.1, 0.3)
    print("Entered password.")
    random_sleep()
    password_field.send_keys(Keys.RETURN)
    print("Submitted login form.")
    random_sleep()

def handle_password_prompt(driver):
    """Handle the password save prompt if it appears."""
    try:
        save_password_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save') or @aria-label='Save']"))
        )
        move_mouse_to_element(driver, save_password_button)
        save_password_button.click()
        print("Clicked on the 'Save' button for password prompt.")
    except (TimeoutException, NoSuchElementException):
        print("No password save prompt found, or it didn't appear.")

def handle_captcha(driver, api_key, captcha_site_key):
    """Handle the CAPTCHA if it appears."""
    try:
        captcha_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title='reCAPTCHA']"))
        )
        driver.switch_to.frame(captcha_iframe)
        print("CAPTCHA iframe found.")
    except (TimeoutException, NoSuchElementException):
        print("No CAPTCHA iframe found, skipping CAPTCHA handling.")
        return
    
    try:
        print("Attempting to solve CAPTCHA...")
        captcha_solution = solve_captcha(api_key, captcha_site_key, driver.current_url)
        print(f"Captcha solution: {captcha_solution}")
        
        driver.switch_to.default_content()  # Switch back to main content
        recaptcha_response = driver.find_element(By.ID, 'g-recaptcha-response')
        driver.execute_script(f"arguments[0].innerHTML='{captcha_solution}';", recaptcha_response)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", recaptcha_response)
        
        submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "submit-button")))
        move_mouse_to_element(driver, submit_button)
        submit_button.click()
        print("Submitted CAPTCHA solution.")
    except Exception as e:
        print(f"Error solving CAPTCHA: {str(e)}")
        raise

def close_popup_ad(driver):
    """Close the popup ad if it appears."""
    try:
        close_popup_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Close']"))
        )
        print(f"Popup element found: {close_popup_button}")
        move_mouse_to_element(driver, close_popup_button)
        close_popup_button.click()
        print("Closed the popup ad.")
    except (TimeoutException, NoSuchElementException):
        print("No popup ad found, or it didn't appear.")

def click_avatar_button(driver):
    """Click the profile avatar button."""
    try:
        avatar_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='ds-avatar']"))
        )
        print(f"Avatar button found: {avatar_button}")
        move_mouse_to_element(driver, avatar_button)
        avatar_button.click()
        print("Clicked on the profile avatar button.")
    except TimeoutException:
        print("Failed to find and click the avatar button.")
        raise

def click_manage_portfolio(driver):
    """Click on 'Manage Portfolio'."""
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Manage Portfolio']"))).click()
    print("Clicked on 'Manage Portfolio'.")

def run_selenium_tests(first_run=False):
    """Run the selenium tests."""
    container_name = "selenium-chrome-grid"
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        options.add_argument(f'user-agent={user_agent}')
        
        print("Connecting to Remote WebDriver...")
        driver = webdriver.Remote(
            command_executor='http://localhost:4444/wd/hub',
            options=options
        )
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("WebDriver connected.")

        if first_run:
            login(driver)
            captcha_site_key = "6LdkZisUAAAAACQ1YvSn_fsTXRLoNCsiYuoKyDH7"  # Your correct site key
            api_key = get_captcha2_apikey()
            handle_captcha(driver, api_key, captcha_site_key)
            WebDriverWait(driver, 20).until(EC.title_contains("Redbubble"))
            print("Login successful.")
            handle_password_prompt(driver)
            save_cookies(driver)
        else:
            driver.get("https://www.redbubble.com/")
            load_cookies(driver)
            random_sleep(2, 4)
            driver.refresh()
            print("Logged in using cookies.")
            random_sleep()

        close_popup_ad(driver)
        click_avatar_button(driver)
        click_manage_portfolio(driver)

        print("Page title:", driver.title)
        driver.quit()
        print("Selenium WebDriver session ended.")
    except Exception as e:
        print(f"Error in Selenium test: {str(e)}")
        stop_docker_container(container_name)

def main():
    image_name = "selenium/standalone-chrome:4.0.0-20211013"
    container_name = "selenium-chrome-grid"
    port_mapping = "4444"
    vnc_port = "7900"

    if start_docker_container(image_name, container_name, port_mapping, vnc_port):
        time.sleep(5)
        webbrowser.open_new_tab("http://localhost:7900")
        run_selenium_tests(first_run=True)
        run_selenium_tests(first_run=False)
        stop_docker_container(container_name)

if __name__ == "__main__":
    main()
