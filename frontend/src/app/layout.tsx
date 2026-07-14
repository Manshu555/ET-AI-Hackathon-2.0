import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { Toaster } from "react-hot-toast";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "EPC-Intel | AI Intelligence Platform",
  description: "AI Intelligence Platform for Data Centre EPC Project Delivery — Compliance, Schedule Risk, Supply Chain, Commissioning & Knowledge Management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans">
        <Toaster position="top-right" toastOptions={{ duration: 4000, style: { background: '#1e293b', color: '#fff' } }} />
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
