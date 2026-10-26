import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const config = [
  ...nextVitals,
  ...nextTs,
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts", "src/styles/tokens.css"] },
  {
    rules: {
      // No hard-coded UI strings: text comes from next-intl messages (UI spec §0.6).
      "react/jsx-no-literals": ["error", { noStrings: true, ignoreProps: true, allowedStrings: ["·", "|", "/", ":"] }],
    },
  },
  { files: ["**/*.test.ts", "**/*.test.tsx", "scripts/**"], rules: { "react/jsx-no-literals": "off" } },
];

export default config;
