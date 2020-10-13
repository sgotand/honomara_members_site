from itertools import groupby
import itertools
import datetime
from flask import render_template, request, abort, redirect, url_for, flash
from honomara_members_site import app, db
from honomara_members_site.login import login_check
from honomara_members_site.model import *
from sqlalchemy import func
from sqlalchemy.sql import text
from honomara_members_site.form import *
from flask_login import login_required, login_user, logout_user
from honomara_members_site.util import validate_course_and_set_name, form_set_time


@app.route('/')
def index():
    after = After.query.order_by(After.updated_at.desc()).limit(1).one()
    training = Training.query.order_by(
        Training.updated_at.desc()).limit(1).one()
    return render_template('index.html', after=after, training=training)


@app.route('/login/', methods=["GET", "POST"])
def login():
    if(request.method == "POST"):
        username = request.form["username"]
        password = request.form["password"]
        if login_check(username, password):
            flash('ログインしました', 'success')
            return redirect(url_for('index'))
        else:
            flash('username または password が正しくありません', 'danger')
            return render_template("login.html")
    else:
        return render_template("login.html")


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました', 'success')
    return redirect(url_for('index'))


@app.route('/member/')
@login_required
def member():
    members = Member.query.order_by(Member.year.desc(), Member.family_kana)
    return render_template('member.html', members=members,
                           groupby=groupby, key=(lambda x: x.year))


