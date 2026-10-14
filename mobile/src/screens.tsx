import React, { useEffect, useState } from "react";
import { Text, View } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { router, useLocalSearchParams } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useApi } from "./api";
import { Alert, Listing, Resolution, Retailer } from "./types";
import retailerDeclarations from "./retailers.json";
import { productUrl, rupees } from "./logic";
import { Button, Card, Empty, Field, Shell, Status, Tag, s } from "./ui";

export function ListingCard({
  listing,
  remove,
}: {
  listing: Listing;
  remove?: () => void;
}) {
  return (
    <Card>
      <View style={s.row}>
        <Tag label={listing.retailer_name} />
        <Tag
          label={
            listing.stale
              ? `${Math.round(listing.age_hours)}h old`
              : "Recent observation"
          }
          good={!listing.stale}
        />
      </View>
      <Text style={s.subtitle}>{listing.title}</Text>
      <Text style={s.body}>
        {Object.values(listing.variant).join(" · ")} · {listing.condition}
      </Text>
      <View style={s.row}>
        <Text style={s.price}>{rupees(listing.price)}</Text>
        <Tag label={listing.availability.replaceAll("_", " ")} />
      </View>
      <Text style={s.body}>{listing.match.reason}</Text>
      <Button
        label="Compare this product"
        onPress={() => router.push(`/product/${listing.id}`)}
      />
      {remove && (
        <Button label="Remove saved product" secondary onPress={remove} />
      )}
    </Card>
  );
}

function Home() {
  const api = useApi();
  const products = useQuery({
    queryKey: ["products", api.base],
    queryFn: () => api.request<Listing[]>("/products"),
    enabled: !!api.base,
  });
  useEffect(() => {
    AsyncStorage.getItem("pulse_onboarded").then((v) => {
      if (!v) router.replace("/onboarding");
    });
  }, []);
  return (
    <Shell
      title={"A better price.\nA clearer decision."}
      subtitle="One product link. Comparable offers. Evidence you can inspect."
    >
      <View style={s.hero}>
        <Tag label="LIVE PRICES ONLY" good />
        <Text style={s.heroTitle}>{"Know what you’re\npaying for."}</Text>
        <Text style={s.heroBody}>
          Compare the exact variant and see the history behind each retailer’s
          price.
        </Text>
        <Button
          label="Paste a product link"
          onPress={() => router.push("/resolve")}
        />
      </View>
      <View style={s.row}>
        <Text style={s.subtitle}>Your next purchase</Text>
        <Button
          label="Search products"
          secondary
          onPress={() => router.push("/search")}
        />
      </View>
      {!api.base && (
        <Empty
          title="Connect your live service"
          body="No demo prices or sample products. Configure your backend to start checking supported retailers."
          action={() => router.push("/settings")}
        />
      )}
      <Status
        loading={products.isLoading}
        error={products.error}
        retry={() => products.refetch()}
      />
      {products.data?.length === 0 && (
        <Empty
          title="No observed products yet"
          body="Paste a supported product link. A price appears only after a successful permitted collection or authorized feed update."
          action={() => router.push("/retailers")}
        />
      )}
      {products.data?.slice(0, 4).map((p) => (
        <ListingCard key={p.id} listing={p} />
      ))}
      <Card>
        <Text style={s.subtitle}>Your data, your decision.</Text>
        <Text style={s.body}>
          Shipping and conditional discounts stay separate. Unknown prices stay
          unknown.
        </Text>
        <Button
          label="How comparisons work"
          secondary
          onPress={() => router.push("/disclosures")}
        />
      </Card>
    </Shell>
  );
}

