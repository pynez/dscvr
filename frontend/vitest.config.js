import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.js",
    include: ["src/test/**/*.test.{js,jsx}"],
    coverage: {
      reporter: ["text", "lcov"],
      include: ["src/hooks/**", "src/components/**", "src/api/**"],
    },
  },
});
