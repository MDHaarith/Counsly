import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        counsly: {
          canvas: "#FAF9F5",
          soft: "#F5F0E8",
          card: "#EFE9DE",
          line: "#E6DFD8",
          ink: "#141413",
          body: "#3D3D3A",
          muted: "#6C6A64",
          dark: "#181715",
          slate: "#252320",
          primary: "#CC785C",
          coral: "#CC785C",
          cream: "#FAF9F5",
          safe: "#5DB872",
          warning: "#D4A017",
          gold: "#E8A55A",
          teal: "#5DB8A6",
        }
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        display: ["Newsreader", "Georgia", "serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out forwards",
        "slide-up": "slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "pulse-subtle": "pulseSubtle 2.5s infinite ease-in-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "scale(0.98)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSubtle: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.85" },
        }
      }
    },
  },
  plugins: [],
};

export default config;
