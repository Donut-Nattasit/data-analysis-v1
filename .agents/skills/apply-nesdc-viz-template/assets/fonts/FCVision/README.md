# FC Vision font files

FC Vision is a third-party commercial font. Its embedded metadata prohibits
redistribution without written permission, so the font binaries are intentionally
excluded from Git.

Authorized users can place their licensed `.otf` or `.ttf` files in this directory.
`apply_style.py` registers them automatically. When the files are absent, charts use
a system-font fallback and emit a warning; the NESDC color and layout rules still
apply.
