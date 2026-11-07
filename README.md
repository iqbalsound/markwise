# MarkWise

A fast, simple assignment and quiz grading assistant with AI-assisted marking
(Google Gemini), course and semester organisation, roster import (Excel/CSV),
shared-drive PDF access, and light/dark themes. Windows and Linux.

## Install
- **Debian/Ubuntu:** `sudo apt install ./markwise_1.0.0_amd64.deb`
- **Other Linux:** extract `MarkWise-linux-x64.tar.gz`, then run `MarkWise/MarkWise`
- **Windows:** unzip `MarkWise-windows-x64.zip` and run `MarkWise.exe`
  (if SmartScreen warns about an unsigned app: More info -> Run anyway)

## Privacy
Student data stays on the teacher's computer except what is sent to Google
Gemini for grading. The free Gemini tier may use that content to improve
Google's products, so students must give consent first. MarkWise skips any
student not marked as having given consent.

## Development
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt -r requirements-dev.txt
    pip install -e .
    python -m markwise
    pytest

---
**MarkWise 1.0.0** by Iqbal Uddin Khan, Assistant Professor | DIT-HU -- NN Site KHI
iqbalsound@yahoo.com · https://github.com/iqbalsound/markwise
© 2026 Iqbal Uddin Khan. Released under the MIT License.
