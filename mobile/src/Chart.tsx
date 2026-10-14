import React, { useState } from "react";
import { Platform, Pressable, Text, View } from "react-native";
import Svg, { Circle, Polyline, Line, Text as SvgText } from "react-native-svg";
import { Point } from "./types";
import { rupees } from "./logic";
import { colors, s } from "./ui";

export function Chart({
  points,
  current,
}: {
  points: Point[];
  current: number;
}) {
  const [selected, setSelected] = useState<number | null>(null);
  if (!points.length)
    return (
      <Text style={s.body}>
        Tracking has just begun. Earlier prices are unavailable.
      </Text>
    );
  const low = Math.min(...points.map((p) => p.price)),
    high = Math.max(...points.map((p) => p.price)),
    range = high - low || 100;
  const start = Date.parse(points[0].timestamp),
    span = Date.parse(points[points.length - 1].timestamp) - start || 1;
  const x = (p: Point) => 70 + ((Date.parse(p.timestamp) - start) / span) * 255;
  const y = (p: Point) => 25 + (1 - (p.price - low) / range) * 130;
  const chosen =
    selected === null
      ? points[points.length - 1]
      : points[Math.min(selected, points.length - 1)];
  return (
    <View style={{ gap: 12 }}>
      <Text style={s.label}>
        Listed price (INR) · Current {rupees(current)}
      </Text>
      <Svg
        viewBox="0 0 350 215"
        width="100%"
        height={215}
        accessibilityLabel="Retailer price history. Individual observations are listed below."
      >
        {[0, 1, 2].map((i) => (
          <React.Fragment key={i}>
            <Line
              x1="70"
              x2="325"
              y1={25 + i * 65}
              y2={25 + i * 65}
              stroke={colors.line}
            />
            <SvgText
              x="62"
              y={29 + i * 65}
              textAnchor="end"
              fontSize="10"
              fill={colors.muted}
            >
              {rupees(high - (i * (high - low)) / 2)}
            </SvgText>
          </React.Fragment>
        ))}
        <Polyline
          points={points.map((p) => `${x(p)},${y(p)}`).join(" ")}
          fill="none"
          stroke={colors.green}
          strokeWidth="3"
        />
        {points.map((p, i) => (
          <Circle
            key={p.timestamp}
            cx={x(p)}
            cy={y(p)}
            r={selected === i ? 6 : 3}
            fill={colors.green}
            onPress={Platform.OS === "web" ? undefined : () => setSelected(i)}
          />
        ))}
        <SvgText x="70" y="183" fontSize="10" fill={colors.muted}>
          {new Date(start).toLocaleDateString()}
        </SvgText>
        <SvgText
          x="325"
          y="183"
          textAnchor="end"
          fontSize="10"
          fill={colors.muted}
        >
          {new Date(points[points.length - 1].timestamp).toLocaleDateString()}
        </SvgText>
        <SvgText
          x="195"
          y="205"
          textAnchor="middle"
          fontSize="11"
          fill={colors.muted}
        >
          Observation date
        </SvgText>
      </Svg>
      <Text style={s.body}>
        {new Date(chosen.timestamp).toLocaleString()} · {rupees(chosen.price)} ·{" "}
        {chosen.source}
      </Text>
      <Text style={s.label}>Tap an observation to inspect it</Text>
      {points.map((p, i) => (
        <Pressable
          accessibilityRole="button"
          key={p.timestamp}
          onPress={() => setSelected(i)}
          style={[s.row, { paddingVertical: 8 }]}
        >
          <Text style={s.body}>{new Date(p.timestamp).toLocaleString()}</Text>
          <Text style={s.link}>{rupees(p.price)}</Text>
        </Pressable>
      ))}
    </View>
  );
}
