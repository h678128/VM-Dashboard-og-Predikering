import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17211f",
        pine: "#0f5d4f",
        mint: "#55d85f",
        night: "#0f1115",
        navy: "#12151a",
        card: "#171a20",
        line: "#2a2f38",
        fjord: "#2f6f91",
        frost: "#f5f8f7",
        coral: "#c95145",
        gold: "#d5a021"
      }
    }
  },
  plugins: []
};

export default config;

