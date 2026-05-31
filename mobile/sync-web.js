// Копирует frontend/ → mobile/www/ перед сборкой Capacitor.
// Запускается через `npm run sync-web`.
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'frontend');
const DST = path.join(__dirname, 'www');

function rmrf(p) {
  if (!fs.existsSync(p)) return;
  fs.rmSync(p, { recursive: true, force: true });
}

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

console.log(`[sync-web] ${SRC} → ${DST}`);
rmrf(DST);
copyDir(SRC, DST);
console.log('[sync-web] done');
