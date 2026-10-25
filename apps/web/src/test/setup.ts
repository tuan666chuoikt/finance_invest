import "@testing-library/jest-dom/vitest";

import tokensCss from "../styles/tokens.css?raw";
import appCss from "../styles/app.css?raw";
import shellCss from "../styles/shell.css?raw";
import scenariosCss from "../features/scenarios/scenarios.css?raw";
import tableCss from "../features/scenarios/table.css?raw";

// Feature sheets are appended here by the tasks that create them.
const style = document.createElement("style");
style.dataset.testid = "app-css";
style.textContent = [tokensCss, appCss, shellCss, scenariosCss, tableCss].join("\n");
document.head.appendChild(style);
