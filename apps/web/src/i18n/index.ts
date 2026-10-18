import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import vi from "./vi.json";

export const LANG_KEY = "finvest.lang";

function stored(): "vi" | "en" {
  try {
    return localStorage.getItem(LANG_KEY) === "en" ? "en" : "vi";
  } catch {
    return "vi";
  }
}

void i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, vi: { translation: vi } },
  lng: stored(),
  fallbackLng: "vi",
  keySeparator: false, // flat keys such as "nav.rules"
  returnNull: false,
  initImmediate: false,
  interpolation: { escapeValue: false },
});

document.documentElement.lang = i18n.language;
i18n.on("languageChanged", (lng) => {
  document.documentElement.lang = lng;
  try {
    localStorage.setItem(LANG_KEY, lng);
  } catch {
    /* storage blocked: the choice lasts for this session only */
  }
});

export default i18n;
