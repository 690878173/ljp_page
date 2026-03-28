from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
from ljp_page.core.base.base_class import Ljp_BaseClass
import re


class _Base_Parse(Ljp_BaseClass):
    @dataclass(slots=True)
    class TsKey:
        """密钥信息封装类"""
        method: str
        uri: str | None = None
        iv: bytes | None = None
        extra: Dict[str, Any] = field(default_factory=dict)

    @dataclass(slots=True)
    class TsInfo:
        """TS片段信息封装类"""
        url: str
        duration: float | None = None
        sequence: int = 0
        key: '_Base_Parse.TsKey | None' = None

    @dataclass(slots=True)
    class MediaInfo:
        """媒体信息封装类（音频、字幕等）"""
        media_type: str
        group_id: str
        language: str | None = None
        name: str | None = None
        default: bool = False
        autoselect: bool = False
        uri: str | None = None
        extra: Dict[str, Any] = field(default_factory=dict)

    @dataclass(slots=True)
    class StreamInfo:
        """流信息封装类（外层m3u8）"""
        bandwidth: int
        url: str
        resolution: tuple[int, int] | None = None
        codecs: str | None = None
        frame_rate: float | None = None
        audio: str | None = None
        subtitles: str | None = None
        extra: Dict[str, Any] = field(default_factory=dict)

    @dataclass(slots=True)
    class M3u8Result:
        """统一的m3u8解析结果类"""
        type: str
        url: str
        streams: List[_Base_Parse.StreamInfo] = field(default_factory=list)
        media_list: List[_Base_Parse.MediaInfo] = field(default_factory=list)
        ts_list: List[_Base_Parse.TsInfo] = field(default_factory=list)
        is_vod: bool = False
        children: List[_Base_Parse.M3u8Result] = field(default_factory=list)
        depth:int = 0

    _key_pattern = re.compile(r'^#EXT-X-KEY:(.*)$', re.IGNORECASE)
    _inf_pattern = re.compile(r'^#EXTINF:([0-9.]+)', re.IGNORECASE)
    _media_seq_pattern = re.compile(r'^#EXT-X-MEDIA-SEQUENCE:(\d+)$', re.IGNORECASE)
    _endlist_pattern = re.compile(r'^#EXT-X-ENDLIST$', re.IGNORECASE)
    _stream_inf_pattern = re.compile(r'^#EXT-X-STREAM-INF:(.*)$', re.IGNORECASE)
    _media_pattern = re.compile(r'^#EXT-X-MEDIA:(.*)$', re.IGNORECASE)

    def __init__(self, logger=None):
        super().__init__(logger)

    @staticmethod
    def __parse_attr_part(attr_part):
        return [attr.strip() for attr in attr_part.split(',') if attr.strip()]

    @staticmethod
    def __parse_attributes(attr_part: str, attr_config: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        attrs = _Base_Parse.__parse_attr_part(attr_part)
        result: Dict[str, Any] = {}
        extra: Dict[str, Any] = {}
        
        for attr in attrs:
            eq_idx = attr.find('=')
            if eq_idx == -1:
                continue
            
            name = attr[:eq_idx].strip()
            name_lower = name.lower().replace('-', '_')
            value = attr[eq_idx + 1:].strip()
            
            if len(value) >= 2 and ((value[0] == '"' and value[-1] == '"') or
                                    (value[0] == "'" and value[-1] == "'")):
                value = value[1:-1]
            
            config = attr_config.get(name_lower)
            
            if config:
                field_name = config.get('field', name_lower)
                attr_type = config.get('type', 'str')
                uppercase = config.get('uppercase', False)
                
                if attr_type == 'int':
                    result[field_name] = int(value)
                elif attr_type == 'float':
                    result[field_name] = float(value)
                elif attr_type == 'bool':
                    result[field_name] = value.upper() == 'YES'
                elif attr_type == 'tuple':
                    parts = value.split('x')
                    if len(parts) == 2:
                        result[field_name] = (int(parts[0]), int(parts[1]))
                elif attr_type == 'hex_bytes':
                    hex_value = value.lower()
                    if hex_value.startswith('0x'):
                        hex_value = hex_value[2:]
                    if len(hex_value) == 32:
                        result[field_name] = bytes.fromhex(hex_value)
                else:
                    result[field_name] = value.upper() if uppercase else value
            else:
                extra[name_lower] = value
        
        if extra:
            result['extra'] = extra
        
        return result

    @staticmethod
    def __text_to_lines(text: str):
        return text.lstrip('\ufeff').splitlines()
    
    @staticmethod
    def _join_url(base_url: str, relative_url: str) -> str:
        pass

    @staticmethod
    def _parse_stream_inf_line(attr_part):
        config = {
            'bandwidth': {'type': 'int'},
            'resolution': {'type': 'tuple', 'field': 'resolution'},
            'codecs': {'type': 'str'},
            'frame_rate': {'type': 'float'},
            'audio': {'type': 'str'},
            'subtitles': {'type': 'str'}
        }
        return _Base_Parse.__parse_attributes(attr_part, config)

    @staticmethod
    def _parse_media_line(attr_part):
        config = {
            'type': {'type': 'str', 'field': 'media_type'},
            'group_id': {'type': 'str'},
            'language': {'type': 'str'},
            'name': {'type': 'str'},
            'uri': {'type': 'str'},
            'default': {'type': 'bool'},
            'autoselect': {'type': 'bool'}
        }
        return _Base_Parse.__parse_attributes(attr_part, config)

    @staticmethod
    def _parse_key_line(attr_part):
        config = {
            'method': {'type': 'str', 'uppercase': True},
            'uri': {'type': 'str'},
            'iv': {'type': 'hex_bytes'}
        }
        return _Base_Parse.__parse_attributes(attr_part, config)

    @staticmethod
    def find_media_by_stream(result, stream_url):
        """根据流的URL递归查找对应的media结果"""
        if result.type == 'media':
            return result

        for child in result.children:
            if child.url == stream_url:
                return child

        return None


class _Parse_M3U8(_Base_Parse):
    def __init__(self, config, logger=None):
        super().__init__(logger)
        self.config = config

    async def _fetch(self, url: str):
        raise NotImplementedError

    def join_url(self, base_url: str, relative_url: str) -> str:
        raise

    async def parse(self, url: str, depth: int = 0, max_depth: int = 10):
        if depth > max_depth:
            raise RecursionError(f"递归深度超过限制：{max_depth}")
        
        m3u8_text = await self._fetch(url)
        result = self._parse(m3u8_text, url,depth)
        
        if result.type == 'master':
            for stream in result.streams:
                stream_url = self.join_url(url, stream.url)
                stream.url = stream_url
                try:
                    child_result = await self.parse(stream_url, depth + 1, max_depth)
                    result.children.append(child_result)
                except Exception as e:
                    self.warning(f"解析子流失败: {stream_url}, 错误: {e}")
        
        return result

    def _parse(self, text, url,depth):
        lines = self.__text_to_lines(text)

        ts_list: List[_Base_Parse.TsInfo] = []
        keys: List[_Base_Parse.TsKey] = []
        streams: List[_Base_Parse.StreamInfo] = []
        media_list: List[_Base_Parse.MediaInfo] = []

        current_duration: float | None = None
        current_stream_attrs: Dict[str, Any] = {}
        media_sequence = 0
        current_key_index = -1
        is_vod = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if not line.startswith('#'):
                if current_stream_attrs:
                    current_stream_attrs['url'] = line
                    streams.append(_Base_Parse.StreamInfo(**current_stream_attrs))
                    current_stream_attrs = {}
                elif current_duration is not None:
                    ts_info = _Base_Parse.TsInfo(
                        url=line,
                        duration=current_duration,
                        sequence=media_sequence,
                        key=keys[current_key_index] if current_key_index >= 0 else None
                    )
                    ts_list.append(ts_info)
                    media_sequence += 1
                current_duration = None
                continue
            
            key_match = self._key_pattern.match(line)
            if key_match:
                key_attrs = self._parse_key_line(key_match.group(1))
                if key_attrs:
                    keys.append(_Base_Parse.TsKey(**key_attrs))
                    current_key_index = len(keys) - 1
                continue    
            
            inf_match = self._inf_pattern.match(line)
            if inf_match:
                current_duration = float(inf_match.group(1))
                continue
            
            seq_match = self._media_seq_pattern.match(line)
            if seq_match:
                media_sequence = int(seq_match.group(1))
                continue

            if self._endlist_pattern.match(line):
                is_vod = True
                continue
            
            media_match = self._media_pattern.match(line)
            if media_match:
                media_attrs = self._parse_media_line(media_match.group(1))
                if media_attrs:
                    media_list.append(_Base_Parse.MediaInfo(**media_attrs))
                continue

            stream_match = self._stream_inf_pattern.match(line)
            if stream_match:
                current_stream_attrs = self._parse_stream_inf_line(stream_match.group(1))

        result_type = 'master' if streams else 'media'
        return _Base_Parse.M3u8Result(
            type=result_type,
            url=url,
            is_vod=is_vod,
            streams=streams,
            media_list=media_list,
            ts_list=ts_list,
            depth = depth
        )


class Parse_M3U8(_Parse_M3U8):
    def __init__(self, config, logger=None):
        super().__init__(config, logger)

    async def _fetch(self, url: str):
        raise NotImplementedError

    def join_url(self, url: str, path: str):
        raise NotImplementedError

    def download_stream(self, result, stream_index=0):
        """下载指定清晰度的视频"""
        if result.type != 'master' or not result.streams:
            raise ValueError("没有可用的流")

        # 选择指定索引的流（默认第一个，通常是最高清晰度）
        selected_stream = result.streams[stream_index]
        print(f"选择清晰度: 带宽={selected_stream.bandwidth}, "
              f"分辨率={selected_stream.resolution}, "
              f"编码={selected_stream.codecs}")

        while result.type != 'media':
            curr_stream = result.streams[stream_index]
            result = self.find_media_by_stream(result, curr_stream.url)
            if result is None:
                raise ValueError('无可用流')

        return result

    def parse_ts_url(self,ts_ls):
        raise NotImplementedError

    async def get(self,url):
        res = await self.parse(url)
        res = self.download_stream(res)
        return res


