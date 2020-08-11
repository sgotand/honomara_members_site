from honomara_members_site import db


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

#     results = db.relationship('Result') # created by backref

    def __repr__(self):
        fields = {}
        fields['id'] = self.id
        fields['family_name'] = self.family_name
        fields['first_name'] = self.first_name
        fields['show_name'] = self.show_name
        fields['year'] = self.year
        fields['sex'] = self.sex

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
    type = db.Column(db.String(30), nullable=False)
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
        #         return "<After(id:{}, {:%Y-%m-%d}, title:'{}')>".format(self.id, self.date, self.title)
        tmp = 'id:{}'.format(self.id)
        if self.date:
            tmp += ', {:%Y-%m-%d}'.format(self.date)
        tmp += ', {}次会'.format(self.after_stage)
        tmp += ', {}'.format(self.title)

        return "<After({})>".format(tmp)


class Competition(db.Model):
    __tablename__ = 'competition'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    kana = db.Column(db.String(60))
    show_name = db.Column(db.String(30))
    place = db.Column(db.String(30))
    comment = db.Column(db.Text)
    courses = db.relationship("Course")

    def __repr__(self):
        return "<Competition(id:{}, name:{}, place:{}, comment:'{}')>".format(self.id, self.name, self.place, self.comment)


class Course(db.Model):
    __tablename__ = 'course'

    id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'))
    competition = db.relationship('Competition')
    type = db.Column(db.String(30))
    show_name = db.Column(db.String(30))
    time = db.Column(db.Integer)
    distance = db.Column(db.Float)
    elevation = db.Column(db.Integer)
    comment = db.Column(db.Text)

    races = db.relationship("Race")

    def __repr__(self):
        return "<Course(id:{}, 大会:{}, 距離:{}km)>".format(self.id, self.competition.name, self.distance)


class Race(db.Model):
    __tablename__ = 'race'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    course = db.relationship('Course')
    date = db.Column(db.Date, nullable=False)
#     results = db.relationship('Result',
#                               backref="race",
#                               order_by='Result.time'
#                               )
    results = db.relationship('Result')
    comment = db.Column(db.Text)

    def __repr__(self):
        return "<Race(id:{}, {}, date {:%Y-%m-%d})>".format(self.id, self.course, self.date)


class RaceParticipant(db.Model):
    __tablename__ = 'race_participant'

    member_id = db.Column(db.Integer, db.ForeignKey(
        'member.id'), primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey(
        'result.id'), primary_key=True)

    def __repr__(self):
        return "<RaceParticipant(result_id:{}, member_id:{})>".format(self.result_id, self.member_id)


class Result(db.Model):
    __tablename__ = 'result'

    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))
    race = db.relationship('Race')
    time = db.Column(db.Integer)
    distance = db.Column(db.Float)
    comment = db.Column(db.Text)

    participants = db.relationship(
        'Member',
        secondary=RaceParticipant.__tablename__,
        order_by='Member.year, Member.family_kana, Member.first_kana'
    )

    def __init__(self, form=None, **args):
        return super().__init__(**args)

    def __repr__(self):
        return "<Result(id:{}, race_id:{}, time:{}, distance:{}, participants:{})>".\
            format(self.id, self.race_id, self.time,
                   self.distance, self.participants)
