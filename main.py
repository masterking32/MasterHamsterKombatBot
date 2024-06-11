# Developed by: MasterkinG32
# Date: 2024
# Github: https://github.com/masterking32

import datetime
import json
import time
import logging
from colorlog import ColoredFormatter
from utilities import HttpRequest, SortUpgrades, number_to_string

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


# Send sync request [Options]
def syncOptionsRequest():
    url = "https://api.hamsterkombat.io/clicker/sync"
    headers = {
        "Access-Control-Request-Headers": "authorization",
        "Access-Control-Request-Method": "POST",
    }

    HttpRequest(url, headers, "OPTIONS", 204)
    return True


# Getting sync data
def syncRequest():
    url = "https://api.hamsterkombat.io/clicker/sync"
    headers = {
        "Authorization": Authorization,
    }
    return HttpRequest(url, headers, "POST", 200)


# Sync data and get account data
def SyncData():
    syncOptionsRequest()
    response = syncRequest()

    if response is None:
        return None

    if "clickerUser" not in response:
        return None

    return response


#  Get list of upgrades [Options]
def upgradesForBuyOptionsRequest():
    url = "https://api.hamsterkombat.io/clicker/upgrades-for-buy"
    headers = {
        "Access-Control-Request-Headers": "authorization,content-type",
        "Access-Control-Request-Method": "POST",
    }

    HttpRequest(url, headers, "OPTIONS", 204)
    return True


# Get list of upgrades
def upgradesToBuyRequest():
    url = "https://api.hamsterkombat.io/clicker/upgrades-for-buy"
    headers = {
        "Authorization": Authorization,
    }

    return HttpRequest(url, headers, "POST", 200)


# Buy upgrade [Options]
def buyUpgradeOptionRequest():
    url = "https://api.hamsterkombat.io/clicker/buy-upgrade"
    headers = {
        "Access-Control-Request-Headers": "authorization",
        "Access-Control-Request-Method": "POST",
    }

    requests.options(url, headers=headers)
    return True


# Buy upgrade
def buyUpgradeRequest(UpgradeId):
    url = "https://api.hamsterkombat.io/clicker/buy-upgrade"
    headers = {
        "Accept": "application/json",
        "Authorization": Authorization,
        "Content-Type": "application/json",
    }

    payload = json.dumps(
        {
            "upgradeId": UpgradeId,
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),
        }
    )

    return HttpRequest(url, headers, "POST", 200, payload)


# Send upgrade request
def SendBuyRequest(upgrade_id):
    buyUpgradeOptionRequest()
    buyUpgradeRequest(upgrade_id)


# Get upgrade list
def GetUpgradeList():
    upgradesForBuyOptionsRequest()
    response = upgradesToBuyRequest()

    if response is None:
        return None

    return response


def TapOptionRequest():
    url = "https://api.hamsterkombat.io/clicker/upgrades-for-buy"
    headers = {
        "Access-Control-Request-Headers": "authorization,content-type",
        "Access-Control-Request-Method": "POST",
    }

    HttpRequest(url, headers, "OPTIONS", 204)
    return True


def TapRequest(tap_count):
    url = "https://api.hamsterkombat.io/clicker/tap"

    headers = {
        "Accept": "application/json",
        "Authorization": Authorization,
        "Content-Type": "application/json",
    }

    payload = json.dumps(
        {
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),
            "availableTaps": 0,
            "count": int(tap_count),
        }
    )

    return HttpRequest(url, headers, "POST", 200, payload)


def Tap(count):
    TapOptionRequest()
    TapRequest(count)
    return True


def BoostsToBuyListOptionsRequest():
    url = "https://api.hamsterkombat.io/clicker/boosts-for-buy"
    headers = {
        "Access-Control-Request-Headers": "authorization",
        "Access-Control-Request-Method": "POST",
    }

    HttpRequest(url, headers, "OPTIONS", 204)
    return True


def BoostsToBuyListRequest():
    url = "https://api.hamsterkombat.io/clicker/boosts-for-buy"
    headers = {
        "Authorization": Authorization,
    }

    return HttpRequest(url, headers, "POST", 200)


def GetBoostsToBuyList():
    BoostsToBuyListOptionsRequest()
    response = BoostsToBuyListRequest()

    if response is None:
        return None

    return response


def BuyBoostOptionRequest():
    url = "https://api.hamsterkombat.io/clicker/buy-boost"
    headers = {
        "Access-Control-Request-Headers": "authorization,content-type",
        "Access-Control-Request-Method": "POST",
    }

    HttpRequest(url, headers, "OPTIONS", 204)
    return True


def BuyBoostRequest(boost_id):
    url = "https://api.hamsterkombat.io/clicker/buy-boost"
    headers = {
        "Accept": "application/json",
        "Authorization": Authorization,
        "Content-Type": "application/json",
    }

    payload = json.dumps(
        {
            "boostId": boost_id,
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),
        }
    )

    return HttpRequest(url, headers, "POST", 200, payload)


def SendBuyBoostRequest(boost_id):
    BuyBoostOptionRequest()
    BuyBoostRequest(boost_id)