function Onboarding() {
  const [step, setStep] = useState(0);
  const content = [
    [
      "Every price needs proof.",
      "PricePulse compares exact variants using actual retailer observations. Coverage depends on each source’s permitted access.",
    ],
    [
      "History, without guesses.",
      "History begins when a product is tracked. Recommendations explain the available evidence and never predict future discounts.",
    ],
    [
      "Private to this device.",
      "Saved products and alerts belong to a private device session. No shopping passwords are collected. Affiliate arrangements are disclosed.",
    ],
  ];
  return (
    <Shell title={content[step][0]} subtitle="PRICEPULSE / ANDROID">
      <Card>
        <Text style={{ fontSize: 54 }}>◉</Text>
        <Text style={s.body}>{content[step][1]}</Text>
        <Tag label={`Step ${step + 1} of 3`} />
        <Button
          label={step === 2 ? "Start comparing" : "Continue"}
          onPress={() => {
            if (step < 2) setStep(step + 1);
            else
              AsyncStorage.setItem("pulse_onboarded", "1").then(() =>
                router.replace("/"),
              );
          }}
        />
      </Card>
      <Button
        label="Privacy and affiliate disclosure"
        secondary
        onPress={() => router.push("/disclosures")}
      />
    </Shell>
  );
}

function Resolve() {
  const api = useApi();
  const params = useLocalSearchParams<{ url?: string }>();
  const [url, setUrl] = useState(params.url ?? "");
  useEffect(() => {
    if (params.url) setUrl(params.url);
  }, [params.url]);
  const [inputError, setInputError] = useState("");
  const mutation = useMutation({
    mutationFn: (value: string) =>
      api.request<Resolution>("/resolve", "POST", { url: value }),
  });
  const job = useQuery({
    queryKey: ["collection", mutation.data?.job_id],
    queryFn: () =>
      api.request<Resolution>("/collection/" + mutation.data?.job_id),
    enabled: !!mutation.data?.job_id,
    refetchInterval: (q) =>
      ["complete", "failed"].includes(q.state.data?.status ?? "")
        ? false
        : 2000,
  });
  const result = job.data?.listing ? job.data : mutation.data;
  return (
    <Shell
      title="Find your exact product"
      subtitle="Paste a product URL or shopping app share text."
      back
    >
      {!api.base && (
        <Empty
          title="Connect before checking prices"
          body="The live service fetches retailer pages and keeps provider keys private. Add its address in Settings."
          action={() => router.push("/settings")}
        />
      )}
      <Card>
        <Field
          label="Product link"
          value={url}
          onChange={setUrl}
          placeholder="https://www.retailer.com/product"
        />
        <Button
          label={mutation.isPending ? "Checking product…" : "Identify product"}
          disabled={mutation.isPending || !api.base}
          onPress={() => {
            try {
              setInputError("");
              mutation.mutate(productUrl(url));
            } catch (e) {
              setInputError((e as Error).message);
            }
          }}
        />
        {!!inputError && (
          <Text accessibilityRole="alert" style={s.body}>
            {inputError}
          </Text>
        )}
      </Card>
      <Status loading={mutation.isPending} error={mutation.error} />
      {mutation.data?.job_id && (
        <Card>
          <Tag label={job.data?.status ?? "pending"} />
          <Text style={s.body}>
            {job.data?.message ?? mutation.data.message}
          </Text>
          {job.data?.status === "failed" && (
            <Button
              label="Retry collection"
              secondary
              onPress={() => mutation.mutate(productUrl(url))}
            />
          )}
          <Status error={job.error} retry={() => job.refetch()} />
        </Card>
      )}
      {result?.listing && (
        <Card>
          <Tag label="PRODUCT IDENTIFIED" good />
          <Text style={s.subtitle}>{result.listing.title}</Text>
          <Text style={s.body}>{result.listing.match.reason}</Text>
          <Text style={s.body}>
            {Object.entries(result.listing.variant)
              .map(([k, v]) => `${k}: ${v}`)
              .join(" · ")}
          </Text>
          <Button
            label="Compare retailer offers"
            onPress={() => router.push(`/product/${result.listing!.id}`)}
          />
        </Card>
      )}
      {mutation.data?.status === "unsupported" && (
        <Empty
          title="Price unavailable for this link"
          body={
            mutation.data.message ?? "This retailer has no connected source."
          }
          action={() => router.push("/retailers")}
        />
      )}
      <Card>
        <Text style={s.subtitle}>No account passwords. No guessed prices.</Text>
        <Text style={s.body}>
          Sharing and tracking links are accepted when a connector can resolve
          them safely. Blocked sources stay unavailable.
        </Text>
      </Card>
    </Shell>
  );
}

