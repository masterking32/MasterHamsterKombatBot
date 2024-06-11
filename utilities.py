# Developed by: MasterkinG32
# Date: 2024
# Github: https://github.com/masterking32
import requests
import json


# Sort upgrades by best profit per hour (profitPerHourDelta / price)
# You can change this to sort by price, profitPerHourDelta, level, etc.
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
def HttpRequest(
    url,
    headers,
    method="POST",
    validStatusCodes=200,
    payload=None,
    proxy={},
    UserAgent="",
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
        "User-Agent": UserAgent,
    }

    # Add and replace new headers to default headers
    for key, value in headers.items():
        defaultHeaders[key] = value

    if method == "POST":
        response = requests.post(url, headers=headers, data=payload, proxies=proxy)
    elif method == "OPTIONS":
        response = requests.options(url, headers=headers, proxies=proxy)
    else:
        print("Invalid method: ", method)
        return None

    if response.status_code != validStatusCodes:
        print("Request failed: ", response.status_code)
        return None

    if method == "OPTIONS":
        return True

    return response.json()
