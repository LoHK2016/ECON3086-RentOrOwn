// Loads our Python package into the browser with Pyodide and calls it.
// All the maths happens in Python (rentorbuy/calc); this file only passes data in and out as JSON.

import type { Estate, Flat, Growth, Option, Recommendation, Result, ScenarioName } from "./types"

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/"

type Pyodide = {
  FS: { mkdirTree(path: string): void; writeFile(path: string, data: string): void }
  globals: { set(name: string, value: unknown): void }
  runPython(code: string): unknown
  runPythonAsync(code: string, options?: { globals?: unknown }): Promise<unknown>
  toPy(value: unknown): unknown
}

declare global {
  interface Window {
    loadPyodide?: (options: { indexURL: string }) => Promise<Pyodide>
  }
}

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script")
    script.src = src
    script.onload = () => resolve()
    script.onerror = () => reject(new Error(`could not load ${src}`))
    document.head.appendChild(script)
  })
}

async function start(): Promise<Pyodide> {
  await loadScript(PYODIDE_URL + "pyodide.js")
  const pyodide = await window.loadPyodide!({ indexURL: PYODIDE_URL })
  const base = import.meta.env.BASE_URL + "py/"
  // "no-cache": ask the server each time, so a new deploy never runs old Python.
  const files: string[] = await (await fetch(base + "files.json", { cache: "no-cache" })).json()
  for (const file of files) {
    const text = await (await fetch(base + file, { cache: "no-cache" })).text()
    const path = "/home/pyodide/" + file
    pyodide.FS.mkdirTree(path.slice(0, path.lastIndexOf("/")))
    pyodide.FS.writeFile(path, text)
  }
  pyodide.runPython("import json, rentorbuy")
  return pyodide
}

let ready: Promise<Pyodide> | null = null

export function loadCalculator(): Promise<Pyodide> {
  if (!ready) ready = start()
  return ready
}

export async function compareScenarios(
  inputs: Record<string, unknown>,
  scenarios: Record<ScenarioName, Growth>,
): Promise<Record<ScenarioName, Result>> {
  const pyodide = await loadCalculator()
  pyodide.globals.set("request_json", JSON.stringify({ inputs, scenarios }))
  const reply = pyodide.runPython(
    "request = json.loads(request_json)\n" +
      "json.dumps(rentorbuy.compare_scenarios(request['inputs'], request['scenarios']))",
  ) as string
  return JSON.parse(reply)
}

export async function recommendEstates(
  estates: Estate[],
  inputs: Record<string, unknown>,
): Promise<Recommendation[]> {
  const pyodide = await loadCalculator()
  pyodide.globals.set("request_json", JSON.stringify({ estates, inputs }))
  const reply = pyodide.runPython(
    "request = json.loads(request_json)\n" +
      "json.dumps(rentorbuy.recommend_estates(request['estates'], request['inputs']))",
  ) as string
  return JSON.parse(reply)
}

// ---- HSBC flat picker: Python calls HSBC from the browser (rentorbuy/valuation.py) ----

/** The ids chosen so far, e.g. {zoneId, districtId, estateId, blockId, floor, flat}. */
export type Chosen = Record<string, string>

async function runValuation(call: string, chosen: Chosen, locale: string): Promise<unknown> {
  const pyodide = await loadCalculator()
  // Each call gets its own globals, so two lookups at once cannot mix up their inputs.
  const scope = pyodide.toPy({ request_json: JSON.stringify({ chosen, locale }) })
  const reply = await pyodide.runPythonAsync(
    "import json\n" +
      "from rentorbuy import valuation, browser\n" +
      "request = json.loads(request_json)\n" +
      `json.dumps(await valuation.${call}(browser.send, request['chosen'], request['locale']))`,
    { globals: scope },
  )
  return JSON.parse(reply as string)
}

const optionCache = new Map<string, Promise<Option[]>>()

/** Choices for the next level (blocks, floors or flats). Each list is asked for once. */
export function hsbcOptions(chosen: Chosen, locale: string): Promise<Option[]> {
  const key = JSON.stringify([chosen, locale])
  if (!optionCache.has(key)) {
    const request = runValuation("get_options", chosen, locale) as Promise<Option[]>
    request.catch(() => optionCache.delete(key)) // let the user try again after a failure
    optionCache.set(key, request)
  }
  return optionCache.get(key)!
}

export function hsbcValuation(chosen: Chosen, locale: string): Promise<Flat> {
  return runValuation("get_valuation", chosen, locale) as Promise<Flat>
}
