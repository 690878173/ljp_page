__all__ = ['Script']




class Script:
    """防检测初始化脚本合集"""

    # 完整合一版（一次注入全部生效）
    FULL = """
    // 彻底隐藏自动化特征
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });

    // 删除 playwright 注入的特征变量
    for (let key in window) {
        if (key.startsWith('cdc_') || key.startsWith('__pw')) {
            delete window[key];
        }
    }

    // 伪造插件数组（解决 plugins.length = 0 的问题）
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            class FakePluginArray extends Array {}
            const plugins = new FakePluginArray();
            plugins.length = 5;
            return plugins;
        }
    });

    // 伪造语言
    Object.defineProperty(navigator, 'languages', {
        get: () => ['zh-CN', 'zh', 'en-US', 'en']
    });

    // 移除运行时特征
    delete window.callPhantom;
    delete window._phantom;
    """


    Del_webdriver = """
    // 彻底隐藏自动化特征
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """

    Del_CDC = """
    delete window.cdc_adoQpoasnfa76pfcMcwq;
    delete window.__pwInitScripts;
    """

    Change_plugins = """
    Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
    """
