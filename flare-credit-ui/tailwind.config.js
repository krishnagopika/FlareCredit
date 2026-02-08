/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#0a0e1a",
          800: "#0f1629",
          700: "#1a2340",
        },
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        "pulse-blue": "pulse-blue 3s ease-in-out infinite",
        glow: "glow 2s ease-in-out infinite",
        "gradient-shift": "gradient-shift 15s ease infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-20px)" },
        },
        "pulse-blue": {
          "0%, 100%": {
            boxShadow: "0 0 20px rgba(59, 130, 246, 0.2)",
          },
          "50%": {
            boxShadow: "0 0 40px rgba(59, 130, 246, 0.4)",
          },
        },
        glow: {
          "0%, 100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
        "gradient-shift": {
          "0%, 100%": { transform: "translate(0%, 0%) scale(1)" },
          "25%": { transform: "translate(10%, -10%) scale(1.1)" },
          "50%": { transform: "translate(-5%, 15%) scale(0.95)" },
          "75%": { transform: "translate(-10%, -5%) scale(1.05)" },
        },
      },
    },
  },
  plugins: [],
};
