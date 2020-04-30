from itertools import groupby
from flask import render_template, request, abort, redirect, url_for, flash
from honomara_members_site import app, db
from honomara_members_site.login import login_check
from honomara_members_site.model import Member, Training, TrainingParticipant, After, Restaurant, Competition, Race, Result
from sqlalchemy import func
from honomara_members_site.form import MemberForm, TrainingForm, AfterForm, CompetitionForm, RaceForm, ResultForm
from flask_login import login_required, login_user, logout_user
from honomara_members_site.util import current_school_year, data_collection
from datetime import date, timedelta


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
    trainings = trainings.order_by(
        Training.date.desc()).paginate(page, per_page)
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


@app.route('/competition/')
def competition():
    competitions = Competition.query
    return render_template('competition.html', competitions=competitions, places=data_collection['place'])


@app.route('/competition/<int:id>')
def competition_individual(id):
    competition = Competition.query.get(id)
    if competition is None:
        return abort(404)
    return render_template('competition_individual.html', competition=competition)


@app.route('/competition/edit', methods=['GET', 'POST'])
@login_required
def competition_edit():
    form = CompetitionForm(formdata=request.form)

    if form.validate_on_submit():
        return redirect(url_for('competition_confirm'), code=307)

    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        competition = Competition.query.get(id)
        form = CompetitionForm(obj=competition)
        form.method.data = 'PUT'
    else:
        form.method.data = 'POST'
    return render_template('competition_edit.html', form=form)


@app.route('/competition/confirm', methods=['POST'])
@login_required
def competition_confirm():
    form = CompetitionForm(formdata=request.form)
    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('user'))

    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            competition = Competition.query.get(form.id.data)
            db.session.delete(competition)
            db.session.commit()
            flash('大会："{}"の削除が完了しました'.format(
                competition.show_name), 'danger')
        elif request.form.get('method') == 'PUT':
            competition = Competition.query.get(form.id.data)
            form.populate_obj(competition)
            db.session.commit()
            flash('大会："{}"の更新が完了しました'.format(
                competition.show_name), 'warning')
        elif request.form.get('method') == 'POST':
            competition = Competition()
            form.populate_obj(competition)
            competition.id = None
            db.session.add(competition)
            db.session.commit()
            flash('大会："{}"の更新が完了しました'.format(
                competition.show_name), 'info')

        return redirect(url_for('competition'))
    else:
        if request.form.get('method') == 'DELETE':
            competition = Competition.query.get(form.id.data)
            form = CompetitionForm(obj=competition)
        return render_template('competition_confirm.html', form=form, places=data_collection['place'])


@app.route('/race/edit/', methods=['GET', 'POST'])
@login_required
def race_edit():
    app.logger.info(request.form)
    form = RaceForm(formdata=request.form)
    if form.validate_on_submit():
        return redirect(url_for('race_confirm'), code=307)
    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        race = Race.query.get(id)
        competition_name = race.competition.show_name
        form = RaceForm(obj=race)
        form.method.data = 'PUT'
    else:
        form.competition_id.data = request.args.get(
            'competition_id')  # 新規登録の場合もcompetiton_idは前もって受け取る。
        competition = Competition.query.get(form.competition_id.data)
        competition_name = competition.show_name
        form.method.data = 'POST'
    return render_template('race_edit.html', form=form, competition_name=competition_name)


@app.route('/race/confirm', methods=['POST'])
@login_required
def race_confirm():
    app.logger.info(request.form)
    form = RaceForm(formdata=request.form)
    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('user'))
    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            race = Race.query.get(form.id.data)
            competition_name = race.competition.name
            db.session.delete(race)
            db.session.commit()
            flash('レース: "{}"・"{}" の削除が完了しました'.format(
                competition_name, race.show_name), 'danger')
        elif request.form.get('method') == 'PUT':
            race = Race.query.get(form.id.data)
            form.populate_obj(race)
            db.session.commit()
            flash('レース:"{}"・"{}" の更新が完了しました'.format(
                race.competition.name, race.show_name), 'warning')
        elif request.form.get('method') == 'POST':
            race = Race()
            form.populate_obj(race)
            race.id = None
            db.session.add(race)
            db.session.commit()
            flash('レース:"{}"・"{}" の登録が完了しました'.format(
                race.competition.name, race.show_name), 'info')
        return redirect(url_for('competition_individual', id=form.competition_id.data))
    else:
        if request.form.get('method') == 'DELETE':
            race = Race.query.get(form.id.data)
            form = RaceForm(obj=race)
        competition = Competition.query.get(form.competition_id.data)
        competition_name = competition.show_name
        return render_template('race_confirm.html', form=form, competition_name=competition_name)


