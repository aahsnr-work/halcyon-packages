// Version sweeps bitwarden/clients' newest desktop-v release (the repo also
// cuts other tags; the raw-text scan picks the first desktop-v tag of the
// releases list, which GitHub orders newest-first).
let text = get("https://api.github.com/repos/bitwarden/clients/releases?per_page=30");
rpm.version(find(`"tag_name":"desktop-v([^"]+)"`, text, 1));
