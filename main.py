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
import uuid
import hashlib
from utilities import *
from promogames import *

try:
    from config import *
except ImportError:
    print("Config file not found.")
    print("Create a copy of config.py.example and rename it to config.py")
    print("And fill in the required fields.")
    exit()

if "ConfigFileVersion" not in locals() or ConfigFileVersion != 1:
    print("Invalid config file version.")
    print("Please update the config file to the latest version.")
    print("Create a copy of config.py.example and rename it to config.py")
    print("And fill in the required fields.")
    exit()

# ---------------------------------------------#
# Logging configuration
LOG_LEVEL = logging.DEBUG
# Include date and time in the log format
LOGFORMAT = "%(log_color)s[Master HamsterKombat Bot]%(reset)s[%(log_color)s%(levelname)s%(reset)s] %(asctime)s %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(
    LOGFORMAT, "%Y-%m-%d %H:%M:%S"
)  # Specify the date/time format
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
        self.configVersion = ""

    def GetConfig(self, key, default=None):
        if key in self.config:
            return self.config[key]
        return default

    def SendTelegramLog(self, message, level="other_errors"):
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

        try:
            requests.get(
                f"https://api.telegram.org/bot{telegramBotLogging['bot_token']}/sendMessage?chat_id={self.telegram_chat_id}&text={message}"
            )
        except Exception as e:
            log.error(f"[{self.account_name}] TelegramLog error: {e}")

    # Send HTTP requests
    def HttpRequest(
        self,
        url,
        headers,
        method="POST",
        validStatusCodes=200,
        payload=None,
        ignore_errors=False,
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
                return None

            if response.status_code != validStatusCodes:
                if ignore_errors:
                    return None

                log.error(
                    f"[{self.account_name}] Status code is not {validStatusCodes}"
                )
                log.error(f"[{self.account_name}] Response: {response.text}")
                self.SendTelegramLog(
                    f"[{self.account_name}] Status code is not {validStatusCodes}",
                    "http_errors",
                )
                return None

            if "config-version" in response.headers:
                self.configVersion = response.headers["config-version"]

            if method == "OPTIONS":
                return True

            return response.json()
        except Exception as e:
            if ignore_errors:
                return None
            log.error(f"[{self.account_name}] Error: {e}")
            self.SendTelegramLog(f"[{self.account_name}] Error: {e}", "http_errors")
            return None

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

    def GetSkins(self):
        url = "https://api.hamsterkombatgame.io/clicker/get-skin"
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

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200, "{}")

    def AccountInfoTelegramRequest(self):
        url = "https://api.hamsterkombatgame.io/auth/account-info"
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

    def GetAccountConfigVersionRequest(self):
        if self.configVersion == "":
            return None

        url = f"https://api.hamsterkombatgame.io/clicker/config/{self.configVersion}"
        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "GET",
        }

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send GET request
        return self.HttpRequest(url, headers, "GET", 200)

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

    def ListBuyOptions(self, selected_upgrades):
        log.info(
            f"[{self.account_name}] List of {self.GetConfig('show_num_buy_options', 0)} best buy options:"
        )
        count = 1
        for selected_card in selected_upgrades:
            if (
                "cooldownSeconds" in selected_card
                and selected_card["cooldownSeconds"] > 0
            ):
                continue
            profitCoefficient = CalculateCardProfitCoefficient(selected_card)
            log.info(
                f"[{self.account_name}] {count}: {selected_card['name']}, Profit: {selected_card['profitPerHourDelta']}, Price: {number_to_string(selected_card['price'])}, Coefficient: {int(profitCoefficient)} Level: {selected_card['level']}"
            )
            count = count + 1
            if count > self.GetConfig("show_num_buy_options", 0):
                break

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
            upgrades, 999_999_999_999
        )  # Set max budget to a high number
        if len(selected_upgrades) == 0:
            log.warning(f"[{self.account_name}] No upgrades available.")
            return False

        if self.GetConfig("show_num_buy_options", 0) > 0:
            self.ListBuyOptions(selected_upgrades)

        current_selected_card = selected_upgrades[0]
        for selected_card in selected_upgrades:
            if (
                "cooldownSeconds" in selected_card
                and selected_card["cooldownSeconds"] > 0
                and selected_card["cooldownSeconds"] < 180
            ):
                log.warning(
                    f"[{self.account_name}] {selected_card['name']} is on cooldown and cooldown is less than 180 seconds..."
                )
                log.warning(
                    f"[{self.account_name}] Waiting for {selected_card['cooldownSeconds'] + 2} seconds..."
                )

                time.sleep(selected_card["cooldownSeconds"] + 2)
                selected_card["cooldownSeconds"] = 0

            if (
                "cooldownSeconds" in selected_card
                and selected_card["cooldownSeconds"] > 0
                and not self.config["enable_parallel_upgrades"]
            ):
                log.warning(
                    f"[{self.account_name}] {selected_card['name']} is on cooldown..."
                )
                return False

            if (
                "cooldownSeconds" in selected_card
                and selected_card["cooldownSeconds"] > 0
            ):
                log.warning(
                    f"[{self.account_name}] {selected_card['name']} is on cooldown, Checking for next card..."
                )
                continue

            profitCoefficient = CalculateCardProfitCoefficient(selected_card)
            coefficientLimit = self.config["parallel_upgrades_max_price_per_hour"]

            if (
                profitCoefficient > coefficientLimit
                and self.config["enable_parallel_upgrades"]
            ):
                log.warning(
                    f"[{self.account_name}] {selected_card['name']} is too expensive to buy in parallel..."
                )
                log.warning(
                    f"[{self.account_name}] Cost is: {int(profitCoefficient)} / coin increase in profit. Cost limit: {coefficientLimit}"
                )
                log.warning(
                    f"[{self.account_name}] Adjust `parallel_upgrades_max_price_per_hour` to change this behaviour"
                )
                return False

            current_selected_card = selected_card
            break

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

        return False

    def StartMiniGame(self, AccountConfigData, AccountID):
        if "dailyKeysMiniGames" not in AccountConfigData:
            log.error(f"[{self.account_name}] Unable to get daily keys mini game.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get daily keys mini game.",
                "other_errors",
            )
            return
        minigames = list(AccountConfigData["dailyKeysMiniGames"].values())
        random.shuffle(minigames)
        for game in minigames:
            if game["id"] not in ["Candles", "Tiles"]:
                log.warning(
                    f"[{self.account_name}] Detected new daily mini game {game['id']}, check project github for updates."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}] Detected new daily mini game {game['id']}, check project github for updates.",
                    "other_errors",
                )
                continue

            if game["isClaimed"] == True:
                log.info(
                    f"\033[1;34m[{self.account_name}] Daily mini game {game['id']} already claimed.\033[0m"
                )
                continue

            if game["id"] == "Candles" and game["remainSecondsToNextAttempt"] > 0:
                log.info(
                    f"[{self.account_name}] Daily mini game {game['id']} is on cooldown..."
                )
                continue

            ## check timer.
            url = "https://api.hamsterkombatgame.io/clicker/start-keys-minigame"

            headers = {
                "Access-Control-Request-Headers": "authorization",
                "Access-Control-Request-Method": "POST",
            }

            # Send OPTIONS request
            self.HttpRequest(url, headers, "OPTIONS", 204)

            headers = {
                "Accept": "application/json",
                "Authorization": self.Authorization,
                "Content-Type": "application/json",
            }

            payload = json.dumps({"miniGameId": game["id"]})

            # Send POST request
            response = self.HttpRequest(url, headers, "POST", 200, payload)

            if response is None:
                log.error(
                    f"[{self.account_name}] Unable to start mini game {game['id']}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}] Unable to start mini game {game['id']}.",
                    "other_errors",
                )
                continue

            if "dailyKeysMiniGames" not in response:
                log.error(
                    f"[{self.account_name}] Unable to get daily mini game {game['id']}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}] Unable to get daily mini game {game['id']}.",
                    "other_errors",
                )
                continue

            if response["dailyKeysMiniGames"]["isClaimed"] == True:
                log.info(
                    f"\033[1;34m[{self.account_name}] Daily mini game {game['id']} already claimed.\033[0m"
                )
                continue

            if "remainSecondsToGuess" not in response["dailyKeysMiniGames"]:
                log.error(
                    f"[{self.account_name}] Unable to get daily mini game {game['id']}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}] Unable to get daily keys mini game {game['id']}.",
                    "other_errors",
                )
                continue

            waitTime = 0
            if game["id"] == "Candles":
                waitTime = int(
                    response["dailyKeysMiniGames"]["remainSecondsToGuess"]
                    - random.randint(8, 15)
                )
            elif game["id"] == "Tiles":
                waitTime = random.randint(20, 60)

            if waitTime < 0:
                log.error(
                    f"[{self.account_name}] Unable to claim mini game {game['id']}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}] Unable to claim mini game {game['id']}.",
                    "other_errors",
                )
                continue

            log.info(
                f"[{self.account_name}] Waiting for {waitTime} seconds, Mini-game {game['id']} will be completed in {waitTime} seconds..."
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

            responseGameData = response["dailyKeysMiniGames"]
            startDate = responseGameData["startDate"]
            remainPoints = responseGameData["remainPoints"]
            number = int(
                datetime.datetime.fromisoformat(
                    startDate.replace("Z", "+00:00")
                ).timestamp()
            )
            number_len = len(str(number))
            index = (number % (number_len - 2)) + 1
            res = ""
            score_per_game = {
                "Candles": 0,
                "Tiles": (
                    random.randint(int(remainPoints * 0.1), remainPoints)
                    if remainPoints > 300
                    else remainPoints
                ),
            }

            for i in range(1, number_len + 1):
                if i == index:
                    res += "0"
                else:
                    res += str(random.randint(0, 9))

            score_cipher = 2 * (number + (score_per_game[responseGameData["id"]]))

            data_string = "|".join(
                [
                    res,
                    AccountID,
                    responseGameData["id"],
                    str(score_cipher),
                    base64.b64encode(
                        hashlib.sha256(
                            f"415t1ng{score_cipher}0ra1cum5h0t".encode()
                        ).digest()
                    ).decode(),
                ]
            ).encode()

            cipher_base64 = base64.b64encode(data_string).decode()

            payload = json.dumps(
                {
                    "miniGameId": response["dailyKeysMiniGames"]["id"],
                    "cipher": cipher_base64,
                }
            )

            # Send POST request
            response = self.HttpRequest(url, headers, "POST", 200, payload)

            if response is None:
                log.error(
                    f"[{self.account_name}] Unable to claim mini game {game['id']}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}] Unable to claim mini game {game['id']}.",
                    "other_errors",
                )
                return
            log.info(
                f"[{self.account_name}] Mini game {game['id']} claimed successfully, + {number_to_string(response['bonus'])} {'keys' if game['id'] == 'Candles' else 'coins'}"
            )

        log.info(f"[{self.account_name}] Mini game phase completed.")

    def StartPlaygroundGame(self):
        if not self.config["auto_playground_games"]:
            log.info(f"[{self.account_name}] Playground games are disabled.")
            return

        log.info(f"[{self.account_name}] Starting getting playground games...")

        url = "https://api.hamsterkombatgame.io/clicker/get-promos"
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
            log.error(f"[{self.account_name}] Unable to get playground games.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get playground games.", "other_errors"
            )
            return

        if "promos" not in response:
            log.error(f"[{self.account_name}] Unable to get playground games.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get playground games.", "other_errors"
            )
            return

        promo_count = 0
        shuffled_promos = response["promos"][:]
        random.shuffle(shuffled_promos)
        for promo in shuffled_promos:

            if promo["promoId"] not in SupportedPromoGames:
                log.warning(
                    f"[{self.account_name}] Detected unknown playground game: {promo['title']['en']}. Check project github for updates."
                )
                continue

            if self.CheckPlayGroundGameState(promo, response):
                promoData = SupportedPromoGames[promo["promoId"]]

                promo_count += 1
                if self.GetConfig(
                    "max_promo_games_per_round", 3
                ) != 0 and promo_count > self.GetConfig("max_promo_games_per_round", 3):
                    log.info(
                        f"[{self.account_name}] Maximum number of playground games reached. We will retrieve other games in the next run."
                    )
                    return

                log.info(
                    f"[{self.account_name}] Starting {promoData['name']} Playground game..."
                )
                time.sleep(1)
                promoCode = self.GetPlayGroundGameKey(promoData)
                if promoCode is not None:
                    log.info(
                        f"\033[1;34m[{self.account_name}] {promoData['name']} key: {promoCode}\033[0m"
                    )
                    time.sleep(2)
                    log.info(f"[{self.account_name}] Claiming {promoData['name']}...")
                    self.ClaimPlayGroundGame(promoCode)
                    log.info(
                        f"[{self.account_name}] {promoData['name']} claimed successfully."
                    )

    def ClaimPlayGroundGame(self, promoCode):
        url = "https://api.hamsterkombatgame.io/clicker/apply-promo"

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
                "promoCode": promoCode,
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200, payload)

    def GetPlayGroundGameKey(self, promoData):
        appToken = promoData["appToken"]
        clientId = f"{int(time.time() * 1000)}-{''.join(str(random.randint(0, 9)) for _ in range(19))}"
        if "clientIdType" in promoData and promoData["clientIdType"] == "16str":
            clientId = "".join(
                random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=16)
            )
        if "clientIdType" in promoData and promoData["clientIdType"] == "32str":
            clientId = "".join(
                random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=32)
            )
        if "clientIdType" in promoData and promoData["clientIdType"] == "uuid":
            clientId = str(uuid.uuid4())

        log.info(f"[{self.account_name}] Getting {promoData['name']} key...")
        url = "https://api.gamepromo.io/promo/login-client"

        headers_option = {
            "Host": "api.gamepromo.io",
            "Origin": "",
            "Referer": "",
            "access-control-request-headers": "content-type",
            "access-control-request-method": "POST",
        }

        headers_post = {
            "Host": "api.gamepromo.io",
            "Origin": "",
            "Referer": "",
            "Content-Type": "application/json; charset=utf-8",
        }

        if "userAgent" in promoData and promoData["userAgent"] != None:
            headers_post["User-Agent"] = promoData["userAgent"]
            headers_option["User-Agent"] = promoData["userAgent"]

        if "x-unity-version" in promoData and promoData["x-unity-version"] != None:
            headers_post["X-Unity-Version"] = promoData["x-unity-version"]
            headers_option["X-Unity-Version"] = promoData["x-unity-version"]

        self.HttpRequest(url, headers_option, "OPTIONS", 204, True)

        payloadData = {
            "appToken": appToken,
            "clientId": clientId,
            "clientOrigin": promoData["clientOrigin"],
        }

        if "clientVersion" in promoData and promoData["clientVersion"] != None:
            payloadData["clientVersion"] = promoData["clientVersion"]

        payload = json.dumps(payloadData)

        response = self.HttpRequest(url, headers_post, "POST", 200, payload)
        if response is None:
            log.error(f"[{self.account_name}] Unable to get {promoData['name']} key.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get {promoData['name']} key.",
                "other_errors",
            )
            return None

        if "clientToken" not in response:
            log.error(f"[{self.account_name}] Unable to get {promoData['name']} key.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get {promoData['name']} key.",
                "other_errors",
            )
            return None

        clientToken = response["clientToken"]

        TimeSleep = promoData["delay"] + random.randint(1, 5)
        log.info(f"[{self.account_name}] Waiting for {TimeSleep} seconds...")
        time.sleep(TimeSleep)

        log.info(
            f"[{self.account_name}] Registering event for {promoData['name']} (This may take a while ~5-20 minutes)..."
        )

        url = "https://api.gamepromo.io/promo/register-event"

        headers_post["Authorization"] = f"Bearer {clientToken}"

        response = None

        retryCount = 0
        while retryCount < 20:
            retryCount += 1
            eventID = str(uuid.uuid4())

            if "eventIdType" in promoData:
                if promoData["eventIdType"] == "uuid":
                    eventID = str(uuid.uuid4())
                elif promoData["eventIdType"] == "timestamp":
                    eventID = str(int(datetime.datetime.now().timestamp() * 1000))
                else:
                    eventID = promoData["eventIdType"]

            headers_option["access-control-request-headers"] = (
                "authorization,content-type"
            )

            self.HttpRequest(url, headers_option, "OPTIONS", 204, True)

            PayloadData = {
                "promoId": promoData["promoId"],
                "eventId": eventID,
                "eventOrigin": promoData["eventOrigin"],
            }

            if "eventType" in promoData and promoData["eventType"] != None:
                PayloadData["eventType"] = promoData["eventType"]

            payload = json.dumps(PayloadData)

            response = self.HttpRequest(url, headers_post, "POST", 200, payload, True)

            if response is None or not isinstance(response, dict):
                time.sleep(promoData["retry_delay"] + random.randint(1, 5))
                continue

            if not response.get("hasCode", False):
                time.sleep(promoData["retry_delay"] + random.randint(1, 5))
                continue

            break

        if (
            response is None
            or not isinstance(response, dict)
            or "hasCode" not in response
        ):
            log.error(f"[{self.account_name}] Unable to register event.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to register event.", "other_errors"
            )
            return None
        elif response and "hasCode" in response and not response.get("hasCode"):
            log.error(
                f"[{self.account_name}] Unable to register event, may need to increase retryCount"
            )
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to register event, may need to increase retryCount",
                "other_errors",
            )
            return None
        elif response and "hasCode" in response and response.get("hasCode"):
            log.info(f"[{self.account_name}] Event registered successfully.")

        url = "https://api.gamepromo.io/promo/create-code"

        headers_option["access-control-request-headers"] = "authorization,content-type"

        self.HttpRequest(url, headers_option, "OPTIONS", 204, True)

        payload = json.dumps(
            {
                "promoId": promoData["promoId"],
            }
        )

        response = self.HttpRequest(url, headers_post, "POST", 200, payload)
        if response is None:
            log.error(f"[{self.account_name}] Unable to get {promoData['name']} key.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get {promoData['name']} key.",
                "other_errors",
            )
            return None

        if (
            "promoCode" not in response
            or response.get("promoCode") is None
            or response.get("promoCode") == ""
        ):
            log.error(f"[{self.account_name}] Unable to get {promoData['name']} key.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get {promoData['name']} key.",
                "other_errors",
            )
            return None

        promoCode = response["promoCode"]
        return promoCode

    def CheckPlayGroundGameState(self, promo, promos):
        if not self.config["auto_playground_games"]:
            log.info(f"[{self.account_name}] Playground games are disabled.")
            return False

        if "states" not in promos:
            return True

        for state in promos["states"]:
            if (
                state["promoId"] == promo["promoId"]
                and state["receiveKeysToday"] >= promo["keysPerDay"]
            ):
                log.info(
                    f"\033[1;34m[{self.account_name}] Playground game {SupportedPromoGames[promo['promoId']]['name']} already claimed.\033[0m"
                )
                return False

        return True

    def Start(self):
        log.info(f"[{self.account_name}] Starting account...")

        log.info(f"[{self.account_name}] Getting basic account data...")
        AccountBasicData = self.AccountInfoTelegramRequest()

        if (
            AccountBasicData is None
            or AccountBasicData is False
            or "accountInfo" not in AccountBasicData
            or "id" not in AccountBasicData["accountInfo"]
        ):
            log.error(f"[{self.account_name}] Unable to get account basic data.")
            self.SendTelegramLog(
                f"[{self.account_name}] Unable to get account basic data.",
                "other_errors",
            )
            return

        log.info(
            f"\033[1;35m[{self.account_name}] Account ID: {AccountBasicData['accountInfo']['id']}, Account Name: {AccountBasicData['accountInfo']['name']}\033[0m"
        )
        self.SendTelegramLog(
            f"[{self.account_name}] Account ID: {AccountBasicData['accountInfo']['id']}",
            "account_info",
        )

        log.info(f"[{self.account_name}] Getting account config data...")
        AccountConfigVersionData = None
        if self.configVersion != "":
            AccountConfigVersionData = self.GetAccountConfigVersionRequest()
            log.info(
                f"[{self.account_name}] Account config version: {self.configVersion}"
            )

        AccountConfigData = self.GetAccountConfigRequest()
        if AccountConfigData is None or AccountConfigData is False:
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

        log.info(f"[{self.account_name}] Getting account airdrop tasks...")
        airdropTasksResponse = self.GetListAirDropTasksRequest()

        if airdropTasksResponse is None:
            log.error(f"[{self.account_name}] Failed to get airdrop tasks list.")

        log.info(f"[{self.account_name}] Getting account IP...")
        ipResponse = self.IPRequest()
        if ipResponse is None:
            log.error(f"[{self.account_name}] Failed to get IP.")
            self.SendTelegramLog(
                f"[{self.account_name}] Failed to get IP.", "other_errors"
            )
            return

        log.info(f"[{self.account_name}] Getting account skins...")
        SkinsData = self.GetSkins()
        if SkinsData is None:
            log.error(f"[{self.account_name}] Failed to get skins.")
            self.SendTelegramLog(
                f"[{self.account_name}] Failed to get skins.", "other_errors"
            )

        log.info(
            f"[{self.account_name}] IP: {ipResponse['ip']} Company: {ipResponse['asn_org']} Country: {ipResponse['country_code']}"
        )

        if self.config["auto_finish_mini_game"]:
            log.info(f"[{self.account_name}] Attempting to finish mini game...")
            time.sleep(1)
            self.StartMiniGame(AccountConfigData, AccountBasicData["accountInfo"]["id"])

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

        if (
            self.config["auto_get_daily_task"]
            and tasksResponse is not None
            and "tasks" in tasksResponse
            and isinstance(tasksResponse["tasks"], list)
        ):
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

        if (
            self.config["auto_get_task"]
            and tasksResponse is not None
            and "tasks" in tasksResponse
            and isinstance(tasksResponse["tasks"], list)
        ):
            log.info(f"[{self.account_name}] Checking for available task...")
            selected_task = None
            for task in tasksResponse["tasks"]:
                TaskType = task.get("type", "")
                if task["isCompleted"] == False and (
                    TaskType == "WithLink" or TaskType == "WithLocaleLink"
                ):
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

        self.StartPlaygroundGame()

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

            if balanceCoins <= self.config["auto_upgrade_min"]:
                log.warning(
                    f"[{self.account_name}] Upgrade purchase would decrease balance below minimum limit, aborting."
                )
                return

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
    log.info("\033[1;35mVersion: 2.3\033[0m")
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
