import { createConnector } from "../framework.mjs";
export default createConnector({"id": "myntra", "name": "Myntra", "host": "myntra.com", "search": "/", "marker": "/buy", "titlePattern": "class=\"pdp-name\"[^>]*>(.*?)<", "pricePattern": "class=\"pdp-price\"[^>]*>[\\s\\S]*?([\\d,]+)"});
