import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "QUANT AI — Intelligent Quantitative Swing Trading & AI Analysis Platform",
  description:
    "Plataforma profesional avanzada de análisis cuantitativo, Smart Money Concepts, Liquidity Intelligence y Asistente IA multimodal.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased selection:bg-quant-cyan/30 selection:text-white">
        <Navbar />
        <main className="p-4 sm:p-6 max-w-7xl mx-auto space-y-6">
          {children}
        </main>
      </body>
    </html>
  );
}
