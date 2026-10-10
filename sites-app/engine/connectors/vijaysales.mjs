import { createConnector } from "../framework.mjs";
export default createConnector({"id": "vijaysales", "name": "Vijay Sales", "host": "vijaysales.com", "search": "/search?q=", "marker": "/product/", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"salePrice\"\\s*:\\s*\"?([\\d.]+)"});
