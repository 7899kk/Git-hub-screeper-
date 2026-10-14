import { spawnSync } from "node:child_process";
import { copyFile, mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
const result = spawnSync("npm", ["run", "build:web"], {
  cwd: root,
  stdio: "inherit",
  env: {
    ...process.env,
    EXPO_NO_TELEMETRY: "1",
    EXPO_OFFLINE: "1",
    PRICEPULSE_PAGES_BASE_PATH:
      process.env.PRICEPULSE_PAGES_BASE_PATH || "/Git-hub-screeper-",
  },
});
if (result.error) throw result.error;
if (result.status !== 0) process.exit(result.status ?? 1);
const output = resolve(root, "dist/web");
await writeFile(resolve(output, ".nojekyll"), "");
await copyFile(resolve(output, "index.html"), resolve(output, "404.html"));
// GitHub Pages serves these navigation URLs directly, including browser refreshes.
for (const route of [
  "onboarding",
  "resolve",
  "search",
  "retailers",
  "watchlist",
  "alerts",
  "settings",
  "disclosures",
]) {
  await mkdir(resolve(output, route), { recursive: true });
  await copyFile(
    resolve(output, "index.html"),
    resolve(output, route, "index.html"),
  );
}
console.log(
  "GitHub Pages export prepared in mobile/dist/web (no provider secrets or simulated prices).",
);
