/**
 * tailwind.config.js — DESIGN TOKENS (the single source of truth for the look).
 *
 * design.md was not provided, so these tokens follow the established HospitalOS style:
 * "Clinical Precision" — alabaster canvas, white cards, medical-teal accent,
 * Plus Jakarta Sans (headings) / Public Sans (body) / JetBrains Mono (numbers).
 * When design.md arrives, change the values HERE and the whole app updates.
 */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F8FAFC",          // page background (alabaster)
        surface: "#FFFFFF",         // cards, panels
        line: "#E2E8F0",            // borders, dividers
        ink: { DEFAULT: "#0F172A", muted: "#475569", subtle: "#94A3B8" },  // text
        primary: {
          DEFAULT: "#0F766E",       // buttons, links, active nav (teal 700)
          hover: "#115E59",
          chart: "#0D9488",         // chart marks (validated: lightness, chroma, contrast)
          soft: "#F0FDFA",          // tinted backgrounds
          ring: "#99F6E4",
        },
        // Status colours are reserved for state, always shown with an icon + label
        ok: { DEFAULT: "#047857", soft: "#ECFDF5" },
        warning: { DEFAULT: "#B45309", soft: "#FFFBEB" },
        critical: { DEFAULT: "#B91C1C", soft: "#FEF2F2" },
        info: { DEFAULT: "#1D4ED8", soft: "#EFF6FF" },
      },
      fontFamily: {
        display: ["'Plus Jakarta Sans'", "system-ui", "sans-serif"],
        sans: ["'Public Sans'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "16px",               // cards and panels
        control: "10px",            // buttons, inputs
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.04), 0 1px 3px rgba(15, 23, 42, 0.06)",
        pop: "0 8px 24px rgba(15, 23, 42, 0.12)",
      },
    },
  },
  plugins: [],
};
