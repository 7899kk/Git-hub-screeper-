import { createConnector } from "../framework.mjs";
export default createConnector({"id": "tatacliq", "name": "Tata CLiQ", "host": "tatacliq.com", "search": "/search/?searchCategory=all&text=", "marker": "/p-", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"sellingPrice\"\\s*:\\s*([\\d.]+)"});
