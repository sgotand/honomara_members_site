from itertools import groupby
from flask import render_template, request, abort, redirect, url_for, flash
from honomara_members_site import app, db
from honomara_members_site.login import login_check
from honomara_members_site.model import Member, Training, TrainingParticipant, After, Restaurant, Competition, CourseBase, Course, Race, Result
from sqlalchemy import func
from honomara_members_site.form import MemberForm, TrainingForm, AfterForm, CompetitionForm, CourseBaseForm, CourseForm
from flask_login import login_required, login_user, logout_user
from honomara_members_site.util import current_school_year, data_collection
from datetime import date, timedelta
import time


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
    competitions_with_data = []
    # ここで時間がかかる。前もって計算しておくと良さそう。
    for competition in competitions:
        sum_mem = 0
        for course in competition.courses:
            for race in course.races:
                for _ in race.results:
                    sum_mem += 1
        years = []
        for course in competition.courses:
            for race in course.races:
                if not race.date.year in years:
                    years.append(race.date.year)
        if len(years) == 0:
            last_year = None
        else:
            last_year = years[len(years)-1]
        competitions_with_data.append(
            [competition, sum_mem, len(years), last_year])
    competitions_with_data.sort(key=lambda x: x[1], reverse=True)
    return render_template('competition.html', competitions_with_data=competitions_with_data)


@app.route('/competition/<int:id>')
def competition_individual(id):
    competition = Competition.query.get(id)
    rankings = db.session.query(Course, Race, Result).\
        join(Result.race).\
        join(Race.course).\
        order_by(Course.id, Result.time, Result.distance).\
        filter(Course.competition_id == id)
    history = db.session.query(Course, Race, Result).\
        join(Result.race).\
        join(Race.course).\
        order_by(Race.date, Course.id, Result.time, Result.distance).\
        filter(Course.competition_id == id)
    if competition is None:
        return abort(404)
    sum_mem = 0
    sum_ind = []
    for course in competition.courses:
        for race in course.races:
            for result in race.results:
                sum_mem += 1
                if len(sum_ind) == 0:
                    sum_ind.append([result.member, 1])
                else:
                    Done = False
                    for i in range(len(sum_ind)):
                        if result.member == sum_ind[i][0]:
                            sum_ind[i][1] += 1
                            Done = True
                            break
                    if not Done:
                        sum_ind.append([result.member, 1])
    sum_ind.sort(key=lambda x: x[1], reverse=True)
    sum_ind_top5 = sum_ind[:5]
    for x in sum_ind[5:]:
        if sum_ind_top5[len(sum_ind_top5)-1][1] == x[1]:
            sum_ind_top5.append(x)
        else:
            break
    dates = []
    for course in competition.courses:
        for race in course.races:
            if not race.date in dates:
                dates.append(race.date)
    season = []
    for date in dates:
        if len(season) == 0:
            season.append(date.month)
        if not date.month in season:
            season.append(date.month)
    key = {}
    key['year'] = (lambda x: x.Race.date.year)
    key['course'] = (lambda x: x.Course)
    return render_template('competition_individual.html', competition=competition, key=key, groupby=groupby, sum_mem=sum_mem, dates=dates, season=season, sum_ind_top5=sum_ind_top5, rankings=rankings, history=history)


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


@app.route('/course-base/')
@login_required
def course_base():
    course_bases = CourseBase.query.\
        order_by(CourseBase.type, CourseBase.distance, CourseBase.duration)
    return render_template('course_base.html', course_bases=course_bases)


@app.route('/course-base/edit/', methods=['GET', 'POST'])
@login_required
def course_base_edit():
    app.logger.info(request.form)
    form = CourseBaseForm(formdata=request.form)
    if form.validate_on_submit():
        return redirect(url_for('course_base_confirm'), code=307)
    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        course_base = CourseBase.query.get(id)
        form = CourseBaseForm(obj=course_base)
        form.distance.data = form.distance.data / 1000  # m->km
        form.method.data = 'PUT'
    else:
        form.method.data = 'POST'
    return render_template('course_base_edit.html', form=form)


