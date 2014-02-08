from flask import flash
from flask_babel import gettext


def write_errors_to_flash(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(gettext('Error in the %(field_name) field - %(error)', field_name=getattr(form, field).label.text, error=error), 'danger')
