import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "./sidebar";

const inter = Inter({ variable: "--font-sans", subsets: ["latin"] });
const mono = JetBrains_Mono({ variable: "--font-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AMKG — Asset Management Knowledge Graph",
  description:
    "Graph-powered analytics for investment portfolios, ESG ratings, and benchmarks",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${mono.variable} font-sans antialiased bg-[#0a0e17] text-slate-200 min-h-screen`}>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 p-4 pt-16 lg:ml-64 lg:p-8 lg:pt-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
