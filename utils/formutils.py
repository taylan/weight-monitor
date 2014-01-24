from flask import flash


def write_errors_to_flash(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash('Error in the {0} field - {1}'.format(getattr(form, field).label.text, error), 'danger')