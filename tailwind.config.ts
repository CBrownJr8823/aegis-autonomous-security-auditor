import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      boxShadow: {
        panel: "0 16px 50px rgba(0, 0, 0, 0.24)"
      }
    }
  },
  plugins: []
};

export default config;
