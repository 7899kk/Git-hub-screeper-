import { createConnector } from "../framework.mjs";
export default createConnector({"id": "croma", "name": "Croma", "host": "croma.com", "search": "/searchB?q=", "marker": "/p/", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"price\"\\s*:\\s*\"?([\\d.]+)"});
