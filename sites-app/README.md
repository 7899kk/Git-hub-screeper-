# Actual hosted application source

Live app: https://pricepulse-india.karthik-konijedu.chatgpt.site

These files expose the actual React frontend, original JavaScript collector engine, D1 schema, migrations and tests used by the hosted app. app/api/pulse/route.ts imports engine/connectors/index.mjs and executes the collectors server-side. Successful observations persist in D1. The root Python project is the runnable self-hosted version; Python does not run in Cloudflare Workers.

Flipkart Android share links and copied share text are accepted. The hosted app starts in live mode, opens the collected listing directly, and retains error messages. Real authenticated hosted API checks registered the Lava product and retrieved its listing.

This subdirectory is a source reference for the hosted engine and frontend, not a standalone Sites deployment bundle: generated Sites build integration/helpers, hosting identity and runtime credentials are omitted. Use the repository-root setup instructions for the complete independent runnable Python application, or use a Sites Vinext starter with these app/engine/schema files when migrating the hosted version. No historical prices are inferred from current observations.
