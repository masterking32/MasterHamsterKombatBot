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
import sys
from banner import show_banner
import warna as w

try:
    from config import *
except ImportError:
    clear_screen()
    print(
        f"""
    ==============================================================================
                    \033[31;1mConfig file not found.
    Create a copy of \033[34;1mconfig.py.example and rename it to \033[34;1mconfig.py
    And fill in the required fields.
    ==============================================================================
          """
    )
    exit()

if "ConfigFileVersion" not in locals() or ConfigFileVersion != 1:
    clear_screen()
    print(
        f"""
    ==============================================================================
                  \033[31;1mInvalid config file version.
    Please update the config file to the latest version.
    Create a copy of \033[34;1mconfig.py.example and rename it to config.py
    And fill in the required fields.
    ==============================================================================
    """
    )
    exit()

# ---------------------------------------------#
# Logging configuration
LOG_LEVEL = logging.DEBUG
# Include date and time in the log format
LOGFORMAT = f"{w.cb}[MasterHamsterKombatBot]{w.rs} {w.bt}[%(asctime)s]{w.bt} %(log_color)s[%(levelname)s]%(reset)s %(log_color)s%(message)s%(reset)s"

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
        self.configData = ""

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
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ TelegramLog error: {w.r}{e}"
            )

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
            # "Host": "api.hamsterkombatgame.io",
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
                response = requests.get(
                    url, headers=defaultHeaders, proxies=self.Proxy, timeout=30
                )
            elif method == "POST":
                response = requests.post(
                    url, headers=defaultHeaders, data=payload, proxies=self.Proxy, timeout=30
                )
            elif method == "OPTIONS":
                response = requests.options(
                    url, headers=defaultHeaders, proxies=self.Proxy, timeout=30
                )
            else:
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Invalid method: {w.r}{method}"
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: ✖ Invalid method: {method}",
                    "http_errors",
                )
                return None

            if response.status_code != validStatusCodes:
                if ignore_errors:
                    return None

                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Status code is not {w.r}{validStatusCodes}"
                )
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Response: {w.r}{response.text}"
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: ✖ Status code is not {validStatusCodes}",
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
            log.error(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Error: {w.r}{e}")
            self.SendTelegramLog(f"[{self.account_name}]: ✖ Error: {e}", "http_errors")
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
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🌐 {w.r}Unable to get account data."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: 🌐 Unable to get account data.",
                "other_errors",
            )
            return False

        if "clickerUser" not in account_data:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ {w.r}Invalid account data."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: ✖ Invalid account data.",
                "other_errors",
            )
            return False

        if "balanceCoins" not in account_data["clickerUser"]:
            log.warning(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ⚠ Invalid balance coins."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: ⚠ Invalid balance coins.",
                "other_errors",
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
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🚀 Checking for free tap boost."
        )

        BoostList = self.BoostsToBuyListRequest()
        if BoostList is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖  Failed to get boosts list."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: ✖  Failed to get boosts list.",
                "other_errors",
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
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ⭐ Free boost found, attempting to buy."
            )
            time.sleep(5)
            self.BuyBoostRequest(BoostForTapList["id"])
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 💸 Free boost bought successfully"
            )
            return True
        else:
            log.info(
                f"\033[1;34m{w.rs}{w.g}[{self.account_name}]{w.rs}: 😓 No free boosts available"
            )

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

    def BuySkin(self, skinId):
        url = "https://api.hamsterkombatgame.io/clicker/buy-skin"
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
                "skinId": skinId,
                "timestamp": int(datetime.datetime.now().timestamp()),
            }
        )

        # Send POST request
        return self.HttpRequest(url, headers, "POST", 200, payload=payload)

    def GetTaskReward(self, taskObj):
        if not self.configData:
            return "Unable to get reward data"
        try:
            tasksData = self.configData.get("tasks", [])
            reward = ""
            currentTaskData = next(
                (item for item in tasksData if item["id"] == taskObj["id"]), None
            )
            if currentTaskData.get("id") == "streak_days_special":
                week = taskObj.get("weeks")
                day = taskObj.get("days")
                rewardsByWeeksAndDays = currentTaskData.get("rewardsByWeeksAndDays", [])
                streakTaskRewards = next(
                    (item for item in rewardsByWeeksAndDays if item["week"] == week),
                    None,
                )
                streakTaskDays = streakTaskRewards.get("days")
                streakRewardObject = next(
                    (item for item in streakTaskDays if item["day"] == day), None
                )
                rewardType = next(
                    (
                        key
                        for key in ["coins", "keys", "skinId"]
                        if key in streakRewardObject
                    ),
                    None,
                )
                if rewardType == "skinId":
                    skinsData = self.configData.get("skins", [])
                    rewardSkin = next(
                        (
                            item
                            for item in skinsData
                            if item["id"] == streakRewardObject[rewardType]
                        ),
                        None,
                    )
                    rewardSkinName = rewardSkin.get("name", "")
                reward = (
                    (
                        f"{number_to_string(streakRewardObject[rewardType]) if rewardType != 'skinId' else rewardSkinName} "
                        f"{rewardType if rewardType != 'skinId' else 'skin'}"
                    )
                    if rewardType
                    else " No reward found for this day."
                )
            else:
                reward = (
                    f"{number_to_string(currentTaskData.get('rewardCoins', 0))} coins"
                )

            return reward
        except Exception as e:
            log.error(
                f" ✖  Failed to recognize the reward for {w.r}{taskObj.get('id','')}"
            )
            return ""

    def ClaimDailyCombo(self):
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: {w.y} 🔎 Checking for daily combo..."
        )

        comboUrl = "https://hamstercombos.com/hamstercombos/public/api/hamster-kombat-card-list"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            comboCards = (
                self.HttpRequest(comboUrl, headers, "POST")
                .get("data", {})
                .get("dailyComboCards", [])
            )
        except Exception as e:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ❌ Error fetching combo cards:{w.r} {e}"
            )
            return

        if comboCards is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Combo cards response is incorrect."
            )
            return

        if not comboCards:
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Combo cards info is empty."
            )
            return

        if len(comboCards) < 3:
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Combo cards info is not full."
            )
            return

        upgradesResponse = self.UpgradesForBuyRequest()

        if upgradesResponse is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to get upgrades for buy."
            )
            return

        isClaimed = upgradesResponse.get("dailyCombo", {}).get("isClaimed", False)

        if isClaimed:
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─ Daily combo already claimed.\033[0m"
            )
            return

        currentComboLength = len(
            upgradesResponse.get("dailyCombo", {}).get("upgradeIds", [])
        )

        if currentComboLength == 3 and not isClaimed:
            claimResponse = self.ClaimDailyComboRequest()
            if claimResponse:
                return

        comboCardNames = [card["card_name"].strip().lower() for card in comboCards]
        comboUpgrades = [
            upgrade
            for upgrade in upgradesResponse.get("upgradesForBuy", [])
            if upgrade["name"].lower() in comboCardNames
        ]
        availableUpgrades = [
            card
            for card in comboUpgrades
            if card["isAvailable"] and not card["isExpired"]
        ]

        if len(availableUpgrades) < len(comboUpgrades):
            unavailableUpgrades = [
                item
                for item in comboUpgrades
                if not item["isAvailable"] or item["isExpired"]
            ]
            unavailableUpgradeNames = [
                item["name"]
                for item in unavailableUpgrades
                if not item["isAvailable"] or item["isExpired"]
            ]
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to claim daily combo."
            )
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Some cards are not available for purchase: "
                + ", ".join(unavailableUpgradeNames)
            )
            for card in unavailableUpgrades:
                if card.get("condition", {}):
                    msg = f"{w.rs}{w.g}[{self.account_name}]{w.rs}: To unlock {card['name']} card requires "
                    conditionType = card.get("condition").get("_type")
                    if conditionType == "ByUpgrade":
                        reqUpgrade = next(
                            (
                                upgrade
                                for upgrade in upgradesResponse.get(
                                    "upgradesForBuy", []
                                )
                                if upgrade["id"] == card["condition"]["upgradeId"]
                            ),
                            None,
                        )
                        msg += (
                            f"{reqUpgrade['name']} Lvl: {card['condition']['level']}."
                        )
                    elif conditionType == "MoreReferralsCount":
                        refCount = card["condition"]["moreReferralsCount"]
                        msg += f"{refCount} more refferals."
                    elif conditionType == "ReferralCount":
                        refCount = card["condition"]["referralCount"]
                        msg += f"{refCount} referrals."
                    log.error(msg)
            return

        comboPrice = sum(card.get("price", 0) for card in comboUpgrades)

        if comboPrice > self.balanceCoins:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Not enough coins to buy a daily combo."
            )
            return

        if comboPrice > self.GetConfig("auto_daily_combo_max_price", 5_000_000):
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: The price of the combo {number_to_string(comboPrice)} exceeds the set limit: {number_to_string(self.GetConfig('auto_daily_combo_max_price', 5_000_000))}"
            )
            return

        existsUpgrades = upgradesResponse.get("dailyCombo", {}).get("upgradeIds", [])
        upgradesForBuy = [
            card for card in availableUpgrades if card["id"] not in existsUpgrades
        ]

        buyResult = None
        for card in upgradesForBuy:
            time.sleep(2)
            if card.get("cooldownSeconds", 0) > 0:
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: The card {card['name']} in cooldown, purchase postponed to next loop."
                )
                continue
            elif card.get("price", 0) > self.balanceCoins:
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Not enough coins to buy a card {card['name']}, purchase postponed to next loop."
                )
                continue

            buyResult = self.BuyUpgradeRequest(card["id"])

            if buyResult is None:
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Failed to buy the card {card['name']} for daily combo.."
                )
                continue

            self.balanceCoins = (
                buyResult.get("clickerUser", {}).get("balanceCoins", 0)
                if buyResult.get("clickerUser", {})
                else 0
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: The {card['name']} card has been successfully purchased for daily combo."
            )

        isClaimed = (
            buyResult.get("dailyCombo", {}).get("isClaimed", False)
            if buyResult
            else False
        )
        currentComboLength = (
            len(buyResult.get("dailyCombo", {}).get("upgradeIds", []))
            if buyResult
            else 0
        )

        if currentComboLength == 3 and not isClaimed:
            claimResponse = self.ClaimDailyComboRequest()

    def ClaimDailyComboRequest(self):
        url = "https://api.hamsterkombatgame.io/clicker/claim-daily-combo"
        headers = {
            "Access-Control-Request-Headers": "authorization,content-type",
            "Access-Control-Request-Method": "POST",
        }

        self.HttpRequest(url, headers, "OPTIONS", 204)

        headers = {
            "Accept": "*/*",
            "Authorization": self.Authorization,
        }

        response = self.HttpRequest(url, headers, "POST", 200)

        if response is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ❌ Unable to claim daily combo."
            )
            return False

        if "error_code" in response:
            if response.get("error_code", "") == "DAILY_COMBO_DOUBLE_CLAIMED":
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 👍 Daily combo already claimed."
                )
            elif response.get("error_code", "") == "DAILY_COMBO_NOT_READY":
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🕐 Daily combo not ready to claim."
                )
            return False
        elif "clickerUser" in response:
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 👍 Daily combo successfully claimed."
            )
            return True

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
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖  Failed to buy the card."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: ✖  Failed to buy the card.",
                "other_errors",
            )
            return False

        log.info(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✔ Card bought successfully")
        time.sleep(3)
        self.balanceCoins -= card["price"]
        self.ProfitPerHour += card["profitPerHourDelta"]
        self.SpendTokens += card["price"]
        self.earnPassivePerHour += card["profitPerHourDelta"]

        return True

    def ListBuyOptions(self, selected_upgrades):
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 📃 List of {w.b}{self.GetConfig('show_num_buy_options', 0)}{w.rs} best buy options:"
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
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🃏 {count}: {w.b}{selected_card['name']}{w.rs}"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Profit: {w.g}{selected_card['profitPerHourDelta']}"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Price: {w.y}{number_to_string(selected_card['price'])}"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─ Coefficient: {w.y}{int(profitCoefficient)}{w.rs} Level: {w.b}{selected_card['level']}"
            )
            count = count + 1
            if count > self.GetConfig("show_num_buy_options", 0):
                break

    def BuyBestCard(self):
        log.info(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🃏 Checking for best card.")
        time.sleep(2)
        upgradesResponse = self.UpgradesForBuyRequest()
        if upgradesResponse is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Failed to get upgrades list."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: ✖ Failed to get upgrades list.",
                "other_errors",
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
            log.warning(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🍃 No upgrades available."
            )
            return False

        balanceCoins = int(self.balanceCoins)
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🔼 Searching for the best upgrades."
        )

        selected_upgrades = SortUpgrades(
            upgrades, 999_999_999_999
        )  # Set max budget to a high number
        if len(selected_upgrades) == 0:
            log.warning(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─  No upgrades available."
            )
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
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: {w.b}{w.b}{selected_card['name']}{w.rs}{w.rs} is on cooldown and cooldown is less than 180 seconds."
                )
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ⏳ Waiting for {w.b}{selected_card['cooldownSeconds'] + 2}{w.rs} seconds."
                )

                time.sleep(selected_card["cooldownSeconds"] + 2)
                selected_card["cooldownSeconds"] = 0

            if (
                "cooldownSeconds" in selected_card
                and selected_card["cooldownSeconds"] > 0
                and not self.config["enable_parallel_upgrades"]
            ):
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ⏳ {w.b}{w.b}{selected_card['name']}{w.rs}{w.rs} is on cooldown."
                )
                return False

            if (
                "cooldownSeconds" in selected_card
                and selected_card["cooldownSeconds"] > 0
            ):
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─  {w.b}{selected_card['name']}{w.rs} is on cooldown, Checking for next card."
                )
                continue

            profitCoefficient = CalculateCardProfitCoefficient(selected_card)
            coefficientLimit = self.config["parallel_upgrades_max_price_per_hour"]

            if (
                profitCoefficient > coefficientLimit
                and self.config["enable_parallel_upgrades"]
            ):
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 💥 {w.b}{selected_card['name']}{w.rs} is too expensive to buy in parallel."
                )
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─  Cost: {w.y}{int(profitCoefficient)}"
                )
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─  Coin increase in profit."
                )
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─  Cost limit: {w.r}{coefficientLimit}"
                )

                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─  Adjust `parallel_upgrades_max_price_per_hour` to change this behaviour"
                )
                return False

            current_selected_card = selected_card
            break

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🃏  Best upgrade is {w.b}{current_selected_card['name']}{w.rs}"
        )
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─  Profit: {w.g}{current_selected_card['profitPerHourDelta']}"
        )
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─  Price: {w.y}{number_to_string(current_selected_card['price'])}"
        )
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─  Level: {w.r}{current_selected_card['level']}"
        )

        if balanceCoins < current_selected_card["price"]:
            log.warning(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 😪 Balance is too low to buy the best card."
            )

            self.SendTelegramLog(
                f"[{self.account_name}]: 😪 Balance is too low to buy the best card, Best card: {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}",
                "upgrades",
            )
            return False

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✍ Attempting to buy the best card."
        )
        buy_result = self.BuyCard(current_selected_card)

        if buy_result:
            time.sleep(2)
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✅ Best card purchase completed successfully | profit increased +{w.b}{number_to_string(self.ProfitPerHour)} {w.rs}coins | Spend tokens: {w.y}{number_to_string(self.SpendTokens)}"
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Bought {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}",
                "upgrades",
            )

            return True

        return False

    def StartMiniGame(self, AccountConfigData, AccountID):
        if "dailyKeysMiniGames" not in AccountConfigData:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Unable to get daily keys mini game."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Unable to get daily keys mini game.",
                "other_errors",
            )
            return

        response = self.GetPromos()

        if response is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Unable to get promo games before starting minigames."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Unable to get promo games before starting minigames.",
                "other_errors",
            )
            return

        minigames = list(AccountConfigData["dailyKeysMiniGames"].values())
        random.shuffle(minigames)
        for game in minigames:
            if game["id"] not in ["Candles", "Tiles"]:
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🤖 {w.y}Detected new daily mini game {w.r}{game['id']}, {w.y}check project github for updates."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: Detected new daily mini game {game['id']}, check project github for updates.",
                    "other_errors",
                )
                continue

            if game["isClaimed"] == True:
                log.info(
                    f"\033[1;34m{w.rs}{w.g}[{self.account_name}]{w.rs}: ✅ Daily mini game {w.r}{game['id']} already claimed."
                )
                continue

            if game["id"] == "Candles" and game["remainSecondsToNextAttempt"] > 0:
                log.info(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ⏳ Daily mini game {w.r}{game['id']} is on cooldown."
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
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Unable to start mini game {w.r}{game['id']}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: ✖ Unable to start mini game {game['id']}.",
                    "other_errors",
                )
                continue

            if "dailyKeysMiniGames" not in response:
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Unable to get daily mini game {w.r}{game['id']}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: ✖ Unable to get daily mini game {game['id']}.",
                    "other_errors",
                )
                continue

            if response["dailyKeysMiniGames"]["isClaimed"] == True:
                log.info(
                    f"\033[1;34m{w.rs}{w.g}[{self.account_name}]{w.rs}: 👍 Daily mini game {w.r}{game['id']} already claimed."
                )
                continue

            if "remainSecondsToGuess" not in response["dailyKeysMiniGames"]:
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Unable to get daily mini game {w.r}{game['id']}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: ✖ Unable to get daily keys mini game {game['id']}.",
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
                waitTime = random.randint(35, 120)

            if waitTime < 0:
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 😶 Unable to claim mini game {w.r}{game['id']}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: 😶 Unable to claim mini game {game['id']}.",
                    "other_errors",
                )
                continue

            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ⏳ Waiting for {waitTime} seconds, Mini-game {w.r}{game['id']} will be completed in {waitTime} seconds."
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
            maxMultiplier = (
                min(self.GetConfig("mg_max_tiles_points_percent", 20), 100) / 100
            )
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
                    random.randint(
                        int(remainPoints * 0.01), int(remainPoints * maxMultiplier)
                    )
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
                            f"R1cHard_AnA1{score_cipher}G1ve_Me_y0u7_Pa55w0rD".encode()
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
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Unable to claim mini game {w.r}{game['id']}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: ✖ Unable to claim mini game {game['id']}.",
                    "other_errors",
                )
                return
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Mini game {w.r}{game['id']} claimed successfully | + {number_to_string(response['bonus'])} {'keys' if game['id'] == 'Candles' else 'coins'}"
            )

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✔ Mini game phase completed."
        )

    def GetPromos(self):
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
        return response

    def StartPlaygroundGame(self):
        if not self.config["auto_playground_games"]:
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🤖 Playground games are disabled."
            )
            return

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🔁 {w.y}Starting getting playground games."
        )

        response = self.GetPromos()

        if response is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Unable to get playground games."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Unable to get playground games.",
                "other_errors",
            )
            return

        if "promos" not in response:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Unable to get playground games."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Unable to get playground games.",
                "other_errors",
            )
            return

        promo_count = 0
        shuffled_promos = response["promos"][:]
        random.shuffle(shuffled_promos)

        for promo in shuffled_promos:
            if promo["promoId"] not in SupportedPromoGames:
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🤖 {w.y}Detected unknown playground game: {w.r}{promo['title']['en']}. {w.y}Check project github for updates."
                )

        for promo in shuffled_promos:
            if promo["promoId"] not in SupportedPromoGames:
                continue
            if self.CheckPlayGroundGameState(promo, response):
                promoData = SupportedPromoGames[promo["promoId"]]

                promo_count += 1
                if self.GetConfig(
                    "max_promo_games_per_round", 3
                ) != 0 and promo_count > self.GetConfig("max_promo_games_per_round", 3):
                    log.info(
                        f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Maximum number of playground games reached. We will retrieve other games in the next run."
                    )
                    return

                log.info(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🎮 {w.r}Starting {w.bb}{promoData['name']}{w.r}{w.r} Playground game."
                )
                time.sleep(1)
                promoCode = self.GetPlayGroundGameKey(promoData)
                if promoCode is not None:
                    log.info(
                        f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ {w.bb}{promoData['name']}{w.rs} | key: {w.y}{promoCode}"
                    )
                    time.sleep(2)
                    log.info(
                        f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Claiming {w.bb}{promoData['name']}{w.rs}."
                    )
                    claimResponse = self.ClaimPlayGroundGame(promoCode)
                    if claimResponse is None:
                        log.error(
                            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to claim {w.bb}{promoData['name']}{w.rs} key."
                        )
                        return

                    rewardType = claimResponse.get("reward").get("type")
                    rewardAmount = claimResponse.get("reward").get("amount")

                    log.info(
                        f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─ {w.bb}{promoData['name']}{w.rs} claimed successfully. Aquired {w.y}{number_to_string(rewardAmount)} {rewardType}."
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
        if "clientIdType" in promoData:
            if promoData["clientIdType"] == "16str":
                clientId = "".join(
                    random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=16)
                )
            elif promoData["clientIdType"] == "32str":
                clientId = "".join(
                    random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=32)
                )
            elif promoData["clientIdType"] == "5+32str":
                p1 = "".join(
                    random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=5)
                )
                p2 = "".join(
                    random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=32)
                )
                clientId = f"{p1}_{p2}"
            elif promoData["clientIdType"] == "7digStr":
                clientId = "".join(random.choices("0123456789", k=7))
            elif promoData["clientIdType"] == "16UpStr":
                clientId = "".join(
                    random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=16)
                ).upper()
            elif promoData["clientIdType"] == "ts+19dig":
                ts = str(int(datetime.datetime.now().timestamp() * 1000))
                nums = "".join(random.choices("0123456789", k=19))
                clientId = f"{ts}-{nums}"
            elif promoData["clientIdType"] == "uuid":
                clientId = str(uuid.uuid4())

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Getting {w.bb}{promoData['name']}{w.rs} key."
        )
        url = "https://api.gamepromo.io/promo/login-client"

        if promoData.get("useNewApi"):
            url = "https://api.gamepromo.io/promo/1/login-client"

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
        if (
            promoData.get("useNewApi")
            and promoData["promoId"] == "e68b39d2-4880-4a31-b3aa-0393e7df10c7"
        ):
            headers_post["Authorization"] = "Bearer"

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
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to get {w.bb}{promoData['name']}{w.rs} key."
            )
            self.SendTelegramLog(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to get {promoData['name']} key.",
                "other_errors",
            )
            return None

        if "clientToken" not in response:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to get {w.bb}{promoData['name']}{w.rs}key."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Unable to get {promoData['name']} key.",
                "other_errors",
            )
            return None

        clientToken = response["clientToken"]

        if promoData.get("useNewApi"):
            url = "https://api.gamepromo.io/promo/1/get-client"
            headers_post["Authorization"] = f"Bearer {clientToken}"

            payloadData = {
                "promoId": promoData["promoId"],
            }

            payload = json.dumps(payloadData)

            response = self.HttpRequest(url, headers_post, "POST", 200, payload)
            if response is None:
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to get {w.bb}{promoData['name']}{w.rs} key."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: Unable to get {promoData['name']} key.",
                    "other_errors",
                )
                return None

        TimeSleep = promoData["delay"] + random.randint(1, 5)
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Waiting for {TimeSleep} seconds."
        )
        time.sleep(TimeSleep)

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Registering event for {w.bb}{promoData['name']}{w.rs} (This may take a while ~5-20 minutes)."
        )

        url = "https://api.gamepromo.io/promo/register-event"

        if promoData.get("useNewApi"):
            url = "https://api.gamepromo.io/promo/1/register-event"

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
                elif promoData["eventIdType"] == "16x2str":
                    string = "".join(
                        random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=32)
                    )
                    eventID = f"{string[:16]}-{string[16:]}"
                elif promoData["eventIdType"] == "7dig":
                    eventID = "".join(random.choices("0123456789", k=7))
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
                timeout = promoData["retry_delay"] + random.randint(1, 5)
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Event registration for {w.bb}{promoData['name']}{w.rs} failed, retry in {timeout} seconds."
                )
                time.sleep(timeout)
                continue

            if not response.get("hasCode", False):
                timeout = promoData["retry_delay"] + random.randint(1, 5)
                log.info(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Event registration for {w.bb}{promoData['name']}{w.rs} was successful, but no code was provided, retry in {timeout} seconds."
                )
                time.sleep(timeout)
                continue

            break

        if (
            response is None
            or not isinstance(response, dict)
            or "hasCode" not in response
        ):
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to register event."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Unable to register event.",
                "other_errors",
            )
            return None
        elif response and "hasCode" in response and not response.get("hasCode"):
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to register event, may need to increase retryCount"
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Unable to register event, may need to increase retryCount",
                "other_errors",
            )
            return None
        elif response and "hasCode" in response and response.get("hasCode"):
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Event registered successfully."
            )

        url = "https://api.gamepromo.io/promo/create-code"
        if promoData.get("useNewApi"):
            url = "https://api.gamepromo.io/promo/1/create-code"

        headers_option["access-control-request-headers"] = "authorization,content-type"

        self.HttpRequest(url, headers_option, "OPTIONS", 204, True)

        payload = json.dumps(
            {
                "promoId": promoData["promoId"],
            }
        )

        response = self.HttpRequest(url, headers_post, "POST", 200, payload)
        if response is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to get {w.bb}{promoData['name']}{w.rs} key."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Unable to get {promoData['name']} key.",
                "other_errors",
            )
            return None

        if (
            "promoCode" not in response
            or response.get("promoCode") is None
            or response.get("promoCode") == ""
        ):
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Unable to get {w.bb}{promoData['name']}{w.rs} key."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Unable to get {promoData['name']} key.",
                "other_errors",
            )
            return None

        promoCode = response["promoCode"]
        return promoCode

    def CheckPlayGroundGameState(self, promo, promos):
        if not self.config["auto_playground_games"]:
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Playground games are disabled."
            )
            return False

        if "states" not in promos:
            return True

        for state in promos["states"]:
            if (
                state["promoId"] == promo["promoId"]
                and state["receiveKeysToday"] >= promo["keysPerDay"]
            ):
                log.info(
                    f"\033[1;34m{w.rs}{w.g}[{self.account_name}]{w.rs}: 😉 Playground game {w.bb}{SupportedPromoGames[promo['promoId']]['name']}{w.rs} already claimed."
                )
                return False

        return True

    def Start(self):
        log.info(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🌌 Starting account.")

        log.info(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 📡 Getting account IP.")
        ipResponse = self.IPRequest()
        if ipResponse is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ {w.r}Failed to get IP."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: ✖ Failed to get IP.",
                "other_errors",
            )
            return

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ IP: {w.g}{ipResponse['ip']}"
        )
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Company: {w.g}{ipResponse['asn_org']}"
        )
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─ Country: {w.g}{ipResponse['country_code']}"
        )

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🛸 Getting basic account data."
        )
        AccountBasicData = self.AccountInfoTelegramRequest()

        if (
            AccountBasicData is None
            or AccountBasicData is False
            or "accountInfo" not in AccountBasicData
            or "id" not in AccountBasicData["accountInfo"]
        ):
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Unable to get account basic data."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: ✖ Unable to get account basic data.",
                "other_errors",
            )
            return

        log.info(
            f"\033[1;35m{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Account ID: {w.mb}{AccountBasicData['accountInfo']['id']}"
        )
        log.info(
            f"\033[1;35m{w.rs}{w.g}[{self.account_name}]{w.rs}: └─ Account Name: {w.mb}{AccountBasicData['accountInfo']['name']}"
        )
        self.SendTelegramLog(
            f"[{self.account_name}]: 🔢 Account ID: {AccountBasicData['accountInfo']['id']}",
            "account_info",
        )

        log.info(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🛸 Getting account data.")
        getAccountDataStatus = self.getAccountData()
        if getAccountDataStatus is False:
            return

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 💰 Account Balance Coins: {w.y}{number_to_string(self.balanceCoins)}"
        )
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Available Taps: {w.g}{self.availableTaps}{w.rs} | Max Taps: {w.g}{self.maxTaps}"
        )
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─ Total Keys: {w.r}{self.totalKeys}{w.rs} | Balance Keys: {w.r}{self.balanceKeys}"
        )

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 📝 Getting account config data."
        )
        AccountConfigVersionData = None
        if self.configVersion != "":
            AccountConfigVersionData = self.GetAccountConfigVersionRequest()
            if AccountConfigVersionData.get("config", {}):
                self.configData = AccountConfigVersionData.get("config", {})
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─ Account config version: {w.b}{self.configVersion}"
            )

        AccountConfigData = self.GetAccountConfigRequest()
        if AccountConfigData is None or AccountConfigData is False:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Unable to get account config data."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: ✖ Unable to get account config data.",
                "other_errors",
            )
            return

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🔧 Getting account upgrades."
        )
        upgradesResponse = self.UpgradesForBuyRequest()

        if upgradesResponse is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Failed to get upgrades list."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: ✖ Failed to get upgrades list.",
                "other_errors",
            )
            return

        log.info(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🎯 Getting account tasks.")
        tasksResponse = self.ListTasksRequest()

        if tasksResponse is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Failed to get tasks list."
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: ✖ Failed to get tasks list.",
                "other_errors",
            )

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🪂 Getting account airdrop tasks."
        )
        airdropTasksResponse = self.GetListAirDropTasksRequest()

        if airdropTasksResponse is None:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Failed to get airdrop tasks list."
            )

        log.info(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 👕 Getting account skins.")
        SkinsData = self.GetSkins()
        if SkinsData is None:
            log.error(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ Failed to get skins.")
            self.SendTelegramLog(
                f"[{self.account_name}]: ✖ Failed to get skins.",
                "other_errors",
            )

        DailyCipher = ""
        if (
            self.config["auto_get_daily_cipher"]
            and "dailyCipher" in AccountConfigData
            and "cipher" in AccountConfigData["dailyCipher"]
        ):
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🔎 Decoding daily cipher."
            )
            DailyCipher = DailyCipherDecode(AccountConfigData["dailyCipher"]["cipher"])
            MorseCode = TextToMorseCode(DailyCipher)
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Daily cipher: {w.bb}{DailyCipher}{w.rs}"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─ Morse code: {w.bb}{MorseCode}{w.rs}"
            )

        # temporarily disabled
        # if self.config["auto_finish_mini_game"]:
        #     log.info(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Attempting to finish mini game.")
        #     time.sleep(1)
        #     self.StartMiniGame(AccountConfigData, AccountBasicData["accountInfo"]["id"])

        # Start tapping
        if self.config["auto_tap"]:
            log.info(f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 👇 Starting to tap.")

            # add loading animastion
            def loading_bar(duration):

                bar_length = 40
                end_time = time.time() + duration
                while time.time() < end_time:
                    for i in range(bar_length + 1):
                        percent = (i / bar_length) * 100
                        bar = "█" * i + "-" * (bar_length - i)
                        sys.stdout.write(f"\r[{bar}] {percent:.2f}%")
                        sys.stdout.flush()
                        time.sleep(
                            duration / bar_length
                        )  # Adjust the duration for each step

                # Clear the loading bar
                sys.stdout.write(
                    "\r" + " " * (bar_length + 8) + "\r"
                )  # Clear the bar and percentage
                sys.stdout.flush()

            loading_bar(4)  # ihope is work properly
            # time.sleep(3)

            self.TapRequest(self.availableTaps)
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 👍 Tapping completed successfully."
            )

        if self.config["auto_get_daily_cipher"] and DailyCipher != "":
            if AccountConfigData["dailyCipher"]["isClaimed"] == True:
                log.info(
                    f"\033[1;34m{w.rs}{w.g}[{self.account_name}]{w.rs}: ✅ Daily cipher already claimed."
                )
            else:
                log.info(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✍ Attempting to claim daily cipher."
                )
                time.sleep(2)
                self.ClaimDailyCipherRequest(DailyCipher)
                log.info(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─  Daily cipher claimed successfully."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: 🙌 Daily cipher claimed successfully. Text was: {DailyCipher}, Morse code was: {TextToMorseCode(DailyCipher)}",
                    "daily_cipher",
                )

        if (
            self.config["auto_get_daily_task"]
            and tasksResponse is not None
            and "tasks" in tasksResponse
            and isinstance(tasksResponse["tasks"], list)
        ):
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🎯 Checking for daily task."
            )
            streak_days = None
            for task in tasksResponse["tasks"]:
                if task["id"] == "streak_days_special":
                    streak_days = task
                    break

            if streak_days is None:
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖  Failed to get daily task."
                )
                return

            if streak_days["isCompleted"] == True:
                log.info(
                    f"\033[1;34m{w.rs}{w.g}[{self.account_name}]{w.rs}: ✅ Daily task already completed."
                )
            else:
                log.info(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✍ Attempting to complete daily task."
                )
                day = streak_days.get("days")
                week = streak_days.get("weeks")
                reward = self.GetTaskReward(streak_days)
                reward = f"{w.g}{reward}" if "Unable" not in reward else f"{w.y}{reward}"

                time.sleep(2)
                self.CheckTaskRequest(streak_days["id"])
                log.info(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─  Daily task completed successfully, Week: {w.g}{week}{w.rs}, Day: {w.g}{day}{w.rs}, Reward: {reward}."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: ✅ Daily task completed successfully, Week: {week}, Day: {day}, Reward: {reward}.",
                    "daily_task",
                )

        if (
            self.config["auto_get_task"]
            and tasksResponse is not None
            and "tasks" in tasksResponse
            and isinstance(tasksResponse["tasks"], list)
        ):
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 📃 Checking for available task."
            )
            selected_task = None
            for task in tasksResponse["tasks"]:
                TaskType = task.get("type", "")
                if task["isCompleted"] == False and (
                    task["id"]
                    not in ["select_exchange", "invite_friends", "streak_days_special"]
                ):
                    log.info(
                        f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✍ Attempting to complete Youtube Or Twitter task."
                    )
                    selected_task = task["id"]
                    reward = self.GetTaskReward(task)
                    reward = f"{w.g}{reward}" if "Unable" not in reward else f"{w.y}{reward}"
                    time.sleep(2)
                    self.CheckTaskRequest(selected_task)
                    log.info(
                        f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─  Task completed - id: {w.r}{selected_task}{w.rs}, Reward: {reward}"
                    )
                    self.SendTelegramLog(
                        f"[{self.account_name}]: ✅ Task completed - id: {selected_task}, Reward: {reward}",
                        "daily_task",
                    )
            if selected_task is None:
                log.info(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🙌 Tasks already done"
                )

        try:
            if self.GetConfig("auto_daily_combo_enable", False):
                self.ClaimDailyCombo()
            else:
                log.info(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🎁 Daily combo is disabled."
                )
        except Exception as e:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}:{w.r} Something went wrong while claming daily combo."
            )

        # Start buying free tap boost
        if (
            self.config["auto_tap"]
            and self.config["auto_free_tap_boost"]
            and self.BuyFreeTapBoostIfAvailable()
        ):
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🚀 Starting to tap with free boost."
            )
            time.sleep(2)
            self.TapRequest(self.availableTaps)
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✅ Tapping with free boost completed successfully."
            )

        # Start Syncing account data after tapping
        if self.config["auto_tap"]:
            self.getAccountData()
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 💲 Account Balance Coins: {w.y}{number_to_string(self.balanceCoins)}"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Available Taps: {w.g}{self.availableTaps}{w.rs} | Max Taps: {w.g}{self.maxTaps}"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─ Total Keys: {w.r}{self.totalKeys}{w.rs} | Balance Keys: {w.r}{self.balanceKeys}"
            )

        self.StartPlaygroundGame()

        # Start buying upgrades
        if not self.config["auto_upgrade"]:
            log.error(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🔨 Auto upgrade is disabled."
            )
            return

        self.ProfitPerHour = 0
        self.SpendTokens = 0

        if self.config["wait_for_best_card"]:
            while True:
                if not self.BuyBestCard():
                    break

            self.getAccountData()
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 💰 Final account balance: {w.y}{number_to_string(self.balanceCoins)}{w.rs} coins"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 💹 Profit per hour is {w.y}{number_to_string(self.earnPassivePerHour)}{w.rs} (+{w.g}{number_to_string(self.ProfitPerHour)}{w.rs})"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 💸 Spent: - {w.r}{number_to_string(self.SpendTokens)}"
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: 💰 Final account balance: {number_to_string(self.balanceCoins)} coins, 💹 Your profit per hour is {number_to_string(self.earnPassivePerHour)} (+{number_to_string(self.ProfitPerHour)}), 💸 Spent: {number_to_string(self.SpendTokens)}",
                "upgrades",
            )
            return

        if self.balanceCoins < self.config["auto_upgrade_start"]:
            log.warning(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ⚠ Balance is too low to start buying upgrades."
            )
            return

        while self.balanceCoins >= self.config["auto_upgrade_min"]:
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🔧 Checking for upgrades."
            )
            time.sleep(2)
            upgradesResponse = self.UpgradesForBuyRequest()
            if upgradesResponse is None:
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖ {w.r}Failed to get upgrades list."
                )
                self.SendTelegramLog(
                    f"[{self.account_name}]: ✖ Failed to get upgrades list.",
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
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 😴 No upgrades available."
                )
                return

            balanceCoins = int(self.balanceCoins)
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🔎 Searching for the best upgrades."
            )

            selected_upgrades = SortUpgrades(upgrades, balanceCoins)
            if len(selected_upgrades) == 0:
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 😴 No upgrades available."
                )
                return

            current_selected_card = selected_upgrades[0]
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 🃏 Best upgrade is {w.b}{current_selected_card['name']}"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Profit: {w.g}{current_selected_card['profitPerHourDelta']}"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ├─ Price: {w.y}{number_to_string(current_selected_card['price'])}"
            )
            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: └─ Level: {w.r}{current_selected_card['level']}"
            )

            balanceCoins -= current_selected_card["price"]

            if balanceCoins <= self.config["auto_upgrade_min"]:
                log.warning(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ⚠ Upgrade purchase would decrease balance below {w.r}{self.config['auto_upgrade_min']}{w.rs}, aborting."
                )
                return

            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✍ Attempting to buy an upgrade."
            )
            time.sleep(2)
            upgradesResponse = self.BuyUpgradeRequest(current_selected_card["id"])
            if upgradesResponse is None:
                log.error(
                    f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✖  Failed to buy an upgrade."
                )
                return

            log.info(
                f"{w.rs}{w.g}[{self.account_name}]{w.rs}: ✅ Upgrade bought successfully"
            )
            self.SendTelegramLog(
                f"[{self.account_name}]: Bought {current_selected_card['name']} with profit {current_selected_card['profitPerHourDelta']} and price {number_to_string(current_selected_card['price'])}, Level: {current_selected_card['level']}",
                "upgrades",
            )
            time.sleep(5)
            self.balanceCoins = balanceCoins
            self.ProfitPerHour += current_selected_card["profitPerHourDelta"]
            self.SpendTokens += current_selected_card["price"]
            self.earnPassivePerHour += current_selected_card["profitPerHourDelta"]

        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: Upgrades purchase completed successfully."
        )
        self.getAccountData()
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 💰 Final account balance: {w.y}{number_to_string(self.balanceCoins)}{w.rs} coins"
        )
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 💹 Profit/hour: {w.g}{number_to_string(self.earnPassivePerHour)}{w.rs} (+{w.g}{number_to_string(self.ProfitPerHour)}{w.rs})"
        )
        log.info(
            f"{w.rs}{w.g}[{self.account_name}]{w.rs}: 💸 Spent: {w.r}{number_to_string(self.SpendTokens)}"
        )

        self.SendTelegramLog(
            f"[{self.account_name}]: 💰 Final account balance: {number_to_string(self.balanceCoins)} coins, 💹 Your profit per hour is {number_to_string(self.earnPassivePerHour)} (+{number_to_string(self.ProfitPerHour)}), 💸 Spent: {number_to_string(self.SpendTokens)}",
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
        print(f" {w.y}===============[ STARTING ALL ACCOUNTS ]=============== {w.rs}")
        for account in accounts:
            account.Start()

        if AccountsRecheckTime < 1 and MaxRandomDelay < 1:
            log.error(
                f"{w.r}AccountsRecheckTime{w.rs} and {w.r}MaxRandomDelay{w.rs} values are set to 0, bot will close now."
            )
            return

        if MaxRandomDelay > 0:
            randomDelay = random.randint(1, MaxRandomDelay)
            log.warning(
                f" 😴 Sleeping for {randomDelay} seconds because of random delay."
            )
            time.sleep(randomDelay)

        if AccountsRecheckTime > 0:
            log.warning(
                f" 💤 Rechecking all accounts in {AccountsRecheckTime} seconds."
            )
            time.sleep(AccountsRecheckTime)


def loading_bar2(duration):
    total_steps = 20
    interval = duration / total_steps

    print("Loading:", end=" ", flush=True)

    for i in range(1, total_steps + 1):
        sys.stdout.write(
            f"\rLoading: {'█' * i}{' ' * (total_steps - i)} {int(i * 100 / total_steps)}%"
        )
        sys.stdout.flush()
        time.sleep(interval)

    sys.stdout.write(f"\rLoading: {'█' * total_steps} 100%\n")
    sys.stdout.flush()


def main():
    clear_screen()
    show_banner()
    loading_bar2(5)
    clear_screen()

    try:
        asyncio.run(RunAccounts())
    except KeyboardInterrupt:
        log.error("Bot Stop by user!")


if __name__ == "__main__":
    main()
