#!/usr/bin/env bash
# Usage: bash packaging/build_deb.sh 1.0.0      (run on Linux, after pyinstaller has built dist/MarkWise)
set -euo pipefail
VERSION="${1:?usage: build_deb.sh <version, no leading v>}"
PKG=markwise
ARCH=amd64
STAGE="build/deb/${PKG}_${VERSION}_${ARCH}"
APPDIR="$STAGE/opt/$PKG"

rm -rf "$STAGE"
mkdir -p "$STAGE"/{DEBIAN,opt/$PKG,usr/bin,usr/share/applications,usr/share/doc/$PKG,usr/share/lintian/overrides}
mkdir -p "$STAGE/usr/share/icons/hicolor/256x256/apps"

cp -r dist/MarkWise/. "$APPDIR/"

# Libraries do not need the execute bit (fixes: shared-library-is-executable)
find "$APPDIR" -type f \( -name '*.so' -o -name '*.so.*' \) -exec chmod 644 {} +

# Remove debug symbols from libraries only, never from the MarkWise program itself
# (fixes: unstripped-binary-or-object). Requires 'strip' from the binutils package.
find "$APPDIR" -type f \( -name '*.so' -o -name '*.so.*' \) \
  -exec strip --strip-unneeded {} \; 2>/dev/null || true

printf '#!/bin/sh\nexec /opt/markwise/MarkWise "$@"\n' > "$STAGE/usr/bin/markwise"
chmod 755 "$STAGE/usr/bin/markwise"

install -m 644 packaging/deb/markwise.desktop "$STAGE/usr/share/applications/markwise.desktop"
install -m 644 packaging/deb/markwise.png "$STAGE/usr/share/icons/hicolor/256x256/apps/markwise.png"
install -m 644 packaging/deb/copyright "$STAGE/usr/share/doc/$PKG/copyright"
install -m 644 packaging/deb/lintian-overrides "$STAGE/usr/share/lintian/overrides/$PKG"

# Changelog (fixes: no-changelog)
sed "s/@VERSION@/$VERSION/" packaging/deb/changelog.in | gzip -9n -c > "$STAGE/usr/share/doc/$PKG/changelog.gz"
chmod 644 "$STAGE/usr/share/doc/$PKG/changelog.gz"

SIZE=$(du -sk "$STAGE" | cut -f1)
sed -e "s/@VERSION@/$VERSION/" -e "s/@SIZE@/$SIZE/" packaging/deb/control.in > "$STAGE/DEBIAN/control"

find "$STAGE" -type d -exec chmod 755 {} +
mkdir -p dist
dpkg-deb --root-owner-group --build "$STAGE" "dist/${PKG}_${VERSION}_${ARCH}.deb"
echo "Built dist/${PKG}_${VERSION}_${ARCH}.deb"
