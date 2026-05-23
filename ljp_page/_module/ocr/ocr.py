from ddddocr import DdddOcr
import cv2
import numpy as np

class Ocr:
    def __init__(self, ocr: bool = True, det: bool = False, old: bool = False, beta: bool = False,
                 use_gpu: bool = False, device_id: int = 0,
                 import_onnx_path: str = "", charsets_path: str = ""):
        self.ocr = DdddOcr(ocr=ocr, det=det, old=old, beta=beta,use_gpu=use_gpu, device_id=device_id,import_onnx_path=import_onnx_path, charsets_path=charsets_path,show_ad=False)


    def classification(self,img,png_fix=False,probability=False,color_filter_colors=None,color_filter_custom_ranges=None):
        """
        OCR识别方法

        Args:
            img: 图片数据（bytes、str、pathlib.PurePath或PIL.Image）
            png_fix: 是否修复PNG透明背景问题
            probability: 是否返回概率信息
            color_filter_colors: 颜色过滤预设颜色列表，如 ['red', 'blue']
            color_filter_custom_ranges: 自定义HSV颜色范围列表，如 [((0,50,50), (10,255,255))]

        Returns:
            识别结果文本或包含概率信息的字典

        Raises:
            DDDDOCRError: 当功能未启用或识别失败时
        """
        return self.ocr.classification(img,png_fix,probability,color_filter_colors,color_filter_custom_ranges)

    @staticmethod
    def prep1(img_bytes):
        '''
        处理图片，无法处理透明背景图片
        '''
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 自适应阈值（比固定阈值强太多！）
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        denoised = cv2.medianBlur(binary, 3)
        _, encoded = cv2.imencode('.png', denoised)
        return encoded.tobytes()