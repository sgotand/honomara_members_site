from itertools import groupby
import itertools
from flask import render_template, request, abort, redirect, url_for, flash
from honomara_members_site import app, db
from honomara_members_site.login import login_check
from honomara_members_site.model import Member, Training, After, Restaurant, Race, RaceBase, RaceType, Result
from honomara_members_site.model import TrainingParticipant
from sqlalchemy import func
from sqlalchemy.sql import text
from honomara_members_site.form import MemberForm, TrainingForm, AfterForm, RaceBaseForm, RaceForm, ResultForm, RestaurantForm
from flask_login import login_required, login_user, logout_user
from honomara_members_site.util import current_school_year


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login/', methods=["GET", "POST"])
def login():
    if(request.method == "POST"):
        username = request.form["username"]
        password = request.form["password"]
        if login_check(username, password):
            return redirect(url_for('index'))
        else:
            return abort(401)
    else:
        return render_template("login.html")


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/member/')
@login_required
def member():
    members = Member.query.order_by(Member.year.desc(), Member.family_kana)
    return render_template('member.html', members=members, groupby=groupby, key=(lambda x: x.year))


@app.route('/member/<int:member_id>')
@login_required
def member_individual(member_id):
    m = Member.query.get(member_id)
    if m is None:
        return abort(404)

    m.results.sort(key=lambda x: x.race.date, reverse=False)
    raw_results = list(
        filter(lambda x: x.race_type.show_name == 'フルマラソン', m.results))

    results = []
    races = []
    for r in raw_results:
        results += [{'x': "{:%Y/%m/%d}".format(r.race.date), 'y': r.result}]
        races += [r.race.race_name]

    return render_template('member_individual.html', member=m, races=str(races), results=str(results))


@app.route('/member/edit', methods=['GET', 'POST'])
@login_required
def member_edit():
    form = MemberForm(formdata=request.form)
    form.visible.data = request.form.get('visible') != 'False'

    if form.validate_on_submit():
        return redirect(url_for('member_confirm'), code=307)

    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        member = Member.query.get(id)
        form = MemberForm(obj=member)
        form.method.data = 'PUT'
    else:
        form.method.data = 'POST'
    return render_template('member_edit.html', form=form)


@app.route('/member/confirm', methods=['POST'])
@login_required
def member_confirm():
    form = MemberForm(formdata=request.form)
    form.visible.data = request.form.get('visible') != 'False'

    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('user'))

    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            member = Member.query.get(form.id.data)
            db.session.delete(member)
            db.session.commit()
            flash('メンバー："{} {}"の削除が完了しました'.format(
                member.family_name, member.first_name), 'danger')
        elif request.form.get('method') == 'PUT':
            member = Member.query.get(form.id.data)
            form.populate_obj(member)
            db.session.commit()
            flash('メンバー："{} {}"の更新が完了しました'.format(
                member.family_name, member.first_name), 'warning')
        elif request.form.get('method') == 'POST':
            member = Member()
            form.populate_obj(member)
            member.id = None
            db.session.add(member)
            db.session.commit()
            flash('メンバー："{} {}"の更新が完了しました'.format(
                member.family_name, member.first_name), 'info')

        return redirect(url_for('member'))
    else:
        if request.form.get('method') == 'DELETE':
            member = Member.query.get(form.id.data)
            form = MemberForm(obj=member)
        return render_template('member_confirm.html', form=form)


@app.route('/training/')
def training():
    per_page = 20
    page = request.args.get('page') or 1
    page = max([1, int(page)])
    trainings = Training.query
    keywords = request.args.get('keyword')
    if keywords is not None:
        for keyword in keywords.split(','):
            keyword = keyword.replace(' ', '')
            keyword = keyword.replace('　', '')
            trainings = trainings.filter(Training.comment.match(keyword))
    trainings = trainings.order_by( Training.date.desc()).paginate(page, per_page)
    return render_template('training.html', pagination=trainings)


@app.route('/training/edit', methods=['GET', 'POST'])
@login_required
def training_edit():
    form = TrainingForm(formdata=request.form)

    if form.validate_on_submit():
        return redirect(url_for('training_confirm'), code=307)

    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        training = Training.query.get(id)
        form = TrainingForm(obj=training)
        form.method.data = 'PUT'
        form.participants.data = [m.id for m in training.participants]
    else:
        form.method.data = 'POST'

    return render_template('training_edit.html', form=form)


