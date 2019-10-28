from honomara_members_site import app
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy(app)


class Member(db.Model):
    __tablename__ = 'members'

    member_id = db.Column(db.Integer, primary_key=True)
    family_name = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    show_name = db.Column(db.String(20), nullable=False)
    kana = db.Column(db.String(40), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    visible = db.Column(db.Boolean, nullable=False)

    def __init__(self, form=None, **args):
        if form is not None:
            args = {}
            if form.get('member_id') != '':
                args['member_id'] = int(form.get('member_id'))
            else:
                args['member_id'] = None

            args['family_name'] = form.get('family_name')
            args['first_name'] = form.get('first_name')

            if form.get('show_name') != '':
                args['show_name'] = form.get('show_name')
            else:
                args['show_name'] = args['family_name']
            args['kana'] = form.get('kana')
            args['year'] = int(form.get('year'))
            args['sex'] = int(form.get('sex'))
            args['visible'] = bool(form.get('visible'))
        return super().__init__(**args)

    def __repr__(self):
        fields = {}
        fields['member_id'] = self.member_id
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
        return "<Member('{member_id}','{family_name}', '{first_name}', '{show_name}', {year}, {sex}, {visible})>".format(**fields)
