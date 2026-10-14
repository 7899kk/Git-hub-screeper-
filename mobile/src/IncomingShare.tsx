import { useEffect } from "react";
import { AppState, Platform } from "react-native";
import { router } from "expo-router";
import * as Sharing from "expo-sharing";

export function IncomingShare() {
  useEffect(() => {
    if (Platform.OS !== "android") return;
    function receive() {
      try {
        const payload = Sharing.getSharedPayloads().find(
          (p) => p.shareType === "text" || p.shareType === "url",
        );
        if (payload) {
          router.push({ pathname: "/resolve", params: { url: payload.value } });
          Sharing.clearSharedPayloads();
        }
      } catch {
        /* Expo Go may not expose incoming share configuration; paste remains available. */
      }
    }
    receive();
    const subscription = AppState.addEventListener("change", (state) => {
      if (state === "active") receive();
    });
    return () => subscription.remove();
  }, []);
  return null;
}
