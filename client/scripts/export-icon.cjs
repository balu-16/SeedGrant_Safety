/* global __dirname */
// Deterministic raster export of our code-native SVG brand mark.
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("@playwright/test");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1024, height: 1024 },
    deviceScaleFactor: 1,
  });
  const svg = fs.readFileSync(
    path.join(__dirname, "../assets/brand/icon.svg"),
    "utf8",
  );
  await page.setContent(
    `<style>body{margin:0}svg{display:block;width:100%;height:100%}</style>${svg}`,
  );
  await page.screenshot({
    path: path.join(__dirname, "../assets/brand/icon.png"),
    omitBackground: true,
  });
  await page.setViewportSize({ width: 64, height: 64 });
  await page.screenshot({
    path: path.join(__dirname, "../assets/brand/favicon.png"),
    omitBackground: true,
  });
  await browser.close();
})();
