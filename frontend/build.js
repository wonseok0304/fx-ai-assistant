// Vercel 빌드 스크립트: 정적 파일을 dist/로 복사하고 API_BASE_URL 환경변수를 config.js에 주입한다.
const fs = require("fs");
const path = require("path");

const api = (process.env.API_BASE_URL || "").replace(/\/$/, "");
if (!api) {
  console.error("API_BASE_URL 환경변수가 필요합니다.");
  process.exit(1);
}
const out = path.join(__dirname, "dist");
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out);
for (const f of ["index.html", "style.css", "app.js"]) fs.copyFileSync(path.join(__dirname, f), path.join(out, f));
fs.writeFileSync(path.join(out, "config.js"), `window.API_BASE_URL = ${JSON.stringify(api)};\n`);
console.log("built with API_BASE_URL =", api);