function Search() {
  const api = useApi();
  const [text, setText] = useState("");
  const [term, setTerm] = useState("");
  const [lat, setLat] = useState(""),
    [lon, setLon] = useState("");
  const grocery = useMutation({
    mutationFn: () => {
      if (
        !text.trim() ||
        !lat.trim() ||
        !lon.trim() ||
        !Number.isFinite(Number(lat)) ||
        !Number.isFinite(Number(lon))
      )
        throw new Error(
          "Enter a product and valid latitude/longitude for local grocery availability.",
        );
      return api.request<{ listings: Listing[] }>(
        "/providers/quickcommerce/search",
        "POST",
        {
          q: text.trim(),
          platform: "BlinkIt",
          lat: Number(lat),
          lon: Number(lon),
        },
      );
    },
  });
  const query = useQuery({
    queryKey: ["search", term, api.base],
    queryFn: () =>
      api.request<Listing[]>("/products?q=" + encodeURIComponent(term)),
    enabled: !!api.base,
  });
  return (
    <Shell
      title="Search observed products"
      subtitle="Search titles from connected sources. Catalogue coverage is never assumed."
      back
    >
      <Card>
        <Field
          label="Product name"
          value={text}
          onChange={setText}
          placeholder="Brand, model or product"
        />
        <Button label="Search" onPress={() => setTerm(text.trim())} />
      </Card>
      <Status
        loading={query.isLoading}
        error={query.error}
        retry={() => query.refetch()}
      />
      {query.data?.length === 0 && (
        <Empty
          title="No observed matches"
          body="Try a product link. We cannot infer a live price from a title alone."
        />
      )}
      {query.data?.map((p) => (
        <ListingCard listing={p} key={p.id} />
      ))}
      <Card>
        <Text style={s.subtitle}>Local groceries · BlinkIt</Text>
        <Text style={s.body}>
          QuickCommerce availability depends on your area. Coordinates are sent
          to the provider only when you search; device location is not accessed.
        </Text>
        <Field
          label="Latitude"
          value={lat}
          onChange={setLat}
          placeholder="Enter your area latitude"
        />
        <Field
          label="Longitude"
          value={lon}
          onChange={setLon}
          placeholder="Enter your area longitude"
        />
        <Button
          label="Search local groceries"
          disabled={grocery.isPending}
          onPress={() => grocery.mutate()}
        />
        <Status loading={grocery.isPending} error={grocery.error} />
        {grocery.data?.listings.length === 0 && (
          <Text style={s.body}>No listings returned for this area.</Text>
        )}
      </Card>
      {grocery.data?.listings.map((p) => (
        <ListingCard key={p.id} listing={p} />
      ))}
    </Shell>
  );
}

function Retailers() {
  const api = useApi();
  const [filter, setFilter] = useState("");
  const query = useQuery({
    queryKey: ["retailers", api.base],
    queryFn: () => api.request<Retailer[]>("/retailers"),
    enabled: !!api.base,
  });
  const declarations: Retailer[] = retailerDeclarations.map((retailer) => ({
    ...retailer,
    status: "Setup required",
    message:
      "Declared retailer integration. Connect the live service to check actual source availability.",
    affiliate: "Unavailable",
    capabilities: [],
  }));
  return (
    <Shell
      title="Retailer directory"
      subtitle={
        api.base
          ? "Implemented connectors and live access are different. Each status reflects actual observations."
          : "Declared integrations. Live availability requires a connected service."
      }
      back
    >
      <Field
        label="Filter retailers"
        value={filter}
        onChange={setFilter}
        placeholder="Search a retailer"
      />
      <Status
        loading={query.isLoading}
        error={query.error}
        retry={() => query.refetch()}
      />
      {(query.data ?? (!api.base ? declarations : []))
        .filter((r) => r.name.toLowerCase().includes(filter.toLowerCase()))
        .map((r) => (
          <Card key={r.id}>
            <View style={s.row}>
              <Text style={s.subtitle}>{r.name}</Text>
              <Tag label={r.status} good={r.status === "Live data available"} />
            </View>
            <Text style={s.body}>{r.message}</Text>
            <Text style={s.body}>
              Affiliate links: {r.affiliate}.{" "}
              {r.capabilities.length
                ? `Capabilities: ${r.capabilities.join(", ")}`
                : "No live capability verified."}
            </Text>
            <Text style={s.footer}>{r.domains.join(" · ")}</Text>
          </Card>
        ))}
    </Shell>
  );
}

