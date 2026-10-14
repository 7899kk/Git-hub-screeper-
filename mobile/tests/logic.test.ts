import { test } from "node:test";
import assert from "node:assert/strict";
import { apiUrl, productUrl, rupees, targetPaise } from "../src/logic";

test("prices remain exact integer paise", () => {
  assert.equal(targetPaise("24999.99"), 2499999);
  assert.equal(targetPaise("0.01"), 1);
  for (const bad of ["0", "-1", "1.999", "free", "1e5", "NaN"])
    assert.throws(() => targetPaise(bad));
  assert.equal(rupees(null), "Unavailable");
  assert.match(rupees(10099), /100.99/);
});
test("share text identifies the HTTPS product URL", () => {
  assert.equal(
    productUrl("Check this https://store.example/p?size=blue"),
    "https://store.example/p?size=blue",
  );
  assert.throws(() => productUrl("https://user:pass@store.example/p"));
  assert.throws(() => productUrl("http://store.example/p"));
});
test("release API connection rejects insecure URLs and credentials", () => {
  assert.equal(apiUrl("https://api.example/", false), "https://api.example");
  assert.throws(() => apiUrl("http://api.example", false));
  assert.throws(() => apiUrl("https://secret@api.example", false));
  assert.equal(
    apiUrl("http://192.168.1.2:8010", true),
    "http://192.168.1.2:8010",
  );
});

test("public retailer declarations contain no prices and match the backend directory", async () => {
  const { readFileSync } = await import("node:fs");
  const frontend = JSON.parse(readFileSync("src/retailers.json", "utf8"));
  const backend = JSON.parse(
    readFileSync("../pulse_api/retailers.json", "utf8"),
  );
  assert.deepEqual(frontend, backend);
  assert.ok(
    frontend.every(
      (r: Record<string, unknown>) => !("price" in r) && !("timestamp" in r),
    ),
  );
});