@app.route('/member/<int:member_id>')
@login_required
def member_individual(member_id):
    m = Member.query.get(member_id)
    if m is None:
        return abort(404)

    m.results.sort(key=lambda x: x.race.date, reverse=False)
    raw_results = list(
        filter(lambda x: x.race.course.distance in [42.195, 21.0975], m.results))

    results1 = []
    results2 = []
    races1 = []
    races2 = []
    for r in raw_results:
        if r.distance == 42.195:
            results1 += [{'x': "{:%Y/%m/%d}".format(r.race.date),
                          'y': r.time // 1000}]
            races1 += [r.race.course.competition.name]
        else:
            results2 += [{'x': "{:%Y/%m/%d}".format(r.race.date),
                          'y': r.time // 1000}]
            races2 += [r.race.course.competition.name]

    trainings = db.session.query(TrainingParticipant.member_id, Training.date).\
        filter(TrainingParticipant.member_id == member_id).\
        join(Training, Training.id == TrainingParticipant.training_id).\
        order_by(Training.date).all()

    afters = db.session.query(AfterParticipant.member_id, After.date).\
        filter(AfterParticipant.member_id == member_id).\
        join(After, After.id == AfterParticipant.after_id).\
        order_by(After.date)

    afterdays = afters.distinct(After.date).all()
    afters = afters.all()
    first_training = trainings[0].date.strftime(
        '%Y/%m/%d') if len(trainings) > 0 else '未参加'
    first_after = afters[0].date.strftime(
        '%Y/%m/%d') if len(afters) > 0 else '未参加'
    count_trainings = len(trainings)
    count_afters = len(afters)
    count_afterdays = len(afterdays)

    def summary(li, name):
        for i in range(len(li)):
            li[i] = {'year': li[i][1].year, 'month': li[i][1].month}
            if li[i]['month'] < 4:
                li[i]['year'] -= 1
                li[i]['month'] += 12
        x = []
        for key, group in groupby(li, key=lambda x: x['year']):
            y = []
            for year in group:
                y.append(year['month'])
            x.append({'year': key, name + '_sum': len(y), name + '_first_half': len(
                [i for i in y if i < 10]), name + '_second_half': len([i for i in y if i >= 10])})

        return x

    participations = []
    for key, group in groupby(sorted(summary(trainings, "trainings") + summary(afters, "afters") +
                                     summary(afterdays, "afterdays"), key=lambda x: x['year']), key=lambda x: x['year']):
        y = []
        for year in group:
            y.append(year)
        for i in range(len(y) - 1):
            y[0].update(y[i + 1])
        participations.append(y[0])

    restaurants = db.session.query(AfterParticipant.member_id, Restaurant.name, Restaurant.id, func.count(After.id).label('cnt')).\
        filter(AfterParticipant.member_id == member_id).\
        join(After, After.id == AfterParticipant.after_id).\
        join(Restaurant, Restaurant.id == After.restaurant_id).\
        group_by(Restaurant.id).order_by(db.text('cnt DESC')).all()

    return render_template('member_individual.html', member=m, results1=str(results1), results2=str(results2), races1=str(races1), races2=str(races2), first_training=first_training,
                           first_after=first_after, count_trainings=count_trainings, count_afters=count_afters, count_afterdays=count_afterdays, participations=participations, restaurants=restaurants)


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
    day_from = request.args.get('from')
    day_until = request.args.get('until')
    if keywords is not None:
        for keyword in keywords.split(','):
            keyword = keyword.replace(' ', '')
            keyword = keyword.replace('　', '')
            trainings = trainings.filter(Training.comment.contains(keyword))
    if day_from is not None and day_from != "":
        day_from = datetime.datetime.strptime(day_from, '%Y-%m-%d')
        trainings = trainings.filter(Training.date >= day_from)
    if day_until is not None and day_until != "":
        day_until = datetime.datetime.strptime(day_until, '%Y-%m-%d')
        trainings = trainings.filter(Training.date <= day_until)
    if request.args.get('submit') == "検索":
        count = trainings.count()
        if count > 0:
            flash('{}件ヒットしました'.format(count), 'info')
        else:
            flash('ヒットしませんでした', 'danger')
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
        form.participants1.data = [m.id for m in training.participants]
        form.participants2.data = [m.id for m in training.participants]
        form.participants3.data = [m.id for m in training.participants]
        form.participants4.data = [m.id for m in training.participants]
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

    form.participants.data = form.participants1.data +\
        form.participants2.data +\
        form.participants3.data +\
        form.participants4.data +\
        form.participants.data

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
    per_page = 20
    page = request.args.get('page') or 1
    page = max([1, int(page)])
    afters = After.query
    stage = request.args.get('stage')
    keywords = request.args.get('keyword')
    day_from = request.args.get('from')
    day_until = request.args.get('until')
    if stage is not None and stage != "":
        afters = afters.filter(After.after_stage == int(stage))
    if keywords is not None:
        for keyword in keywords.split(','):
            keyword = keyword.replace(' ', '')
            keyword = keyword.replace('　', '')
            afters = afters.filter(After.comment.contains(keyword))
    if day_from is not None and day_from != "":
        day_from = datetime.datetime.strptime(day_from, '%Y-%m-%d')
        afters = afters.filter(After.date >= day_from)
    if day_until is not None and day_until != "":
        day_until = datetime.datetime.strptime(day_until, '%Y-%m-%d')
        afters = afters.filter(After.date <= day_until)
    if request.args.get('submit') == "検索":
        count = afters.count()
        if count > 0:
            flash('{}件ヒットしました'.format(count), 'info')
        else:
            flash('ヒットしませんでした', 'danger')
    afters = afters.order_by(After.date.desc()).paginate(page, per_page)
    return render_template('after.html', pagination=afters)


@app.route('/after/edit', methods=['GET', 'POST'])
@login_required
def after_edit():
    form = AfterForm(formdata=request.form)
    keyword = request.args.get('keyword')
    app.logger.info(form.data)

    if form.validate_on_submit():
        return redirect(url_for('after_confirm'), code=307)

    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        after = After.query.get(id)
        form = AfterForm(obj=after)
        form.participants1.data = [m.id for m in after.participants]
        form.participants2.data = [m.id for m in after.participants]
        form.participants3.data = [m.id for m in after.participants]
        form.participants4.data = [m.id for m in after.participants]
        form.participants.data = [m.id for m in after.participants]
        app.logger.info(form.participants1)
        app.logger.info(form.participants2)
        app.logger.info(form.participants3)
        app.logger.info(form.participants4)
        app.logger.info(form.participants)
        form.restaurant.data = after.restaurant.id
        form.method.data = 'PUT'
    else:
        if keyword is not None:
            form.restaurant.choices = [(r.id, "{}({})".format(
                r.name, r.place)) for r in Restaurant.query.filter(Restaurant.name.contains(keyword)).order_by(Restaurant.score.desc()).all()]
        form.method.data = 'POST'

    return render_template('after_edit.html', form=form)


@app.route('/after/confirm', methods=['POST'])
@login_required
def after_confirm():
    form = AfterForm(formdata=request.form)
    app.logger.info(form.data)
    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('after'))

    form.participants.data = form.participants1.data +\
        form.participants2.data +\
        form.participants3.data +\
        form.participants4.data +\
        form.participants.data

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
            app.logger.info(after)
            app.logger.info(form.data)
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
            form.participants1.data = after.participants
            form.participants2.data = after.participants
            form.participants3.data = after.participants
            form.participants4.data = after.participants
            form.participants.data = after.participants
            form.restaurant.data = after.restaurant
        return render_template('after_confirm.html', form=form)


@app.route('/result/')
def result():
    per_page = 40
    page = request.args.get('page') or 1
    page = max([1, int(page)])
    results = Race.query.join(Course).order_by(
        Race.date.desc(), text("course.competition_id")).paginate(page, per_page)
    return render_template('result.html', pagination=results)


@app.route('/competition/')
def competition():
    competitions = Competition.query.order_by(
        Competition.place)
    return render_template('competition.html', competitions=competitions)


@app.route('/competition/<int:competition_id>')
@login_required
def competition_individual(competition_id):
    c = Competition.query.get(competition_id)
    if c is None:
        return abort(404)

    return render_template('competition_individual.html', competition=c)


@app.route('/competition/edit', methods=['GET', 'POST'])
@login_required
def competition_edit():
    form = CompetitionForm(formdata=request.form)
#     form.visible.data = request.form.get('visible') != 'False'

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
#     form.visible.data = request.form.get('visible') != 'False'

    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('competition'))

    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            competition = Competition.query.get(form.id.data)
            db.session.delete(competition)
            db.session.commit()
            flash('大会："{}"の削除が完了しました'.format(competition.name), 'danger')
        elif request.form.get('method') == 'PUT':
            competition = Competition.query.get(form.id.data)
            form.populate_obj(competition)
            db.session.commit()
            flash('大会："{}"の更新が完了しました'.format(competition.name), 'warning')
        elif request.form.get('method') == 'POST':
            competition = Competition()
            form.populate_obj(competition)
            competition.id = None
            db.session.add(competition)
            db.session.commit()
            flash('大会："{}"の登録が完了しました'.format(competition.name), 'info')

        return redirect(url_for('competition'))
    else:
        if request.form.get('method') == 'DELETE':
            competition = Competition.query.get(form.id.data)
            form = CompetitionForm(obj=competition)
        return render_template('competition_confirm.html', form=form)


@app.route('/course/edit', methods=["GET", "POST"])
def course_edit():
    form = CourseForm(formdata=request.form)
    errmsg = validate_course_and_set_name(form=form)

    if errmsg is not None:
        flash(errmsg, 'danger')
    if form.validate_on_submit() and errmsg is None:
        return redirect(url_for('course_confirm'), code=307)

    competition_id = request.args.get(
        "competition_id", default=-1, type=int) or request.form.get('competition_id')

    if competition_id == -1:
        return render_template('template_message.html',
                               message='大会指定が無効です<br>先に大会を作成してください')

    competition = Competition.query.get(competition_id)
    form.competition_id.data = competition.id

    if form.validate_on_submit():
        return redirect(url_for('course_confirm'), code=307)

    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        course = course.query.get(id)
        form = courseForm(obj=course)
        form.method.data = 'PUT'
    else:
        form.method.data = 'POST'
    return render_template('course_edit.html', form=form,
                           competition=competition)


@app.route('/course/confirm', methods=["POST"])
def course_confirm():
    form = CourseForm(formdata=request.form)
    validate_course_and_set_name(form=form)  # set form.show_name.data
    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('competition'))

    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            course = Course.query.get(form.id.data)
            db.session.delete(course)
            db.session.commit()
            flash('大会："{}"の削除が完了しました'.format(course.name), 'danger')
        elif request.form.get('method') == 'PUT':
            course = Course.query.get(form.id.data)
            form.populate_obj(course)
            db.session.commit()
            flash('大会："{}"の更新が完了しました'.format(course.name), 'warning')
        elif request.form.get('method') == 'POST':
            course = Course()
            form.populate_obj(course)
            course.id = None
            db.session.add(course)
            db.session.commit()
            flash('コース："{}"の登録が完了しました'.format(course.show_name), 'info')
        return redirect(url_for('result'))
    else:
        if request.form.get('method') == 'DELETE':
            course = Course.query.get(form.id.data)
            form = CourseForm(obj=course)
        competition = Competition.query.get(form.competition_id.data)
        return render_template('course_confirm.html',
                               form=form, competition=competition)


@app.route('/race/')
def race():
    return redirect(url_for('result'))


@app.route('/race/edit', methods=['GET', 'POST'])
@login_required
def race_edit():
    form = RaceForm(formdata=request.form)

    if form.validate_on_submit():
        return redirect(url_for('race_confirm'), code=307)
    else:
        app.logger.info(form.errors)
    course = None

    if request.form.get('method') == 'PUT':
        race = Race.query.get(form.id.data)
        if race is None:
            flash('該当の大会日程は登録されていません', "danger")
            return redirect(url_for('result'))
        form = RaceForm(obj=race)
        course = race.course
#         form.method.data = 'PUT'
    else:
        course = Course.query.get(request.form.get("course_id"))
        if course is None:
            flash('該当の大会種目は登録されていません', "danger")
            return redirect(url_for('result'))
        form.method.data = 'POST'  # unnecessary

    return render_template('race_edit.html', form=form, course=course)


@app.route('/race/confirm', methods=['POST'])
@login_required
def race_confirm():
    form = RaceForm(formdata=request.form)
    app.logger.info(request.form)
    app.logger.info(form.data)
    course = Course.query.get(form.course_id.data)

    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('result'))

    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            race = Race.query.get(form.id.data)
            db.session.delete(race)
            flash('大会: "{}({})" の削除が完了しました'.format(
                race.course.competition.name, race.date), 'danger')

        elif request.form.get('method') == 'PUT':
            race = Race.query.get(form.id.data)
            form.populate_obj(race)
            flash('大会: "{}({})" の更新が完了しました'.format(
                race.course.competition.name, race.date), 'warning')

        elif request.form.get('method') == 'POST':
            race = Race()
            form.populate_obj(race)
            race.id = None
            db.session.add(race)
            flash('大会: "{}({})" の登録が完了しました'.format(
                race.course.competition.name, race.date), 'info')
        db.session.commit()
        return redirect(url_for('race'))
    else:
        if request.form.get('method') == 'DELETE':
            race = Race.query.get(form.id.data)
            form = RaceForm(obj=race)
        return render_template('race_confirm.html', form=form, course=course)


