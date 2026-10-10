import { createConnector } from "../framework.mjs";
export default createConnector({"id": "decathlon", "name": "Decathlon India", "host": "decathlon.in", "search": "/search?query=", "marker": "/p/", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"price\"\\s*:\\s*\"?([\\d.]+)"});
