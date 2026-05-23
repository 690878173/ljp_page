from ljp_page.exceptions import Yes


def t1():

    try:
        s = 1 / 0
    except Exception as e:
        raise Yes('计算出错') from e

def t2():

    try:
        t1()
    except Exception as e:
        raise Yes('t1错误') from e


try:
    t2()
except Exception as e:
    print(e)

