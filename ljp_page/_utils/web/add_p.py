def add_p(txt):
    ls = txt.split('\n')
    l2 = []
    for i in ls:
        l2.append(f'<p>{i}</p>')

    return "".join(l2)

def add_br(txt):
    # 先保护字符串里的 \n：替换成临时标记
    txt = txt.replace('"\n', '"PROTECTED_N')
    txt = txt.replace('\n"', 'PROTECTED_N"')

    # 只替换真正的换行 → <br>
    txt = txt.replace('\n', '<br>')

    # 恢复被保护的 \n
    txt = txt.replace('"PROTECTED_N', '"\\n')
    txt = txt.replace('PROTECTED_N"', '\\n"')

    return f"<p>{txt}</p>"


__all__ = ["add_p", "add_br"]
