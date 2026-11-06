// Fails the production build when NEXT_PUBLIC_UI_FIXTURES is set: fixtures are for development only.
if (process.env.NEXT_PUBLIC_UI_FIXTURES) {
  console.error("NEXT_PUBLIC_UI_FIXTURES must not be set for a production build (fixtures are dev only).");
  process.exit(1);
}
console.log("no UI fixtures flag in the build environment");