@app.route('/result/edit', methods=['GET', 'POST'])
@login_required
def result_edit():
    app.logger.info(request.form)
    form = ResultAllForm(formdata=request.form)
    app.logger.info(form.data)
    form_set_time(form=form)
    competition, course = None, None

    if request.args.get("restart") == "race":
        race = Race.query.get(request.args.get("race_id"))
        form.race_id.data = race.id
        form.course_id.data = race.course_id
        form.competition_id.data = race.course.competition_id
        form.date.data = race.date
        form.method.data = "POST"
        app.logger.info("restart")
        app.logger.info(form.data)

    form.competition_id.choices = [(c.id, c.name) for c in Competition.query.order_by(
        Competition.name.desc()).all()]

    # 大会未指定時は大会選択へjump
    if form.competition_id.data is None:
        form.method.data = 'POST'
        return render_template('result_edit_competition.html', form=form)

    competition = Competition.query.get(form.competition_id.data)

    form.course_id.choices = [(c.id, c.distance) for c in Course.query.filter(Course.competition_id == form.competition_id.data).order_by(
        Course.distance.desc()).all()]

    if form.method.data == "POST":
        # コース未指定時はコース選択へjump
        if form.course_id.data is None:
            return render_template(
                'result_edit_course.html', form=form, competition=competition)
        else:
            course = Course.query.get(form.course_id.data)

        # レース(日付)未指定時は
        if form.date.data is None:
            if form.race_id.data is None:
                return render_template(
                    'result_edit_race.html', form=form, competition=competition, course=course)
            else:
                race = Race.query.get(form.race_id.data)
                form.date.data = race.date
        d = form.validate()
        if not d:
            app.logger.info(d)
            app.logger.info(form.errors)
        if form.validate_on_submit():
            return redirect(url_for('result_confirm'), code=307)

    elif form.method.data == 'PUT':
        if form.validate_on_submit():
            return redirect(url_for('result_confirm'), code=307)
        result_id = request.form.get('result_id')  # request.args.get('id')
        result = Result.query.get(result_id)
        form = ResultAllForm(obj=result)  # TODO
        form_set_time(form=form)
        form.date.data = result.race.date
        course = result.race.course
        form.course_id.data = course.id
        form.race_id.data = result.race_id
        form.participants.data = [m.id for m in result.participants]
        form.method.data = 'PUT'