function Watchlist() {
  const api = useApi();
  const cache = useQueryClient();
  const query = useQuery({
    queryKey: ["watchlist", api.base],
    queryFn: () => api.request<Listing[]>("/watchlist"),
  });
  const remove = useMutation({
    mutationFn: (id: string) => api.request("/watchlist/" + id, "DELETE"),
    onSuccess: () => cache.invalidateQueries({ queryKey: ["watchlist"] }),
  });
  return (
    <Shell
      title="Saved for later"
      subtitle="Your private device watchlist. Observations keep their original timestamps."
      back
    >
      <Status
        loading={query.isLoading}
        error={query.error ?? remove.error}
        retry={() => query.refetch()}
      />
      {query.data?.length === 0 && (
        <Empty
          title="Nothing saved yet"
          body="Identify a product, then save it from its comparison screen."
        />
      )}
      {query.data?.map((p) => (
        <ListingCard
          key={p.id}
          listing={p}
          remove={() => remove.mutate(p.id)}
        />
      ))}
    </Shell>
  );
}

function Alerts() {
  const api = useApi();
  const cache = useQueryClient();
  const query = useQuery({
    queryKey: ["alerts", api.base],
    queryFn: () => api.request<Alert[]>("/alerts"),
    refetchInterval: 60000,
  });
  const remove = useMutation({
    mutationFn: (id: number) => api.request("/alerts/" + id, "DELETE"),
    onSuccess: () => cache.invalidateQueries({ queryKey: ["alerts"] }),
  });
  return (
    <Shell
      title="Your price targets"
      subtitle="In-app alerts update when actual observations reach your target. Background phone push is not configured."
      back
    >
      <Status
        loading={query.isLoading}
        error={query.error ?? remove.error}
        retry={() => query.refetch()}
      />
      {query.data?.length === 0 && (
        <Empty
          title="No price targets yet"
          body="Set a rupee target on a retailer’s detail screen."
        />
      )}
      {query.data?.map((a) => (
        <Card key={a.id}>
          <Tag
            label={a.triggered ? "Target reached" : "Watching for your target"}
            good={a.triggered}
          />
          <Text style={s.subtitle}>{a.listing.title}</Text>
          <Text style={s.body}>
            {a.listing.retailer_name} · Target {rupees(a.target)} · Observed{" "}
            {rupees(a.listing.price)}
          </Text>
          {a.listing.stale && <Tag label="Observation is stale" />}
          <Button
            label="Open retailer details"
            onPress={() => router.push(`/product/${a.listing.id}?view=detail`)}
          />
          <Button
            label="Delete target"
            secondary
            onPress={() => remove.mutate(a.id)}
          />
        </Card>
      ))}
    </Shell>
  );
}

