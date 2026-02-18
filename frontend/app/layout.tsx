import "./globals.css";
import type { Metadata } from "next";
import { Header } from "@/components/header";

export const metadata: Metadata = {
  title: "Trendr",
  description: "Agentic content creation platform (skeleton)"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main className="mx-auto max-w-6xl p-4">{children}</main>
      </body>
    </html>
  );
}
