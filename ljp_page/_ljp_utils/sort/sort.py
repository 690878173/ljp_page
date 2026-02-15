from bisect import bisect_left

def ef_search(ls, x, sort=False):
    """二分查找算法

    :param ls: 列表。
    :param x: 被查找的数。
    :param sort: 是否要启动排序，False表示不启动排序，默认是不启动。
    :return: 找到返回True，反之亦然
    """
    if sort:
        ls = sorted(ls)
    v = bisect_left(ls, x)
    if v != len(ls) and ls[v] == x:
        return True
    return False




def mp_sort(ls):
    """冒泡算法

    # >>> import random
    # >>> import time
    # >>> s = []
    # >>> for _ in range(100):
    #         jr = random.randint(0, 1000)
    #         s.append(jr)
    # >>> start = time.time()
    # >>> bs = bubbled_sort(s)
    # >>> print(bs)
    # >>> print(time.time() - start)
    """
    length = len(ls)
    flag = True  # 判断是否要进行数据交换，True表示要进行
    k = length - 1  # 表示已经排序好的上界值,默认是列表的长度
    last = 0  # 记住上一次循环交换的位置。默认是开头
    for i in range(length):
        if not flag:
            break
        flag = False  # 每次循环都默认为不进行数据交换
        for j in range(k):
            if ls[j] > ls[j + 1]:
                ls[j], ls[j + 1] = ls[j + 1], ls[j]
                flag = True  # 要交换数据
                last = j  # 交换数据的位置
        k = last
    return ls