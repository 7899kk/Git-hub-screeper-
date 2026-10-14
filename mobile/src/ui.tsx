import React from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

export const colors = {
  ink: "#172C35",
  muted: "#62777E",
  bg: "#F4F7F5",
  card: "#FFFFFF",
  line: "#E0E9E4",
  green: "#167456",
  pale: "#E2F2EA",
  amber: "#926117",
};
export function Button({
  label,
  onPress,
  secondary = false,
  disabled = false,
}: {
  label: string;
  onPress: () => void;
  secondary?: boolean;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        s.button,
        secondary && s.secondary,
        { opacity: disabled ? 0.5 : pressed ? 0.75 : 1 },
      ]}
    >
      <Text style={[s.buttonText, secondary && { color: colors.ink }]}>
        {label}
      </Text>
    </Pressable>
  );
}
export function Card({ children }: { children: React.ReactNode }) {
  return <View style={s.card}>{children}</View>;
}
export function Tag({
  label,
  good = false,
}: {
  label: string;
  good?: boolean;
}) {
  return (
    <View style={[s.tag, good && { backgroundColor: colors.pale }]}>
      <Text
        style={{
          color: good ? colors.green : colors.muted,
          fontSize: 12,
          fontWeight: "600",
        }}
      >
        {label}
      </Text>
    </View>
  );
}
export function Field({
  value,
  onChange,
  placeholder,
  label,
  numeric = false,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  label: string;
  numeric?: boolean;
}) {
  return (
    <View style={{ gap: 8 }}>
      <Text style={s.label}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        style={s.input}
        value={value}
        onChangeText={onChange}
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType={numeric ? "decimal-pad" : "default"}
      />
    </View>
  );
}
export function Status({
  loading,
  error,
  retry,
}: {
  loading?: boolean;
  error?: Error | null;
  retry?: () => void;
}) {
  if (loading)
    return (
      <Card>
        <ActivityIndicator color={colors.green} />
        <Text style={s.body}>Connecting to the live service…</Text>
      </Card>
    );
  if (error)
    return (
      <Card>
        <Tag label="Connection needs attention" />
        <Text accessibilityRole="alert" style={s.body}>
          {error.message}
        </Text>
        {retry && <Button label="Retry connection" secondary onPress={retry} />}
        <Button
          label="Connection settings"
          secondary
          onPress={() => router.push("/settings")}
        />
      </Card>
    );
  return null;
}
export function Empty({
  title,
  body,
  action,
  actionLabel = "Explore retailers",
}: {
  title: string;
  body: string;
  action?: () => void;
  actionLabel?: string;
}) {
  return (
    <Card>
      <Text style={s.subtitle}>{title}</Text>
      <Text style={s.body}>{body}</Text>
      {action && <Button label={actionLabel} secondary onPress={action} />}
    </Card>
  );
}

