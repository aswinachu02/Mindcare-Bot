import os, time, json, requests
from dotenv import load_dotenv

load_dotenv()

TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME")
TWITTER_PASSWORD = os.environ.get("TWITTER_PASSWORD")
TWITTER_EMAIL = os.environ.get("TWITTER_EMAIL")
TARGETS = ["mpigliucci"]
TWITTER_BASE_URL = "https://twitter.com"
TWITTER_LOGIN_URL = f"{TWITTER_BASE_URL}/i/flow/login"
TWITTER_PROFILE_URL = lambda uname: f"{TWITTER_BASE_URL}/{uname}"
TWITTER_FOLLOWERS_URL = lambda uname: f"{TWITTER_BASE_URL}/{uname}/followers"
IS_LOGGED_IN = False
# USERS = []
USERS = ["@ASNandanunni", "@AbhinavRajesh"]
TWEETS = {}
RESULTS = {}

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def err_logger(error: Exception, location: str):
    print(f"ERR :: {location} ::", error)


def msg_logger(message: str, location: str):
    print(f"MSG :: {location} ::", message)


def Login(driver: webdriver.Chrome):
    global IS_LOGGED_IN
    try:
        driver.get(TWITTER_LOGIN_URL)
        time.sleep(3)
        inputs = driver.find_elements(By.TAG_NAME, "input")
        inputs[0].send_keys(TWITTER_USERNAME)
        next_button = None
        links = driver.find_elements(By.TAG_NAME, "div")
        for link in links:
            if link.aria_role == "button" and link.text == "Next":
                next_button = link
        if next_button:
            next_button.click()
            time.sleep(2)
            inputs = driver.find_elements(By.TAG_NAME, "input")
            inputs[1].send_keys(TWITTER_PASSWORD)
            next_button = None
            links = driver.find_elements(By.TAG_NAME, "div")
            for link in links:
                if link.aria_role == "button" and link.text == "Log in":
                    next_button = link

        if next_button:
            next_button.click()
            time.sleep(5)
            IS_LOGGED_IN = True
            msg_logger("Login success", "Login")
    except Exception as err:
        err_logger(err, "Login")


def GetFollowers(driver: webdriver.Chrome):
    global USERS
    try:
        if not IS_LOGGED_IN:
            raise Exception("Unauthorized, not logged in")
        count = 0
        for username in TARGETS:
            driver.get(TWITTER_FOLLOWERS_URL(username))
            time.sleep(5)
            links = driver.find_elements(By.TAG_NAME, "a")
            start = False
            for link in links:
                if start and link.text.startswith("@"):
                    USERS.append(link.text)
                if link.text == "Following":
                    start = True
            count += 1
            msg_logger(f"[{count}/{len(TARGETS)}] {username} success", "GetFollowers")
            time.sleep(3)
    except Exception as err:
        err_logger(err, "GetFollowers")


def GetTweets(driver: webdriver.Chrome):
    global USERS, TWEETS
    try:
        count = 0
        for username in USERS:
            username = username.replace("@", "")
            driver.get(TWITTER_PROFILE_URL(username))
            time.sleep(5)
            articles = driver.find_elements(By.TAG_NAME, "article")
            user_tweets = []
            for article in articles:
                user_tweets.append(article.accessible_name)
            TWEETS[username] = user_tweets
            count += 1
            msg_logger(f"[{count}/{len(USERS)}] {username} success", "GetTweets")
    except Exception as err:
        err_logger(err, "GetTweets")


def WriteToJSONFile():
    global USERS, TWEETS
    try:
        json_object = json.dumps(TWEETS, indent=4)
        with open("tweets.json", "w") as outfile:
            outfile.write(json_object)
        msg_logger(f"Data saved to JSON file", "WriteToJSONFile")
    except Exception as err:
        err_logger(err, "WriteToJSONFile")


def PredictWithModel():
    global USERS, TWEETS, RESULTS
    count = 0
    for username in USERS:
        username = username.replace("@", "")
        try:
            url = "http://127.0.0.1:5000/predict"
            tweets = TWEETS[username]
            data = {"tweets": tweets}
            response = requests.post(url, json=data)
            response_data = json.loads(response.text)
            print(response_data)
            if response_data["success"]:
                RESULTS[username] = response_data["data"]
            else:
                statuses = []
                for tweet in tweets:
                    statuses.append(True if "depress" in tweet else False)
                data = {"is_depressed": True if any(statuses) else False}
                RESULTS[username] = data
            count += 1
            msg_logger(f"[{count}/{len(USERS)}] {username} success", "PredictWithModel")

        except Exception as err:
            count += 1
            msg_logger(f"[{count}/{len(USERS)}] {username} failed", "PredictWithModel")
            err_logger(err, "PredictWithModel")


def DisplayResults():
    print("\n\n------------------ RESULTS ------------------\n")
    for username in RESULTS.keys():
        print(username, " =>", RESULTS[username])
        print("____________________________________________\n")


def Main():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    try:
        # Login(driver=driver)
        # GetFollowers(driver=driver)
        GetTweets(driver=driver)
        WriteToJSONFile()
        PredictWithModel()
        DisplayResults()
    except KeyboardInterrupt:
        msg_logger("Halting process", "Main")
        driver.quit()
        exit()
    except Exception as err:
        err_logger(err, "Main")
    finally:
        driver.quit()


if __name__ == "__main__":
    Main()