@app.route('/result/')
def result():
    list_type = request.args.get('list_type') or 'latest'
    year = request.args.get('year') or current_school_year
    results = Result.query.order_by(
        Result.date.desc(), Result.competition_id, Result.race_id, Result.record).filter(Result.date > (date.today() - timedelta(days=400)))
    key = {}
    key['date'] = (lambda x: x.date)
    key['competition'] = (lambda x: x.competition)
    key['race'] = (lambda x: x.race)
    if list_type == 'year':
        year = int(year)
        results_by_year = Result.query.order_by(
            Result.date, Result.competition_id, Result.race_id, Result.record).filter(Result.date >= date(year, 4, 1)).filter(Result.date < date(year+1, 4, 1))
        results = results_by_year
    return render_template('result.html', results=results, groupby=groupby, key=key, list_type=list_type, current_school_year=current_school_year, year=year)


@app.route('/result/edit', methods=['GET', 'POST'])
@login_required
def result_edit():
    form = ResultForm(formdata=request.form)
    form.record.data = form.record_h.data * 3600 + \
        form.record_m.data * 60 + form.record_s.data
    app.logger.info(request.form)
    if form.submit.data:
        if request.form['step'] == 'step1':
            step = "step2"
            form.race_id.choices = [(r.id, "{}({})".format(r.show_name, r.competition.show_name))
                                    for r in Race.query.filter(Race.competition_id == form.competition_id.data)]
            return render_template('result_edit.html', form=form, step=step)
        elif request.form['step'] == 'step2':
            if form.validate_on_submit():
                return redirect(url_for('result_confirm'), code=307)

    if request.args.get('method') == 'PUT':
        id = request.args.get('id')
        result = Result.query.get(id)
        form = ResultForm(obj=result)
        form.record_h.data = int(result.record)//3600
        form.record_m.data = (int(result.record) % 3600)//60
        form.record_s.data = int(result.record) % 60
        form.method.data = 'PUT'
        step = "step2"
    else:
        form.method.data = 'POST'
        step = "step1"
    return render_template('result_edit.html', form=form, step=step)


@app.route('/result/confirm', methods=['POST'])
@login_required
def result_confirm():
    form = ResultForm(formdata=request.form)
    form.record.data = form.record_h.data * 3600 + \
        form.record_m.data * 60 + form.record_s.data
    app.logger.info(request.form)

    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('user'))

    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            result = Result.query.get(form.id.data)
            member_name = result.member.show_name
            competition_name = result.competition.show_name
            db.session.delete(result)
            db.session.commit()
            flash('{}さんの{}の結果の削除が完了しました'.format(
                member_name, competition_name), 'danger')

        elif request.form.get('method') == 'PUT':
            result = Result.query.get(form.id.data)
            form.populate_obj(result)
            db.session.commit()
            flash('{}さんの{}の結果の更新が完了しました'.format(
                result.member.show_name, result.competition.show_name), 'warning')

        elif request.form.get('method') == 'POST':
            result = Result()
            form.populate_obj(result)
            result.id = None
            db.session.add(result)
            db.session.commit()
            flash('{}さんの{}の結果の登録が完了しました'.format(
                result.member.show_name, result.competition.show_name), 'info')

        return redirect(url_for('result'))
    else:
        if request.form.get('method') == 'DELETE':
            result = Result.query.get(form.id.data)
            form = ResultForm(obj=result)
        competition = Competition.query.get(form.competition_id.data)
        competition_name = competition.show_name
        race = Race.query.get(form.race_id.data)
        race_name = race.show_name
        member = Member.query.get(form.member_id.data)
        member_name = member.show_name
        return render_template('result_confirm.html', form=form, competition_name=competition_name, race_name=race_name, member_name=member_name)


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
