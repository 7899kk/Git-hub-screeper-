import React, { createContext, useContext, useEffect, useState } from "react";
import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";
import * as Crypto from "expo-crypto";
import { useQueryClient } from "@tanstack/react-query";
import { apiUrl } from "./logic";

type Connection = {
  base: string;
  update: (url: string) => Promise<void>;
  request: <T>(path: string, method?: string, body?: unknown) => Promise<T>;
  erase: () => Promise<void>;
};
const Context = createContext<Connection | null>(null);
export const useApi = () => {
  const ctx = useContext(Context);
  if (!ctx) throw new Error("Missing connection provider");
  return ctx;
};

async function tokenKey(base: string) {
  return (
    "pulse_token_" +
    (await Crypto.digestStringAsync(Crypto.CryptoDigestAlgorithm.SHA256, base))
  );
}
async function readToken(key: string) {
  return Platform.OS === "web"
    ? AsyncStorage.getItem(key)
    : SecureStore.getItemAsync(key);
}
async function writeToken(key: string, value: string | null) {
  if (Platform.OS === "web") {
    if (value) await AsyncStorage.setItem(key, value);
    else await AsyncStorage.removeItem(key);
  } else if (value) await SecureStore.setItemAsync(key, value);
  else await SecureStore.deleteItemAsync(key);
}

export function ApiProvider({ children }: { children: React.ReactNode }) {
  const [base, setBase] = useState(process.env.EXPO_PUBLIC_API_URL ?? "");
  const [initialized, setInitialized] = useState(false);
  const cache = useQueryClient();
  useEffect(() => {
    AsyncStorage.getItem("pulse_api")
      .then((url) => {
        if (url) setBase(url);
      })
      .catch(() => {})
      .finally(() => setInitialized(true));
  }, []);
  // Share session creation across parallel queries.
  const inFlight = React.useRef(new Map<string, Promise<string>>());
  async function session(url: string): Promise<string> {
    const key = await tokenKey(url);
    const old = await readToken(key);
    if (old) return old;
    const current = inFlight.current.get(url);
    if (current) return current;
    const creating = (async () => {
      const response = await fetch(url + "/sessions", {
        method: "POST",
        signal: AbortSignal.timeout(15000),
      });
      if (!response.ok)
        throw new Error(
          "Live service could not create a private device session.",
        );
      const result: { token: string } = await response.json();
      await writeToken(key, result.token);
      return result.token;
    })();
    inFlight.current.set(url, creating);
    try {
      return await creating;
    } finally {
      inFlight.current.delete(url);
    }
  }
  async function request<T>(
    path: string,
    method = "GET",
    body?: unknown,
  ): Promise<T> {
    if (!initialized) throw new Error("Loading connection settings…");
    if (!base)
      throw new Error(
        "Connect your live service in Settings. No prices are simulated.",
      );
    const url = apiUrl(base, __DEV__);
    const token = await session(url);
    let response: Response;
    try {
      response = await fetch(url + path, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + token,
        },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: AbortSignal.timeout(15000),
      });
    } catch {
      throw new Error(
        "Live service is unreachable. Check your connection and retry. Cached observations retain their timestamps.",
      );
    }
    if (!response.ok) {
      const result = await response
        .json()
        .catch(() => ({ detail: "Live service returned an error." }));
      throw new Error(
        typeof result.detail === "string"
          ? result.detail
          : "The request is invalid. Check your input.",
      );
    }
    return response.status === 204 ? (undefined as T) : response.json();
  }
  async function update(url: string) {
    const next = apiUrl(url.trim(), __DEV__);
    await AsyncStorage.setItem("pulse_api", next);
    cache.clear();
    setBase(next);
  }
  async function erase() {
    await request("/sessions", "DELETE");
    await writeToken(await tokenKey(base), null);
    cache.clear();
  }
  return (
    <Context.Provider value={{ base, update, request, erase }}>
      {children}
    </Context.Provider>
  );
}
