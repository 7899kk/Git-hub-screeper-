import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PricePulse India — Shop with perspective",
  description: "Independent Indian shopping price comparisons, recorded history and alerts.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
