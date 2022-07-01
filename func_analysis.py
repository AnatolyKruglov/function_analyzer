from sympy import Symbol, S, Union, Interval, pretty, oo, is_decreasing, is_increasing, solveset, Eq, exp, log, sin, cos, tan
from sympy.calculus.util import continuous_domain, function_range
from sympy.utilities.lambdify import lambdify
from sympy.parsing.sympy_parser import parse_expr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')
import seaborn as sns
import numpy as np
import telebot
import os
import shutil
import re

bot = telebot.TeleBot('5524493984:AAGw7g17hyGiCMIVYT6ui45-CzbUAtz3KtY')

x = Symbol("x")


def analyze(step, f, x, id, **kwargs):
    step = step.lower().replace('функции','').strip()
    step = step[0].upper() + step[1:]
    if step in ('Промежутки монотонности', 'Монотонность'):
        analyze('Промежутки убывания', f, x, id, **kwargs)
        return analyze('Промежутки возрастания', f, x, id, **kwargs)
    elif step == 'Область определения':
        return analyze('Промежутки возрастания', f, x, id, **kwargs)
    elif step == 'Область значений':
        return analyze('Промежутки возрастания', f, x, id, **kwargs)

    loc = (int(f==f.subs(x,-x)),int(-f==f.subs(x,-x)))
    symmetry = np.array([
        ['общ. вида', 'нечетная'],
        ['четная', None]
    ])[loc]
    steps = {
        'Df':continuous_domain(f, x, S.Reals),
        'Ef':function_range(f, x, S.Reals),
        'Четность':symmetry,
        'Нули':solveset(Eq(f, 0), x),
        'Производная':f.diff(x),
        'Экстремумы':solveset(Eq(f.diff(x), 0), x)
    }
    points = (Interval.open(-oo,oo) - (steps['Экстремумы']^steps['Df'])) & steps['Df']
    a = [-oo, *list(points), oo]
    a = list(Interval.open(*x) for x in zip(a[:-1], a[1:]))
    dec, inc = [], []
    for interval in a:
        if is_decreasing(f, interval):
            dec.append(interval)
        elif is_increasing(f, interval):
            inc.append(interval)
    steps['Промежутки убывания'] = Union(*dec, steps['Экстремумы']) if dec else None
    steps['Промежутки возрастания'] = Union(*inc, steps['Экстремумы']) if inc else None

    # steps['Асимптоты'] = 

    if step in steps:
        printed = pretty(steps[step])
        if "\n" in printed:
            bot.send_message(id, f"{step}: " + str(steps[step]))
        else:
            bot.send_message(id, f"{step}: " + printed)
    else:
        bot.send_message(id, 'Не понял вас( опечатка?')

def graph(f, x, id, graph_start=-10, graph_end=10, graph_density=100, graph_derivatives=False, **kwargs):
    xs = list(filter(lambda n: n in continuous_domain(f, x, S.Reals), list(np.linspace(graph_start, graph_end, graph_density))))
    g = lambdify(x, f)
    ys = [g(n) for n in xs]

    os.makedirs(os.getcwd() + f"\\function_analyzer\\images\\{id}", 0o777)

    path = os.getcwd() + f"\\function_analyzer\\images\\{id}\\fig.png"
    fig = sns.scatterplot(x=xs, y=ys).get_figure()
    fig.savefig(path)
    plt.clf()
    bot.send_photo(id, open(path, 'rb'))

    if graph_derivatives:
        for der in graph_derivatives:
            h = lambdify(x, f.diff(x, der))
            d_xs, d_ys = [], []
            for n in xs:
                h_val = h(n)
                if abs(h_val) < 25:
                    d_xs.append(n)
                    d_ys.append(h_val)
            path = os.getcwd() + f"\\function_analyzer\\images\\{id}\\fig{der}.png"
            fig = sns.scatterplot(x=xs, y=ys).get_figure()
            fig.savefig(path)
            plt.clf()
            bot.send_photo(id, open(path, 'rb'))

    shutil.rmtree(os.getcwd() + f"\\function_analyzer\\images\\{id}")

def full_analysis(f, x, id, **kwargs):
    for step in ('Df','Ef','Нули','Четность','Производная','Экстремумы','Промежутки монотонности','Асимптоты'):
        analyze(step, f, x, id, **kwargs)
    graph(f, x, id, graph_derivatives=(1), **kwargs)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message,
        "Просто отправьте функцию, которую нужно исследовать, в любом формате\n\n"
        "Сейчас поддерживаю\n"
        "● полиномы: x^2, x**3, 1/x + x ...\n"
        "● логарифмы: ln(x), log(x), log(x, 10) ...\n"
        "● показательные: exp(x), 3**x, e^x ...\n"
        "● их композиции\n"
    )

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    try:
        sp = message.text.split(',')
        expr = sp[0].split('=')[-1]\
            .replace('^','**')\
            .replace('e**x','exp(x)')\
            .replace('e^x','exp(x)')\
            .replace('ln(x)','log(x)')
        expr = re.sub(r'([0-9]+)x', r'\1*x', expr)
        f = parse_expr(expr)

        if len(sp) > 1:
            options = [opt.lower().strip() for opt in sp[1:]]
            if 'асимптоты' in options:
                pass
            elif 'график производных' in options:
                pass

        full_analysis(f, x, message.from_user.id)
    except Exception as e:
        bot.send_message(message.from_user.id, str(e))

bot.infinity_polling()
