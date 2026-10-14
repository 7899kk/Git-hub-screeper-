import React, { useState } from "react";
import { Image, Linking, Text, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useApi } from "./api";
import { History, Listing } from "./types";
import { rupees, targetPaise } from "./logic";
import { Button, Card, Empty, Field, Shell, Status, Tag, s } from "./ui";
import { Chart } from "./Chart";

export function ProductScreen() {
  const { id, view } = useLocalSearchParams<{ id: string; view?: string }>();
  const api = useApi();
  const cache = useQueryClient();
  const [days, setDays] = useState(30),
    [filter, setFilter] = useState("exact"),
    [stock, setStock] = useState(false),
    [retailer, setRetailer] = useState(""),
    [sort, setSort] = useState("low"),
    [excluded, setExcluded] = useState<string[]>([]),
    [target, setTarget] = useState("");
  const product = useQuery({
    queryKey: ["product", id, api.base],
    queryFn: () => api.request<Listing>("/products/" + id),
  });
  const comparison = useQuery({
    queryKey: ["comparison", id, api.base],
    queryFn: () =>
      api.request<{ listings: Listing[]; message: string }>(
        "/products/" + id + "/comparison",
      ),
    enabled: !!product.data,
  });
  const history = useQuery({
    queryKey: ["history", id, days, api.base],
    queryFn: () => api.request<History>(`/products/${id}/history?days=${days}`),
    enabled: !!product.data,
  });
  const analysis = useQuery({
    queryKey: ["analysis", id, days, api.base],
    queryFn: () =>
      api.request<{ label: string; reason: string }>(
        `/products/${id}/analysis?days=${days}`,
      ),
    enabled: !!product.data,
  });
  const save = useMutation({
    mutationFn: () => api.request("/watchlist/" + id, "PUT"),
    onSuccess: () => cache.invalidateQueries({ queryKey: ["watchlist"] }),
  });
  const alert = useMutation({
    mutationFn: () =>
      api.request("/alerts", "PUT", {
        listing_id: id,
        target: targetPaise(target),
      }),
    onSuccess: () => cache.invalidateQueries({ queryKey: ["alerts"] }),
  });
  const deal = useMutation({
    mutationFn: async () => {
      const link = await api.request<{
        url: string;
        affiliate: boolean;
        message: string;
      }>(`/products/${id}/outbound`, "POST");
      await Linking.openURL(link.url);
      return link;
    },
  });
  const discovery = useMutation({
    mutationFn: () =>
      api.request<{ job_id: string }>(`/products/${id}/discover`, "POST"),
  });
  const discoveryStatus = useQuery({
    queryKey: ["discovery", discovery.data?.job_id],
    queryFn: () =>
      api.request<{
        status: string;
        message: string;
        result: {
          sources?: { retailer: string; status: string; message?: string }[];
        };
      }>("/collection/" + discovery.data?.job_id),
    enabled: !!discovery.data?.job_id,
    refetchInterval: (q) =>
      ["complete", "failed"].includes(q.state.data?.status ?? "")
        ? false
        : 3000,
  });
  React.useEffect(() => {
    if (discoveryStatus.data?.status === "complete")
      cache.invalidateQueries({ queryKey: ["comparison", id] });
  }, [discoveryStatus.data?.status, cache, id]);
  const item = product.data;
  const candidates = comparison.data?.listings ?? [];
  const visible = candidates
    .filter(
      (p) =>
        (filter === "all" || p.match.status === filter) &&
        (!stock || p.availability === "in_stock") &&
        (!retailer ||
          p.retailer_name.toLowerCase().includes(retailer.toLowerCase())) &&
        !excluded.includes(p.id),
    )
    .sort((a, b) =>
      sort === "low"
        ? a.price - b.price
        : sort === "high"
          ? b.price - a.price
          : a.age_hours - b.age_hours,
    );
  const cheapest = candidates
    .filter(
      (p) =>
        p.match.status === "exact" && !p.stale && p.availability === "in_stock",
    )
    .sort((a, b) => a.price - b.price)[0];
  return (
    <Shell
      title={
        view === "detail"
          ? "Retailer price detail"
          : view === "history"
            ? "Recorded price history"
            : "Compare with confidence"
      }
      subtitle={item?.retailer_name}
      back
    >
      <Status
        loading={product.isLoading}
        error={product.error}
        retry={() => product.refetch()}
      />
      {item && (
        <>
          <Card>
            <View style={s.row}>
              <Tag label={item.retailer_name} />
              <Tag
                label={
                  item.stale
                    ? "Stale observation"
                    : item.price_evidence
                      ? "Retailer page excerpt"
                      : "Provider observation"
                }
                good={!item.stale}
              />
            </View>
            {item.image && (
              <Image
                source={{ uri: item.image }}
                accessibilityLabel={item.title}
                style={{ width: 160, height: 160, alignSelf: "center" }}
                resizeMode="contain"
              />
            )}
            <Text style={s.subtitle}>{item.title}</Text>
            <Text style={s.body}>
              {Object.entries(item.variant)
                .map(([k, v]) => `${k}: ${v}`)
                .join(" · ")}{" "}
              · {item.condition}
            </Text>
            <Text style={s.price}>{rupees(item.price)}</Text>
            <Text style={s.body}>
              Source: {item.source} ·{" "}
              {new Date(item.timestamp).toLocaleString()} ·{" "}
              {Math.round(item.age_hours)} hours old
            </Text>
            {!!item.price_evidence && (
              <Text style={s.body}>
                Retailer price evidence: {item.price_evidence}
              </Text>
            )}
            <Text style={s.body}>
              Seller: {item.seller ?? "Unavailable"} · Shipping:{" "}
              {rupees(item.shipping)}
            </Text>
            <Text style={s.body}>
              Stock: {item.availability.replaceAll("_", " ")} · Delivery:
              unavailable
            </Text>
            <Text style={s.body}>
              Coupons, bank offers and membership eligibility: unavailable.{" "}
              {item.offers.join(" · ")}
            </Text>
            <Tag
              label={
                item.match.status === "exact"
                  ? "Verified exact variant"
                  : item.match.status
              }
            />
            <Text style={s.body}>{item.match.reason}</Text>
            <View style={s.wrap}>
              <Button
                label={save.isSuccess ? "Saved to watchlist" : "Save product"}
                secondary
                onPress={() => save.mutate()}
                disabled={save.isPending}
              />
              <Button
                label="View Deal"
                onPress={() => deal.mutate()}
                disabled={deal.isPending}
              />
            </View>
            <Text style={s.footer}>
              {deal.data?.message ??
                "Affiliate tracking unavailable. Opens the original product."}
            </Text>
            <Status error={save.error ?? deal.error} />
          </Card>
          <View style={s.wrap}>
            <Button
              label="Comparison"
              secondary
              onPress={() => router.setParams({ view: "compare" })}
            />
            <Button
              label="Retailer detail"
              secondary
              onPress={() => router.setParams({ view: "detail" })}
            />
            <Button
              label="History"
              secondary
              onPress={() => router.setParams({ view: "history" })}
            />
          </View>
          <Card>
            <Text style={s.subtitle}>Find equivalent listings</Text>
            <Text style={s.body}>
              Request a permitted search across implemented retailers. Each
              source can fail independently. New listings remain unverified
              until their identifiers and variants agree.
            </Text>
            <Button
              label="Search other retailers"
              disabled={
                discovery.isPending ||
                ["pending", "running"].includes(
                  discoveryStatus.data?.status ?? "",
                )
              }
              onPress={() => discovery.mutate()}
            />
            <Status error={discovery.error ?? discoveryStatus.error} />
            {discoveryStatus.data && (
              <>
                <Tag label={discoveryStatus.data.status} />
                <Text style={s.body}>{discoveryStatus.data.message}</Text>
                {discoveryStatus.data.result.sources?.map((source) => (
                  <Text key={source.retailer} style={s.body}>
                    {source.retailer}: {source.status}
                    {source.message ? ` · ${source.message}` : ""}
                  </Text>
                ))}
              </>
            )}
          </Card>
          {view !== "detail" && view !== "history" && (
            <>
              <View style={s.row}>
                <Text style={s.subtitle}>Retailer offers</Text>
                <Tag label="Listing prices · INR" />
              </View>
              {cheapest && (
                <Card>
                  <Tag label="LOWEST FRESH EXACT LISTING" good />
                  <Text style={s.subtitle}>
                    {cheapest.retailer_name} · {rupees(cheapest.price)}
                  </Text>
                  <Text style={s.body}>
                    Shipping and conditional discounts are excluded. Check
                    availability at checkout.
                  </Text>
                </Card>
              )}
              <Card>
                <View style={s.wrap}>
                  {["exact", "likely", "similar", "unverified", "all"].map(
                    (f) => (
                      <Button
                        key={f}
                        label={filter === f ? `✓ ${f}` : f}
                        secondary={filter !== f}
                        onPress={() => setFilter(f)}
                      />
                    ),
                  )}
                </View>
                <Field
                  label="Retailer filter"
                  value={retailer}
                  onChange={setRetailer}
                  placeholder="Any retailer"
                />
                <View style={s.wrap}>
                  <Button
                    label={stock ? "In stock only ✓" : "In stock only"}
                    secondary
                    onPress={() => setStock(!stock)}
                  />
                  {["low", "high", "recent"].map((v) => (
                    <Button
                      key={v}
                      label={
                        v === "low"
                          ? "Lowest price"
                          : v === "high"
                            ? "Highest price"
                            : "Most recent"
                      }
                      secondary={sort !== v}
                      onPress={() => setSort(v)}
                    />
                  ))}
                </View>
                {excluded.length > 0 && (
                  <Button
                    label="Restore excluded listings"
                    secondary
                    onPress={() => setExcluded([])}
                  />
                )}
              </Card>
              <Status
                error={comparison.error}
                loading={comparison.isLoading}
                retry={() => comparison.refetch()}
              />
              {!visible.length && (
                <Empty
                  title="No offers match these filters"
                  body="Broaden the filters to review uncertain matches. They will not be labeled as exact products."
                />
              )}
              {visible.map((p) => (
                <Card key={p.id}>
                  <View style={s.row}>
                    <Tag label={p.retailer_name} />
                    <Tag
                      label={
                        p.match.status === "exact"
                          ? "Verified exact match"
                          : p.match.status
                      }
                      good={p.match.status === "exact"}
                    />
                  </View>
                  <Text style={s.subtitle}>{p.title}</Text>
                  <Text style={s.price}>{rupees(p.price)}</Text>
                  <Text style={s.body}>
                    {Object.values(p.variant).join(" · ")} · {p.match.reason}
                  </Text>
                  <Text style={s.body}>
                    {p.stale ? "Stale · " : ""}
                    {new Date(p.timestamp).toLocaleString()} ·{" "}
                    {p.availability.replaceAll("_", " ")}
                  </Text>
                  <Button
                    label="Inspect this retailer"
                    onPress={() => router.push(`/product/${p.id}?view=detail`)}
                  />
                  {p.match.status !== "exact" && (
                    <Button
                      label="Exclude this listing"
                      secondary
                      onPress={() => setExcluded([...excluded, p.id])}
                    />
                  )}
                </Card>
              ))}
            </>
          )}
          {(view === "detail" || view === "history") && (
            <>
              <Card>
                <Text style={s.subtitle}>This retailer’s history</Text>
                <View style={s.wrap}>
                  {[7, 30, 90, 180, 0].map((range) => (
                    <Button
                      key={range}
                      label={range ? `${range} days` : "All available"}
                      secondary={days !== range}
                      onPress={() => setDays(range)}
                    />
                  ))}
                </View>
                <Status
                  loading={history.isLoading}
                  error={history.error}
                  retry={() => history.refetch()}
                />
                {history.data && (
                  <>
                    <View style={s.wrap}>
                      {(
                        ["minimum", "maximum", "average", "median"] as const
                      ).map((k) => (
                        <View key={k} style={s.stat}>
                          <Text style={s.label}>{k}</Text>
                          <Text style={s.statValue}>
                            {rupees(history.data!.statistics[k])}
                          </Text>
                        </View>
                      ))}
                    </View>
                    <Chart points={history.data.points} current={item.price} />
                    <Text style={s.body}>{history.data.message}</Text>
                  </>
                )}
              </Card>
              <Card>
                <Text style={s.subtitle}>
                  {analysis.data?.label ?? "Analyzing observed prices…"}
                </Text>
                <Text style={s.body}>
                  {analysis.data?.reason ??
                    "No recommendation without recorded evidence."}
                </Text>
                <Status error={analysis.error} />
              </Card>
              <Card>
                <Text style={s.subtitle}>Set your price target</Text>
                <Field
                  label="Target price in rupees"
                  numeric
                  value={target}
                  onChange={setTarget}
                  placeholder="e.g. 24999.00"
                />
                <Button
                  label="Save price target"
                  onPress={() => alert.mutate()}
                  disabled={alert.isPending}
                />
                {alert.isSuccess && <Tag label="Target saved" good />}
                <Status error={alert.error} />
                <Text style={s.body}>
                  Targets are checked against actual observations. Alerts appear
                  in the app; background phone push is not configured.
                </Text>
              </Card>
            </>
          )}
        </>
      )}
    </Shell>
  );
}
