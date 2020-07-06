from honomara_members_site import db
from geoalchemy2 import Geometry


class Member(db.Model):
    __tablename__ = 'member'

    id = db.Column(db.Integer, primary_key=True)
    family_name = db.Column(db.String(30), nullable=False)
    first_name = db.Column(db.String(30), nullable=False)
    show_name = db.Column(db.String(30), nullable=False)
    # kana = db.Column(db.String(60), nullable=False)
    family_kana = db.Column(db.String(30), nullable=True)
    first_kana = db.Column(db.String(30), nullable=True)
    year = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    visible = db.Column(db.Boolean, nullable=False)

    results = db.relationship(
        'Result',
        backref='member',
        order_by='Result.time, Result.distance'
    )

    def __init__(self, form=None, **args):
        return super().__init__(**args)

    def __repr__(self):
        fields = {}
        fields['id'] = self.id
        fields['family_name'] = self.family_name
        fields['first_name'] = self.first_name
        fields['show_name'] = self.show_name
        fields['year'] = self.year
        if self.sex == 0:
            fields['sex'] = 'male'
        elif self.sex == 1:
            fields['sex'] = 'female'
        else:
            fields['sex'] = 'unknown or other'
        fields['visible'] = self.visible
        return "<Member('{id}','{family_name}', '{first_name}', '{show_name}', {year}, {sex}, {visible})>".format(**fields)


class TrainingParticipant(db.Model):
    __tablename__ = 'training_participant'

    member_id = db.Column(db.Integer, db.ForeignKey(
        'member.id'), primary_key=True)
    training_id = db.Column(db.Integer, db.ForeignKey(
        'training.id'), primary_key=True)

    def __repr__(self):
        return "<TrainingParticipant(training_id:{}, member_id:{})>".\
            format(self.training_id, self.member_id)


class Training(db.Model):
    __tablename__ = 'training'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    place = db.Column(db.String(30), nullable=False)
    weather = db.Column(db.String(30), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    comment = db.Column(db.Text)

    participants = db.relationship(
        'Member',
        secondary=TrainingParticipant.__tablename__,
        order_by='Member.year, Member.family_kana, Member.first_kana'
    )

    def __init__(self, form=None, **args):
        return super().__init__(**args)

    def __repr__(self):
        return "<Training(id:{}, {:%Y-%m-%d}, place:{}, title:'{}')>"\
            .format(self.id, self.date, self.place, self.title)


class AfterParticipant(db.Model):
    __tablename__ = 'after_participant'

    member_id = db.Column(db.Integer, db.ForeignKey(
        'member.id'), primary_key=True)
    after_id = db.Column(db.Integer, db.ForeignKey(
        'after.id'), primary_key=True)

    def __repr__(self):
        return "<AfterParticipant(after_id:{}, member_id:{})>".\
            format(self.after_id, self.member_id)


class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    place = db.Column(db.String(20))
    score = db.Column(db.Float, server_default=db.text('0'))
    comment = db.Column(db.Text)

    def __repr__(self):
        return "<Restaurant(id:{}, name:{}, plase:{})>".\
            format(self.id, self.name, self.place)


class After(db.Model):
    __tablename__ = 'after'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    after_stage = db.Column(db.Integer, nullable=False,
                            server_default=db.text('1'))
    restaurant_id = db.Column(db.Integer, db.ForeignKey(
        'restaurant.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    comment = db.Column(db.Text)
    restaurant = db.relationship('Restaurant')

    participants = db.relationship(
        'Member',
        secondary=AfterParticipant.__tablename__,
        order_by='Member.year, Member.family_kana, Member.first_kana'
    )

    def __init__(self, form=None, **args):
        return super().__init__(**args)

    def __repr__(self):
        return "<After(id:{}, {:%Y-%m-%d}, title:'{}')>".\
            format(self.id, self.date, self.title)


class Competition(db.Model):
    __tablename__ = 'competition'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_kana = db.Column(db.String(100))
    show_name = db.Column(db.String(100))
    location = db.Column(db.String(30))
    url = db.Column(db.Text)
    comment = db.Column(db.Text)

    courses = db.relationship(
        'Course',
        backref="competition",
        order_by='Course.course_base_id'
    )

    def __init__(self, form=None, **args):
        return super().__init__(**args)

    def __repr__(self):  # location書けていない
        return "<competition(id:{}, name:{}, name_kana:{}, show_name:{}, url:{}, comment:{}, courses:{})>".\
            format(self.id, self.name, self.name_kana, self.show_name,
                   self.url, self.comment, len(self.courses))


class CourseBase(db.Model):
    __tablename__ = 'course_base'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(30), nullable=False)
    distance = db.Column(db.Integer)
    duration = db.Column(db.Integer)
    comment = db.Column(db.Text)

    courses = db.relationship(
        'Course',
        backref='course_base',
        order_by='Course.competition_id'
    )

    def __init__(self, form=None, **args):
        return super().__init__(**args)

    def __repr__(self):
        return "<course_base(id:{}, type:{}, distance:{}, dulation:{}, comment:{}, coueses:{})>".\
            format(self.id, self.type, self.distance,
                   self.dulation, self.comment, len(self.courses))


class Course(db.Model):
    __tablename__ = 'course'

    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(
        db.Integer, db.ForeignKey('competition.id'))
    # competition by backref
    course_base_id = db.Column(
        db.Integer, db.ForeignKey('course_base.id'))
    # course_base by backref
    name = db.Column(db.String(60))
    cumulative_elevation = db.Column(db.Integer)
    comment = db.Column(db.Text)

    races = db.relationship(
        'Race',
        backref='course',
        order_by='Race.date'
    )

    def __init__(self, form=None, **args):
        return super().__init__(**args)

    def __repr__(self):
        return "<course(id:{}, competition:{}, course_base_id:{}, name:{}, cumulative_elevation:{}, comment:{})>".\
            format(self.id, self.competition.name, self.course_base_id,
                   self.name, self.cumulative_elevation, self.comment)


class Race(db.Model):
    __tablename__ = 'race'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(
        db.Integer, db.ForeignKey('course.id'))
    # course by backref
    date = db.Column(db.Date, nullable=False)
    comment = db.Column(db.Text)

    results = db.relationship(
        'Result',
        backref='race',
        order_by='Result.time, Result.distance'
    )

    def __init__(self, form=None, **args):
        return super().__init__(**args)

    def __repr__(self):
        return "<race(id:{}, course:{}, date:{}, {:%Y-%m-%d}, comment:{})>".\
            format(self.id, self.course.name, self.date, self.comment)


class Result(db.Model):
    __tablename__ = 'result'

    member_id = db.Column(
        db.Integer, db.ForeignKey('member.id'), primary_key=True)
    # member by backref
    race_id = db.Column(
        db.Integer, db.ForeignKey('race.id'), primary_key=True)
    # race by backref
    time = db.Column(db.Integer)
    distance = db.Column(db.Integer)
    comment = db.Column(db.Text)

    def __init__(self, form=None, **args):
        return super().__init__(**args)

    def __repr__(self):
        return "<result(id:{}, member:{}, race_id:{}, time:{}, distance:{}, comment:{})>".\
            format(self.id, self.member.show_name, self.race_id,
                   self.time, self.distance, self.comment)
