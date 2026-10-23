#!/usr/bin/env node
// Prints the packaging artwork to PNG textures, using the site's own typeface and the
// Terrier doodle, so the 3D packaging carries exactly the brand's graphics.
//   node assets/3d/scripts/make_labels.mjs
// Needs Chrome (set CHROME_PATH if it is not in a standard location).
// Output: assets/3d/textures/packaging_<label>.png
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const here = dirname(fileURLToPath(import.meta.url));
const project = resolve(here, "..", "..", "..");
const out = resolve(here, "..", "textures");
mkdirSync(out, { recursive: true });

const chrome = [
  process.env.CHROME_PATH,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
].find((p) => p && existsSync(p));
if (!chrome) throw new Error("Chrome not found. Set CHROME_PATH.");

// Must match PAPER in build_packaging.py so label and carton are the same stock.
const PAPER = "#eee9e0";
const INK = "#0b0b0b";
const font = readFileSync(join(project, "src", "fonts", "archivo-variable.woff2")).toString("base64");

// Same drawing as <Terrier /> in src/components/doodles (156 x 108 units).
const terrier = (x, y, k) => `
  <g transform="translate(${x} ${y}) scale(${k})" fill="none" stroke="${INK}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M30 50 C27 38 25 28 27 16 C32 26 35 36 38 47 C60 43 82 43 98 46 C100 36 101 26 103 18 L108 4 L113 18 L116 17 L122 5 L125 20 C130 22 134 26 134 31 L146 33 C151 34 151 40 146 41 L140 42 C141 50 138 58 130 60 C124 61 118 56 116 50 C114 58 112 64 112 70 L112 98 C112 103 100 103 100 98 L100 82 C84 86 62 86 50 82 L50 98 C50 103 38 103 38 98 L36 78 C30 70 28 58 30 50"/>
    <path d="M121 27 C125 22 131 23 134 28"/>
    <path d="M101 40 C105 45 111 47 116 46"/>
    <path d="M122 46 L123 53 M128 47 L128 55 M134 46 L133 53"/>
    <circle cx="128" cy="31" r="2.2" fill="${INK}" stroke="none"/>
    <ellipse cx="147" cy="37" rx="3.4" ry="3" fill="${INK}" stroke="none"/>
  </g>`;
const wordmark = (x, y, size, anchor = "middle") =>
  `<text x="${x}" y="${y}" font-size="${size}" text-anchor="${anchor}" class="display">SNUGDOG</text>`;
const strap = (x, y, size, anchor = "start") =>
  `<text x="${x}" y="${y}" font-size="${size}" text-anchor="${anchor}" class="label">HOT DOGS FOR HAPPIER HUMANS</text>`;

const LABELS = {
  box_front: [2048, 720, `${wordmark(96, 440, 330, "start")}${strap(104, 560, 46)}${terrier(1400, 150, 3.7)}`],
  box_top: [2048, 880, `${wordmark(1024, 600, 470)}`],
  cup: [1024, 1024, `${wordmark(512, 400, 236)}${terrier(318, 470, 2.5)}${strap(512, 880, 30, "middle")}`],
  bag: [1024, 1024, `${terrier(190, 120, 4.1)}${wordmark(512, 860, 262)}${strap(512, 950, 32, "middle")}`],
};

const browser = await puppeteer.launch({ executablePath: chrome, headless: true });
const page = await browser.newPage();
for (const [name, [w, h, art]] of Object.entries(LABELS)) {
  await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
  await page.setContent(`<!doctype html><style>
    @font-face { font-family: "Archivo"; src: url(data:font/woff2;base64,${font}) format("woff2"); font-weight: 100 900; font-stretch: 62% 125%; }
    html, body { margin: 0; background: ${PAPER}; }
    svg { display: block; }
    text { font-family: "Archivo"; fill: ${INK}; }
    .display { font-weight: 900; font-stretch: 62%; letter-spacing: -0.012em; }
    .label { font-weight: 650; letter-spacing: 0.16em; }
  </style><svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${art}</svg>`);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: join(out, `packaging_${name}.png`) });
  console.log(`packaging_${name}.png  ${w}x${h}`);
}
await browser.close();
