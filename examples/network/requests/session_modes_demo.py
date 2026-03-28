import asyncio
from ljp_page.modules.request import Requests


def _mode_1_simple_requests():
    """模式1：简单请求模式 - 直接使用请求器"""
    print("\n" + "="*50)
    print("模式1：简单请求模式")
    print("="*50)

    req = Requests()

    # 每次请求自动管理session
    response = req.get("https://www.baidu.com")
    print(f"请求1成功，响应长度: {len(response)} 字符")

    response = req.get("https://www.baidu.com")
    print(f"请求2成功，响应长度: {len(response)} 字符")

    print("\n模式1优点：")
    print("- 使用简单，一个对象搞定所有请求")
    print("- 自动管理session生命周期")
    print("- 适合单次或少量请求")


async def est_mode_2_session_wrapper():
    """模式2：Session封装模式 - 使用封装的Session对象"""
    print("\n" + "="*50)
    print("模式2：Session封装模式（上下文管理器）")
    print("="*50)

    req = Requests()

    # 使用上下文管理器，自动关闭session
    async with (await req.async_create_session(wrapper=True)) as session:
        response = await session.get("https://www.baidu.com")
        print(f"请求1成功，响应长度: {len(response)} 字符")

        response = await session.get("https://www.baidu.com")
        print(f"请求2成功，响应长度: {len(response)} 字符")

    print("\n模式2优点：")
    print("- 复用同一个session，性能更好")
    print("- 自动管理连接池")
    print("- 支持上下文管理器，自动关闭")


def est_mode_2_sync_session():
    """模式2同步版本"""
    print("\n" + "="*50)
    print("模式2：Session封装模式（同步）")
    print("="*50)

    req = Requests()

    # 使用上下文管理器
    with req.create_session(wrapper=True) as session:
        response = session.get("https://www.baidu.com")
        print(f"请求1成功，响应长度: {len(response)} 字符")

        response = session.get("https://www.baidu.com")
        print(f"请求2成功，响应长度: {len(response)} 字符")


def est_mode_3_manual_session():
    """模式3：手动管理Session"""
    print("\n" + "="*50)
    print("模式3：手动管理Session")
    print("="*50)

    req = Requests()

    # 手动创建和关闭session
    session = req.create_session(wrapper=True)
    try:
        urls = ["https://www.baidu.com"] * 5
        for i, url in enumerate(urls, 1):
            response = session.get(url)
            print(f"请求{i}成功，响应长度: {len(response)} 字符")
    finally:
        session.close()

    print("\n模式3优点：")
    print("- 完全控制session生命周期")
    print("- 适合批量请求和长期运行的任务")
    print("- 可复用session，性能最优")


async def est_batch_request_comparison():
    """批量请求性能对比"""
    print("\n" + "="*50)
    print("批量请求性能对比")
    print("="*50)

    urls = ["https://www.baidu.com"] * 10

    # 模式1：每次请求创建新session（同步版本）
    print("\n模式1（简单请求-同步）:")
    req = Requests()
    import time
    start = time.time()
    for i, url in enumerate(urls, 1):
        req.get(url)
    end = time.time()
    print(f"完成{len(urls)}个请求，耗时: {end-start:.2f}秒")

    # 模式2：复用session（同步版本）
    print("\n模式2（Session封装-同步）:")
    start = time.time()
    with req.create_session(wrapper=True) as session:
        for url in urls:
            session.get(url)
    end = time.time()
    print(f"完成{len(urls)}个请求，耗时: {end-start:.2f}秒")

    # 模式3：异步批量请求
    print("\n模式3（异步Session封装）:")
    start = time.time()
    async with (await req.async_create_session(wrapper=True)) as session:
        tasks = [session.get(url) for url in urls]
        await asyncio.gather(*tasks)
    end = time.time()
    print(f"完成{len(urls)}个请求，耗时: {end-start:.2f}秒")


def print_comparison_table():
    """打印对比表格"""
    print("\n" + "="*50)
    print("方案对比总结")
    print("="*50)
    print("| 维度 | 简单请求模式 | Session封装模式 |")
    print("|------|-------------|----------------|")
    print("| 使用复杂度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |")
    print("| 代码简洁性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |")
    print("| session控制 | 自动管理 | 用户完全控制 |")
    print("| 批量请求 | 每次创建新session | 复用同一个session |")
    print("| 连接池复用 | 自动处理 | 手动控制，性能更好 |")
    print("| 资源管理 | 自动清理 | 需要手动close（或用上下文管理器） |")
    print("| 灵活性 | 一般 | 高 |")
    print("| 适合场景 | 简单请求、快速开发 | 批量请求、长期运行 |")


if __name__ == "__main__":
    print("\n" + "="*50)
    print("请求器使用模式对比测试")
    print("="*50)

    # 测试模式1：简单请求
    _mode_1_simple_requests()

    # 测试模式2：Session封装（同步）
    est_mode_2_sync_session()

    # 运行异步测试
    asyncio.run(est_mode_2_session_wrapper())

    # 运行异步测试
    asyncio.run(est_mode_2_session_wrapper())

    # 运行批量请求性能对比
    asyncio.run(est_batch_request_comparison())

    # 打印对比表格
    print_comparison_table()

    print("\n" + "="*50)
    print("结论")
    print("="*50)
    print("1. 简单请求模式：适合快速开发、少量请求")
    print("2. Session封装模式：适合批量请求、长期运行任务")
    print("3. 混合模式：支持两种方式，根据场景选择")
    print("4. 推荐：批量请求使用Session封装模式，并使用上下文管理器")
