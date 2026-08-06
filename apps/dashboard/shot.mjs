import { createRequire } from "module";
const require = createRequire("C:/Users/chidv/AppData/Local/npm-cache/_npx/fda707cb69e33483/package.json");
const { chromium } = require("playwright");

const BASE = "http://localhost:3000";

async function snap(page, path, file, wait = 1200) {
  await page.goto(`${BASE}${path}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(wait);
  await page.screenshot({ path: file, fullPage: true });
  console.log(`✓ ${file}`);
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.on("pageerror", (e) => console.log("PAGE ERROR:", e.message));

await snap(page, "/", "shots/dashboard.png");
await snap(page, "/clients", "shots/clients.png");
await snap(page, "/clients/4", "shots/client-detail.png");
await snap(page, "/meetings", "shots/meetings.png");
await snap(page, "/learning", "shots/learning.png");

await browser.close();
console.log("done");
