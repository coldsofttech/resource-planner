import esbuild from "esbuild";

const modules = ["setup"];

const builds = [
  esbuild.build({
    entryPoints: ["apps/web/static/js/components/index.js"],
    bundle: true,
    minify: true,
    format: "esm",
    outfile: "apps/web/static/js/dist/components.min.js",
  }),
  ...modules.map((m) =>
    esbuild.build({
      entryPoints: [`apps/web/static/js/modules/${m}/index.js`],
      bundle: true,
      minify: true,
      format: "esm",
      outfile: `apps/web/static/js/dist/${m}.min.js`,
    }),
  ),
];

Promise.all(builds).catch(() => process.exit(1));
