from flask import render_template
from flask_login import login_required
from . import main
from .forms import MainForm

@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = MainForm()
    if form.validate_on_submit():
        pass
    return render_template('index.html')
