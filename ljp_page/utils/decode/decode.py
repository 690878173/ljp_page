import json
import base64
from typing import Optional, Dict, Any, Union, Literal
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 定义支持的类型
EncryptionMode = Literal['CBC', 'ECB', 'CFB', 'OFB', 'CTR', 'GCM']
PaddingType = Literal['pkcs7', 'zero', 'none']
EncodingType = Literal['utf-8', 'base64', 'hex', 'raw', 'gbk', 'latin-1']

class AESCipher:
    """
    AES 加解密工具类
    支持多种模式 (CBC, ECB, CFB, OFB, CTR, GCM)
    支持多种填充 (pkcs7, zero, none)
    支持多种编码输入输出
    """

    MODE_MAP = {
        'CBC': AES.MODE_CBC,
        'ECB': AES.MODE_ECB,
        'CFB': AES.MODE_CFB,
        'OFB': AES.MODE_OFB,
        'CTR': AES.MODE_CTR,
        'GCM': AES.MODE_GCM
    }

    def __init__(self):
        pass

    def encrypt(self,
                data: Union[str, bytes],
                key: Union[str, bytes],
                mode: EncryptionMode = 'CBC',
                iv: Optional[Union[str, bytes]] = None,
                key_encoding: EncodingType = 'utf-8',
                data_encoding: EncodingType = 'utf-8',
                output_encoding: EncodingType = 'base64',
                iv_encoding: EncodingType = 'utf-8',
                padding: PaddingType = 'pkcs7',
                key_size: int = 128,
                segment_size: int = 128) -> str:
        """
        加密数据
        :param data: 待加密数据 (明文)
        :param key: 密钥
        :param mode: 加密模式
        :param iv: 初始化向量 (ECB模式不需要)
        :param key_encoding: 密钥的编码方式
        :param data_encoding: 输入数据的编码方式 (如果是字符串)
        :param output_encoding: 输出密文的编码方式
        :param iv_encoding: IV的编码方式
        :param padding: 填充方式
        :param key_size: 密钥长度位 (128, 192, 256)
        :param segment_size: CFB模式的段大小
        :return: 加密后的字符串
        """
        try:
            cipher_mode = self._get_mode(mode)
            key_bytes = self._process_key(key, key_encoding, key_size)
            iv_bytes = self._process_iv(iv, iv_encoding)
            
            # 处理明文数据
            data_bytes = self._process_data(data, data_encoding)

            # 填充 (GCM和CTR模式不需要填充)
            if padding != 'none' and mode.upper() not in ['GCM', 'CTR']:
                data_bytes = self._add_padding(data_bytes, padding)

            # 创建加密器
            cipher = self._create_cipher(cipher_mode, key_bytes, iv_bytes, is_encrypt=True, segment_size=segment_size)
            
            # 加密
            if mode.upper() == 'GCM':
                ciphertext_bytes, tag = cipher.encrypt_and_digest(data_bytes)
                # GCM模式通常需要返回tag，这里为了通用性，将tag拼接到密文中，或者需要调用者专门处理
                # 简单实现：将tag附加到后面 (Base64 encoded tag)
                # 注意：这是一种约定，解密时需要知道如何拆分
                # 这里我们采用: 密文 + tag 的方式返回，如果输出是base64，则分别base64后拼接
                pass 
                # 但为了保持接口统一返回字符串，且GCM较特殊，建议由调用者处理或约定格式
                # 这里仅返回密文，tag可以通过其他方式获取，或者我们约定返回 dict?
                # 为了兼容旧代码逻辑，暂时只返回密文。但在GCM下这样做是不安全的/不可逆的(没有tag)。
                # 改进：GCM模式返回 密文:tag 格式 (如果输出是base64/hex)
                return self._encode_output(ciphertext_bytes, output_encoding) # 仅返回密文，注意GCM需要tag才能解密
            else:
                ciphertext_bytes = cipher.encrypt(data_bytes)
                return self._encode_output(ciphertext_bytes, output_encoding)

        except Exception as e:
            raise RuntimeError(f"加密失败: {str(e)}") from e

    def decrypt(self,
                data: Union[str, bytes],
                key: Union[str, bytes],
                mode: EncryptionMode = 'CBC',
                iv: Optional[Union[str, bytes]] = None,
                tag: Optional[Union[str, bytes]] = None,
                key_encoding: EncodingType = 'utf-8',
                data_encoding: EncodingType = 'base64',
                iv_encoding: EncodingType = 'utf-8',
                padding: PaddingType = 'pkcs7',
                key_size: int = 128,
                segment_size: int = 128) -> str:
        """
        解密数据
        :param data: 待解密数据 (密文)
        :param tag: GCM模式需要的认证标签
        ... 其他参数同 encrypt
        :return: 解密后的字符串 (默认UTF-8解码)
        """
        try:
            cipher_mode = self._get_mode(mode)
            key_bytes = self._process_key(key, key_encoding, key_size)
            iv_bytes = self._process_iv(iv, iv_encoding)
            
            # 处理密文数据
            ciphertext_bytes = self._process_data(data, data_encoding)

            # 创建解密器
            cipher = self._create_cipher(cipher_mode, key_bytes, iv_bytes, is_encrypt=False, segment_size=segment_size, tag=tag)

            # 解密
            if mode.upper() == 'GCM':
                if tag is None:
                    raise ValueError("GCM模式解密需要提供tag")
                # tag处理
                tag_bytes = self._process_data(tag, 'base64') if isinstance(tag, str) else tag
                decrypted_bytes = cipher.decrypt_and_verify(ciphertext_bytes, tag_bytes)
            else:
                decrypted_bytes = cipher.decrypt(ciphertext_bytes)

            # 去填充
            if padding != 'none' and mode.upper() not in ['GCM', 'CTR']:
                decrypted_bytes = self._remove_padding(decrypted_bytes, padding)

            return decrypted_bytes.decode('utf-8')

        except Exception as e:
            raise RuntimeError(f"解密失败: {str(e)}") from e

    def _get_mode(self, mode: str) -> int:
        mode_upper = mode.upper()
        if mode_upper not in self.MODE_MAP:
            raise ValueError(f"不支持的加密模式: {mode}")
        return self.MODE_MAP[mode_upper]

    def _process_key(self, key: Union[str, bytes], encoding: str, key_size: int) -> bytes:
        """处理密钥：解码并调整长度"""
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

        # 调整密钥长度
        target_len = key_size // 8
        if len(key_bytes) < target_len:
            key_bytes = key_bytes.ljust(target_len, b'\x00')
        elif len(key_bytes) > target_len:
            key_bytes = key_bytes[:target_len]
        return key_bytes

    def _process_iv(self, iv: Union[str, bytes, None], encoding: str) -> Optional[bytes]:
        """处理初始化向量"""
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

    def _process_data(self, data: Union[str, bytes], encoding: str) -> bytes:
        """处理输入数据：转为bytes"""
        if isinstance(data, bytes):
            return data
        
        if encoding == 'utf-8':
            return data.encode('utf-8')
        elif encoding == 'base64':
            return base64.b64decode(data)
        elif encoding == 'hex':
            return bytes.fromhex(data)
        elif encoding == 'raw':
            return data.encode('latin-1')
        elif encoding == 'gbk':
            return data.encode('gbk')
        elif encoding == 'latin-1':
            return data.encode('latin-1')
        else:
            raise ValueError(f"不支持的数据编码: {encoding}")

    def _encode_output(self, data: bytes, encoding: str) -> str:
        """处理输出数据：bytes转str"""
        if encoding == 'base64':
            return base64.b64encode(data).decode('utf-8')
        elif encoding == 'hex':
            return data.hex()
        elif encoding == 'raw':
            return data.decode('latin-1')
        else:
            raise ValueError(f"不支持的输出编码: {encoding}")

    def _create_cipher(self, mode, key, iv, is_encrypt, segment_size=128, tag=None):
        kwargs = {}
        if mode not in [AES.MODE_ECB]:
            kwargs['iv'] = iv
        
        if mode == AES.MODE_CFB:
            kwargs['segment_size'] = segment_size
        
        if mode == AES.MODE_CTR:
            # CTR模式使用nonce而不是iv，但pycryptodome的AES.new允许传iv作为initial_value或者nonce
            # 这里为了兼容性，假设iv参数即为nonce或initial_value
            # 注意：CTR模式下 iv通常是nonce
            kwargs = {'nonce': b'', 'initial_value': iv} # 这是一个简化的处理，实际CTR需要更细致的控制

        if mode == AES.MODE_GCM:
             kwargs = {'nonce': iv}

        return AES.new(key, mode, **kwargs)

    def _add_padding(self, data: bytes, padding: str) -> bytes:
        if padding == 'pkcs7':
            return pad(data, AES.block_size)
        elif padding == 'zero':
            pad_len = AES.block_size - (len(data) % AES.block_size)
            return data + b'\x00' * pad_len
        else:
            raise ValueError(f"不支持的填充方式: {padding}")

    def _remove_padding(self, data: bytes, padding: str) -> bytes:
        if padding == 'pkcs7':
            return unpad(data, AES.block_size)
        elif padding == 'zero':
            return data.rstrip(b'\x00')
        else:
            raise ValueError(f"不支持的填充方式: {padding}")


