import { createConnector } from "../framework.mjs";
export default createConnector({"id": "pepperfry", "name": "Pepperfry", "host": "pepperfry.com", "search": "/search?q=", "marker": "/product/", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"offer_price\"\\s*:\\s*\"?([\\d.]+)"});
