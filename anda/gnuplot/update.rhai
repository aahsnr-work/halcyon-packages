// Version sweeps SourceForge's best_release.json (gnuplot publishes there,
// not on GitHub); the linux filename carries the version.
let file = get_json("https://sourceforge.net/projects/gnuplot/best_release.json")
	.platform_releases.linux.filename;
rpm.version(find(`gnuplot-([0-9.]+)\.tar\.gz$`, file, 1));
