// Copies the Python calculator and today's data into public/ so the site can load them.
// The scrapers are left out: they never run in the browser.
import { cpSync, mkdirSync, readdirSync, writeFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

const web = dirname(dirname(fileURLToPath(import.meta.url)))
const repo = dirname(web)
const out = join(web, "public", "py")

const files = ["rentorbuy/__init__.py", "rentorbuy/valuation.py", "rentorbuy/browser.py", "rentorbuy/export.py"]
for (const name of readdirSync(join(repo, "rentorbuy", "calc"))) {
  if (name.endsWith(".py")) files.push(`rentorbuy/calc/${name}`)
}
for (const file of files) {
  mkdirSync(dirname(join(out, file)), { recursive: true })
  cpSync(join(repo, file), join(out, file))
}
writeFileSync(join(out, "files.json"), JSON.stringify(files, null, 2))

mkdirSync(join(web, "public", "data"), { recursive: true })
cpSync(join(repo, "data", "latest.json"), join(web, "public", "data", "latest.json"))
console.log(`copied ${files.length} Python files and data/latest.json`)
