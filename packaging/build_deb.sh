#!/usr/bin/env bash
# Usage: bash packaging/build_deb.sh 1.0.0      (run on Linux, after pyinstaller has built dist/MarkWise)
set -euo pipefail
VERSION="${1:?usage: build_deb.sh <version, no leading v>}"
PKG=markwise
ARCH=amd64
STAGE="build/deb/${PKG}_${VERSION}_${ARCH}"

rm -rf "$STAGE"
mkdir -p "$STAGE"/{DEBIAN,opt/$PKG,usr/bin,usr/share/applications,usr/share/doc/$PKG}
mkdir -p "$STAGE/usr/share/icons/hicolor/256x256/apps"

cp -r dist/MarkWise/. "$STAGE/opt/$PKG/"

printf '#!/bin/sh\nexec /opt/markwise/MarkWise "$@"\n' > "$STAGE/usr/bin/markwise"
chmod 755 "$STAGE/usr/bin/markwise"

install -m 644 packaging/deb/markwise.desktop "$STAGE/usr/share/applications/markwise.desktop"
install -m 644 packaging/deb/markwise.png "$STAGE/usr/share/icons/hicolor/256x256/apps/markwise.png"
install -m 644 packaging/deb/copyright "$STAGE/usr/share/doc/$PKG/copyright"

SIZE=$(du -sk "$STAGE" | cut -f1)
sed -e "s/@VERSION@/$VERSION/" -e "s/@SIZE@/$SIZE/" packaging/deb/control.in > "$STAGE/DEBIAN/control"

find "$STAGE" -type d -exec chmod 755 {} +
mkdir -p dist
dpkg-deb --root-owner-group --build "$STAGE" "dist/${PKG}_${VERSION}_${ARCH}.deb"
echo "Built dist/${PKG}_${VERSION}_${ARCH}.deb"
