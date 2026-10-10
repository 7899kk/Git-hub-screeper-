import { createConnector } from "../framework.mjs";
export default createConnector({"id": "reliancedigital", "name": "Reliance Digital", "host": "reliancedigital.in", "search": "/search?q=", "marker": "/p/", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"offerPrice\"\\s*:\\s*\"?([\\d.]+)"});