#         app.logger.info("participants of results")
#         app.logger.info(form.participants)

    return render_template('result_edit.html', form=form,
                           competition=competition, course=course)


@app.route('/result/confirm', methods=['POST'])
@login_required
def result_confirm():
    app.logger.info(request.form)
    form = ResultAllForm(formdata=request.form)
    form_set_time(form=form)
    app.logger.info(form.data)

    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('result'))

#     competition = form.competition.data
#     course = form.course.data
#     race = form.race_id.data or -1
#     participants = form.participants.data

    form.competition_id.choices = [(c.id, c.name) for c in Competition.query.order_by(
        Competition.name.desc()).all()]

    form.course_id.choices = [(c.id, c.distance) for c in Course.query.join(Competition).filter(
        Competition.id == form.competition_id.data).order_by(Course.distance.desc()).all()]

    if form.validate_on_submit() and request.form.get('confirmed') == 'True':
        if request.form.get('method') == 'DELETE':
            result = Result.query.get(request.form.get('id'))
            competition_name = result.race.course.competition.name
            participant_name = result.participants[0].show_name
            db.session.delete(result)
            db.session.commit()
            flash('{}さんの{}の結果の削除が完了しました'.format(
                participant_name, competition_name), 'danger')
        elif request.form.get('method') == 'PUT':

            result = Result.query.get(form.id.data)
            competition_name = result.race.course.competition.name
            participant_name = result.participants[0].show_name
            app.logger.info(result)
            app.logger.info(form.data)
            form.participants.data = [Member.query.get(
                int(member_id)) for member_id in form.participants.data]
            form.populate_obj(result)
            db.session.commit()
            flash('{}さんの{}の結果の更新が完了しました'.format(
                participant_name, competition_name), 'warning')

        elif request.form.get('method') == 'POST':
            race = None
            # create race if not exists
            if form.race_id.data is not None and form.race_id.data >= 0:
                race = Race.query.get(form.race_id.data)
            elif form.date.data is not None:
                race = Race.query.filter(Race.course_id == form.course_id.data).filter(
                    Race.date == form.date.data).all()
                if len(race) == 1:
                    race = race[0]
                elif len(race) == 0:
                    race = Race()
                    race.course_id = form.course_id.data
                    race.date = form.date.data
                    db.session.add(race)
                    race = Race.query.filter(Race.course_id == race.course_id).filter(
                        Race.date == race.date).one()
                else:
                    assert(False)  # TODO
            else:
                race = None
            form2 = ResultForm(formdata=request.form)
            form2.race_id.data = race.id
            form2.participants.data = [Member.query.get(
                int(member_id)) for member_id in form.participants.data]

            result = Result()
            form2.populate_obj(result)
            result.id = None
            db.session.add(result)
            db.session.commit()
            flash('{}さんの{}の結果の登録が完了しました'.format(
                result.participants[0].show_name, result.race.course.competition.name), 'info')

        app.logger.info("form.submit.data")
        app.logger.info(form.submit.data)
        app.logger.info(request.form.get("submit"))
        if request.form.get("submitValue") == "登録して、同じ大会の記録を追加":
            return redirect(
                url_for('result_edit', restart="race", race_id=result.race_id))
        else:
            return redirect(url_for('result'))
    else:  # show confirm view when not confirmed
        app.logger.info(form.errors)

        if request.form.get('method') == 'DELETE':
            result = Result.query.get(request.form.get("result_id"))
            form = ResultAllForm(obj=result)
            form_set_time(form=form)
            form.course_id.data = result.race.course_id
            form.competition_id.data = result.race.course.competition_id
            form.participants.data = [m.id for m in result.participants]
            form.date.data = result.race.date