@app.route('/training/confirm', methods=['POST'])
@login_required
def training_confirm():
    app.logger.info(request.form)
    form = TrainingForm(formdata=request.form)
    app.logger.info(form.participants.data)

    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('training'))

    if form.participants.data:
        form.participants.data = [Member.query.get(
            int(member_id)) for member_id in form.participants.data]

    if form.validate_on_submit() or request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            training = Training.query.get(form.id.data)
            db.session.delete(training)
            db.session.commit()
            flash('練習録: "{}" の削除が完了しました'.format(training.title), 'danger')
        elif request.form.get('method') == 'PUT':
            training = Training.query.get(form.id.data)
            training.title = training.title.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            training.comment = training.comment.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            form.populate_obj(training)
            db.session.commit()
            flash('練習録: "{}" の更新が完了しました'.format(training.title), 'warning')
        elif request.form.get('method') == 'POST':
            training = Training()
            form.populate_obj(training)
            training.title = training.title.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            training.comment = training.comment.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            training.id = None
            db.session.add(training)
            db.session.commit()
            flash('練習録: "{}" の登録が完了しました'.format(training.title), 'info')
        return redirect(url_for('training'))
    else:
        if request.form.get('method') == 'DELETE':
            training = Training.query.get(form.id.data)
            form = TrainingForm(obj=training)
            form.participants.data = training.participants
        app.logger.info(form.participants.data)

        return render_template('training_confirm.html', form=form)


@app.route('/after/')
def after():
    per_page = 40
    page = request.args.get('page') or 1
    page = max([1, int(page)])
    afters = After.query
    keywords = request.args.get('keyword')
    if keywords is not None:
        for keyword in keywords.split(','):
            keyword = keyword.replace(' ', '')
            keyword = keyword.replace('　', '')
            afters = afters.filter(After.comment.match(keyword))

    afters = afters.order_by(After.date.desc()).paginate(page, per_page)
    return render_template('after.html', pagination=afters)


@app.route('/after/edit', methods=['GET', 'POST'])
@login_required
def after_edit():
    form = AfterForm(formdata=request.form)

    if form.validate_on_submit():
        return redirect(url_for('after_confirm'), code=307)

    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        after = After.query.get(id)
        form = AfterForm(obj=after)
        form.participants.data = [m.id for m in after.participants]
        form.restaurant.data = after.restaurant.id
        form.method.data = 'PUT'
    else:
        form.method.data = 'POST'

    return render_template('after_edit.html', form=form)


@app.route('/after/confirm', methods=['POST'])
@login_required
def after_confirm():
    form = AfterForm(formdata=request.form)
    app.logger.info(request.form)
    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('after'))

    if form.participants.data:
        form.participants.data = [Member.query.get(
            int(member_id)) for member_id in form.participants.data]

    if form.restaurant.data:
        form.restaurant.data = Restaurant.query.get(int(form.restaurant.data))

    app.logger.info(form.restaurant.data)
    if form.validate_on_submit() or request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            after = After.query.get(form.id.data)
            db.session.delete(after)
            db.session.commit()
            flash('アフター録: "{}" の削除が完了しました'.format(after.title), 'danger')

        elif request.form.get('method') == 'PUT':
            after = After.query.get(form.id.data)
            after.title = after.title.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            after.comment = after.comment.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            form.populate_obj(after)
            db.session.commit()
            flash('アフター録: "{}" の更新が完了しました'.format(after.title), 'warning')

        elif request.form.get('method') == 'POST':
            after = After()
            form.populate_obj(after)
            after.title = after.title.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            after.comment = after.comment.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            after.id = None
            db.session.add(after)
            db.session.commit()
            flash('アフター録: "{}" の登録が完了しました'.format(after.title), 'info')

        return redirect(url_for('after'))
    else:
        if request.form.get('method') == 'DELETE':
            after = After.query.get(form.id.data)
            form = AfterForm(obj=after)
            form.participants.data = after.participants
            form.restaurant.data = after.restaurant
        return render_template('after_confirm.html', form=form)


@app.route('/result/')
def result():
    per_page = 40
    page = request.args.get('page') or 1
    page = max([1, int(page)])
    results = Race.query.order_by(Race.date.desc()).paginate(page, per_page)
    return render_template('result.html', pagination=results, groupby=groupby, key=(lambda x: x.race_type.show_name))


@app.route('/race/')
def race():
    return redirect(url_for('result'))


