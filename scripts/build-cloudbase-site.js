const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const siteDir = path.join(root, "site");
const distDir = path.join(root, "dist");

if (!fs.existsSync(path.join(siteDir, "index.html"))) {
  throw new Error("site/index.html was not found. Run python build_static_site.py before deploying.");
}

fs.rmSync(distDir, { recursive: true, force: true });
copyDirectory(siteDir, distDir);

console.log(`Copied ${path.relative(root, siteDir)} to ${path.relative(root, distDir)} for CloudBase.`);

function copyDirectory(source, target) {
  fs.mkdirSync(target, { recursive: true });
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const sourcePath = path.join(source, entry.name);
    const targetPath = path.join(target, entry.name);

    if (entry.isDirectory()) {
      copyDirectory(sourcePath, targetPath);
      continue;
    }

    if (entry.isFile()) {
      fs.copyFileSync(sourcePath, targetPath);
    }
  }
}