function Settings() {
  const api = useApi();
  const providers = useQuery({
    queryKey: ["providers", api.base],
    queryFn: () =>
      api.request<
        Record<string, { configured: boolean; message: string; model?: string }>
      >("/providers/status"),
    enabled: !!api.base,
  });
  const [base, setBase] = useState(api.base);
  const [message, setMessage] = useState("");
  const [confirm, setConfirm] = useState(false);
  useEffect(() => setBase(api.base), [api.base]);
  const save = useMutation({
    mutationFn: async () => {
      await api.update(base);
      setMessage("Connection saved. Open Home to load live observations.");
    },
  });
  const erase = useMutation({
    mutationFn: () => api.erase(),
    onSuccess: () => {
      setConfirm(false);
      setMessage("Private saved products and alerts deleted.");
    },
  });
  return (
    <Shell
      title="Make it yours"
      subtitle="Connection and privacy controls."
      back
    >
      <Card>
        <Text style={s.subtitle}>Live service</Text>
        <Field
          label="Backend URL"
          value={base}
          onChange={setBase}
          placeholder="https://your-api.example"
        />
        <Text style={s.body}>
          A public release requires your deployed HTTPS backend. Never enter
          provider keys here.
        </Text>
        <Button
          label="Save connection"
          disabled={save.isPending}
          onPress={() => save.mutate()}
        />
        {save.error && (
          <Text accessibilityRole="alert" style={s.body}>
            {save.error.message}
          </Text>
        )}
        {!!message && <Text style={s.body}>{message}</Text>}
      </Card>
      <Card>
        <Text style={s.subtitle}>Price sources</Text>
        <Text style={s.body}>
          Groq extracts details from accessible retailer pages. Prices need page
          evidence; unavailable shipping, stock and discounts remain unknown.
        </Text>
        {!api.base && (
          <Text style={s.body}>
            Connect the live service to check provider configuration.
          </Text>
        )}
        <Status
          loading={providers.isLoading}
          error={providers.error}
          retry={() => providers.refetch()}
        />
        {Object.entries(providers.data ?? {}).map(([name, provider]) => (
          <View key={name}>
            <Tag
              label={`${name === "groq" ? "Groq" : "QuickCommerce"}: ${provider.configured ? "Configured" : "Setup required"}`}
              good={provider.configured}
            />
            <Text style={s.body}>{provider.message}</Text>
          </View>
        ))}
      </Card>
      <Card>
        <Text style={s.subtitle}>Your private device session</Text>
        <Text style={s.body}>
          Saved products are not synced across devices. Clearing app storage
          loses this device’s access. You can delete server-side saved products
          and targets here.
        </Text>
        <Button
          label={
            confirm ? "Confirm deletion of saved data" : "Delete my saved data"
          }
          secondary
          disabled={erase.isPending}
          onPress={() => (confirm ? erase.mutate() : setConfirm(true))}
        />
        {confirm && (
          <Button
            label="Cancel deletion"
            secondary
            onPress={() => setConfirm(false)}
          />
        )}
        <Status error={erase.error} />
      </Card>
      <Button
        label="Privacy and affiliate disclosure"
        secondary
        onPress={() => router.push("/disclosures")}
      />
      <Button
        label="Read the introduction"
        secondary
        onPress={() => router.push("/onboarding")}
      />
    </Shell>
  );
}

function Disclosures() {
  return (
    <Shell
      title="Trust comes first"
      subtitle="Privacy, prices and affiliate links."
      back
    >
      <Card>
        <Text style={s.subtitle}>Affiliate disclosure</Text>
        <Text style={s.body}>
          An eligible purchase through a configured affiliate link may earn the
          operator a commission at no extra cost to you. No affiliate provider
          is configured in this release. View Deal opens the original product
          URL. Recommendations never consider commissions.
        </Text>
      </Card>
      <Card>
        <Text style={s.subtitle}>Privacy</Text>
        <Text style={s.body}>
          The backend stores a hashed device credential, saved listing IDs,
          price targets, and candidate retailer domains. Native device
          credentials use secure storage. The web preview stores its session
          locally. Product URLs may contain personal tracking identifiers:
          remove them before submission when safe. No shopping passwords,
          precise location, contacts or advertising identifiers are collected.
          Delete saved data in Settings. Public observations are retained as
          product history.
        </Text>
      </Card>
      <Card>
        <Text style={s.subtitle}>Price evidence</Text>
        <Text style={s.body}>
          Prices are observed INR listing prices. Shipping, coupons,
          memberships, bank eligibility and delivery remain unavailable unless
          explicitly supplied. History is per retailer and cannot be
          reconstructed from a current price. Stale observations and uncertain
          matches cannot support a confident buying recommendation.
        </Text>
      </Card>
      <Card>
        <Text style={s.subtitle}>Contact and release policy</Text>
        <Text style={s.body}>
          The operator must supply a public support address and hosted privacy
          policy before store submission. No customer support address has been
          invented.
        </Text>
      </Card>
    </Shell>
  );
}

export function Screen({ page }: { page: string }) {
  const pages: Record<string, React.ReactNode> = {
    home: <Home />,
    onboarding: <Onboarding />,
    resolve: <Resolve />,
    search: <Search />,
    retailers: <Retailers />,
    watchlist: <Watchlist />,
    alerts: <Alerts />,
    settings: <Settings />,
    disclosures: <Disclosures />,
  };
  return (
    pages[page] ?? (
      <Shell title="Page unavailable">
        <Button label="Go home" onPress={() => router.replace("/")} />
      </Shell>
    )
  );
}
