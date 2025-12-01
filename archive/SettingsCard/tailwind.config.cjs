const defaultTheme = require("tailwindcss/defaultTheme");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", ...defaultTheme.fontFamily.sans]
      },
      colors: {
        pilot: {
          primary: "#00e6e6",
          accent: "#2196f3",
          danger: "#ef4444"
        }
      }
    }
  },
  plugins: []
};
