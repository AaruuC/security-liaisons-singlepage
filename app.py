from flask import Flask
from flask import request
from flask import render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import grouper_find_members
import grouper_add_member
import grouper_remove_member


db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///persisted_list.db'
db.init_app(app)


# Primary Liaisons
class PrimaryItem(db.Model):
    pennkey = db.Column(db.Integer)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    schctr = db.Column(db.String(200), primary_key=True)


# Additional Designees
class UserItem(db.Model):
    pennkey = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    schctr = db.Column(db.String(200))


@app.route("/")
def home():
    memberList = grouper_find_members.main()
    memberList = sorted(memberList, key=lambda x: (x['schctr'], x['name']))

    for member in memberList:
        # If the member is primary liaison, skip
        checkPrimary = db.session.execute(db.select(PrimaryItem).filter_by(
            pennkey=member['pennkey'])).scalar_one_or_none()
        if checkPrimary:
            memberList.remove(member)
            continue

        # If the member is not in database, add it
        item_to_update = db.session.execute(db.select(UserItem).filter_by(
            pennkey=member['pennkey'])).scalar_one_or_none()
        if not item_to_update:
            user = UserItem(
                pennkey=member['pennkey'],
                name=member['name'],
                email=member['email'],
                schctr=member['schctr']
            )
            db.session.add(user)
            db.session.commit()

    primaryLiaisons = db.session.execute(
        db.select(PrimaryItem).order_by(PrimaryItem.schctr)).scalars()
    return render_template('template.html', members=memberList,
                           primaryLiaisons=primaryLiaisons)


@app.route('/add_member', methods=['POST'])
def add_member():
    id = request.form['id']
    grouper_add_member.main(id)
    return redirect(url_for('home'))


@app.route('/remove_member', methods=['POST'])
def remove_member():
    selected_id = request.form.getlist('select')

    grouper_remove_member.main(selected_id[0])

    delete = db.session.execute(db.select(PrimaryItem).filter_by(
        pennkey=int(selected_id[0]))).scalar_one_or_none()
    if delete:
        db.session.delete(delete)
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/update_primary', methods=['POST'])
def update_primary():
    selected_id = request.form.getlist('select')
    updated_details = db.session.execute(db.select(UserItem).filter_by(
        pennkey=int(selected_id[0]))).scalar_one_or_none()
    if updated_details:
        item_to_update = db.session.execute(db.select(PrimaryItem).filter_by(
            schctr=updated_details.schctr)).scalar_one_or_none()
    # Overwriting a primary liaison
    if item_to_update:
        db.session.delete(item_to_update)
        db.session.add(PrimaryItem(
            pennkey=updated_details.pennkey,
            name=updated_details.name,
            email=updated_details.email,
            schctr=updated_details.schctr
        ))
        db.session.commit()
    # No primary liaison for that school/center
    else:
        db.session.add(PrimaryItem(
            pennkey=updated_details.pennkey,
            name=updated_details.name,
            email=updated_details.email,
            schctr=updated_details.schctr
        ))
        db.session.commit()
    return redirect(url_for('home'))


@app.route('/save_permissions', methods=['POST'])
def save_permissions():
    # boxfolder = request.form.getlist('boxfolder')
    # mailinglist = request.form.getlist('mailinglist')
    contact = request.form.getlist('contact')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
    with app.app_context():
        db.create_all()
