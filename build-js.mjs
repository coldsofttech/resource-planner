import esbuild from "esbuild";

const esmModules = [
  "auth",
  "emp-types",
  "financial-years",
  "holidays",
  "leaves",
  "locations",
  "main",
  "roles",
  "setup",
  "skills",
  "teams",
  "users",
  "utils",
];

const buildConfigs = [
  // Web-component bundle (ESM)
  {
    label: "components.js",
    outLabel: "components.min.js",
    entryPoints: ["apps/web/static/js/components/index.js"],
    outfile: "apps/web/static/js/dist/components.min.js",
    format: "esm",
  },
  // Tiny blocking IIFE for flash-of-contrary-theme prevention
  {
    label: "theme-init.js",
    outLabel: "theme-init.min.js",
    entryPoints: ["apps/web/static/js/modules/utils/theme-init.js"],
    outfile: "apps/web/static/js/dist/theme-init.min.js",
    format: "iife",
  },
  // ESM module bundles
  ...esmModules.map((m) => ({
    label: `${m}.js`,
    outLabel: `${m}.min.js`,
    entryPoints: [`apps/web/static/js/modules/${m}/index.js`],
    outfile: `apps/web/static/js/dist/${m}.min.js`,
    format: "esm",
  })),
];

const builds = buildConfigs.map(({ label, outLabel, format, ...config }) =>
  esbuild
    .build({ bundle: true, minify: true, format, ...config })
    .then(() => console.log(`  ${label} > ${outLabel} created`)),
);

Promise.all(builds).catch(() => process.exit(1));
