import React from "react";
import { Stack } from "expo-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { ApiProvider } from "../api";
import { IncomingShare } from "../IncomingShare";

const client = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 60000, refetchOnWindowFocus: true },
  },
});
export default function Layout() {
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={client}>
        <ApiProvider>
          <StatusBar style="dark" />
          <Stack screenOptions={{ headerShown: false }} />
          <IncomingShare />
        </ApiProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
