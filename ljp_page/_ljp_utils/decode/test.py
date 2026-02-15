from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from typing import Optional, Callable, Dict, Any


class Aes:
    """
    通用AES加解密工具类，支持多种模式、填充方式和编码格式，方便扩展和维护。
    """

    MODE_MAP = {
        'CBC': AES.MODE_CBC,
        'ECB': AES.MODE_ECB,
        'CFB': AES.MODE_CFB,
        'OFB': AES.MODE_OFB,
        'CTR': AES.MODE_CTR,
        'GCM': AES.MODE_GCM
    }
    SUPPORTED_KEY_SIZES = [128, 192, 256]
    SUPPORTED_PLAIN_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    SUPPORTED_CIPHER_ENCODINGS = ['base64', 'hex', 'raw']
    SUPPORTED_PADDING = ['pkcs7', 'zero', 'none']

    def __init__(self):
        self.padding_map: Dict[str, Dict[str, Callable]] = {
            'pkcs7': {
                'pad': lambda data: pad(data, AES.block_size),
                'unpad': lambda data: unpad(data, AES.block_size)
            },
            'zero': {
                'pad': self._zero_pad,
                'unpad': self._zero_unpad
            },
            'none': {
                'pad': lambda data: data,
                'unpad': lambda data: data
            }
        }

    def encode(self,
               data: str,
               key: str,
               mode: str = 'CBC',
               iv: Optional[str] = None,
               key_encoding: str = 'utf-8',
               output_encoding: str = 'base64',
               iv_encoding: str = 'utf-8',
               padding: str = 'pkcs7',
               key_size: int = 128
               ) -> str:
        """
        加密接口
        :param data: 明文
        :param key: 密钥
        :param mode: 模式
        :param iv: 初始向量
        :param key_encoding: 密钥编码
        :param output_encoding: 密文输出编码
        :param iv_encoding: IV编码
        :param padding: 填充方式
        :param key_size: 密钥长度
        :return: 密文
        """
        try:
            cipher_mode = self._get_mode(mode)
            key_bytes = self._decode_key(key, key_encoding, key_size)
            iv_bytes = self._decode_iv(iv, iv_encoding) if iv else None
            data_bytes = self._decode_data(data, data_type='plain', encoding='utf-8')

            if padding != 'none' and mode.upper() not in ['GCM', 'CTR']:
                data_bytes = self._add_padding(data_bytes, padding)

            if cipher_mode == AES.MODE_ECB:
                cipher = AES.new(key_bytes, cipher_mode)
            elif cipher_mode == AES.MODE_GCM:
                cipher = AES.new(key_bytes, cipher_mode, nonce=iv_bytes)
                encrypted_bytes, tag = cipher.encrypt_and_digest(data_bytes)
                # 输出密文+tag（常见做法），你也可以单独返回tag
                result = self._encode_cipher(encrypted_bytes, output_encoding) + ':' + base64.b64encode(tag).decode()
                return result
            elif cipher_mode == AES.MODE_CTR:
                cipher = AES.new(key_bytes, cipher_mode, nonce=iv_bytes)
                encrypted_bytes = cipher.encrypt(data_bytes)
            else:
                cipher = AES.new(key_bytes, cipher_mode, iv=iv_bytes)
                encrypted_bytes = cipher.encrypt(data_bytes)

            return self._encode_cipher(encrypted_bytes, output_encoding)
        except Exception as e:
            return f"加密失败: {str(e)}"

    def decode(self,
               data: str,
               key: str,
               mode: str = 'CBC',
               iv: Optional[str] = None,
               key_encoding: str = 'utf-8',
               cipher_encoding: str = 'base64',
               iv_encoding: str = 'utf-8',
               padding: str = 'pkcs7',
               key_size: int = 128,
               tag: Optional[str] = None
        ) -> str:
        """
        解密接口
        """
        try:
            cipher_mode = self._get_mode(mode)
            key_bytes = self._decode_key(key, key_encoding, key_size)
            iv_bytes = self._decode_iv(iv, iv_encoding) if iv else None

            # GCM模式下tag通常和密文拼一起传入，也可以单独参数
            if cipher_mode == self.MODE_MAP['GCM']:
                # 支持密文:tag，或密文+tag参数
                if ':' in data:
                    cipher_text_b64, tag_b64 = data.split(':')
                    data_bytes = self._decode_data(cipher_text_b64, data_type='cipher', encoding=cipher_encoding)
                    tag_bytes = base64.b64decode(tag_b64)
                elif tag:
                    data_bytes = self._decode_data(data, data_type='cipher', encoding=cipher_encoding)
                    tag_bytes = base64.b64decode(tag)
                else:
                    raise ValueError("GCM模式解密需要tag")
                cipher = AES.new(key_bytes, cipher_mode, nonce=iv_bytes)
                decrypted_bytes = cipher.decrypt_and_verify(data_bytes, tag_bytes)
            elif cipher_mode == self.MODE_MAP['ECB']:
                data_bytes = self._decode_data(data, data_type='cipher', encoding=cipher_encoding)
                cipher = AES.new(key_bytes, cipher_mode)
                decrypted_bytes = cipher.decrypt(data_bytes)
            elif cipher_mode == self.MODE_MAP['CTR']:
                data_bytes = self._decode_data(data, data_type='cipher', encoding=cipher_encoding)
                cipher = AES.new(key_bytes, cipher_mode, nonce=iv_bytes)
                decrypted_bytes = cipher.decrypt(data_bytes)
            else:
                data_bytes = self._decode_data(data, data_type='cipher', encoding=cipher_encoding)
                cipher = AES.new(key_bytes, cipher_mode, iv=iv_bytes)
                decrypted_bytes = cipher.decrypt(data_bytes)

            # CTR、GCM模式无需去填充
            if padding != 'none' and mode.upper() not in ['GCM', 'CTR']:
                decrypted_bytes = self._remove_padding(decrypted_bytes, padding)
            return decrypted_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            if 'Padding is incorrect' in str(e):
                return f"解密失败: {str(e)} 请检查填充方式或数据编码是否正确"
            return f"解密失败: {str(e)}"

    def _get_mode(self, mode: str) -> int:
        mode_upper = mode.upper()
        if mode_upper not in self.MODE_MAP:
            raise ValueError(f"不支持的加密模式: {mode}")
        return self.MODE_MAP[mode_upper]

    def _decode_key(self, key: str, encoding: str, key_size: int) -> bytes:
        if key_size not in self.SUPPORTED_KEY_SIZES:
            raise ValueError(f"AES仅支持{self.SUPPORTED_KEY_SIZES}位密钥，传入：{key_size}")
        if isinstance(key, bytes):
            key_bytes = key
        elif encoding == 'utf-8':
            key_bytes = key.encode('utf-8')
        elif encoding == 'base64':
            key_bytes = base64.b64decode(key)
        elif encoding == 'hex':
            key_bytes = bytes.fromhex(key)
        else:
            raise ValueError(f"不支持的密钥编码: {encoding}")
        target_len = key_size // 8
        if len(key_bytes) < target_len:
            key_bytes = key_bytes.ljust(target_len, b'\x00')
        elif len(key_bytes) > target_len:
            key_bytes = key_bytes[:target_len]
        return key_bytes

    def _decode_iv(self, iv: Optional[str], encoding: str) -> Optional[bytes]:
        if iv is None:
            return None
        if isinstance(iv, bytes):
            return iv
        if encoding == 'utf-8':
            return iv.encode('utf-8')
        elif encoding == 'base64':
            return base64.b64decode(iv)
        elif encoding == 'hex':
            return bytes.fromhex(iv)
        else:
            raise ValueError(f"不支持的IV编码: {encoding}")

    def _decode_data(self, data: Any, data_type: str, encoding: str) -> bytes:
        if isinstance(data, bytes):
            return data
        if data_type == 'plain':
            if encoding not in self.SUPPORTED_PLAIN_ENCODINGS:
                raise ValueError(f"明文支持的编码：{self.SUPPORTED_PLAIN_ENCODINGS}，传入：{encoding}")
            return data.encode(encoding)
        elif data_type == 'cipher':
            if encoding not in self.SUPPORTED_CIPHER_ENCODINGS:
                raise ValueError(f"密文支持的编码：{self.SUPPORTED_CIPHER_ENCODINGS}，传入：{encoding}")
            if encoding == 'base64':
                return base64.b64decode(data)
            elif encoding == 'hex':
                return bytes.fromhex(data)
            elif encoding == 'raw':
                return data.encode('latin-1')
        else:
            raise ValueError(f"data_type仅支持'plain'或'cipher'，传入：{data_type}")

    def _encode_cipher(self, cipher_bytes: bytes, encoding: str = 'base64') -> str:
        if encoding not in self.SUPPORTED_CIPHER_ENCODINGS:
            raise ValueError(f"密文输出支持的编码：{self.SUPPORTED_CIPHER_ENCODINGS}，传入：{encoding}")
        if encoding == 'base64':
            return base64.b64encode(cipher_bytes).decode('utf-8')
        elif encoding == 'hex':
            return cipher_bytes.hex()
        elif encoding == 'raw':
            return cipher_bytes.decode('latin-1')

    def _add_padding(self, data: bytes, padding: str) -> bytes:
        if padding not in self.padding_map:
            raise ValueError(f"不支持的填充方式: {padding}")
        return self.padding_map[padding]['pad'](data)

    def _remove_padding(self, data: bytes, padding: str) -> bytes:
        if padding not in self.padding_map:
            raise ValueError(f"不支持的填充方式: {padding}")
        return self.padding_map[padding]['unpad'](data)

    def _zero_pad(self, data: bytes) -> bytes:
        pad_len = AES.block_size - (len(data) % AES.block_size)
        return data + (b'\x00' * pad_len)

    def _zero_unpad(self, data: bytes) -> bytes:
        return data.rstrip(b'\x00')


if __name__ == '__main__':
    aes = Aes()
    plaintext = "这个是测试的加密信息"
    key = "12345678311324354265"
    iv = '123456789abcdefg'
    print("AES-256加密参数:", plaintext, key, iv, 256, 'CBC', 'hex')
    # 加密（AES-256）
    ciphertext = aes.encode(
        data=plaintext,
        key=key,
        mode='CBC',
        iv=iv,
        key_size=256,
        output_encoding='hex'
    )
    print("AES-256加密结果:", ciphertext)
    # 解密
    decrypted = aes.decode(
        data=ciphertext,
        key=key,
        mode='CBC',
        iv=iv,
        key_size=256,
        cipher_encoding='hex'
    )
    print("AES-256解密结果:", decrypted)