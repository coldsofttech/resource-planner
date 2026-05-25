import esbuild from "esbuild";

const modules = ["utils", "main", "setup"];

const buildConfigs = [
  {
    label: "components.js",
    outLabel: "components.min.js",
    entryPoints: ["apps/web/static/js/components/index.js"],
    outfile: "apps/web/static/js/dist/components.min.js",
  },
  ...modules.map((m) => ({
    label: `${m}.js`,
    outLabel: `${m}.min.js`,
    entryPoints: [`apps/web/static/js/modules/${m}/index.js`],
    outfile: `apps/web/static/js/dist/${m}.min.js`,
  })),
];

const builds = buildConfigs.map(({ label, outLabel, ...config }) =>
  esbuild
    .build({ bundle: true, minify: true, format: "esm", ...config })
    .then(() => console.log(`  ${label} > ${outLabel} created`)),
);

Promise.all(builds).catch(() => process.exit(1));
