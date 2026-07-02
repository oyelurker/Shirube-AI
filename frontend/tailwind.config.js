/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Shirube AI base palette
        base: "#0A0F1C",
        surface: "#0F1626",
        accent: "#38BDF8",
      },
    },
  },
  plugins: [],
};
