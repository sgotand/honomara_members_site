from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, FloatField
from wtforms import HiddenField, TextAreaField, SelectMultipleField, SelectField
from wtforms.fields.html5 import IntegerField, DateField
from wtforms.validators import Optional, InputRequired
from honomara_members_site.model import *
from honomara_members_site.util import current_school_year


visible_member_list_for_form = [(m.id, m.show_name)
                                for m in Member.query.filter_by(visible=True).
                                filter(Member.year <= current_school_year).
                                order_by(Member.year.desc()).all()]

visible_member_list_for_form_1 = [(m.id, m.show_name)
                                  for m in Member.query.filter_by(visible=True).
                                  filter(Member.year == current_school_year).
                                  order_by(Member.family_kana).all()]

visible_member_list_for_form_2 = [(m.id, m.show_name)
                                  for m in Member.query.filter_by(visible=True).
                                  filter(Member.year == current_school_year-1).
                                  order_by(Member.family_kana).all()]

visible_member_list_for_form_3 = [(m.id, m.show_name)
                                  for m in Member.query.filter_by(visible=True).
                                  filter(Member.year == current_school_year-2).
                                  order_by(Member.family_kana).all()]

visible_member_list_for_form_4 = [(m.id, m.show_name)
                                  for m in Member.query.filter_by(visible=True).
                                  filter(Member.year == current_school_year-3).
                                  order_by(Member.family_kana).all()]

visible_member_list_for_form_5 = [(m.id, m.show_name)
                                  for m in Member.query.filter_by(visible=True).
                                  filter(Member.year <= current_school_year-4).
                                  order_by(Member.year.desc(), Member.family_kana).all()]

training_place_list = [('代々木公園', '代々木公園'), ('皇居', '皇居'), ('山手線企画',
                                                          '山手線企画'), ('箱根企画', '箱根企画'), ('距離練', '距離練'), ('その他', 'その他')]
weather_list = [('晴れ', '晴れ'), ('曇り', '曇り'), ('雨', '雨'),
                ('強風', '強風'), ('雪', '雪'), ('その他', 'その他')]


class MemberForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    year = SelectField('入学年度:', coerce=int, validators=[InputRequired()],
                       choices=[(i, i) for i in range(current_school_year, 1990, -1)])
    family_name = StringField('姓:')
    family_kana = StringField('カナ(姓):')
    first_name = StringField('名:')
    first_kana = StringField('カナ(名):')
    show_name = StringField('表示名:', validators=[InputRequired()])
    sex = RadioField('性別:', default='male', choices=[
                     ('male', '男'), ('female', '女')])
    visible = RadioField('状態:', coerce=bool, choices=[
                         (True, '表示'), (False, '非表示')],
                         validators=[InputRequired()])
    method = HiddenField(validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    submit = SubmitField('確定')


class TrainingForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    date = DateField('練習日:', validators=[InputRequired()])
    type = SelectField('練習場所等:', coerce=str,  validators=[
        InputRequired()], choices=training_place_list)
    weather = SelectField('天気:', validators=[Optional()], choices=weather_list)
    participants1 = SelectMultipleField('1年生', coerce=int,
                                        choices=visible_member_list_for_form_1
                                        )
    participants2 = SelectMultipleField('2年生', coerce=int,
                                        choices=visible_member_list_for_form_2
                                        )
    participants3 = SelectMultipleField('3年生', coerce=int,
                                        choices=visible_member_list_for_form_3
                                        )
    participants4 = SelectMultipleField('4年生', coerce=int,
                                        choices=visible_member_list_for_form_4
                                        )
    participants = SelectMultipleField('5年生以上', coerce=int,
                                       choices=visible_member_list_for_form_5
                                       )
    title = StringField('タイトル:', validators=[InputRequired()])
    comment = TextAreaField('コメント:', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class AfterForm(FlaskForm):
    restaurants_choices = [(r.id, "{}({})".format(
        r.name, r.place)) for r in Restaurant.query.order_by(Restaurant.score.desc()).all()]

    id = HiddenField(validators=[Optional()])
    date = DateField('日付:', validators=[InputRequired()])
    after_stage = SelectField('何次会:', coerce=int, default=1, choices=[
                              (i, i) for i in range(0, 10)], validators=[InputRequired()])
    restaurant = SelectField('店:', coerce=int, validators=[InputRequired()],
                             choices=restaurants_choices)
    participants1 = SelectMultipleField('1年生', coerce=int,
                                        choices=visible_member_list_for_form_1
                                        )
    participants2 = SelectMultipleField('2年生', coerce=int,
                                        choices=visible_member_list_for_form_2
                                        )
    participants3 = SelectMultipleField('3年生', coerce=int,
                                        choices=visible_member_list_for_form_3
                                        )
    participants4 = SelectMultipleField('4年生', coerce=int,
                                        choices=visible_member_list_for_form_4
                                        )
    participants = SelectMultipleField('5年生以上', coerce=int,
                                       choices=visible_member_list_for_form_5
                                       )
    title = StringField('タイトル:', validators=[InputRequired()])
    comment = TextAreaField('コメント:', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class CompetitionForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    name = StringField('大会名:', validators=[InputRequired()])
    kana = StringField('大会名(カナ):',  validators=[Optional()])
    show_name = StringField('表示名:',  validators=[Optional()])
    place = StringField('場所(県名、地域名等):', validators=[Optional()])
    comment = TextAreaField('コメント:', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class CourseForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    competition_id = IntegerField(validators=[InputRequired()])
    type = SelectField('競技種類', validators=[InputRequired()], choices=[
        ('road', 'ロード'), ('track', 'トラック競技'), ('trail', 'トレイル'), ('time', '時間走'), ('relay', 'リレーマラソン'), ('other', 'その他')]
    )
    show_name = StringField('表示名(オプション:ファンラン、ロング等)',  validators=[Optional()])
    distance = FloatField('距離(km単位)', validators=[Optional()], default=None)
    time = IntegerField('競技時間((時間単位))', validators=[Optional()], default=None)
    elevation = FloatField('累積標高(m単位)', validators=[Optional()], default=0)
    comment = TextAreaField('コメント(制限時間、感想等):', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class RaceForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    course_id = IntegerField(validators=[InputRequired()])
    date = DateField('大会日程:', validators=[])
    comment = TextAreaField('コメント:', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class ResultAllForm(FlaskForm):
    id = HiddenField(validators=[Optional()])  # for result table
    competition_id = SelectField('大会:', coerce=int, validators=[
        InputRequired()], default=None)
    course_id = SelectField('コース:', coerce=int, validators=[
        InputRequired()], default=None)
    date = DateField('大会日程:', validators=[])
    race_id = IntegerField(validators=[InputRequired()], default=None)
    participants = SelectMultipleField('参加者:', coerce=int, validators=[InputRequired()],
                                       choices=visible_member_list_for_form)
    distance = FloatField('記録(距離km)', validators=[Optional()], default=0)
    time = IntegerField('記録(時間)', validators=[Optional()], default=None)
    time_h = SelectField('記録(時間)', validators=[Optional()], default=0, coerce=int, choices=[
        (i, i) for i in range(100)
    ])
    time_m = SelectField('記録(分)', validators=[Optional()], default=0, coerce=int, choices=[
        (i, i) for i in range(60)])
    time_s = SelectField('記録(秒)', validators=[Optional()], default=0, coerce=int, choices=[
        (i, i) for i in range(60)])
    time_ms = IntegerField('記録(ミリ秒)', validators=[Optional()], default=0)
    comment = TextAreaField(
        '備考:', validators=[Optional()])  # comment for result
    confirmed = HiddenField(validators=[Optional()], default='False')
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class ResultForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    race_id = IntegerField(validators=[InputRequired()])
    participants = SelectMultipleField('参加者:', coerce=int, validators=[InputRequired()],
                                       choices=visible_member_list_for_form)
    distance = FloatField('記録(距離km)', validators=[Optional()], default=0)
    time = IntegerField('記録(時間)', validators=[Optional()], default=0)
    comment = TextAreaField(
        '備考:', validators=[Optional()])  # comment for result
    confirmed = HiddenField(validators=[Optional()], default='False')
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])


class RestaurantForm(FlaskForm):
    id = HiddenField(validators=[Optional()])
    name = StringField('店名:', validators=[InputRequired()])
    place = StringField('場所:', validators=[InputRequired()])
    score = FloatField('スコア:', validators=[InputRequired()])
    comment = TextAreaField('コメント:', validators=[Optional()])
    confirmed = HiddenField(validators=[Optional()])
    method = HiddenField(validators=[Optional()])
    submit = SubmitField('確定', validators=[Optional()])
