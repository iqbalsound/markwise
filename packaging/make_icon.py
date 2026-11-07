import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter

app = QGuiApplication(sys.argv)
image = QImage(256, 256, QImage.Format.Format_ARGB32)
image.fill(Qt.GlobalColor.transparent)
painter = QPainter(image)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.setPen(Qt.PenStyle.NoPen)
painter.setBrush(QColor("#2f6fed"))
painter.drawRoundedRect(QRectF(8, 8, 240, 240), 48, 48)
painter.setPen(QColor("white"))
painter.setFont(QFont("Sans", 100, QFont.Weight.Bold))
painter.drawText(QRectF(0, 0, 256, 256), Qt.AlignmentFlag.AlignCenter, "A+")
painter.end()
image.save("packaging/deb/markwise.png")
print("Saved packaging/deb/markwise.png")
