
def war(func):
    def wrapper(*args, **kwargs):
        dc = {
            'args': args,
            'kwargs': kwargs,
        }
        print(dc)
        n2 = kwargs.get('n2')
        _init_dic = {
            'n2': n2,
            **kwargs
        }
        return func(*args, **_init_dic)
    return wrapper






@war
def get_n(n,n2=2,n3=3,*args,**kwargs):
    dc = {
        'n':n,
        'n2':n2,
        'n3':n3,
        'args':args,
        'kwargs':kwargs,
    }
    print(dc)
    if n2==2:
        print('n2:2')





get_n(1,n3=2,n4=7)