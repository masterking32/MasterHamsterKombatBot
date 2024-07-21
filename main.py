# Developed by: MasterkinG32
# Date: 2024
# Github: https://github.com/masterking32

import asyncio
import datetime
import json
import logging
import random
import time

import requests
from colorlog import ColoredFormatter

from utilities import *

# ---------------------------------------------#
# Configuration
# ---------------------------------------------#
# Recheck time in seconds to check all accounts again (60 seconds = 1 minute and 0 means no recheck)
AccountsRecheckTime = 300

# Adds a random delay to the AccountsRecheckTime interval to make it more unpredictable and less detectable.
# Set it to 0 to disable the random delay.
# For example, if set to 120, the bot will introduce a random delay between 1 and 120 seconds each time it rechecks.
MaxRandomDelay = 120

# Accounts will be checked in the order they are listed
AccountList = [
    {
        "account_name": "Account 1",  # A custom name for the account (not important, just for logs)
        "Authorization": "Bearer TOKEN_HERE",  # To get the token, refer to the README.md file
        "UserAgent": "Your UserAgent",  # Refer to the README.md file to obtain a user agent
        "Proxy": {},  # You can use proxies to avoid getting banned. Use {} for no proxy
        # Example of using a proxy:
        # "Proxy": {
        #   "https": "https://10.10.1.10:3128",
        #   "http": "http://user:pass@10.10.1.10:3128/"
        # },
        "config": {
            "auto_tap": True,  # Enable auto tap by setting it to True, or set it to False to disable
            "auto_finish_mini_game": True,  # Enable auto finish mini game by setting it to True, or set it to False to disable
            "auto_free_tap_boost": True,  # Enable auto free tap boost by setting it to True, or set it to False to disable
            "auto_get_daily_cipher": True,  # Enable auto get daily cipher by setting it to True, or set it to False to disable
            "auto_get_daily_task": True,  # Enable auto get daily task by setting it to True, or set it to False to disable
            "auto_upgrade": True,  # Enable auto upgrade by setting it to True, or set it to False to disable
            "auto_upgrade_start": 2000000,  # Start buying upgrades when the balance is greater than this amount
            "auto_upgrade_min": 100000,  # Stop buying upgrades when the balance is less than this amount
            # This feature will ignore the auto_upgrade_start and auto_upgrade_min.
            # By changing it to True, the bot will first find the overall best card and then wait for the best card to be available (based on cooldown or price).
            # When the best card is available, the bot will buy it and then wait for the next best card to be available.
            # This feature will stop buying upgrades when the balance is less than the price of the best card.
            "wait_for_best_card": False,  # Recommended to keep it True for high level accounts
            "auto_get_task": True,  # Enable auto get (Youtube/Twitter and ...) task to True, or set it to False to disable
            "enable_parallel_upgrades": True, # Enable parallel card upgrades. This will buy cards in parallel if best card is on cooldown. Should speed up the profit
            "parallel_upgrades_max_price_per_hour": 6_000_000,  # Cards with less than X coins per 1k will be bought
        },
        # If you have enabled Telegram bot logging,
        # you can add your chat ID below to receive logs in your Telegram account.
        # You can obtain your chat ID by messaging @chatIDrobot.
        # Example: "telegram_chat_id": "12345678".
        # If you do not wish to use this feature for this account, leave it empty.
        # This feature is optional and is required to enable the telegramBotLogging feature below.
        "telegram_chat_id": "",  # String - you can get it from https://t.me/chatIDrobot
    },
    # Add more accounts if you want to use multiple accounts
    # {
    #     "account_name": "Account 2",
    #     "Authorization": "Bearer Token_Here",
    #     ...
    #     other configurations like the first account
    # },
]

# ---------------------------------------------#
# Telegram Logging
# By enabling this feature, you will receive logs in your Telegram account.
# To use this feature, you need to create a bot and obtain the token from @BotFather.
# Note: Only important logs are sent to Telegram, feel free to include more logs as needed.
# You can also use this feature to receive logs from a bot running on a server.
# If you don't want to use this feature, set "is_active" to False and leave "bot_token" and "uid" fields empty.
# This feature is optional, and you can disable it by setting "is_active" to False.
telegramBotLogging = {
    "is_active": False,  # Set it to True if you want to use it, and make sure to fill out the below fields
    "bot_token": "",  # HTTP API access token from https://t.me/BotFather ~ Start your bot after creating it
    # Configure the what you want to receive logs from the bot
    "messages": {
        "general_info": True,  # General information
        "account_info": True,  # Account information
        "http_errors": False,  # HTTP errors
        "other_errors": False,  # Other errors
        "daily_cipher": True,  # Daily cipher
        "daily_task": False,  # Daily task
        "upgrades": True,  # Upgrades
    },
}

