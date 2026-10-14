export function rupees(paise: number | null | undefined) {
  return paise == null
    ? "Unavailable"
    : new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
      }).format(paise / 100);
}
export function targetPaise(value: string): number {
  if (!/^\d+(\.\d{1,2})?$/.test(value.trim()))
    throw new Error(
      "Enter a positive rupee amount with up to two decimal places.",
    );
  const [whole, fraction = ""] = value.trim().split(".");
  const price = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
  if (!Number.isSafeInteger(price) || price <= 0 || price > 1e11)
    throw new Error("Target is outside the supported range.");
  return price;
}
export function productUrl(text: string) {
  const raw = text.trim().match(/https:\/\/[^\s<>]+/)?.[0] ?? text.trim();
  const url = new URL(raw);
  if (
    url.protocol !== "https:" ||
    url.username ||
    url.password ||
    (url.port && url.port !== "443")
  )
    throw new Error("Paste a public HTTPS shopping link without credentials.");
  return url.toString();
}
export function apiUrl(value: string, development: boolean) {
  const url = new URL(value);
  if (
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    (url.protocol !== "https:" && !(development && url.protocol === "http:"))
  )
    throw new Error(
      "Use an HTTPS API address (HTTP is allowed only in development).",
    );
  return value.replace(/\/$/, "");
}
