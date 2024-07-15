// ==UserScript==
// @name         Hamster Kombat Game
// @namespace    http://tampermonkey.net/
// @match        *://*.hamsterkombatgame.io/*
// @grant        none
// ==/UserScript==

(function () {
  "use strict";

  function replaceScriptUrl() {
    const newUrl =
      "https://api.masterking32.com/hamsterkombat.io-telegram-web-app.php"; // Change this to your own URL

    const scripts = document.getElementsByTagName("script");
    for (let script of scripts) {
      if (script.src.includes("telegram-web-app.js")) {
        const newScript = document.createElement("script");
        newScript.src = newUrl;
        newScript.type = "text/javascript";
        script.parentNode.replaceChild(newScript, script);
        console.log("Script URL replaced:", newScript.src);
      }
    }
  }

  const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      if (mutation.addedNodes.length) {
        replaceScriptUrl();
      }
    });
  });

  const config = {
    childList: true,
    subtree: true,
  };

  observer.observe(document.body, config);

  replaceScriptUrl();
})();
