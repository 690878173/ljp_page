from __future__ import annotations

from typing import TYPE_CHECKING, Optional
__all__ = ['InputCommands']
from ..protocol.base import Command
from ..protocol.input.methods import (
    DispatchDragEventParams,
    DispatchKeyEventParams,
    DispatchMouseEventParams,
    DispatchTouchEventParams,
    EmulateTouchFromMouseEventParams,
    ImeSetCompositionParams,
    InputMethod,
    InsertTextParams,
    SetIgnoreInputEventsParams,
    SetInterceptDragsParams,
    SynthesizePinchGestureParams,
    SynthesizeScrollGestureParams,
    SynthesizeTapGestureParams,
)

if TYPE_CHECKING:
    from ..protocol.input.methods import (
        CancelDraggingCommand,
        DispatchDragEventCommand,
        DispatchKeyEventCommand,
        DispatchMouseEventCommand,
        DispatchTouchEventCommand,
        DragData,
        EmulateTouchFromMouseEventCommand,
        ImeSetCompositionCommand,
        InsertTextCommand,
        SetIgnoreInputEventsCommand,
        SetInterceptDragsCommand,
        SynthesizePinchGestureCommand,
        SynthesizeScrollGestureCommand,
        SynthesizeTapGestureCommand,
        TouchPoint,
    )
    from ..protocol.input.types import (
        DragEventType,
        GestureSourceType,
        KeyEventType,
        KeyLocation,
        KeyModifier,
        MouseButton,
        MouseEventType,
        PointerType,
        TouchEventType,
    )