@app.route('/race/edit', methods=['GET', 'POST'])
@login_required
def race_edit():
    app.logger.info(request.form)
    RaceBaseForm.race_name.choices = [
        (r.race_name, r.race_name) for r in RaceBase.query.all()]
    form = RaceForm(formdata=request.form)

    if form.validate_on_submit():
        return redirect(url_for('race_confirm'), code=307)
    form.race_name.choices = [
        (r.race_name, r.race_name) for r in RaceBase.query.all()]

    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        race = Race.query.get(id)
        form = RaceForm(obj=race)
        form.method.data = 'PUT'
    else:
        form.method.data = 'POST'

    return render_template('race_edit.html', form=form)


@app.route('/race/confirm', methods=['POST'])
@login_required
def race_confirm():
    form = RaceForm(formdata=request.form)
    app.logger.info(request.form)

    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('user'))

    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') in ['PUT', 'POST'] and len(form.race_name_option.data) > 3:
            rb = RaceBase.query.get(form.race_name_option.data)
            if rb is None:
                rb = RaceBase()
                rb.race_name = form.race_name_option.data
                db.session.add(rb)
                db.session.commit()
                app.logger.info('register race_base {}'.format(rb))
            form.race_name.data = rb.race_name

        if request.form.get('method') == 'DELETE':
            race = Race.query.get(form.id.data)
            db.session.delete(race)
            db.session.commit()
            flash('大会: "{}({})" の削除が完了しました'.format(
                race.race_name, race.date), 'danger')

        elif request.form.get('method') == 'PUT':
            race = Race.query.get(form.id.data)
            form.populate_obj(race)
            db.session.commit()
            flash('大会: "{}({})" の更新が完了しました'.format(
                race.race_name, race.date), 'warning')

        elif request.form.get('method') == 'POST':
            race = Race()
            form.populate_obj(race)
            race.id = None
            db.session.add(race)
            db.session.commit()
            flash('大会: "{}({})" の登録が完了しました'.format(
                race.race_name, race.date), 'info')

        return redirect(url_for('race'))
    else:
        if request.form.get('method') == 'DELETE':
            race = Race.query.get(form.id.data)
            form = RaceForm(obj=race)
        return render_template('race_confirm.html', form=form)


@app.route('/result/edit', methods=['GET', 'POST'])
@login_required
def result_edit():
    form = ResultForm(formdata=request.form)
    form.result.data = form.result_h.data * 3600 + \
        form.result_m.data * 60 + form.result_s.data

    if form.validate_on_submit():
        return redirect(url_for('result_confirm'), code=307)

    if request.args.get('method') == 'PUT':
        race_id = int(request.args.get('race_id'))
        race_type_id = int(request.args.get('race_type_id'))
        member_id = int(request.args.get('member_id'))
        result = Result.query.get(
            {"race_id": race_id, "race_type_id": race_type_id, "member_id": member_id})
        form = ResultForm(obj=result)
        form.race = Race.query.get(race_type_id)
        form.result_h.data = int(result.result)//3600
        form.result_m.data = (int(result.result) % 3600)//60
        form.result_s.data = int(result.result) % 60
        form.method.data = 'PUT'

    else:
        race_id = int(request.args.get('race_id'))
        result = Result()
        result.race_id = race_id
        form = ResultForm(obj=result)
        form.race = Race.query.get(race_id)
        form.method.data = 'POST'

    return render_template('result_edit.html', form=form)


@app.route('/result/confirm', methods=['POST'])
@login_required
def result_confirm():
    form = ResultForm(formdata=request.form)
    form.result.data = form.result_h.data * 3600 + \
        form.result_m.data * 60 + form.result_s.data

    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('user'))

    race_id = int(form.race_id.data)
    race_type_id = int(form.race_type_id.data)
    member_id = int(form.member_id.data)

    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            result = Result.query.get(
                {"race_id": race_id, "race_type_id": race_type_id, "member_id": member_id})
            db.session.delete(result)
            db.session.commit()
            flash('{}さんの{}の結果の削除が完了しました'.format(
                result.member.show_name, result.race.race_name), 'danger')

        elif request.form.get('method') == 'PUT':
            result = Result.query.get(
                {"race_id": race_id, "race_type_id": race_type_id, "member_id": member_id})
            form.populate_obj(result)
            db.session.commit()
            flash('{}さんの{}の結果の更新が完了しました'.format(
                result.member.show_name, result.race.race_name), 'warning')

        elif request.form.get('method') == 'POST':
            result = Result()
            form.populate_obj(result)
            db.session.add(result)
            db.session.commit()
            flash('{}さんの{}の結果の登録が完了しました'.format(
                result.member.show_name, result.race.race_name), 'info')

        return redirect(url_for('result'))
    else:
        if request.form.get('method') == 'DELETE':
            result = Result.query.get(
                {"race_id": race_id, "race_type_id": race_type_id, "member_id": member_id})
            form = ResultForm(obj=result)
        form.member = Member.query.get(int(form.member_id.data))
        form.race_type = RaceType.query.get(int(form.race_type_id.data))
        form.race = Race.query.get(int(form.race_id.data))
        return render_template('result_confirm.html', form=form)


