import { defineConfig, globalIgnores } from "eslint/config";

export default defineConfig([
  globalIgnores(["dist/**", "node_modules/**", "app/**", ".next/**", "next-env.d.ts"]),
]);
