# Developed by: MasterkinG32
# Date: 2024
# Github: https://github.com/masterking32

import datetime
import json
import time
import requests

Authorization = "Bearer TOKEN_HERE" # GET from web browser console!
Upgrades_Start = 2000000 # Start upgrades at 2m
Upgrades_Min = 100000 # Upgrades until budget is 100k
UserAgent = "A user agent string here..."

# Sort upgrades by best profit per hour
def SortUpgrades(upgrades, max_budget):
    upgrades = [item for item in upgrades if item["price"] <= max_budget]
    upgrades.sort(key=lambda x: x["price"] / x["profitPerHourDelta"])
    return upgrades

# Convert number to string with k, m, b, t to make it more readable
def number_to_string(num):
    if num < 1000:
        return str(num)
    elif num < 1000000:
        return str(round(num / 1000, 2)) + "k"
    elif num < 1000000000:
        return str(round(num / 1000000, 2)) + "m"
    elif num < 1000000000000:
        return str(round(num / 1000000000, 2)) + "b"
    else:
        return str(round(num / 1000000000000, 2)) + "t"

# Send HTTP requests
def HttpRequest(url, headers, method="POST", validStatusCodes=200, payload=None):
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
        "User-Agent": UserAgent
    }

    # Add and replace new headers to default headers
    for key, value in headers.items():
        defaultHeaders[key] = value

    if method == "POST":
        response = requests.post(url, headers=headers, data=payload)
    elif method == "OPTIONS":
        response = requests.options(url, headers=headers)
    else:
        print("Invalid method: ", method)
        return None

    if response.status_code != validStatusCodes:
        print("Request failed: ", response.status_code)
        return None

    if method == "OPTIONS":
        return True

    return response.json()

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

    payload = json.dumps({
        "upgradeId": UpgradeId,
        "timestamp": int(datetime.datetime.now().timestamp() * 1000)
    })

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

    payload = json.dumps({
        "timestamp": int(datetime.datetime.now().timestamp() * 1000),
        "availableTaps": 0,
        "count": int(tap_count)
    })

    return HttpRequest(url, headers, "POST", 200, payload)

def Tap(count):
    TapOptionRequest()
    TapRequest(count)
    return True

def main():
    # Get account data
    account_data = SyncData()
    if account_data is None:
        return

    # Get balance coins
    balanceCoins = account_data["clickerUser"]["balanceCoins"]
    availableTaps = account_data["clickerUser"]["availableTaps"]
    maxTaps = account_data["clickerUser"]["maxTaps"]

    print("Account Balance Coins: ", number_to_string(balanceCoins), "Available Taps: ", availableTaps, "Max Taps: ", maxTaps)
    print("Starting to tap...")
    Tap(availableTaps)
    print("Tapping completed successfully.")

    account_data = SyncData()
    if account_data is None:
        return
    balanceCoins = account_data["clickerUser"]["balanceCoins"]
    availableTaps = account_data["clickerUser"]["availableTaps"]
    maxTaps = account_data["clickerUser"]["maxTaps"]

    print("Account Balance Coins: ", number_to_string(balanceCoins), "Available Taps: ", availableTaps, "Max Taps: ", maxTaps)

    NewProfitPerHour = 0
    SpendTokens = 0
    # Start buying upgrades if balance is more than Upgrades_Start
    if balanceCoins >= Upgrades_Start:
        print("Starting to buy upgrades...")
        while balanceCoins >= Upgrades_Min:
            upgradesResponse = GetUpgradeList() # Get upgrade list
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
                item for item in upgradesResponse["upgradesForBuy"]
                if not item["isExpired"] and item["isAvailable"] and item["profitPerHourDelta"] > 0 and ("cooldownSeconds" not in item or item["cooldownSeconds"] == 0)
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

            print(f"Best upgrade is {selected_upgrades[0]['name']} with profit {selected_upgrades[0]['profitPerHourDelta']} and price {number_to_string(selected_upgrades[0]['price'])}, Level: {selected_upgrades[0]['level']}")
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
        print(f"Final account balance: {number_to_string(balanceCoins)} coins, Your profit per hour increased by {number_to_string(NewProfitPerHour)} coins, Spend tokens: {number_to_string(SpendTokens)}")
    else:
        print("Balance is too low to start buying upgrades...")

if __name__ == "__main__":
    main()