def main():

    # Prompt the user to decide if they want to use AutoTap.
    use_auto_tap: str = input("Do you want to use auto tap? (yes/no): ").strip().lower()

    # Get account data
    account_data = SyncData()
    if account_data is None:
        return

    # Get balance coins
    balanceCoins = account_data["clickerUser"]["balanceCoins"]
    availableTaps = account_data["clickerUser"]["availableTaps"]
    maxTaps = account_data["clickerUser"]["maxTaps"]
    print(
        "Account Balance Coins: ",
        number_to_string(balanceCoins),
        "Available Taps: ",
        availableTaps,
        "Max Taps: ",
        maxTaps,
    )

    if use_auto_tap == "yes":
        print("Starting to tap...")
        time.sleep(2)
        Tap(availableTaps)
        print("Tapping completed successfully.")
        print("Checking for free boosts...")
        while True:
            BoostList = GetBoostsToBuyList()

            if (
                BoostList is None
                or len(BoostList["boostsForBuy"]) == 0
                or "boostsForBuy" not in BoostList
            ):
                print("Failed to get boost list")
                break

            BoostForTapList = None
            for boost in BoostList["boostsForBuy"]:
                if boost["price"] == 0 and boost["id"] == "BoostFullAvailableTaps":
                    BoostForTapList = boost
                    break

            if (
                BoostForTapList is None
                or "price" not in BoostForTapList
                or "cooldownSeconds" not in BoostForTapList
                or BoostForTapList["price"] != 0
                or BoostForTapList["cooldownSeconds"] > 0
            ):
                print("No free boosts available")
                break

            print("Free boost found, attempting to buy...")
            time.sleep(5)
            SendBuyBoostRequest(BoostForTapList["id"])
            print("Free boost bought successfully")
            time.sleep(1)

            account_data = SyncData()
            if account_data is None:
                return
            balanceCoins = account_data["clickerUser"]["balanceCoins"]
            availableTaps = account_data["clickerUser"]["availableTaps"]
            maxTaps = account_data["clickerUser"]["maxTaps"]

            print(
                "Account Balance Coins: ",
                number_to_string(balanceCoins),
                "Available Taps: ",
                availableTaps,
                "Max Taps: ",
                maxTaps,
            )
            print("Starting to tap...")
            time.sleep(3)
            Tap(availableTaps)
            print("Tapping completed successfully.")
            account_data = SyncData()
            if account_data is None:
                return
            balanceCoins = account_data["clickerUser"]["balanceCoins"]
            availableTaps = account_data["clickerUser"]["availableTaps"]
            maxTaps = account_data["clickerUser"]["maxTaps"]
            print(
                "Account Balance Coins: ",
                number_to_string(balanceCoins),
                "Available Taps: ",
                availableTaps,
                "Max Taps: ",
                maxTaps,
            )

    NewProfitPerHour = 0
    SpendTokens = 0
    # Start buying upgrades if balance is more than Upgrades_Start
    if balanceCoins >= Upgrades_Start:
        print("Starting to buy upgrades...")
        while balanceCoins >= Upgrades_Min:
            upgradesResponse = GetUpgradeList()  # Get upgrade list
            if upgradesResponse is None:
                print("Failed to get upgrade list, retrying in 30 seconds...")
                time.sleep(30)
                continue

            if upgradesResponse is None:
                print("Failed to get upgrade list, retrying in 30 seconds...")
                time.sleep(30)
                continue

            # Filter upgrades
            upgrades = [
                item
                for item in upgradesResponse["upgradesForBuy"]
                if not item["isExpired"]
                and item["isAvailable"]
                and item["profitPerHourDelta"] > 0
                and ("cooldownSeconds" not in item or item["cooldownSeconds"] == 0)
            ]

            if len(upgrades) == 0:
                print("No upgrades available, Please try again later...")
                break

            balanceCoins = int(balanceCoins)
            print("Searching for the best upgrades...")

            selected_upgrades = SortUpgrades(upgrades, balanceCoins)
            if len(selected_upgrades) == 0:
                print("No upgrades available, Please try again later...")
                break

            print(
                f"Best upgrade is {selected_upgrades[0]['name']} with profit {selected_upgrades[0]['profitPerHourDelta']} and price {number_to_string(selected_upgrades[0]['price'])}, Level: {selected_upgrades[0]['level']}"
            )
            balanceCoins -= selected_upgrades[0]["price"]
            NewProfitPerHour += selected_upgrades[0]["profitPerHourDelta"]
            SpendTokens += selected_upgrades[0]["price"]
            print("Attempting to buy an upgrade...")
            upgradesResponse = SendBuyRequest(selected_upgrades[0]["id"])
            print("Upgrade bought, New balance: ", number_to_string(balanceCoins))
            time.sleep(5)

        print("Upgrades purchase completed successfully.")

        account_data = SyncData()
        if account_data is None:
            return

        balanceCoins = account_data["clickerUser"]["balanceCoins"]
        print(
            f"Final account balance: {number_to_string(balanceCoins)} coins, Your profit per hour increased by {number_to_string(NewProfitPerHour)} coins, Spend tokens: {number_to_string(SpendTokens)}"
        )
    else:
        print("Balance is too low to start buying upgrades...")


if __name__ == "__main__":
    main()