const tabs = [
  { path: "/", label: "Home", symbol: "⌂" },
  { path: "/resolve", label: "Find", symbol: "⌕" },
  { path: "/watchlist", label: "Saved", symbol: "♡" },
  { path: "/retailers", label: "Stores", symbol: "▦" },
  { path: "/settings", label: "Settings", symbol: "⚙" },
];
export function Shell({
  title,
  subtitle,
  children,
  back = false,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  back?: boolean;
}) {
  return (
    <SafeAreaView style={s.safe} edges={["top", "bottom"]}>
      <View style={s.brandRow}>
        <View>
          <Text style={s.brand}>
            pricepulse<Text style={{ color: colors.green }}> ◉</Text>
          </Text>
          <Text style={s.eyebrow}>THE PRICE. THE EVIDENCE.</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Open alerts"
          onPress={() => router.navigate("/alerts")}
          style={s.alertButton}
        >
          <Text style={{ fontSize: 20 }}>♧</Text>
        </Pressable>
      </View>
      <ScrollView
        contentContainerStyle={s.content}
        keyboardShouldPersistTaps="handled"
      >
        {back && (
          <Pressable
            accessibilityRole="button"
            onPress={() =>
              router.canGoBack() ? router.back() : router.replace("/")
            }
          >
            <Text style={s.link}>← Back</Text>
          </Pressable>
        )}
        <View style={{ gap: 8 }}>
          <Text accessibilityRole="header" style={s.title}>
            {title}
          </Text>
          {!!subtitle && <Text style={s.body}>{subtitle}</Text>}
        </View>
        {children}
        <Text style={s.footer}>
          Prices need evidence. Recommendations never predict future discounts.
        </Text>
      </ScrollView>
      <View style={s.tabbar}>
        {tabs.map((tab) => (
          <Pressable
            key={tab.path}
            accessibilityRole="button"
            accessibilityLabel={tab.label}
            onPress={() => router.navigate(tab.path as "/")}
            style={s.tab}
          >
            <Text style={{ fontSize: 21, color: colors.green }}>
              {tab.symbol}
            </Text>
            <Text style={s.tabText}>{tab.label}</Text>
          </Pressable>
        ))}
      </View>
    </SafeAreaView>
  );
}
export const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  brandRow: {
    paddingHorizontal: 24,
    paddingVertical: 16,
    backgroundColor: colors.card,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  brand: {
    fontSize: 24,
    fontWeight: "800",
    letterSpacing: -1,
    color: colors.ink,
  },
  eyebrow: { fontSize: 9, letterSpacing: 2, color: colors.muted, marginTop: 3 },
  alertButton: { padding: 12, borderRadius: 16, backgroundColor: colors.bg },
  content: {
    padding: 24,
    gap: 20,
    maxWidth: 1000,
    width: "100%",
    alignSelf: "center",
    paddingBottom: 36,
  },
  title: {
    fontSize: 32,
    lineHeight: 38,
    fontWeight: "800",
    color: colors.ink,
    letterSpacing: -0.7,
  },
  subtitle: { fontSize: 20, fontWeight: "700", color: colors.ink },
  body: { fontSize: 15, lineHeight: 23, color: colors.muted },
  label: { fontSize: 13, fontWeight: "600", color: colors.ink },
  input: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 12,
    padding: 15,
    fontSize: 16,
    color: colors.ink,
    backgroundColor: colors.card,
  },
  button: {
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: colors.green,
    borderRadius: 12,
    alignItems: "center",
    minHeight: 48,
  },
  secondary: {
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.line,
  },
  buttonText: { color: "white", fontSize: 14, fontWeight: "700" },
  card: {
    padding: 20,
    gap: 14,
    backgroundColor: colors.card,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.line,
  },
  tag: {
    alignSelf: "flex-start",
    backgroundColor: colors.bg,
    borderRadius: 7,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    flexWrap: "wrap",
  },
  wrap: { flexDirection: "row", gap: 8, flexWrap: "wrap" },
  price: {
    fontSize: 30,
    fontWeight: "800",
    color: colors.ink,
    letterSpacing: -0.7,
  },
  link: { color: colors.green, fontWeight: "600", fontSize: 14 },
  footer: {
    fontSize: 12,
    lineHeight: 19,
    color: colors.muted,
    textAlign: "center",
  },
  tabbar: {
    flexDirection: "row",
    backgroundColor: colors.card,
    borderTopWidth: 1,
    borderTopColor: colors.line,
    paddingVertical: 9,
  },
  tab: { flex: 1, alignItems: "center", gap: 4, paddingVertical: 4 },
  tabText: { fontSize: 11, fontWeight: "600", color: colors.ink },
  divider: { height: 1, backgroundColor: colors.line },
  hero: { backgroundColor: colors.ink, borderRadius: 22, padding: 24, gap: 16 },
  heroTitle: {
    fontSize: 29,
    lineHeight: 35,
    color: "white",
    fontWeight: "700",
  },
  heroBody: { color: "#C9DBD6", fontSize: 15, lineHeight: 23 },
  stat: {
    flex: 1,
    minWidth: 110,
    gap: 5,
    padding: 12,
    backgroundColor: colors.bg,
    borderRadius: 12,
  },
  statValue: { fontSize: 19, fontWeight: "700", color: colors.ink },
});
