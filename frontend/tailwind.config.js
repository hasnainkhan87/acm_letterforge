// Palette taken from nmamit.acm.org (deep indigo/violet, estimated from a screenshot of the site).
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {
    colors: {
      desk: "#0F0A2A", surface: "#171040", sidebar: "#0B0720", field: "#120C33", line: "#2E2569",
      primary: { DEFAULT: "#5B4BDB", soft: "#7466EA" }, accent: "#B8AEF5", main: "#EDEBFF", muted: "#A59FD0",
    },
    fontFamily: { sans: ['"Hanken Grotesk"', "system-ui", "sans-serif"], serif: ["Newsreader", "Georgia", "serif"] },
  } },
  plugins: [],
};
