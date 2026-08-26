// Копирует frontend/ → mobile/www/ перед сборкой Capacitor.
// Запускается через `npm run sync-web` и `make sync-web`.
const fs = require("fs");
const path = require("path");

const SRC = path.join(__dirname, "..", "frontend");
const DST = path.join(__dirname, "www");

function rmrf(p) {
  if (!fs.existsSync(p)) return;
  fs.rmSync(p, { recursive: true, force: true });
}

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  let n = 0;
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (entry.name.startsWith(".")) continue;
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) n += copyDir(s, d);
    else {
      fs.copyFileSync(s, d);
      n += 1;
    }
  }
  return n;
}

if (!fs.existsSync(SRC) || !fs.statSync(SRC).isDirectory()) {
  console.error(`[sync-web] missing source: ${SRC}`);
  process.exit(1);
}

console.log(`[sync-web] ${SRC} → ${DST}`);
rmrf(DST);
const count = copyDir(SRC, DST);
if (count < 1) {
  console.error("[sync-web] copied 0 files");
  process.exit(1);
}
console.log(`[sync-web] done (${count} files)`);
