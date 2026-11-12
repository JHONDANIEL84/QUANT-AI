import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080B11",
        surface: "#0D111A",
        "surface-card": "#131926",
        "surface-hover": "#1C2436",
        border: "#1F293D",
        "border-light": "#2E3D5B",
        quant: {
          green: "#00E676",
          "green-dim": "#00E67622",
          red: "#FF5252",
          "red-dim": "#FF525222",
          blue: "#2979FF",
          cyan: "#00E5FF",
          amber: "#FFB300",
          purple: "#7C4DFF",
        },
      },
      fontFamily: {
        mono: ["var(--font-mono)", "JetBrains Mono", "Courier New", "monospace"],
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