class InputCommands:
    """使用 Chrome DevTools 协议模拟用户输入事件的类。

    输入域提供了模拟用户输入的方法，包括：
    - 键盘事件（按键、释放）
    - 鼠标事件（点击、移动、滚轮）
    - 触摸事件（点击、多点触摸手势）
    - 拖放事件
    - 合成手势（捏合、滚动、点击）

    这些方法允许对输入事件进行编程控制，而不需要
    实际的用户交互，使其对于测试和自动化很有用。"""

    @staticmethod
    def cancel_dragging() -> CancelDraggingCommand:
        """生成一个命令以取消页面中任何活动的拖动。

        当您需要中断正在进行的拖动操作时，这非常有用
        这可能是通过dispatchDragEvent 或其他方式启动的。

        返回：
            命令：取消拖动的 CDP 命令。"""
        return Command(method=InputMethod.CANCEL_DRAGGING)

    @staticmethod
    def dispatch_key_event(  #编号：PLR0912
        type: KeyEventType,
        modifiers: Optional[KeyModifier] = None,
        timestamp: Optional[float] = None,
        text: Optional[str] = None,
        unmodified_text: Optional[str] = None,
        key_identifier: Optional[str] = None,
        code: Optional[str] = None,
        key: Optional[str] = None,
        windows_virtual_key_code: Optional[int] = None,
        native_virtual_key_code: Optional[int] = None,
        auto_repeat: Optional[bool] = None,
        is_keypad: Optional[bool] = None,
        is_system_key: Optional[bool] = None,
        location: Optional[KeyLocation] = None,
        commands: Optional[list[str]] = None,
    ) -> DispatchKeyEventCommand:
        """生成一个命令以将按键事件分派到页面。

        该方法可以模拟各种类型的键盘事件如按键、
        按键释放和字符输入。

        参数：
            type：按键事件的类型。允许的值：keyDown、keyUp、rawKeyDown、char。
                 - keyDown：对应于用户按下某个键
                 - keyUp：对应于用户释放按键
                 - rawKeyDown：物理按键，不经过文字处理
                 - char：生成一个没有显式按键事件的字符
            修饰符：表示按下的修饰键的位字段。价值观：
                      Alt=1、Ctrl=2、Meta/Command=4、Shift=8（默认值：0）。
                      例如，要模拟 Ctrl+Shift，请使用 10。
            时间戳：事件发生的时间，自纪元以来以秒为单位。
            文本：通过使用键盘布局处理虚拟键代码生成的文本。
                 “keyUp”和“rawKeyDown”事件不需要（默认值：“”）。
            unmodified_text：不带修饰符的键盘生成的文本
                           （轮班除外）。对于快捷键处理很有用（默认值：“”）。
            key_identifier：唯一密钥标识符（例如“U+0041”）（默认值：“”）。
            code：每个物理键的唯一 DOM 定义字符串值（例如“KeyA”）
                （默认值：“”）。
            key: 唯一的 DOM 定义的字符串值，描述 key 的含义
                活动修饰符、键盘布局等的上下文（例如“AltGr”）
                （默认值：“”）。
            windows_virtual_key_code：Windows 虚拟键代码（默认值：0）。
            native_virtual_key_code：本机虚拟键代码（默认值：0）。
            auto_repeat：事件是否由自动重复生成（默认值：false）。
            is_keypad：事件是否由键盘生成（默认值：false）。
            is_system_key：该事件是否是系统按键事件（默认值：false）。
            location：事件是来自键盘的左侧还是右侧：
                     0=默认，1=左，2=右（默认：0）。
            命令：编辑要与按键事件一起发送的命令（例如“selectAll”）
                     （默认值：[]）。这些与命令名称相关但不等于
                     用于“document.execCommand”和 NSStandardKeyBindingResponding。

        返回：
            Command：用于调度按键事件的 CDP 命令。"""
        params = DispatchKeyEventParams(type=type)
        if modifiers is not None:
            params['modifiers'] = modifiers
        if timestamp is not None:
            params['timestamp'] = timestamp
        if text is not None:
            params['text'] = text
        if unmodified_text is not None:
            params['unmodifiedText'] = unmodified_text
        if key_identifier is not None:
            params['keyIdentifier'] = key_identifier
        if code is not None:
            params['code'] = code
        if key is not None:
            params['key'] = key
        if windows_virtual_key_code is not None:
            params['windowsVirtualKeyCode'] = windows_virtual_key_code
        if native_virtual_key_code is not None:
            params['nativeVirtualKeyCode'] = native_virtual_key_code
        if auto_repeat is not None:
            params['autoRepeat'] = auto_repeat
        if is_keypad is not None:
            params['isKeypad'] = is_keypad
        if is_system_key is not None:
            params['isSystemKey'] = is_system_key
        if location is not None:
            params['location'] = location
        if commands is not None:
            params['commands'] = commands
        return Command(method=InputMethod.DISPATCH_KEY_EVENT, params=params)

    @staticmethod
    def dispatch_mouse_event(
        type: MouseEventType,
        x: int,
        y: int,
        modifiers: Optional[KeyModifier] = None,
        timestamp: Optional[float] = None,
        button: Optional[MouseButton] = None,
        click_count: Optional[int] = None,
        force: Optional[float] = None,
        tangential_pressure: Optional[float] = None,
        tilt_x: Optional[float] = None,
        tilt_y: Optional[float] = None,
        twist: Optional[int] = None,
        delta_x: Optional[float] = None,
        delta_y: Optional[float] = None,
        pointer_type: Optional[PointerType] = None,
    ) -> DispatchMouseEventCommand:
        """生成一个命令以将鼠标事件分派到页面。

        该方法允许模拟各种鼠标交互，例如单击，
        移动和滚轮滚动。

        参数：
            type：鼠标事件的类型。允许值：
                 - mousePressed：按下鼠标按钮
                 - mouseReleased：释放鼠标按钮
                 - mouseMoved：鼠标移动
                 - mouseWheel：鼠标滚轮旋转
            x：事件相对于主框架视口的 X 坐标（以 CSS 像素为单位）。
            y：事件相对于主框架视口的 Y 坐标（以 CSS 像素为单位）。
                0 指视口的顶部，Y 向下增加。
            修饰符：表示按下的修饰键的位字段。价值观：
                Alt=1、Ctrl=2、Meta/Command=4、Shift=8（默认值：0）。
            时间戳：事件发生的时间，自纪元以来以秒为单位。
            按钮：按下/释放鼠标按钮。默认为“无”。
                允许的值：“无”、“左”、“中”、“右”、“后”、“前”。
            click_count：单击鼠标按钮的次数（默认值：0）。
                例如，2 表示双击。
            force：标准化压力，范围为[0,1]（默认：0）。
                主要用于压力敏感输入。
            tangential_Pressure：归一化切向压力，有一个范围
                [-1,1]（默认值：0）。用于手写笔输入。
            倾斜_x：Y-Z 平面与包含触笔的平面之间的平面角度
                轴和 Y 轴，以度为单位，范围为 [-90,90]。正倾斜X是
                向右（默认值：0）。
            倾斜_y：X-Z平面与包含触笔的平面之间的平面角度
                轴和 X 轴，以度为单位，范围为 [-90,90]。正倾斜Y是
                面向用户（默认值：0）。
            扭曲：手写笔绕其自身主轴顺时针旋转，
                以度为单位，范围为 [0,359]（默认值：0）。
            delta_x：鼠标滚轮事件的 CSS 像素 X 增量（默认值：0）。
                正值向右滚动。
            delta_y：鼠标滚轮事件的 CSS 像素 Y 增量（默认值：0）。
                正值向上滚动。
            pointer_type：指针类型（默认值：“鼠标”）。允许的值：“鼠标”、“笔”。

        返回：
            Command：用于调度鼠标事件的 CDP 命令。"""
        params = DispatchMouseEventParams(type=type, x=x, y=y)
        if modifiers is not None:
            params['modifiers'] = modifiers
        if timestamp is not None:
            params['timestamp'] = timestamp
        if button is not None:
            params['button'] = button
        if click_count is not None:
            params['clickCount'] = click_count
        if force is not None:
            params['force'] = force
        if tangential_pressure is not None:
            params['tangentialPressure'] = tangential_pressure
        if tilt_x is not None:
            params['tiltX'] = tilt_x
        if tilt_y is not None:
            params['tiltY'] = tilt_y
        if twist is not None:
            params['twist'] = twist
        if delta_x is not None:
            params['deltaX'] = delta_x
        if delta_y is not None:
            params['deltaY'] = delta_y
        if pointer_type is not None:
            params['pointerType'] = pointer_type
        return Command(method=InputMethod.DISPATCH_MOUSE_EVENT, params=params)

    @staticmethod
    def dispatch_touch_event(
        type: TouchEventType,
        touch_points: list[TouchPoint],
        modifiers: Optional[KeyModifier] = None,
        timestamp: Optional[float] = None,
    ) -> DispatchTouchEventCommand:
        """生成一个命令以将触摸事件分派到页面。

        此方法允许在支持触摸的设备上模拟触摸交互
        或模拟触摸环境。

        参数：
            type：触摸事件的类型。允许值：
                 - touchStart：触摸开始 - 必须指定至少一个点
                 - touchEnd：触摸结束 - 不再按下的点应被删除
                 - touchMove：触摸移动 - 活动点应更新
                 - touchCancel：触摸取消 - 清除所有触摸点
                 触摸结束和取消事件不得包含任何触摸点，
                 而 touch start 和 move 必须至少包含一个。
            touch_points：活动触摸点列表。每个更改点发生一个事件
                        （与之前的事件相比）被生成，模拟
                        按下/移动/释放点一一对应。
                        每个点都包含坐标和其他属性。
            修饰符：表示按下的修饰键的位字段。价值观：
                      Alt=1、Ctrl=2、Meta/Command=4、Shift=8（默认值：0）。
            时间戳：事件发生的时间，自纪元以来以秒为单位。

        返回：
            Command：用于调度触摸事件的 CDP 命令。"""
        params = DispatchTouchEventParams(type=type, touchPoints=touch_points)
        if modifiers is not None:
            params['modifiers'] = modifiers
        if timestamp is not None:
            params['timestamp'] = timestamp
        return Command(method=InputMethod.DISPATCH_TOUCH_EVENT, params=params)

    @staticmethod
    def set_ignore_input_events(ignore: bool) -> SetIgnoreInputEventsCommand:
        """生成一个命令来忽略输入事件（在审核页面时有用）。

        当ignore为true时，所有输入事件都将被忽略，这很有用
        在自动化测试期间或当您想要阻止用户交互时
        在执行某些操作时。

        参数：
            忽略：如果为 true，则输入事件处理将被忽略。

        返回：
            命令：用于设置忽略输入事件的 CDP 命令。"""
        params = SetIgnoreInputEventsParams(ignore=ignore)
        return Command(method=InputMethod.SET_IGNORE_INPUT_EVENTS, params=params)

    @staticmethod
    def dispatch_drag_event(
        type: DragEventType,
        x: int,
        y: int,
        data: DragData,
        modifiers: Optional[KeyModifier] = None,
    ) -> DispatchDragEventCommand:
        """生成一个命令以将拖动事件分派到页面中。

        该实验方法允许模拟拖放操作
        通过在特定坐标处调度拖动事件。

        参数：
            type：拖动事件的类型。允许值：
                 - DragEnter：当拖动的项目进入有效的放置目标时触发
                 - DragOver：当拖动的项目被拖动到有效的放置目标上时触发
                 - drop：当物品被扔到有效的放置目标上时触发
                 - DragCancel：取消拖动操作时触发
            x：事件相对于主框架视口的 X 坐标（以 CSS 像素为单位）。
            y：事件相对于主框架视口的 Y 坐标（以 CSS 像素为单位）。
                0 指视口的顶部，Y 向下增加。
            data：包含被拖动项目、其 MIME 类型和其他信息的拖动数据。
            修饰符：表示按下的修饰键的位字段。价值观：
                      Alt=1、Ctrl=2、Meta/Command=4、Shift=8（默认值：0）。

        返回：
            命令：用于调度拖动事件的 CDP 命令。"""
        params = DispatchDragEventParams(type=type, data=data, x=x, y=y)
        if modifiers is not None:
            params['modifiers'] = modifiers
        return Command(method=InputMethod.DISPATCH_DRAG_EVENT, params=params)

    @staticmethod
    def emulate_touch_from_mouse_event(  #编号: PLR0913, PLR0917
        type: MouseEventType,
        x: int,
        y: int,
        button: MouseButton,
        timestamp: Optional[float] = None,
        delta_x: Optional[float] = None,
        delta_y: Optional[float] = None,
        modifiers: Optional[KeyModifier] = None,
        click_count: Optional[int] = None,
    ) -> EmulateTouchFromMouseEventCommand:
        """生成一个命令以根据鼠标事件参数模拟触摸事件。

        该实验方法允许将鼠标事件转换为触摸事件，
        对于在触摸不可用的环境中测试触摸交互非常有用。

        参数：
            type：要转换的鼠标事件的类型。允许值：
                 - mousePressed：转换为 touchStart
                 - mouseReleased：转换为touchEnd
                 - mouseMoved：转换为 touchMove
                 - mouseWheel：可能会触发滚动
            x：鼠标指针的 X 坐标，以设备无关像素 (DIP) 为单位。
            y：DIP 中鼠标指针的 Y 坐标。
            按钮：鼠标按钮。仅支持“无”、“左”、“右”。
            时间戳：事件发生的时间，自纪元以来以秒为单位。
                      默认为当前时间。
            delta_x：鼠标滚轮事件的 DIP 中的 X 增量（默认值：0）。用于滚动。
            delta_y：鼠标滚轮事件的 DIP 中的 Y 增量（默认值：0）。用于滚动。
            修饰符：表示按下的修饰键的位字段。价值观：
                      Alt=1、Ctrl=2、Meta/Command=4、Shift=8（默认值：0）。
            click_count：单击鼠标按钮的次数（默认值：0）。
                       例如，2 表示双击。

        返回：
            命令：模拟鼠标触摸事件的 CDP 命令。"""
        params = EmulateTouchFromMouseEventParams(type=type, x=x, y=y, button=button)
        if timestamp is not None:
            params['timestamp'] = timestamp
        if delta_x is not None:
            params['deltaX'] = delta_x
        if delta_y is not None:
            params['deltaY'] = delta_y
        if modifiers is not None:
            params['modifiers'] = modifiers
        if click_count is not None:
            params['clickCount'] = click_count
        return Command(method=InputMethod.EMULATE_TOUCH_FROM_MOUSE_EVENT, params=params)

    @staticmethod
    def ime_set_composition(
        text: str,
        selection_start: int,
        selection_end: int,
        replacement_start: Optional[int] = None,
        replacement_end: Optional[int] = None,
    ) -> ImeSetCompositionCommand:
        """生成一个命令来设置 IME 的当前候选文本。

        此实验方法设置输入法编辑器 (IME) 的文本，
        用于输入需要更多字符的语言
        击键次数多于字符数（如中文、日文、韩文）。

        使用 imeCommitComposition 提交最终文本。
        使用 imeSetComposition 以空字符串作为文本来取消合成。

        参数：
            text：作为 IME 组合插入的文本。
            Selection_start：所选内容在合成文本中的开始位置。
            Selection_end：所选内容在合成文本中的结束位置。
            replacement_start：要替换的文本的起始位置
                （默认值：与选择开始相同）。
            replacement_end：要替换的文本的结束位置
                （默认值：与selection_end相同）。

        返回：
            命令：用于设置 IME 组合的 CDP 命令。"""
        params = ImeSetCompositionParams(
            text=text,
            selectionStart=selection_start,
            selectionEnd=selection_end,
        )
        if replacement_start is not None:
            params['replacementStart'] = replacement_start
        if replacement_end is not None:
            params['replacementEnd'] = replacement_end
        return Command(method=InputMethod.IME_SET_COMPOSITION, params=params)

    @staticmethod
    def insert_text(
        text: str,
    ) -> InsertTextCommand:
        """生成一个命令来模拟插入并非来自按键的文本。

        此实验方法对于插入通常会插入的文本很有用
        来自键盘以外的来源，例如表情符号选择器、IME 或
        剪贴板粘贴。

        参数：
            文本：要插入的文本。

        返回：
            命令：用于插入文本的 CDP 命令。"""
        params = InsertTextParams(text=text)
        return Command(method=InputMethod.INSERT_TEXT, params=params)

    @staticmethod
    def set_intercept_drags(enabled: bool) -> SetInterceptDragsCommand:
        """生成命令来控制拖放事件的拦截。

        这种实验方法可以防止默认的拖放行为，而是
        发出 Input.dragIntercepted 事件。拖放行为可以
        通过Input.dispatchDragEvent直接控制。

        这对于实现自定义拖放逻辑或测试非常有用
        自动化测试中的拖放行为。

        参数：
            启用：如果为 true，拖动事件将被拦截并报告为
                    DragIntercepted 事件，防止默认行为。

        返回：
            命令：用于设置拖动拦截的 CDP 命令。"""
        params = SetInterceptDragsParams(enabled=enabled)
        return Command(method=InputMethod.SET_INTERCEPT_DRAGS, params=params)

    @staticmethod
    def synthesize_pinch_gesture(
        x: int,
        y: int,
        scale_factor: float,
        relative_speed: Optional[int] = None,
        gesture_source_type: Optional[GestureSourceType] = None,
    ) -> SynthesizePinchGestureCommand:
        """生成在一段时间内合成捏合手势的命令。

        该实验方法创建了一个合成的捏合手势（放大/缩小）
        随着时间的推移发出适当的触摸事件。这对于测试很有用
        Web 应用程序中的捏合缩放功能。

        参数：
            x：手势开始的 X 坐标（以 CSS 像素为单位）。
            y：手势开始的 Y 坐标（以 CSS 像素为单位）。
            scale_factor：缩放后的相对比例因子：
                        - >1.0 放大（手指分开）
                        - <1.0 缩小（手指一起移动）
            relative_speed：相对指针速度，以每秒像素为单位（默认值：800）。
                          控制手势发生的速度。
            gesture_source_type：要生成哪种类型的输入事件：
                              - 'default'：平台的首选输入类型
                              - '触摸'：触摸输入
                              - '鼠标'：鼠标输入

        返回：
            命令：用于合成捏合手势的 CDP 命令。"""
        params = SynthesizePinchGestureParams(x=x, y=y, scaleFactor=scale_factor)
        if relative_speed is not None:
            params['relativeSpeed'] = relative_speed
        if gesture_source_type is not None:
            params['gestureSourceType'] = gesture_source_type
        return Command(method=InputMethod.SYNTHESIZE_PINCH_GESTURE, params=params)

    @staticmethod
    def synthesize_scroll_gesture(
        x: int,
        y: int,
        x_distance: Optional[float] = None,
        y_distance: Optional[float] = None,
        x_overscroll: Optional[float] = None,
        y_overscroll: Optional[float] = None,
        prevent_fling: Optional[bool] = None,
        speed: Optional[int] = None,
        gesture_source_type: Optional[GestureSourceType] = None,
        repeat_count: Optional[int] = None,
        repeat_delay_ms: Optional[int] = None,
        interaction_marker_name: Optional[str] = None,
    ) -> SynthesizeScrollGestureCommand:
        """生成一个命令来合成一段时间内的滚动手势。

        该实验方法通过发出以下命令创建合成滚动手势
        随着时间的推移适当的触摸事件。这对于测试滚动很有用
        Web 应用程序中的行为。

        参数：
            x：手势开始的 X 坐标（以 CSS 像素为单位）。
            y：手势开始的 Y 坐标（以 CSS 像素为单位）。
            x_distance：沿 X 轴滚动的距离（向左滚动为正）。
            y_distance：沿 Y 轴滚动的距离（正值向上滚动）。
            x_overscroll：沿 X 轴向后滚动的附加像素数，
                        除了给定的距离之外。这会产生过度滚动
                        效果（橡皮筋）。
            y_overscroll：沿 Y 轴向后滚动的附加像素数，
                        除了给定的距离之外。这会产生过度滚动
                        效果（橡皮筋）。
            Prevent_fling：防止 fling（默认值：true）。如果为 false，则可能会出现 fling 动画
                         手势后继续。
            速度：以每秒像素为单位的滑动速度（默认值：800）。
            gesture_source_type：要生成哪种类型的输入事件：
                              - 'default'：平台的首选输入类型
                              - '触摸'：触摸输入
                              - '鼠标'：鼠标输入
            Repeat_count：重复手势的次数（默认值：0）。
            Repeat_delay_ms：每次重复之间的延迟毫秒数（默认值：250）。
            Interaction_marker_name：要生成的交互标记的名称（如果不为空）。
                                  用于跟踪性能测量中的手势计时。

        返回：
            命令：用于合成滚动手势的 CDP 命令。"""
        params = SynthesizeScrollGestureParams(x=x, y=y)
        if x_distance is not None:
            params['xDistance'] = x_distance
        if y_distance is not None:
            params['yDistance'] = y_distance
        if x_overscroll is not None:
            params['xOverscroll'] = x_overscroll
        if y_overscroll is not None:
            params['yOverscroll'] = y_overscroll
        if prevent_fling is not None:
            params['preventFling'] = prevent_fling
        if speed is not None:
            params['speed'] = speed
        if gesture_source_type is not None:
            params['gestureSourceType'] = gesture_source_type
        if repeat_count is not None:
            params['repeatCount'] = repeat_count
        if repeat_delay_ms is not None:
            params['repeatDelayMs'] = repeat_delay_ms
        if interaction_marker_name is not None:
            params['interactionMarkerName'] = interaction_marker_name
        return Command(method=InputMethod.SYNTHESIZE_SCROLL_GESTURE, params=params)

    @staticmethod
    def synthesize_tap_gesture(
        x: int,
        y: int,
        duration: Optional[int] = None,
        tap_count: Optional[int] = None,
        gesture_source_type: Optional[GestureSourceType] = None,
    ) -> SynthesizeTapGestureCommand:
        """生成一个命令来合成一段时间内的点击手势。

        该实验方法通过发出以下命令创建合成点击手势
        随着时间的推移适当的触摸事件。这对于测试很有用
        Web 应用程序中的触摸交互。

        参数：
            x：手势开始的 X 坐标（以 CSS 像素为单位）。
            y：手势开始的 Y 坐标（以 CSS 像素为单位）。
            持续时间：触地和触地事件之间的持续时间（以毫秒为单位）（默认值：50）。
                     控制点击手势所需的时间。
            tap_count：执行点击的次数（例如，双击 2 次，默认值：1）。
            gesture_source_type：要生成哪种类型的输入事件：
                              - 'default'：平台的首选输入类型
                              - '触摸'：触摸输入
                              - '鼠标'：鼠标输入

        返回：
            命令：用于合成点击手势的 CDP 命令。"""
        params = SynthesizeTapGestureParams(x=x, y=y)
        if duration is not None:
            params['duration'] = duration
        if tap_count is not None:
            params['tapCount'] = tap_count
        if gesture_source_type is not None:
            params['gestureSourceType'] = gesture_source_type
        return Command(method=InputMethod.SYNTHESIZE_TAP_GESTURE, params=params)