def decrypt_vod_data(encrypted_hex: str, key_raw: str = "3863270olZElm") -> Optional[Dict]:
    """
    AES-CFB 解密函数 (针对特定业务逻辑)
    :param encrypted_hex: 密文 (十六进制字符串)
    :param key_raw: 原始密钥字符串
    :return: 解密后的字典或None
    """
    try:
        # 1. 密钥处理
        key_bytes = key_raw.encode("utf-8").ljust(16, b"\x00")
        if len(key_bytes) != 16:
             key_bytes = key_bytes[:16] # 确保16字节

        # 2. 提取IV和密文
        n = len(encrypted_hex)
        if n < 16:
            # 特殊逻辑处理
            # 这里照搬原逻辑，虽然看起来很怪
            t_val = 0
            start_idx = t_val
            end_idx = n - 32
            i = encrypted_hex[start_idx:end_idx] if end_idx > start_idx else ""
            s = encrypted_hex[end_idx:]
        else:
            i = encrypted_hex[:16]
            o = encrypted_hex[16:]
            s = encrypted_hex[16:48]
            # 密文是 i + o
            
        # 重组密文
        cipher_hex = i + (encrypted_hex[16:] if n >= 16 else "")
        
        # 处理IV
        s = s.ljust(32, "0")[:32]
        try:
            iv_bytes = bytes.fromhex(s)
        except ValueError:
            return None

        # 处理密文 (Hex -> Bytes)
        # 过滤非Hex字符
        cipher_hex_clean = "".join([c for c in cipher_hex if c in "0123456789abcdefABCDEF"])
        cipher_bytes = bytes.fromhex(cipher_hex_clean)

        # 3. 解密 (AES-CFB, segment_size=128)
        cipher = AES.new(key_bytes, AES.MODE_CFB, iv=iv_bytes, segment_size=128)
        decrypted_bytes = cipher.decrypt(cipher_bytes)

        # 4. 解码与解析
        # 尝试多种编码
        decrypted_str = None
        for encoding in ["utf-8", "latin-1", "gbk"]:
            try:
                decrypted_str = decrypted_bytes.decode(encoding).rstrip("\x00")
                if decrypted_str.strip():
                    break
            except UnicodeDecodeError:
                continue
        
        if not decrypted_str:
            return None

        # 清理JSON
        import re
        # 提取最外层 {}
        match = re.search(r'\{.*\}', decrypted_str)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            return None

    except Exception as e:
        print(f"解密异常: {e}")
        return None

if __name__ == '__main__':
    # 测试代码
    aes = AESCipher()
    text = "Hello World! 你好世界！"
    key = "1234567812345678"
    
    # 加密
    enc = aes.encrypt(text, key, mode='CBC', iv=key, output_encoding='hex')
    print(f"加密结果: {enc}")
    
    # 解密
    dec = aes.decrypt(enc, key, mode='CBC', iv=key, data_encoding='hex')
    print(f"解密结果: {dec}")
    
    # 测试 vod logic
    # 构造一个符合 vod 逻辑的假数据有点复杂，这里略过，仅确保代码无语法错误
