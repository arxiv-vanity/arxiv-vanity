// Log when page has been translated by Google Translate
// https://stackoverflow.com/questions/4887156/detecting-google-chrome-translation
document.addEventListener(
  "DOMSubtreeModified",
  function(e) {
    if (e.target.tagName === "HTML") {
      if (e.target.className.match("translated")) {
        var language = e.target.getAttribute("lang");
        gtag("event", "translate", { language: language });
        mixpanel.track("Translate", { language: language });
      }
    }
  },
  true
);