@app.route('/ranking')
def ranking():
    q1 = db.session.query(Member.show_name, func.count(TrainingParticipant.training_id).label('cnt'), Member.sex).\
        join(TrainingParticipant, TrainingParticipant.member_id == Member.id).\
        group_by(TrainingParticipant.member_id)
    year_list = request.args.getlist('year_list')
    app.logger.info(year_list)
    if year_list:
        q2 = q1.\
            filter(Member.year.in_(year_list))
    else:
        q2 = q1

    items = [{'rank': i+1, 'show_name': d[0], 't_cnt': d[1], 'sex': d[2]}
             for i, d in enumerate(q2.order_by(db.text('cnt DESC')).all())
             ]

    return render_template('ranking.html', items=items, years=range(current_school_year, 1990, -1))


@app.route('/search/')
def search():
    return render_template('search.html')


@app.route('/race-type/')
@login_required
def race_type():
    race_types = RaceType.query.order_by(RaceType.race_type, RaceType.duration)
    return render_template('race_type.html', race_types=race_types)


@app.route('/restaurant/')
@login_required
def restaurant():
    afters = list(set(list(itertools.chain.from_iterable(db.session.query(After.restaurant_id).all()))))
    per_page = 40
    page = request.args.get('page') or 1
    page = max([1, int(page)])
    #t = text("SELECT R.*, COUNT(A.restaurant_id) AS cnt FROM restaurant AS R LEFT JOIN after AS A ON R.id = A.restaurant_id GROUP BY R.id ORDER BY cnt DESC")
    #restaurants = db.session.execute(t)
    restaurants = db.session.query(Restaurant, func.count(After.restaurant_id).label('cnt')).\
        outerjoin(After, Restaurant.id == After.restaurant_id).group_by(Restaurant.id).order_by(db.text('cnt DESC')).paginate(page, per_page)
    return render_template('restaurant.html', pagination=restaurants, afters=afters)


@app.route('/restaurant/edit', methods=['GET', 'POST'])
@login_required
def restaurant_edit():
    form = RestaurantForm(formdata=request.form)

    if form.validate_on_submit():
        return redirect(url_for('restaurant_confirm'), code=307)

    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        restaurant = Restaurant.query.get(id)
        form = RestaurantForm(obj=restaurant)
        form.name.data = restaurant.name
        form.place.data = restaurant.place
        form.score.data = restaurant.score
        form.comment.data = restaurant.comment
        form.method.data = 'PUT'
    else:
        form.method.data = 'POST'

    return render_template('restaurant_edit.html', form=form)


@app.route('/restaurant/confirm', methods=['POST'])
@login_required
def restaurant_confirm():
    form = RestaurantForm(formdata=request.form)

    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('restaurant'))

    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            restaurant = Restaurant.query.get(form.id.data)
            db.session.delete(restaurant)
            db.session.commit()
            flash('レストラン: "{}" の削除が完了しました'.format(restaurant.name), 'danger')

        elif request.form.get('method') == 'PUT':
            restaurant = Restaurant.query.get(form.id.data)
            restaurant.name = restaurant.name.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            restaurant.comment = restaurant.comment.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            form.populate_obj(restaurant)
            db.session.commit()
            flash('レストラン: "{}" の更新が完了しました'.format(restaurant.name), 'warning')

        elif request.form.get('method') == 'POST':
            restaurant = Restaurant()
            form.populate_obj(restaurant)
            restaurant.name = restaurant.name.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            restaurant.comment = restaurant.comment.encode(
                'euc-jp', errors='xmlcharrefreplace').decode('euc-jp')
            restaurant.id = None
            db.session.add(restaurant)
            db.session.commit()
            flash('レストラン: "{}" の登録が完了しました'.format(restaurant.name), 'info')

        return redirect(url_for('restaurant'))

    else:
        if request.form.get('method') == 'DELETE':
            restaurant = Restaurant.query.get(form.id.data)
            form = RestaurantForm(obj=restaurant)
        return render_template('restaurant_confirm.html', form=form)
