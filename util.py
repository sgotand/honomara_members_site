from flask import render_template as flask_render_template
from datetime import date, datetime
from locale import setlocale, LC_TIME
from honomara_members_site import app, db


try:
    setlocale(LC_TIME, 'ja_JP.UTF-8')  # for get_wday
except Exception as e:
    pass


def render(template, **args):
    args['template'] = template
    return flask_render_template('flame.html', **args)


def year_to_grade(year, current_school_year):
    return current_school_year + 1 - year


def get_school_year(date):
    if date.month < 4:
        return date.year - 1
    else:
        return date.year


def str_to_date(str):
    return datetime.strptime(str, '%Y-%m-%d').date()


def get_wday(date):
    return date.strftime('%a')


def validate_course_and_set_name(form=None):
    if form is None:
        msg = 'generate_course_name needs form'
        app.logger.warning(msg)
        return msg

    if form.type.data in ['road', 'track', 'trail']:
        if form.distance.data is None or form.distance.data <= 0:
            msg = 'type {} need distance'.format(form.type.data)
            app.logger.warning(msg)
            return msg
        elif form.type.data == 'road':
            if form.distance.data == 42.195:
                form.show_name.data = 'フルマラソン'
            elif form.distance.data == 42.195/2:
                form.show_name.data = 'ハーフマラソン'
            elif form.show_name.data is None:
                form.show_name.data = '{:f}km'.format(form.distance.data)
        elif form.type.data == 'track':
            if form.show_name.data is None:
                form.show_name.data = '{:f}m走'.format(
                    int(form.distance.data*1000))
        elif form.type.trail == 'trail':
            if form.show_name.data is None:
                form.show_name.data = '{:f}kmコース'.format(form.distance.data)

    elif form.type.data in ['time', 'relay']:
        if form.time.data is None or form.time.data <= 0:
            msg = 'type {} need time'.format(form.type.data)
            app.logger.warning(msg)
            return msg
        if form.type.data == 'time':
            form.show_name.data = '{:f}時間走'.format(
                form.time.data / 3600 // 1000)
        if form.type.data == 'relay':
            form.show_name.data = '{:f}時間リレー'.format(
                form.time.data / 3600 // 1000)
    else:  # other
        if form.show_name.data is None:
            form.show_name.data = '{}km, {}時間'.format(
                form.distance.data, form.time.data / 3600 / 1000)
            # generate_course_name(None)
    return None


def form_set_time(form=None):
    if form is None:
        return
    elif form.time.data is None:
        form.time_h.data = form.time_h.data or 0
        form.time_m.data = form.time_m.data or 0
        form.time_s.data = form.time_s.data or 0
        form.time_ms.data = form.time_ms.data or 0
        form.time.data = ((form.time_h.data * 60 + form.time_m.data)
                          * 60 + form.time_s.data) * 1000 + form.time_ms.data
    else:
        tmp = form.time.data
        form.time_ms.data, tmp = tmp % 1000, tmp//1000
        form.time_s.data, tmp = tmp % 60, tmp//60
        form.time_m.data, tmp = tmp % 60, tmp//60
        form.time_h.data = tmp


current_school_year = get_school_year(date.today())
