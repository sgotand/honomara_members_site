from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, FloatField, IntegerField
from wtforms import HiddenField, TextAreaField, DateField, SelectMultipleField, SelectField
from wtforms.validators import Optional, InputRequired
from honomara_members_site.model import Member, Restaurant, Competition, Race
from honomara_members_site.util import current_school_year, data_collection


visible_member_list_for_form = [(m.id, m.show_name)
                                for m in Member.query.filter_by(visible=True).
                                filter(Member.year <= current_school_year).
                                order_by(Member.year.desc()).all()]

training_place_list = [('代々木公園', '代々木公園'), ('皇居', '皇居'), ('山手線企画',
                                                          '山手線企画'), ('箱根企画', '箱根企画'), ('距離練', '距離練'), ('その他', 'その他')]
weather_list = [('晴れ', '晴れ'), ('曇り', '曇り'), ('雨', '雨'),
                ('強風', '強風'), ('雪', '雪'), ('その他', 'その他')]

restaurants_choices = [(r.id, "{}({})".format(
    r.name, r.place)) for r in Restaurant.query.order_by(Restaurant.score.desc()).all()]

competition_list_for_form = [(c.id, c.show_name)
                             for c in Competition.query.all()]
race_list_for_form = [(r.id, "{}({})".format(
    r.show_name, r.competition.show_name)) for r in Race.query.all()]


class MemberForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    year = SelectField('入学年度:', coerce=int, validators=[InputRequired()],
                       choices=[(i, i) for i in range(current_school_year, 1990, -1)])
    family_name = StringField('姓:', validators=[InputRequired()])
    family_kana = StringField('カナ(姓):', validators=[InputRequired()])
    first_name = StringField('名:', validators=[InputRequired()])
    first_kana = StringField('カナ(名):', validators=[InputRequired()])
    show_name = StringField('表示名:', validators=[InputRequired()])
    sex = RadioField('性別:', default=0, coerce=int,
                     choices=[(0, '男'), (1, '女')])
    visible = RadioField('状態:', coerce=bool, choices=[
                         (True, '表示'), (False, '非表示')],
                         validators=[InputRequired()])
    method = HiddenField(validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    submit = SubmitField('確定')


class TrainingForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    date = DateField('練習日:', validators=[InputRequired()])
    place = SelectField('練習場所:', coerce=str,  validators=[
                        InputRequired()], choices=training_place_list)
    weather = SelectField('天気:', validators=[Optional()], choices=weather_list)
    participants = SelectMultipleField('参加者:', coerce=int, validators=[InputRequired()],
                                       choices=visible_member_list_for_form)
    title = StringField('タイトル:', validators=[InputRequired()])
    comment = TextAreaField('コメント:', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class AfterForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    date = DateField('日付:', validators=[InputRequired()])
    after_stage = SelectField('何次会:', coerce=int, default=1, choices=[
                              (i, i) for i in range(0, 10)], validators=[InputRequired()])
    restaurant = SelectField('店:', coerce=int, validators=[InputRequired()],
                             choices=restaurants_choices)
    participants = SelectMultipleField('参加者:', coerce=int, validators=[InputRequired()],
                                       choices=visible_member_list_for_form
                                       )
    title = StringField('タイトル:', validators=[InputRequired()])
    comment = TextAreaField('コメント:', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class CompetitionForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    name = StringField('大会名(正式名称):', validators=[InputRequired()])
    name_kana = StringField('大会名(カナ):', validators=[InputRequired()])
    show_name = StringField('大会名(表示名):', validators=[InputRequired()])
    place = SelectField('開催地:', coerce=int, validators=[InputRequired()],
                        choices=data_collection['place'])
    url = TextAreaField('URL:', validators=[Optional()])
    comment = TextAreaField('備考:', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class RaceForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    competition_id = HiddenField(validators=[Optional()])
    show_name = StringField('表示名:', validators=[InputRequired()])
    type = SelectField('分類:', coerce=int, validators=[InputRequired()],
                       choices=data_collection['type'])
    distance = FloatField('距離(km):', validators=[Optional()], default=0)
    dulation = FloatField('制限時間(h):', validators=[Optional()], default=0)
    cumulative_elevation = FloatField(
        '累積標高(m):', validators=[Optional()], default=0)
    comment = TextAreaField('コメント:', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class ResultForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    date = DateField('日付:', validators=[InputRequired()])
    member_id = SelectField('参加者:', coerce=int, validators=[InputRequired()],
                            choices=visible_member_list_for_form)
    competition_id = SelectField('大会:', coerce=int, validators=[InputRequired()],
                                 choices=competition_list_for_form)
    race_id = SelectField('種目:', coerce=int, validators=[InputRequired()],
                          choices=race_list_for_form)
    record = HiddenField('記録', validators=[Optional()])
    record_h = IntegerField('記録(時間)', validators=[InputRequired()], default=0)
    record_m = IntegerField('記録(分)', validators=[InputRequired()], default=0)
    record_s = IntegerField('記録(秒)', validators=[InputRequired()], default=0)
    comment = TextAreaField('備考:', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])
