#!/usr/bin/env bash
# Checks a built MarkWise .deb package. Run on Linux AFTER build_deb.sh.
# Usage: bash packaging/check_deb.sh 1.0.0
set -uo pipefail

VERSION="${1:?usage: bash packaging/check_deb.sh <version, e.g. 1.0.0>}"
DEB="dist/markwise_${VERSION}_amd64.deb"
FAILS=0

ok()   { echo "  PASS: $1"; }
bad()  { echo "  FAIL: $1"; FAILS=$((FAILS + 1)); }
skip() { echo "  SKIP: $1"; }

echo "== 1. Package file exists"
if [ -f "$DEB" ]; then ok "$DEB"; else bad "$DEB not found. Run: bash packaging/build_deb.sh $VERSION"; exit 1; fi

echo "== 2. Package contains the required files"
LIST="$(mktemp)"
dpkg-deb --contents "$DEB" > "$LIST"
for path in \
  "./opt/markwise/MarkWise" \
  "./usr/bin/markwise" \
  "./usr/share/applications/markwise.desktop" \
  "./usr/share/icons/hicolor/256x256/apps/markwise.png" \
  "./usr/share/doc/markwise/copyright" \
  "./usr/share/doc/markwise/changelog.gz"; do
  if grep -q " ${path}\$" "$LIST"; then ok "$path"; else bad "missing $path"; fi
done
rm -f "$LIST"

echo "== 3. Package details"
dpkg-deb --info "$DEB" | grep -E "Package:|Version:|Maintainer:|Homepage:" || bad "could not read package info"
if dpkg-deb --field "$DEB" Version | grep -qx "$VERSION"; then
  ok "version is $VERSION"
else
  bad "package version does not match $VERSION"
fi

echo "== 4. Lintian (only errors count)"
if command -v lintian >/dev/null 2>&1; then
  ERRORS="$(lintian --tag-display-limit 0 "$DEB" | grep '^E:' || true)"
  if [ -z "$ERRORS" ]; then ok "no lintian errors"; else bad "lintian errors:"; echo "$ERRORS"; fi
else
  skip "lintian not installed (sudo apt install lintian)"
fi

echo "== 5. Extract the package and run its built-in self-test"
TMP="$(mktemp -d)"
dpkg-deb -x "$DEB" "$TMP"
if QT_QPA_PLATFORM=offscreen "$TMP/opt/markwise/MarkWise" --selftest; then
  ok "selftest exit code 0"
else
  bad "selftest failed. See /tmp/markwise_selftest.log"
fi
rm -rf "$TMP"

echo "== 6. Clean install in fresh containers (Docker)"
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  for IMG in ubuntu:22.04 ubuntu:24.04 debian:12; do
    echo "  -- $IMG"
    if docker run --rm -v "$PWD/dist:/pkg:ro" "$IMG" bash -c '
        set -e
        apt-get update -qq
        apt-get install -y /pkg/markwise_*.deb >/dev/null
        QT_QPA_PLATFORM=offscreen markwise --selftest
        test -f /usr/share/applications/markwise.desktop
        apt-get remove -y markwise >/dev/null
        test ! -e /opt/markwise
      '; then
      ok "$IMG install, run, remove"
    else
      bad "$IMG failed. Send me the message printed above this line"
    fi
  done
else
  skip "Docker not available or not running (this step is optional on your own PC; CI runs it)"
fi

echo
if [ "$FAILS" -eq 0 ]; then
  echo "ALL CHECKS PASSED. The package is ready for the manual desktop test."
  exit 0
else
  echo "$FAILS CHECK(S) FAILED. Fix them before tagging a release."
  exit 1
fi