#             app.logger.info(result)
            app.logger.info(form.data)
#             abort(404)
            # TODO
        competition = Competition.query.get(form.competition_id.data)
        course = Course.query.get(form.course_id.data)
        form.participants = [Member.query.get(mid)
                             for mid in form.participants.data]
        return render_template(
            'result_confirm.html', form=form, competition=competition, course=course)


@ app.route('/ranking')
def ranking():
    query = db.session.query(Member.show_name, func.count(TrainingParticipant.training_id).label('cnt'), Member.sex, Member.id).join(
        TrainingParticipant, TrainingParticipant.member_id == Member.id).join(Training, TrainingParticipant.training_id == Training.id)
    year_list = request.args.getlist('year_list')
    app.logger.info(request.form)

    begin = request.args.get("begin") or datetime.datetime(1990, 1, 1)
    end = request.args.get("end") or datetime.datetime.today()
    query = query.filter(Training.date >= begin) if begin else query
    query = query.filter(Training.date <= end)
    query = query.group_by(TrainingParticipant.member_id)
    items = []
    if year_list:
        query = query.filter(Member.year.in_(year_list))
        items = [{'rank': i + 1, 'show_name': d[0], 't_cnt': d[1], 'sex': d[2], 'id': d[3]}
                 for i, d in enumerate(query.order_by(db.text('cnt DESC')).all())
                 ]
    year_list = map(lambda x: int(x), year_list)

    return render_template('ranking.html', items=items, begin=begin, end=end,
                           year_list=year_list, years=range(current_school_year, 1990, -1))


@ app.route('/search/')
def search():
    return render_template('search.html')


@ app.route('/restaurant/')
@ login_required
def restaurant():
    afters = list(set(list(itertools.chain.from_iterable(
        db.session.query(After.restaurant_id).all()))))
    per_page = 40
    page = request.args.get('page') or 1
    page = max([1, int(page)])
    restaurants = Restaurant.query.order_by(
        Restaurant.score.desc()).paginate(page, per_page)
    return render_template(
        'restaurant.html', pagination=restaurants, afters=afters)


@ app.route('/restaurant/edit', methods=['GET', 'POST'])
@ login_required
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


@ app.route('/restaurant/confirm', methods=['POST'])
@ login_required
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


@app.errorhandler(404)
def page_not_found(error):
    return render_template('template_message.html',
                           message='指定されたページは存在しません'), 404
