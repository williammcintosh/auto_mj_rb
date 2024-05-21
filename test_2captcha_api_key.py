import requests

def get_captcha2_apikey():
    """Retrieve the 2Captcha API key."""
    with open('captcha2_apikey.txt', 'r') as file:
        return file.read().strip()

def test_2captcha_api_key():
    api_key = get_captcha2_apikey()
    response = requests.get(f"http://2captcha.com/res.php?key={api_key}&action=getbalance")
    
    if response.status_code == 200:
        balance = response.text
        if "ERROR" in balance:
            print(f"Error with API key: {balance}")
        else:
            print(f"API key is valid. Current balance: {balance}")
    else:
        print(f"Failed to connect to 2Captcha. Status code: {response.status_code}")

if __name__ == "__main__":
    test_2captcha_api_key()
