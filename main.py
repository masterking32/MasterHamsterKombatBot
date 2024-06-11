# Developed by: MasterkinG32
# Date: 2024
# Github: https://github.com/masterking32

import datetime
import requests
import json
import time
import logging
from colorlog import ColoredFormatter
from utilities import SortUpgrades, number_to_string

AccountList = [
    {
        "account_name": "Account 1",  # A custom name for the account (not important, just for logs)
        "Authorization": "Bearer Token_Here",  # To get the token, refer to the README.md file
        "UserAgent": "PLACE A USER AGENT HERE",  # Refer to the README.md file to obtain a user agent
        "Proxy": {},  # You can use proxies to avoid getting banned. Use {} for no proxy
        # Example of using a proxy:
        # "Proxy": {
        #   "https": "https://10.10.1.10:3128",
        #   "http": "http://user:pass@10.10.1.10:3128/"
        # },
        "config": {
            "auto_tap": True,  # Enable auto tap by setting it to True, or set it to False to disable
            "auto_free_tap_boost": True,  # Enable auto free tap boost by setting it to True, or set it to False to disable
            "auto_upgrade": True,  # Enable auto upgrade by setting it to True, or set it to False to disable
            "auto_upgrade_start": 2000000,  # Start buying upgrades when the balance is greater than this amount
            "auto_upgrade_min": 100000,  # Stop buying upgrades when the balance is less than this amount
            "recheck_time": 300,  # Time to wait before rechecking the account data in seconds
        },
    },
    # Add more accounts if you want to use multiple accounts
    # {
    #     "account_name": "Account 2",
    #     "Authorization": "Bearer Token_Here",
    #     ...
    # },
]

# Logging configuration
LOG_LEVEL = logging.DEBUG
LOGFORMAT = "%(log_color)s[MasterHamsterKombatBot]%(reset)s |  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger("pythonConfig")
log.setLevel(LOG_LEVEL)
log.addHandler(stream)


