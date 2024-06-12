# Developed by: MasterkinG32
# Date: 2024
# Github: https://github.com/masterking32

import datetime
import requests
import json
import time
import logging
import asyncio
import random
from colorlog import ColoredFormatter
from utilities import SortUpgrades, number_to_string

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
            "auto_free_tap_boost": True,  # Enable auto free tap boost by setting it to True, or set it to False to disable
            "auto_upgrade": True,  # Enable auto upgrade by setting it to True, or set it to False to disable
            "auto_upgrade_start": 2000000,  # Start buying upgrades when the balance is greater than this amount
            "auto_upgrade_min": 100000,  # Stop buying upgrades when the balance is less than this amount
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
LOGFORMAT = "%(log_color)s[Master HamsterKombat Bot]%(reset)s[%(log_color)s%(levelname)s%(reset)s] %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger("pythonConfig")
log.setLevel(LOG_LEVEL)
log.addHandler(stream)


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
        self.SpendTokens = 0
        self.account_data = None

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
            if method == "POST":
                response = requests.post(
                    url, headers=headers, data=payload, proxies=self.Proxy
                )
            elif method == "OPTIONS":
                response = requests.options(url, headers=headers, proxies=self.Proxy)
            else:
                log.error(f"[{self.account_name}] Invalid method: {method}")
                return False

            if response.status_code != validStatusCodes:
                log.error(
                    f"[{self.account_name}] Status code is not {validStatusCodes}"
                )
                log.error(f"[{self.account_name}] Response: {response.text}")
                return False

            if method == "OPTIONS":
                return True

            return response.json()
        except Exception as e:
            log.error(f"[{self.account_name}] Error: {e}")
            return False

    # Sending sync request
    def syncRequest(self):
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

        # Send OPTIONS request
        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Authorization": self.Authorization,
        }

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200)

    # Buy an upgrade
    def BuyUpgradeRequest(self, UpgradeId):
        url = "https://api.hamsterkombat.io/clicker/buy-upgrade"
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
        url = "https://api.hamsterkombat.io/clicker/tap"
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
        url = "https://api.hamsterkombat.io/clicker/boosts-for-buy"
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
        url = "https://api.hamsterkombat.io/clicker/buy-boost"
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
            return False

        if "clickerUser" not in account_data:
            log.error(f"[{self.account_name}] Invalid account data.")
            return False

        if "balanceCoins" not in account_data["clickerUser"]:
            log.error(f"[{self.account_name}] Invalid balance coins.")
            return False

        self.account_data = account_data
        self.balanceCoins = account_data["clickerUser"]["balanceCoins"]
        self.availableTaps = account_data["clickerUser"]["availableTaps"]
        self.maxTaps = account_data["clickerUser"]["maxTaps"]

        return account_data

    def BuyFreeTapBoostIfAvailable(self):
        log.info(f"[{self.account_name}] Checking for free tap boost...")

        BoostList = self.BoostsToBuyListRequest()
        if BoostList is None:
            log.error(f"[{self.account_name}] Failed to get boosts list.")
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
            log.warning(f"[{self.account_name}] No free boosts available")

        return False

    def MeTelegramRequest(self):
        url = "https://api.hamsterkombat.io/auth/me-telegram"
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
        url = "https://api.hamsterkombat.io/clicker/list-tasks"
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
        url = "https://api.hamsterkombat.io/clicker/list-airdrop-tasks"
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
            return

        log.debug(
            f"[{self.account_name}] Account ID: {AccountBasicData['telegramUser']['id']}, Account detected as bot: {AccountBasicData['telegramUser']['isBot']}"
        )

        log.info(f"[{self.account_name}] Getting account data...")
        getAccountDataStatus = self.getAccountData()
        if getAccountDataStatus is False:
            return

        log.info(
            f"[{self.account_name}] Account Balance Coins: {number_to_string(self.balanceCoins)}, Available Taps: {self.availableTaps}, Max Taps: {self.maxTaps}"
        )

        log.info(f"[{self.account_name}] Getting account upgrades...")
        upgradesResponse = self.UpgradesForBuyRequest()

        if upgradesResponse is None:
            log.error(f"[{self.account_name}] Failed to get upgrades list.")
            return

        log.info(f"[{self.account_name}] Getting account tasks...")
        tasksResponse = self.ListTasksRequest()

        if tasksResponse is None:
            log.error(f"[{self.account_name}] Failed to get tasks list.")
            return

        log.info(f"[{self.account_name}] Getting account airdrop tasks...")
        airdropTasksResponse = self.GetListAirDropTasksRequest()

        if airdropTasksResponse is None:
            log.error(f"[{self.account_name}] Failed to get airdrop tasks list.")
            return

        # Start tapping
        if self.config["auto_tap"]:
            log.info(f"[{self.account_name}] Starting to tap...")
            time.sleep(2)
            self.TapRequest(self.availableTaps)
            log.info(f"[{self.account_name}] Tapping completed successfully.")

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
                f"[{self.account_name}] Account Balance Coins: {number_to_string(self.balanceCoins)}, Available Taps: {self.availableTaps}, Max Taps: {self.maxTaps}"
            )

        # Start buying upgrades
        if not self.config["auto_upgrade"]:
            log.error(f"[{self.account_name}] Auto upgrade is disabled.")
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

            log.info(
                f"[{self.account_name}] Best upgrade is {selected_upgrades[0]['name']} with profit {selected_upgrades[0]['profitPerHourDelta']} and price {number_to_string(selected_upgrades[0]['price'])}, Level: {selected_upgrades[0]['level']}"
            )

            balanceCoins -= selected_upgrades[0]["price"]

            log.info(f"[{self.account_name}] Attempting to buy an upgrade...")
            time.sleep(2)
            upgradesResponse = self.BuyUpgradeRequest(selected_upgrades[0]["id"])
            if upgradesResponse is None:
                log.error(f"[{self.account_name}] Failed to buy an upgrade.")
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


def RunAccounts():
    accounts = []
    for account in AccountList:
        accounts.append(HamsterKombatAccount(account))

    while True:
        log.warning("Starting all accounts...")
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
    log.info("\033[1;35mVersion: 1.5\033[0m")
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
