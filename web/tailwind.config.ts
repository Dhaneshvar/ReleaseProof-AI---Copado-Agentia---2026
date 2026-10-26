import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0d0b",
        surface: "#111411",
        panel: "#171a16",
        line: "#2b3027",
        accent: "#c8ff68",
        mint: "#c8ff68",
        sky: "#a9c6a0",
        amber: "#ed9b50",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Consolas", "monospace"],
      },
      boxShadow: {
        glow: "0 18px 70px rgba(132, 108, 255, .18)",
      },
    },
  },
  plugins: [],
};

export default config;

