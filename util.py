from flask import render_template as flask_render_template
from datetime import date, datetime
from locale import setlocale, LC_TIME


setlocale(LC_TIME, 'ja_JP.UTF-8')  # for get_wday


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


current_school_year = get_school_year(date.today())

place = [(1, '北海道'), (2, '青森県'), (3, '岩手県'), (4, '宮城県'), (5, '秋田県'), (6, '山形県'), (7, '福島県'),
            (8, '茨城県'), (9, '栃木県'), (10, '群馬県'), (11, '埼玉県'), (12, '千葉県'), (13, '東京都'),(14, '神奈川県'),
            (15, '新潟県'),(16, '富山県'), (17, '石川県'), (18, '福井県'), (19, '山梨県'), (20, '長野県'), (21, '岐阜県'), (22, '静岡県'), (23, '愛知県'),
            (24, '三重県'), (25, '滋賀県'), (26, '京都府'), (27, '大阪府'), (28, '兵庫県'), (29, '奈良県'), (30, '和歌山県'),
            (31, '鳥取県'), (32, '島根県'),(33, '岡山県'), (34, '広島県'), (35, '山口県'),
            (36, '徳島県'), (37, '香川県'), (38, '愛媛県'), (39, '高知県'),
            (40, '福岡県'), (41, '佐賀県'), (42, '長崎県'), (43, '熊本県'), (44, '大分県'), (45, '宮崎県'), (46, '鹿児島県'), (47, '沖縄県'),
            (48, '国外'), (-1, 'その他')]

type = [(0, 'Road'), (1, 'Trail'), (2, 'Track'), (3, 'Time', (-1, 'Others'))]

choice = {'place': place, 'type': type}