<?php
# Developed by: MasterkinG32
# Date: 2024
# Github: https://github.com/masterking32

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: *');
header('Access-Control-Allow-Methods: *');
header('Access-Control-Allow-Credentials: true');

header('Content-Type: application/javascript');

// Set cache for 1 hour
header('Cache-Control: max-age=3600');

// Get content from "https://hamsterkombatgame.io/js/telegram-web-app.js"
$telegram_web_app = file_get_contents('https://hamsterkombatgame.io/js/telegram-web-app.js');

$telegram_web_app = str_replace("return webAppPlatform;", 'return "ios";', $telegram_web_app);

echo $telegram_web_app;