# ---------------------------------------------#
# Logging configuration
LOG_LEVEL = logging.DEBUG
LOGFORMAT = "%(log_color)s[Master HamsterKombat Bot]%(reset)s[%(log_color)s%(levelname)s%(reset)s] %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger("pythonConfig")
log.setLevel(LOG_LEVEL)
log.addHandler(stream)
# End of configuration
# ---------------------------------------------#


class HamsterKombatAccount:
    def __init__(self, AccountData):
        self.account_name = AccountData["account_name"]
        self.Authorization = AccountData["Authorization"]
        self.UserAgent = AccountData["UserAgent"]
        self.Proxy = AccountData["Proxy"]
        self.config = AccountData["config"]
        self.isAndroidDevice = "Android" in self.UserAgent
        self.balanceCoins = 0
        self.availableTaps = 0
        self.maxTaps = 0
        self.ProfitPerHour = 0
        self.earnPassivePerHour = 0
        self.SpendTokens = 0
        self.account_data = None
        self.telegram_chat_id = AccountData["telegram_chat_id"]
        self.totalKeys = 0
        self.balanceKeys = 0

    def SendTelegramLog(self, message, level):
        if (
            not telegramBotLogging["is_active"]
            or self.telegram_chat_id == ""
            or telegramBotLogging["bot_token"] == ""
        ):
            return

        if (
            level not in telegramBotLogging["messages"]
            or telegramBotLogging["messages"][level] is False
        ):
            return

        requests.get(
            f"https://api.telegram.org/bot{telegramBotLogging['bot_token']}/sendMessage?chat_id={self.telegram_chat_id}&text={message}"
        )

    # Send HTTP requests
    def HttpRequest(
        self,
        url,
        headers,
        method="POST",
        validStatusCodes=200,
        payload=None,
    ):
        # Default headers
        defaultHeaders = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Host": "api.hamsterkombatgame.io",
            "Origin": "https://hamsterkombatgame.io",
            "Referer": "https://hamsterkombatgame.io/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.UserAgent,
        }

        # Add default headers for Android devices to avoid detection, Not needed for iOS devices
        if self.isAndroidDevice:
            defaultHeaders["HTTP_SEC_CH_UA_PLATFORM"] = '"Android"'
            defaultHeaders["HTTP_SEC_CH_UA_MOBILE"] = "?1"
            defaultHeaders["HTTP_SEC_CH_UA"] = (
                '"Android WebView";v="125", "Chromium";v="125", "Not.A/Brand";v="24"'
            )
            defaultHeaders["HTTP_X_REQUESTED_WITH"] = "org.telegram.messenger.web"

        # Add and replace new headers to default headers
        for key, value in headers.items():
            defaultHeaders[key] = value

        try:
            if method == "GET":
                response = requests.get(url, headers=defaultHeaders, proxies=self.Proxy)
            elif method == "POST":
                response = requests.post(
                    url, headers=headers, data=payload, proxies=self.Proxy
                )
            elif method == "OPTIONS":
                response = requests.options(url, headers=headers, proxies=self.Proxy)
            else:
                log.error(f"[{self.account_name}] Invalid method: {method}")
                self.SendTelegramLog(
                    f"[{self.account_name}] Invalid method: {method}", "http_errors"
                )
                return False

            if response.status_code != validStatusCodes:
                log.error(
                    f"[{self.account_name}] Status code is not {validStatusCodes}"
                )
                log.error(f"[{self.account_name}] Response: {response.text}")
                self.SendTelegramLog(
                    f"[{self.account_name}] Status code is not {validStatusCodes}",
                    "http_errors",
                )
                return False

            if method == "OPTIONS":
                return True

            return response.json()
        except Exception as e:
            log.error(f"[{self.account_name}] Error: {e}")
            self.SendTelegramLog(f"[{self.account_name}] Error: {e}", "http_errors")
            return False

    # Sending sync request
    def syncRequest(self):
        url = "https://api.hamsterkombatgame.io/clicker/sync"
        headers = {
            "Access-Control-Request-Headers": self.Authorization,
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200)

    # Get list of upgrades to buy
    def UpgradesForBuyRequest(self):
        url = "https://api.hamsterkombatgame.io/clicker/upgrades-for-buy"
        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200)

    # Buy an upgrade
    def BuyUpgradeRequest(self, UpgradeId):
        url = "https://api.hamsterkombatgame.io/clicker/buy-upgrade"
        headers = {
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = json.dumps(
            {
                "upgradeId": UpgradeId,
                "timestamp": int(datetime.datetime.now().timestamp() * 1000),
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200, payload)

    # Tap the hamster
    def TapRequest(self, tap_count):
        url = "https://api.hamsterkombatgame.io/clicker/tap"
        headers = {
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Accept": "application/json",
            "Authorization": self.Authorization,
            "Content-Type": "application/json",
        }

        payload = json.dumps(
            {
                "timestamp": int(datetime.datetime.now().timestamp() * 1000),
                "availableTaps": 0,
                "count": int(tap_count),
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200, payload)

    # Get list of boosts to buy
    def BoostsToBuyListRequest(self):
        url = "https://api.hamsterkombatgame.io/clicker/boosts-for-buy"
        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200)

    # Buy a boost
    def BuyBoostRequest(self, boost_id):
        url = "https://api.hamsterkombatgame.io/clicker/buy-boost"
        headers = {
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Accept": "application/json",
            "Authorization": self.Authorization,
            "Content-Type": "application/json",
        }

        payload = json.dumps(
            {
                "boostId": boost_id,
                "timestamp": int(datetime.datetime.now().timestamp() * 1000),
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200, payload)

    def getAccountData(self):
        account_data = self.syncRequest()
        if account_data is None or account_data is False:
            log.error(f"[{self.account_name}] Unable to get account data.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get account data.", "other_errors"
            )
            return False

        if "clickerUser" not in account_data:
            log.error(f"[{self.account_name}] Invalid account data.")
            self.SendTelegramLog(
                f"[{self.account_name}] Invalid account data.", "other_errors"
            )
            return False

        if "balanceCoins" not in account_data["clickerUser"]:
            log.error(f"[{self.account_name}] Invalid balance coins.")
            self.SendTelegramLog(
                f"[{self.account_name}] Invalid balance coins.", "other_errors"
            )
            return False

        self.account_data = account_data
        self.balanceCoins = account_data["clickerUser"]["balanceCoins"]
        self.availableTaps = account_data["clickerUser"]["availableTaps"]
        self.maxTaps = account_data["clickerUser"]["maxTaps"]
        self.earnPassivePerHour = account_data["clickerUser"]["earnPassivePerHour"]
        if "balanceKeys" in account_data["clickerUser"]:
            self.balanceKeys = account_data["clickerUser"]["balanceKeys"]
        else:
            self.balanceKeys = 0

        if "totalKeys" in account_data["clickerUser"]:
            self.totalKeys = account_data["clickerUser"]["totalKeys"]
        else:
            self.totalKeys = 0

        return account_data

    def BuyFreeTapBoostIfAvailable(self):
        log.info(f"[{self.account_name}] Checking for free tap boost...")

        BoostList = self.BoostsToBuyListRequest()
        if BoostList is None:
            log.error(f"[{self.account_name}] Failed to get boosts list.")
            self.SendTelegramLog(
                f"[{self.account_name}] Failed to get boosts list.", "other_errors"
            )
            return None

        BoostForTapList = None
        for boost in BoostList["boostsForBuy"]:
            if boost["price"] == 0 and boost["id"] == "BoostFullAvailableTaps":
                BoostForTapList = boost
                break

        if (
            BoostForTapList is not None
            and "price" in BoostForTapList
            and "cooldownSeconds" in BoostForTapList
            and BoostForTapList["price"] == 0
            and BoostForTapList["cooldownSeconds"] == 0
        ):
            log.info(f"[{self.account_name}] Free boost found, attempting to buy...")
            time.sleep(5)
            self.BuyBoostRequest(BoostForTapList["id"])
            log.info(f"[{self.account_name}] Free boost bought successfully")
            return True
        else:
            log.info(f"\033[1;34m[{self.account_name}] No free boosts available\033[0m")

        return False

    def IPRequest(self):
        url = "https://api.hamsterkombatgame.io/ip"
        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "GET",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 200)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send GET request
        return self.HttpRequest(url, headers, "GET", 200)

    def MeTelegramRequest(self):
        url = "https://api.hamsterkombatgame.io/auth/me-telegram"
        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200)

    def ListTasksRequest(self):
        url = "https://api.hamsterkombatgame.io/clicker/list-tasks"
        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200)

    def GetListAirDropTasksRequest(self):
        url = "https://api.hamsterkombatgame.io/clicker/list-airdrop-tasks"
        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200)

    def GetAccountConfigRequest(self):
        url = "https://api.hamsterkombatgame.io/clicker/config"
        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200)

    def ClaimDailyCipherRequest(self, DailyCipher):
        url = "https://api.hamsterkombatgame.io/clicker/claim-daily-cipher"
        headers = {
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Accept": "application/json",
            "Authorization": self.Authorization,
            "Content-Type": "application/json",
        }

        payload = json.dumps(
            {
                "cipher": DailyCipher,
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200, payload)

    def CheckTaskRequest(self, task_id):
        url = "https://api.hamsterkombatgame.io/clicker/check-task"
        headers = {
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Accept": "application/json",
            "Authorization": self.Authorization,
            "Content-Type": "application/json",
        }

        payload = json.dumps(
            {
                "taskId": task_id,
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200, payload)

    def BuyCard(self, card):
        upgradesResponse = self.BuyUpgradeRequest(card["id"])

        if upgradesResponse is None:
            log.error(f"[{self.account_name}] Failed to buy the card.")
            self.SendTelegramLog(
                f"[{self.account_name}] Failed to buy the card.", "other_errors"
            )
            return False

        log.info(f"[{self.account_name}] Card bought successfully")
        time.sleep(3)
        self.balanceCoins -= card["price"]
        self.ProfitPerHour += card["profitPerHourDelta"]
        self.SpendTokens += card["price"]
        self.earnPassivePerHour += card["profitPerHourDelta"]

        return True

    def BuyBestCard(self):
        log.info(f"[{self.account_name}] Checking for best card...")
        time.sleep(2)
        upgradesResponse = self.UpgradesForBuyRequest()
        if upgradesResponse is None:
            log.error(f"[{self.account_name}] Failed to get upgrades list.")
            self.SendTelegramLog(
                f"[{self.account_name}] Failed to get upgrades list.", "other_errors"
            )
            return False

        upgrades = [
            item
            for item in upgradesResponse["upgradesForBuy"]
            if not item["isExpired"]
            and item["isAvailable"]
            and item["profitPerHourDelta"] > 0
        ]

        if len(upgrades) == 0:
            log.warning(f"[{self.account_name}] No upgrades available.")
            return False

        balanceCoins = int(self.balanceCoins)
        log.info(f"[{self.account_name}] Searching for the best upgrades...")

        selected_upgrades = SortUpgrades(
            upgrades, 999999999999
        )  # Set max budget to a high number
        if len(selected_upgrades) == 0:
            log.warning(f"[{self.account_name}] No upgrades available.")
            return False

        current_selected_card = selected_upgrades[0]
        log.info(
            f"[{self.account_name}] Best upgrade is {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}"
        )

        if balanceCoins < current_selected_card["price"]:
            log.warning(
                f"[{self.account_name}] Balance is too low to buy the best card."
            )

            self.SendTelegramLog(
                f"[{self.account_name}] Balance is too low to buy the best card, Best card: {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}",
                "upgrades",
            )
            return False

        if (
            "cooldownSeconds" in current_selected_card
            and current_selected_card["cooldownSeconds"] > 0
        ):
            log.warning(f"[{self.account_name}] Best card is on cooldown...")
            if current_selected_card["cooldownSeconds"] > 300:
                self.SendTelegramLog(
                    f"[{self.account_name}] Best card is on cooldown for more than 5 minutes, Best card: {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}",
                    "upgrades",
                )
                if self.config['enable_parallel_upgrades']:
                    offset = 1
                    while True:
                        log.info(f"[{self.account_name}] Trying to find a card for parallel buy")

                        best_next_card = FindBestCardWithLowerCoefficient(upgrades[offset:], self.config['parallel_upgrades_max_price_per_hour'])

                        if best_next_card is not None and self.balanceCoins > best_next_card["price"]:
                            log.info(f"[{self.account_name}] Found next card with lower coefficient: {best_next_card['name']} with profit {best_next_card['profitPerHourDelta']} and price {number_to_string(best_next_card['price'])}, Level: {best_next_card['level']}")
                            log.info(f"[{self.account_name}] Attempting to buy the card...")

                            self.BuyCard(best_next_card)
                            time.sleep(3)

                            offset += 1
                        else:
                            log.warning(f"[{self.account_name}] No more cards for parallel buy")
                            break

                return False
            log.info(
                f"[{self.account_name}] Waiting for {current_selected_card['cooldownSeconds']} seconds, Cooldown will be completed in {current_selected_card['cooldownSeconds']} seconds..."
            )
            time.sleep(current_selected_card["cooldownSeconds"] + 1)

        log.info(f"[{self.account_name}] Attempting to buy the best card...")

        buy_result = self.BuyCard(current_selected_card)

        if buy_result:
            time.sleep(2)
            log.info(
                f"[{self.account_name}] Best card purchase completed successfully, Your profit per hour increased by {number_to_string(self.ProfitPerHour)} coins, Spend tokens: {number_to_string(self.SpendTokens)}"
            )
            self.SendTelegramLog(
                f"[{self.account_name}] Bought {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}",
                "upgrades",
            )

            return True

    def StartMiniGame(self, AccountConfigData, AccountID):
        if "dailyKeysMiniGame" not in AccountConfigData:
            log.error(f"[{self.account_name}] Unable to get daily keys mini game.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get daily keys mini game.",
                "other_errors",
            )
            return

        if AccountConfigData["dailyKeysMiniGame"]["isClaimed"] == True:
            log.info(f"[{self.account_name}] Daily keys mini game already claimed.")
            return

        if AccountConfigData["dailyKeysMiniGame"]["remainSecondsToNextAttempt"] > 0:
            log.info(f"[{self.account_name}] Daily keys mini game is on cooldown...")
            return

        ## check timer.
        url = "https://api.hamsterkombatgame.io/clicker/start-keys-minigame"

        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send POST request
        response = self.HttpRequest(url, headers, "POST", 200)

        if response is None:
            log.error(f"[{self.account_name}] Unable to start mini game.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to start mini game.", "other_errors"
            )
            return

        if "dailyKeysMiniGame" not in response:
            log.error(f"[{self.account_name}] Unable to get daily keys mini game.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get daily keys mini game.",
                "other_errors",
            )
            return

        if response["dailyKeysMiniGame"]["isClaimed"] == True:
            log.info(f"[{self.account_name}] Daily keys mini game already claimed.")
            return

        if "remainSecondsToGuess" not in response["dailyKeysMiniGame"]:
            log.error(f"[{self.account_name}] Unable to get daily keys mini game.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get daily keys mini game.",
                "other_errors",
            )
            return

        waitTime = int(
            response["dailyKeysMiniGame"]["remainSecondsToGuess"]
            - random.randint(8, 15)
        )

        if waitTime < 0:
            log.error(f"[{self.account_name}] Unable to claim mini game.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to claim mini game.", "other_errors"
            )
            return

        log.info(
            f"[{self.account_name}] Waiting for {waitTime} seconds, Mini-game will be completed in {waitTime} seconds..."
        )
        time.sleep(waitTime)

        url = "https://api.hamsterkombatgame.io/clicker/claim-daily-keys-minigame"

        headers = {
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Method": "POST",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Accept": "application/json",
            "Authorization": self.Authorization,
            "Content-Type": "application/json",
        }

        cipher = (
            ("0" + str(waitTime) + str(random.randint(10000000000, 99999999999)))[:10]
            + "|"
            + str(AccountID)
        )
        cipher_base64 = base64.b64encode(cipher.encode()).decode()

        payload = json.dumps(
            {
                "cipher": cipher_base64,
            }
        )

        # Send POST request
        response = self.HttpRequest(url, headers, "POST", 200, payload)

        if response is None:
            log.error(f"[{self.account_name}] Unable to claim mini game.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to claim mini game.", "other_errors"
            )
            return

        log.info(f"[{self.account_name}] Mini game claimed successfully.")

    def Start(self):
        log.info(f"[{self.account_name}] Starting account...")

        log.info(f"[{self.account_name}] Getting basic account data...")
        AccountBasicData = self.MeTelegramRequest()

        if (
            AccountBasicData is None
            or AccountBasicData is False
            or "telegramUser" not in AccountBasicData
            or "id" not in AccountBasicData["telegramUser"]
        ):
            log.error(f"[{self.account_name}] Unable to get account basic data.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get account basic data.",
                "other_errors",
            )
            return

        log.info(
            f"\033[1;35m[{self.account_name}] Account ID: {AccountBasicData['telegramUser']['id']}, Account detected as bot: {AccountBasicData['telegramUser']['isBot']}\033[0m"
        )
        self.SendTelegramLog(
            f"[{self.account_name}] Account ID: {AccountBasicData['telegramUser']['id']}, Account detected as bot: {AccountBasicData['telegramUser']['isBot']}",
            "account_info",
        )

        log.info(f"[{self.account_name}] Getting account config data...")
        AccountConfigData = self.GetAccountConfigRequest()
        if (
            AccountConfigData is None
            or AccountConfigData is False
            or "clickerConfig" not in AccountConfigData
        ):
            log.error(f"[{self.account_name}] Unable to get account config data.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get account config data.",
                "other_errors",
            )
            return

        DailyCipher = ""
        if (
            self.config["auto_get_daily_cipher"]
            and "dailyCipher" in AccountConfigData
            and "cipher" in AccountConfigData["dailyCipher"]
        ):
            log.info(f"[{self.account_name}] Decoding daily cipher...")
            DailyCipher = DailyCipherDecode(AccountConfigData["dailyCipher"]["cipher"])
            MorseCode = TextToMorseCode(DailyCipher)
            log.info(
                f"\033[1;34m[{self.account_name}] Daily cipher: {DailyCipher} and Morse code: {MorseCode}\033[0m"
            )

        log.info(f"[{self.account_name}] Getting account data...")
        getAccountDataStatus = self.getAccountData()
        if getAccountDataStatus is False:
            return

        log.info(
            f"[{self.account_name}] Account Balance Coins: {number_to_string(self.balanceCoins)}, Available Taps: {self.availableTaps}, Max Taps: {self.maxTaps}, Total Keys: {self.totalKeys}, Balance Keys: {self.balanceKeys}"
        )

        log.info(f"[{self.account_name}] Getting account upgrades...")
        upgradesResponse = self.UpgradesForBuyRequest()

        if upgradesResponse is None:
            log.error(f"[{self.account_name}] Failed to get upgrades list.")
            self.SendTelegramLog(
                f"[{self.account_name}] Failed to get upgrades list.", "other_errors"
            )
            return

        log.info(f"[{self.account_name}] Getting account tasks...")
        tasksResponse = self.ListTasksRequest()

        if tasksResponse is None:
            log.error(f"[{self.account_name}] Failed to get tasks list.")
            self.SendTelegramLog(
                f"[{self.account_name}] Failed to get tasks list.", "other_errors"
            )
            return

        log.info(f"[{self.account_name}] Getting account airdrop tasks...")
        airdropTasksResponse = self.GetListAirDropTasksRequest()

        if airdropTasksResponse is None:
            log.error(f"[{self.account_name}] Failed to get airdrop tasks list.")
            self.SendTelegramLog(
                f"[{self.account_name}] Failed to get airdrop tasks list.",
                "other_errors",
            )
            return

        log.info(f"[{self.account_name}] Getting account IP...")
        ipResponse = self.IPRequest()
        if ipResponse is None:
            log.error(f"[{self.account_name}] Failed to get IP.")
            self.SendTelegramLog(
                f"[{self.account_name}] Failed to get IP.", "other_errors"
            )
            return

        log.info(
            f"[{self.account_name}] IP: {ipResponse['ip']} Company: {ipResponse['asn_org']} Country: {ipResponse['country_code']}"
        )

        if self.config["auto_finish_mini_game"]:
            log.info(f"[{self.account_name}] Attempting to finish mini game...")
            time.sleep(1)
            self.StartMiniGame(
                AccountConfigData, AccountBasicData["telegramUser"]["id"]
            )

        # Start tapping
        if self.config["auto_tap"]:
            log.info(f"[{self.account_name}] Starting to tap...")
            time.sleep(2)
            self.TapRequest(self.availableTaps)
            log.info(f"[{self.account_name}] Tapping completed successfully.")

        if self.config["auto_get_daily_cipher"] and DailyCipher != "":
            if AccountConfigData["dailyCipher"]["isClaimed"] == True:
                log.info(
                    f"\033[1;34m[{self.account_name}] Daily cipher already claimed.\033[0m"
                )
            else:
                log.info(f"[{self.account_name}] Attempting to claim daily cipher...")
                time.sleep(2)
                self.ClaimDailyCipherRequest(DailyCipher)
                log.info(f"[{self.account_name}] Daily cipher claimed successfully.")
                self.SendTelegramLog(
                    f"[{self.account_name}] Daily cipher claimed successfully. Text was: {DailyCipher}, Morse code was: {TextToMorseCode(DailyCipher)}",
                    "daily_cipher",
                )

        if self.config["auto_get_daily_task"]:
            log.info(f"[{self.account_name}] Checking for daily task...")
            streak_days = None
            for task in tasksResponse["tasks"]:
                if task["id"] == "streak_days":
                    streak_days = task
                    break

            if streak_days is None:
                log.error(f"[{self.account_name}] Failed to get daily task.")
                return

            if streak_days["isCompleted"] == True:
                log.info(
                    f"\033[1;34m[{self.account_name}] Daily task already completed.\033[0m"
                )
            else:
                log.info(f"[{self.account_name}] Attempting to complete daily task...")
                day = streak_days["days"]
                rewardCoins = streak_days["rewardCoins"]
                time.sleep(2)
                self.CheckTaskRequest("streak_days")
                log.info(
                    f"[{self.account_name}] Daily task completed successfully, Day: {day}, Reward coins: {number_to_string(rewardCoins)}"
                )
                self.SendTelegramLog(
                    f"[{self.account_name}] Daily task completed successfully, Day: {day}, Reward coins: {number_to_string(rewardCoins)}",
                    "daily_task",
                )

        if self.config["auto_get_task"]:
            log.info(f"[{self.account_name}] Checking for available task...")
            selected_task = None
            for task in tasksResponse["tasks"]:
                link = task.get("link", "")
                if task["isCompleted"] == False and ("https://" in link):
                    log.info(
                        f"[{self.account_name}] Attempting to complete Youtube Or Twitter task..."
                    )
                    selected_task = task["id"]
                    rewardCoins = task["rewardCoins"]
                    time.sleep(2)
                    self.CheckTaskRequest(selected_task)
                    log.info(
                        f"[{self.account_name}] Task completed - id: {selected_task}, Reward coins: {number_to_string(rewardCoins)}"
                    )
                    self.SendTelegramLog(
                        f"[{self.account_name}] Task completed - id: {selected_task}, Reward coins: {number_to_string(rewardCoins)}",
                        "daily_task",
                    )
            if selected_task is None:
                log.info(f"\033[1;34m[{self.account_name}] Tasks already done\033[0m")

        # Start buying free tap boost
        if (
            self.config["auto_tap"]
            and self.config["auto_free_tap_boost"]
            and self.BuyFreeTapBoostIfAvailable()
        ):
            log.info(f"[{self.account_name}] Starting to tap with free boost...")
            time.sleep(2)
            self.TapRequest(self.availableTaps)
            log.info(
                f"[{self.account_name}] Tapping with free boost completed successfully."
            )

        # Start Syncing account data after tapping
        if self.config["auto_tap"]:
            self.getAccountData()
            log.info(
                f"[{self.account_name}] Account Balance Coins: {number_to_string(self.balanceCoins)}, Available Taps: {self.availableTaps}, Max Taps: {self.maxTaps}, Total Keys: {self.totalKeys}, Balance Keys: {self.balanceKeys}"
            )

        # Start buying upgrades
        if not self.config["auto_upgrade"]:
            log.error(f"[{self.account_name}] Auto upgrade is disabled.")
            return

        self.ProfitPerHour = 0
        self.SpendTokens = 0

        if self.config["wait_for_best_card"]:
            while True:
                if not self.BuyBestCard():
                    break

            self.getAccountData()
            log.info(
                f"[{self.account_name}] Final account balance: {number_to_string(self.balanceCoins)} coins, Your profit per hour is {number_to_string(self.earnPassivePerHour)} (+{number_to_string(self.ProfitPerHour)}), Spent: {number_to_string(self.SpendTokens)}"
            )
            self.SendTelegramLog(
                f"[{self.account_name}] Final account balance: {number_to_string(self.balanceCoins)} coins, Your profit per hour is {number_to_string(self.earnPassivePerHour)} (+{number_to_string(self.ProfitPerHour)}), Spent: {number_to_string(self.SpendTokens)}",
                "upgrades",
            )
            return

        if self.balanceCoins < self.config["auto_upgrade_start"]:
            log.warning(
                f"[{self.account_name}] Balance is too low to start buying upgrades."
            )
            return

        while self.balanceCoins >= self.config["auto_upgrade_min"]:
            log.info(f"[{self.account_name}] Checking for upgrades...")
            time.sleep(2)
            upgradesResponse = self.UpgradesForBuyRequest()
            if upgradesResponse is None:
                log.warning(f"[{self.account_name}] Failed to get upgrades list.")
                self.SendTelegramLog(
                    f"[{self.account_name}] Failed to get upgrades list.",
                    "other_errors",
                )
                return

            upgrades = [
                item
                for item in upgradesResponse["upgradesForBuy"]
                if not item["isExpired"]
                and item["isAvailable"]
                and item["profitPerHourDelta"] > 0
                and ("cooldownSeconds" not in item or item["cooldownSeconds"] == 0)
            ]

            if len(upgrades) == 0:
                log.warning(f"[{self.account_name}] No upgrades available.")
                return

            balanceCoins = int(self.balanceCoins)
            log.info(f"[{self.account_name}] Searching for the best upgrades...")

            selected_upgrades = SortUpgrades(upgrades, balanceCoins)
            if len(selected_upgrades) == 0:
                log.warning(f"[{self.account_name}] No upgrades available.")
                return

            current_selected_card = selected_upgrades[0]
            log.info(
                f"[{self.account_name}] Best upgrade is {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}"
            )

            balanceCoins -= current_selected_card["price"]

            log.info(f"[{self.account_name}] Attempting to buy an upgrade...")
            time.sleep(2)
            upgradesResponse = self.BuyUpgradeRequest(current_selected_card["id"])
            if upgradesResponse is None:
                log.error(f"[{self.account_name}] Failed to buy an upgrade.")
                return

            log.info(f"[{self.account_name}] Upgrade bought successfully")
            self.SendTelegramLog(
                f"[{self.account_name}] Bought {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}",
                "upgrades",
            )
            time.sleep(5)
            self.balanceCoins = balanceCoins
            self.ProfitPerHour += current_selected_card["profitPerHourDelta"]
            self.SpendTokens += current_selected_card["price"]
            self.earnPassivePerHour += current_selected_card["profitPerHourDelta"]

        log.info(f"[{self.account_name}] Upgrades purchase completed successfully.")
        self.getAccountData()
        log.info(
            f"[{self.account_name}] Final account balance: {number_to_string(self.balanceCoins)} coins, Your profit per hour is {number_to_string(self.earnPassivePerHour)} (+{number_to_string(self.ProfitPerHour)}), Spent: {number_to_string(self.SpendTokens)}"
        )
        self.SendTelegramLog(
            f"[{self.account_name}] Final account balance: {number_to_string(self.balanceCoins)} coins, Your profit per hour is {number_to_string(self.earnPassivePerHour)} (+{number_to_string(self.ProfitPerHour)}), Spent: {number_to_string(self.SpendTokens)}",
            "account_info",
        )


def RunAccounts():
    accounts = []
    for account in AccountList:
        accounts.append(HamsterKombatAccount(account))
        accounts[-1].SendTelegramLog(
            f"[{accounts[-1].account_name}] Hamster Kombat Auto farming bot started successfully.",
            "general_info",
        )

    while True:
        log.info("\033[1;33mStarting all accounts...\033[0m")
        for account in accounts:
            account.Start()

        if AccountsRecheckTime < 1 and MaxRandomDelay < 1:
            log.error(
                f"AccountsRecheckTime and MaxRandomDelay values are set to 0, bot will close now."
            )
            return

        if MaxRandomDelay > 0:
            randomDelay = random.randint(1, MaxRandomDelay)
            log.error(f"Sleeping for {randomDelay} seconds because of random delay...")
            time.sleep(randomDelay)

        if AccountsRecheckTime > 0:
            log.error(f"Rechecking all accounts in {AccountsRecheckTime} seconds...")
            time.sleep(AccountsRecheckTime)


def main():
    log.info("------------------------------------------------------------------------")
    log.info("------------------------------------------------------------------------")
    log.info("\033[1;32mWelcome to [Master Hamster Kombat] Auto farming bot...\033[0m")
    log.info(
        "\033[1;34mProject Github: https://github.com/masterking32/MasterHamsterKombatBot\033[0m"
    )
    log.info("\033[1;33mDeveloped by: MasterkinG32\033[0m")
    log.info("\033[1;35mVersion: 2.0\033[0m")
    log.info("\033[1;36mTo stop the bot, press Ctrl + C\033[0m")
    log.info("------------------------------------------------------------------------")
    log.info("------------------------------------------------------------------------")

    time.sleep(2)
    try:
        asyncio.run(RunAccounts())
    except KeyboardInterrupt:
        log.error("Stopping Master Hamster Kombat Auto farming bot...")


if __name__ == "__main__":
    main()
