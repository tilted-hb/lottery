# IMPORTS
from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user

import models
from app import db
from lottery.forms import DrawForm
from models import Draw

# CONFIG
lottery_blueprint = Blueprint('lottery', __name__, template_folder='templates')


# VIEWS
# view lottery page
@lottery_blueprint.route('/lottery')
@login_required
def lottery():
    return render_template('lottery/lottery.html', name=current_user.firstname)


# view all draws that have not been played
@lottery_blueprint.route('/create_draw', methods=['POST'])
def create_draw():
    form = DrawForm()

    if form.validate_on_submit():
        # finished string of numbers
        submitted_numbers = ''
        # list to get numbers from form
        prepared_numbers = []
        # previous number to compare
        previous_num = 0

        # add submitted numbers to the list
        prepared_numbers.append(int(form.number1.data))
        prepared_numbers.append(int(form.number2.data))
        prepared_numbers.append(int(form.number3.data))
        prepared_numbers.append(int(form.number4.data))
        prepared_numbers.append(int(form.number5.data))
        prepared_numbers.append(int(form.number6.data))

        # check for repeated numbers in a form
        for i in prepared_numbers:
            if i == previous_num:
                flash('Error! Numbers cannot be same' % prepared_numbers)
                return redirect(url_for('lottery.lottery'))

            submitted_numbers += (' ' + str(i))

            previous_num = i
        # encrypt the numbers
        encrypted_numbers = models.encrypt(submitted_numbers, current_user.key)

        # create a new draw with the form data.
        new_draw = Draw(user_id=current_user.id, numbers=encrypted_numbers, master_draw=False, lottery_round=0)
        # add the new draw to the database
        db.session.add(new_draw)
        db.session.commit()

        # re-render lottery.page
        flash('Draw %s submitted.' % submitted_numbers)
        return redirect(url_for('lottery.lottery'))

    return render_template('lottery/lottery.html', name=current_user.firstname, form=form)


# view all draws that have not been played
@lottery_blueprint.route('/view_draws', methods=['POST'])
def view_draws():
    # get all draws that have not been played [played=0]
    playable_draws = Draw.query.filter_by(been_played=False, user_id=current_user.id).all()

    # if playable draws exist
    if len(playable_draws) != 0:
        for i in playable_draws:
            # decrypt the numbers
            numbers = models.decrypt(i.numbers, current_user.key)
            i.numbers = numbers

        # re-render lottery page with playable draws
        return render_template('lottery/lottery.html', playable_draws=playable_draws)
    else:
        flash('No playable draws.')
        return lottery()


# view lottery results
@lottery_blueprint.route('/check_draws', methods=['POST'])
def check_draws():
    # get played draws
    played_draws = Draw.query.filter_by(been_played=True, user_id=current_user.id).all()

    # if played draws exist
    if len(played_draws) != 0:
        return render_template('lottery/lottery.html', results=played_draws, played=True)

    # if no played draws exist [all draw entries have been played therefore wait for next lottery round]
    else:
        flash("Next round of lottery yet to play. Check you have playable draws.")
        return lottery()


# delete all played draws
@lottery_blueprint.route('/play_again', methods=['POST'])
def play_again():
    Draw.query.filter_by(been_played=True, master_draw=False, user_id=current_user.id).delete(synchronize_session=False)
    db.session.commit()

    flash("All played draws deleted.")
    return lottery()


