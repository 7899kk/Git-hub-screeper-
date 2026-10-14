import type { ConfigContext } from "expo/config";
export default ({ config }: ConfigContext) => {
  if (process.env.EAS_BUILD_PROFILE === "production") {
    const backend = process.env.EXPO_PUBLIC_API_URL;
    if (!backend || new URL(backend).protocol !== "https:")
      throw new Error(
        "A production build requires EXPO_PUBLIC_API_URL pointing to your deployed HTTPS backend.",
      );
  }
  const pagesPath = process.env.PRICEPULSE_PAGES_BASE_PATH;
  if (pagesPath && !/^\/[A-Za-z0-9][A-Za-z0-9._-]*$/.test(pagesPath)) {
    throw new Error(
      "PRICEPULSE_PAGES_BASE_PATH must be a repository path such as /Git-hub-screeper-.",
    );
  }
  return pagesPath
    ? {
        ...config,
        experiments: { ...config.experiments, baseUrl: pagesPath },
        web: { ...config.web, output: "single" },
      }
    : config;
};