@app.route('/course-base/confirm', methods=['POST'])
@login_required
def course_base_confirm():
    app.logger.info(request.form)
    form = CourseBaseForm(formdata=request.form)
    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('user'))
    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            course_base = CourseBase.query.get(form.id.data)
            db.session.delete(course_base)
            db.session.commit()
            flash('コース分類: "{} {} {}" の削除が完了しました'.format(
                course_base.type, course_base.distance/1000, course_base.duration), 'danger')
        elif request.form.get('method') == 'PUT':
            course_base = CourseBase.query.get(form.id.data)
            form.populate_obj(course_base)
            course_base.distance = course_base.distance * 1000  # km->m
            db.session.commit()
            flash('コース分類:"{} {} {}" の更新が完了しました'.format(
                course_base.type, course_base.distance/1000, course_base.duration), 'warning')
        elif request.form.get('method') == 'POST':
            course_base = CourseBase()
            form.populate_obj(course_base)
            course_base.id = None
            course_base.distance = course_base.distance * 1000  # km->m
            db.session.add(course_base)
            db.session.commit()
            flash('コース分類:"{} {} {}" の登録が完了しました'.format(
                course_base.type, course_base.distance/1000, course_base.duration), 'info')
        return redirect(url_for('course_base'))
    else:
        if request.form.get('method') == 'DELETE':
            course_base = CourseBase.query.get(form.id.data)
            form = CourseBaseForm(obj=course_base)
        return render_template('course_base_confirm.html', form=form)


@app.route('/course/edit/', methods=['GET', 'POST'])
@login_required
def course_edit():
    app.logger.info(request.form)
    form = CourseForm(formdata=request.form)
    if form.validate_on_submit():
        return redirect(url_for('course_confirm'), code=307)
    if request.args.get('method') == 'PUT':
        id = int(request.args.get('id'))
        course = Course.query.get(id)
        competition_name = course.competition.show_name
        form = CourseForm(obj=course)
        form.method.data = 'PUT'
    else:
        form.competition_id.data = request.args.get(
            'competition_id')  # 新規登録の場合もcompetiton_idは前もって受け取る。
        competition = Competition.query.get(form.competition_id.data)
        competition_name = competition.show_name
        form.method.data = 'POST'
    return render_template('course_edit.html', form=form, competition_name=competition_name)


@app.route('/course/confirm', methods=['POST'])
@login_required
def course_confirm():
    app.logger.info(request.form)
    form = CourseForm(formdata=request.form)
    if request.form.get('submit') == 'キャンセル':
        return redirect(url_for('user'))
    if form.validate_on_submit() and request.form.get('confirmed'):
        if request.form.get('method') == 'DELETE':
            course = Course.query.get(form.id.data)
            competition_name = course.competition.name
            db.session.delete(course)
            db.session.commit()
            flash('レース: "{}"・"{}" の削除が完了しました'.format(
                competition_name, course.name), 'danger')
        elif request.form.get('method') == 'PUT':
            course = Course.query.get(form.id.data)
            form.populate_obj(course)
            db.session.commit()
            flash('レース:"{}"・"{}" の更新が完了しました'.format(
                course.competition.name, course.name), 'warning')
        elif request.form.get('method') == 'POST':
            course = Course()
            form.populate_obj(course)
            course.id = None
            db.session.add(course)
            db.session.commit()
            flash('レース:"{}"・"{}" の登録が完了しました'.format(
                course.competition.name, course.name), 'info')
        return redirect(url_for('competition_individual', id=form.competition_id.data))
    else:
        if request.form.get('method') == 'DELETE':
            course = Course.query.get(form.id.data)
            form = CourseForm(obj=course)
        competition = Competition.query.get(form.competition_id.data)
        competition_name = competition.show_name
        return render_template('course_confirm.html', form=form, competition_name=competition_name)


@app.route('/result/')
def result():
    start = time.time()  # 実行時間測定用いずれ消す。
    list_type = request.args.get('list_type') or 'latest'
    year = request.args.get('year') or current_school_year
    type = request.args.get('type') or 'road'
    if list_type == "latest":
        results = db.session.query(Race, Competition).\
            join(Race.course).\
            join(Course.competition).\
            order_by(Race.date.desc()).\
            filter(Race.date > (date.today() - timedelta(days=400)))
    elif list_type == "year":
        year = int(year)
        results = db.session.query(Race, Competition).\
            join(Race.course).\
            join(Course.competition).\
            order_by(Race.date.desc()).\
            filter(Race.date >= date(year, 4, 1),
                   Race.date < date(year+1, 4, 1))
    key = {'date': lambda x: x.Race.date,
           'competition': lambda x: x.Competition}
    print("実行時間1：{}".format(time.time()-start))
    # startからここまで0.001秒ほど。（何回か繰り返したのでキャッシュが溜まっている可能性あり？）
    # htmlが生成されるまで0.06秒ほど。
    return render_template('result.html', results=results, current_school_year=current_school_year, groupby=groupby, key=key, list_type=list_type, type=type, year=year, time=time, start=start)


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


@app.route('/manage/')
@login_required
def manage():
    return render_template('manage.html')
