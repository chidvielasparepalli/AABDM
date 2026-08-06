/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
      colors: {
        // liquid glass palette
        glass: {
          DEFAULT: "rgba(255,255,255,0.06)",
          strong: "rgba(255,255,255,0.10)",
          line: "rgba(255,255,255,0.10)",
        },
        ink: {
          DEFAULT: "#E8EBF2",
          dim: "#9AA3B5",
          faint: "#5A6478",
        },
        base: {
          DEFAULT: "#0A0D16",
          deep: "#070910",
        },
        aurora: {
          violet: "#8B7CF6",
          cyan: "#5EEAD4",
          amber: "#F5C97B",
        },
      },
      boxShadow: {
        glass: "inset 0 1px 0 rgba(255,255,255,0.08), 0 8px 32px rgba(0,0,0,0.35)",
        glow: "0 0 40px rgba(139,124,246,0.25)",
      },
      keyframes: {
        "orb-drift": {
          "0%,100%": { transform: "translate(0,0) scale(1)" },
          "33%": { transform: "translate(60px,-40px) scale(1.15)" },
          "66%": { transform: "translate(-40px,30px) scale(0.92)" },
        },
        "fade-up": {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "orb-drift": "orb-drift 18s ease-in-out infinite",
        "fade-up": "fade-up 0.4s ease-out both",
      },
    },
  },
  plugins: [],
};
