import React from "react";
import { useLocalSearchParams } from "expo-router";
import { Screen } from "../screens";
export default function Page() {
  const { page } = useLocalSearchParams<{ page: string }>();
  return <Screen page={page} />;
}
