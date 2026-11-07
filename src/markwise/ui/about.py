from PySide6.QtWidgets import QMessageBox

from markwise import app_info as I


def show_about(parent):
    QMessageBox.about(parent, f"About {I.APP_NAME}",
        f"<h2>{I.APP_NAME} {I.APP_VERSION}</h2>"
        f"<p>{I.APP_DESCRIPTION.replace(chr(10), ' ')}</p>"
        f"<p><b>{I.AUTHOR_NAME}</b><br>{I.AUTHOR_TITLE}<br>"
        f"<a href='mailto:{I.AUTHOR_EMAIL}'>{I.AUTHOR_EMAIL}</a><br>"
        f"<a href='{I.GITHUB_URL}'>{I.GITHUB_URL}</a></p>"
        f"<p>{I.COPYRIGHT}</p>")
