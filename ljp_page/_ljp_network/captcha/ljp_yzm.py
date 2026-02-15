import ddddocr

ocr = ddddocr.DdddOcr(show_ad=False)

def yzm(img_bytes):
    result = ocr.classification(img_bytes)
    return result