class HamsterKombatAccount:
    def __init__(self, account_name, Authorization, UserAgent, Proxy, config):
        self.account_name = account_name
        self.Authorization = Authorization
        self.UserAgent = UserAgent
        self.Proxy = Proxy
        self.config = config
        self.balanceCoins = 0
        self.availableTaps = 0
        self.maxTaps = 0
        self.account_data = None
        self.ProfitPerHour = 0
        self.SpendTokens = 0
        self.recheck_time = config["recheck_time"]

    # Check if the device is an Android device
    def isAndroidDevice(self):
        return "Android" in self.UserAgent

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
            "Host": "api.hamsterkombat.io",
            "Origin": "https://hamsterkombat.io",
            "Referer": "https://hamsterkombat.io/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.UserAgent,
        }

        # Add default headers for Android devices to avoid detection, Not needed for iOS devices
        if self.isAndroidDevice():
            defaultHeaders["HTTP_SEC_CH_UA_PLATFORM"] = '"Android"'
            defaultHeaders["HTTP_SEC_CH_UA_MOBILE"] = "?1"
            defaultHeaders["HTTP_SEC_CH_UA"] = (
                '"Android WebView";v="125", "Chromium";v="125", "Not.A/Brand";v="24"'
            )
            defaultHeaders["HTTP_X_REQUESTED_WITH"] = "org.telegram.messenger.web"

        # Add and replace new headers to default headers
        for key, value in headers.items():
            defaultHeaders[key] = value

        if method == "POST":
            response = requests.post(
                url, headers=headers, data=payload, proxies=self.Proxy
            )
        elif method == "OPTIONS":
            response = requests.options(url, headers=headers, proxies=self.Proxy)
        else:
            print("Invalid method: ", method)
            return False

        if response.status_code != validStatusCodes:
            print("Request failed: ", response.status_code)
            return False

        if method == "OPTIONS":
            return True

        return response.json()

    # Sending sync request
    def syncOptionsRequest(self):
        url = "https://api.hamsterkombat.io/clicker/sync"
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
        url = "https://api.hamsterkombat.io/clicker/upgrades-for-buy"
        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "POST",
        }

        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        return self.HttpRequest(url, headers, "POST", 200)

    def BuyUpgradeRequest(self, UpgradeId):
        url = "https://api.hamsterkombat.io/clicker/buy-upgrade"
        headers = {
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Method": "POST",
        }

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

        return self.HttpRequest(url, headers, "POST", 200, payload)

    def TapRequest(self, tap_count):
        url = "https://api.hamsterkombat.io/clicker/upgrades-for-buy"
        headers = {
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Method": "POST",
        }

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

        return self.HttpRequest(url, headers, "POST", 200, payload)

    def BoostsToBuyListRequest(self):
        url = "https://api.hamsterkombat.io/clicker/boosts-for-buy"
        headers = {
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": "POST",
        }

        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        return self.HttpRequest(url, headers, "POST", 200)

    def BuyBoostRequest(self, boost_id):
        url = "https://api.hamsterkombat.io/clicker/buy-boost"
        headers = {
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Method": "POST",
        }

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

        return self.HttpRequest(url, headers, "POST", 200, payload)

    def getAccountData(self):
        account_data = self.syncOptionsRequest()
        if account_data is None:
            return None

        self.account_data = account_data
        self.balanceCoins = account_data["clickerUser"]["balanceCoins"]
        self.availableTaps = account_data["clickerUser"]["availableTaps"]
        self.maxTaps = account_data["clickerUser"]["maxTaps"]

        return account_data

    def Start(self):
        self.getAccountData()
        log.info(
            f"[{self.account_name}] Account Balance Coins: {number_to_string(self.balanceCoins)}, Available Taps: {self.availableTaps}, Max Taps: {self.maxTaps}"
        )

        if self.config["auto_tap"]:
            log.info(f"[{self.account_name}] Starting to tap...")
            time.sleep(2)
            self.Tap(self.availableTaps)
            log.info(f"[{self.account_name}] Tapping completed successfully.")

        if self.config["auto_tap"] and self.config["auto_free_tap_boost"]:
            log.info(f"[{self.account_name}] Checking for free tap boost...")
            time.sleep(2)
            BoostList = self.BoostsToBuyListRequest()
            if BoostList is not None:
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
                    log.info(
                        f"[{self.account_name}] Free boost found, attempting to buy..."
                    )
                    time.sleep(5)
                    self.BuyBoostRequest(BoostForTapList["id"])
                    log.info(f"[{self.account_name}] Free boost bought successfully")
                    time.sleep(1)
                    log.info(f"[{self.account_name}] Starting to tap...")
                    time.sleep(2)
                    self.Tap(self.availableTaps)
                    log.info(f"[{self.account_name}] Tapping completed successfully.")
                    self.getAccountData()
                    log.info(
                        f"[{self.account_name}] Account Balance Coins: {number_to_string(self.balanceCoins)}, Available Taps: {self.availableTaps}, Max Taps: {self.maxTaps}"
                    )
                else:
                    log.info(f"[{self.account_name}] No free boosts available")
            else:
                log.info(
                    f"[{self.account_name}] Failed to get boost list, retrying in {self.recheck_time} seconds..."
                )
                time.sleep(self.recheck_time)

        elif self.config["auto_tap"] and not self.config["auto_free_tap_boost"]:
            self.getAccountData()
            log.info(
                f"[{self.account_name}] Account Balance Coins: {number_to_string(self.balanceCoins)}, Available Taps: {self.availableTaps}, Max Taps: {self.maxTaps}"
            )

        if (
            self.config["auto_upgrade"]
            and self.balanceCoins >= self.config["auto_upgrade_start"]
        ):
            while self.balanceCoins >= self.config["auto_upgrade_min"]:
                log.info(f"[{self.account_name}] Checking for upgrades...")
                time.sleep(2)
                upgradesResponse = self.UpgradesForBuyRequest()
                if upgradesResponse is None:
                    log.info(
                        f"[{self.account_name}] Failed to get upgrades list, retrying in {self.recheck_time} seconds..."
                    )
                    time.sleep(self.recheck_time)
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
                    log.info(
                        f"[{self.account_name}] No upgrades available, retrying in {self.recheck_time} seconds..."
                    )
                    time.sleep(self.recheck_time)
                    return

                balanceCoins = int(self.balanceCoins)
                log.info(f"[{self.account_name}] Searching for the best upgrades...")

                selected_upgrades = SortUpgrades(upgrades, balanceCoins)
                if len(selected_upgrades) == 0:
                    log.info(
                        f"[{self.account_name}] No upgrades available, retrying in {self.recheck_time} seconds..."
                    )
                    time.sleep(self.recheck_time)
                    break

                log.info(
                    f"[{self.account_name}] Best upgrade is {selected_upgrades[0]['name']} with profit {selected_upgrades[0]['profitPerHourDelta']} and price {number_to_string(selected_upgrades[0]['price'])}, Level: {selected_upgrades[0]['level']}"
                )

                balanceCoins -= selected_upgrades[0]["price"]

                log.info(f"[{self.account_name}] Attempting to buy an upgrade...")
                time.sleep(2)
                upgradesResponse = self.BuyUpgradeRequest(selected_upgrades[0]["id"])
                if upgradesResponse is None:
                    log.info(
                        f"[{self.account_name}] Failed to buy an upgrade, retrying in {self.recheck_time} seconds..."
                    )
                    time.sleep(self.recheck_time)
                    return

                log.info(f"[{self.account_name}] Upgrade bought successfully")
                time.sleep(5)
                self.balanceCoins = balanceCoins
                self.ProfitPerHour += selected_upgrades[0]["profitPerHourDelta"]
                self.SpendTokens += selected_upgrades[0]["price"]

            log.info(f"[{self.account_name}] Upgrades purchase completed successfully.")
            self.getAccountData()
            log.info(
                f"[{self.account_name}] Final account balance: {number_to_string(self.balanceCoins)} coins, Your profit per hour increased by {number_to_string(self.ProfitPerHour)} coins, Spend tokens: {number_to_string(self.SpendTokens)}"
            )
        elif (
            self.config["auto_upgrade"]
            and self.balanceCoins < self.config["auto_upgrade_start"]
        ):
            log.info(
                f"[{self.account_name}] Balance is too low to start buying upgrades, retrying in {self.recheck_time} seconds..."
            )
            time.sleep(self.recheck_time)
            return


def main():
    print("Starting MasterHamsterKombatBot...")


if __name__ == "__main__":
    main()
