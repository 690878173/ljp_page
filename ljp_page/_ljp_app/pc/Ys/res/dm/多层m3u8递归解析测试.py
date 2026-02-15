import asyncio
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ljp_page._ljp_applications.pc.Ys.ljp_m3u8 import Parse_M3U8
@dataclass(slots=True)
class TsKey:
    method: str
    uri: str | None = None
    iv: bytes | None = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TsInfo:
    url: str
    duration: float | None = None
    sequence: int = 0
    key: 'TsKey | None' = None


@dataclass(slots=True)
class MediaInfo:
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
    type: str
    url: str
    streams: List[StreamInfo] = field(default_factory=list)
    media_list: List[MediaInfo] = field(default_factory=list)
    ts_list: List[TsInfo] = field(default_factory=list)
    is_vod: bool = False
    children: List['M3u8Result'] = field(default_factory=list)
    depth:int=0


class M3u8TestClient:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self._key_pattern = re.compile(r'^#EXT-X-KEY:(.*)$', re.IGNORECASE)
        self._inf_pattern = re.compile(r'^#EXTINF:([0-9.]+)', re.IGNORECASE)
        self._media_seq_pattern = re.compile(r'^#EXT-X-MEDIA-SEQUENCE:(\d+)$', re.IGNORECASE)
        self._endlist_pattern = re.compile(r'^#EXT-X-ENDLIST$', re.IGNORECASE)
        self._stream_inf_pattern = re.compile(r'^#EXT-X-STREAM-INF:(.*)$', re.IGNORECASE)
        self._media_pattern = re.compile(r'^#EXT-X-MEDIA:(.*)$', re.IGNORECASE)

    async def _fetch(self, url: str) -> str:
        filename = os.path.basename(url)
        filepath = os.path.join(self.data_dir, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _join_url(self, base_url: str, relative_url: str) -> str:
        if not relative_url:
            return base_url
        if relative_url.startswith(('http://', 'https://')):
            return relative_url
        if relative_url.startswith('/'):
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{relative_url}"
        return urljoin(base_url, relative_url)

    @staticmethod
    def __parse_attr_part(attr_part):
        return [attr.strip() for attr in attr_part.split(',') if attr.strip()]

    @staticmethod
    def __parse_attributes(attr_part: str, attr_config: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        attrs = M3u8TestClient.__parse_attr_part(attr_part)
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

        result['extra'] = extra
        return result

    def _parse_stream_inf_line(self, attr_part):
        config = {
            'bandwidth': {'type': 'int'},
            'resolution': {'type': 'tuple', 'field': 'resolution'},
            'codecs': {'type': 'str'},
            'frame_rate': {'type': 'float'},
            'audio': {'type': 'str'},
            'subtitles': {'type': 'str'}
        }
        return self.__parse_attributes(attr_part, config)

    def _parse_media_line(self, attr_part):
        config = {
            'type': {'type': 'str', 'field': 'media_type'},
            'group_id': {'type': 'str'},
            'language': {'type': 'str'},
            'name': {'type': 'str'},
            'uri': {'type': 'str'},
            'default': {'type': 'bool'},
            'autoselect': {'type': 'bool'}
        }
        return self.__parse_attributes(attr_part, config)

    def _parse_key_line(self, attr_part):
        config = {
            'method': {'type': 'str', 'uppercase': True},
            'uri': {'type': 'str'},
            'iv': {'type': 'hex_bytes'}
        }
        return self.__parse_attributes(attr_part, config)

    def _parse(self, text, url,i):
        lines = text.split('\n')

        ts_list: List[TsInfo] = []
        keys: List[TsKey] = []
        streams: List[StreamInfo] = []
        media_list: List[MediaInfo] = []

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
                    streams.append(StreamInfo(**current_stream_attrs))
                    current_stream_attrs = {}
                elif current_duration is not None:
                    ts_info = TsInfo(
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
                    keys.append(TsKey(**key_attrs))
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
                    media_list.append(MediaInfo(**media_attrs))
                continue

            stream_match = self._stream_inf_pattern.match(line)
            if stream_match:
                current_stream_attrs = self._parse_stream_inf_line(stream_match.group(1))

        result_type = 'master' if (streams or media_list) else 'media'
        return M3u8Result(
            type=result_type,
            url=url,
            streams=streams,
            media_list=media_list,
            ts_list=ts_list,
            is_vod=is_vod,
            depth=i
        )

    async def parse(self, url: str, depth: int = 0, max_depth: int = 10) -> M3u8Result:
        if depth > max_depth:
            raise RecursionError(f"递归深度超过限制：{max_depth}")

        m3u8_text = await self._fetch(url)
        result = self._parse(m3u8_text, url,depth)

        if result.type == 'master':
            for stream in result.streams:
                stream_url = self._join_url(url, stream.url)
                stream.url = stream_url
                try:
                    child_result = await self.parse(stream_url, depth + 1, max_depth)
                    result.children.append(child_result)
                except Exception as e:
                    print(f"警告: 解析子流失败: {stream_url}, 错误: {e}")

        return result

    def download_stream(self, result, stream_index=0, output_dir='downloads'):
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

    @staticmethod
    def find_media_by_stream(result, stream_url):
        """根据流的URL递归查找对应的media结果"""
        if result.type == 'media':
            return result

        for child in result.children:
            if child.url == stream_url:
                return child

        return None


def print_result(result, indent=0):
    prefix = '  ' * indent
    print(result)
    
    print(f"{prefix}类型: {result.type}")
    print(f"{prefix}URL: {result.url}")
    
    if result.type == 'master':
        print(f"{prefix}流数量: {len(result.streams)}")
        for i, stream in enumerate(result.streams):
            print(f"{prefix}  流{i+1}:")
            print(f"{prefix}    带宽: {stream.bandwidth}")
            if stream.resolution:
                print(f"{prefix}    分辨率: {stream.resolution[0]}x{stream.resolution[1]}")
            if stream.codecs:
                print(f"{prefix}    编码: {stream.codecs}")
            if stream.frame_rate:
                print(f"{prefix}    帧率: {stream.frame_rate}")
            if stream.audio:
                print(f"{prefix}    音频组: {stream.audio}")
            if stream.subtitles:
                print(f"{prefix}    字幕组: {stream.subtitles}")
        
        print(f"{prefix}媒体数量: {len(result.media_list)}")
        for i, media in enumerate(result.media_list):
            print(f"{prefix}  媒体{i+1}:")
            print(f"{prefix}    类型: {media.media_type}")
            print(f"{prefix}    组ID: {media.group_id}")
            if media.language:
                print(f"{prefix}    语言: {media.language}")
            if media.name:
                print(f"{prefix}    名称: {media.name}")
            print(f"{prefix}    默认: {media.default}")
            print(f"{prefix}    自动选择: {media.autoselect}")
            if media.uri:
                print(f"{prefix}    URI: {media.uri}")
        
        print(f"{prefix}子解析结果数量: {len(result.children)}")
        for i, child in enumerate(result.children):
            print(f"{prefix}  子结果{i+1}:")
            print_result(child, indent + 2)
    
    elif result.type == 'media':
        print(f"{prefix}TS数量: {len(result.ts_list)}")
        print(f"{prefix}是否VOD: {result.is_vod}")
        for i, ts in enumerate(result.ts_list[:3]):
            print(f"{prefix}  TS{i+1}: {ts.url} (时长: {ts.duration}, 序列: {ts.sequence})")
        if len(result.ts_list) > 3:
            print(f"{prefix}  ... 共{len(result.ts_list)}个TS片段")


async def main():
    print("=" * 60)
    print("多层m3u8递归解析测试")
    print("=" * 60)
    
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'res_data')
    client = M3u8TestClient(data_dir)
    
    print("\n【第一层：主播放列表】")
    print("URL: 第一层_master.m3u8")
    
    result = await client.parse("第一层_master.m3u8")
    
    print("\n解析结果:")
    print("-" * 60)
    print_result(result)
    
    print("\n" + "=" * 60)
    print("验证结果:")
    print("=" * 60)
    
    # 验证第一层
    assert result.type == 'master', "第一层类型应为master"
    assert len(result.streams) == 3, "第一层应有3个流"
    assert len(result.media_list) == 3, "第一层应有3个媒体(2个音频+1个字幕)"
    print("✓ 第一层验证通过")
    
    # 验证第二层
    assert len(result.children) == 3, "应有3个第二层子结果"
    for child in result.children:
        assert child.type == 'master', "第二层类型应为master"
    print("✓ 第二层验证通过")
    
    # 验证第三层
    third_layer_count = sum(len(grandchild.children) for grandchild in result.children)
    assert third_layer_count == 4, "应有4个第三层子结果(1080p有2个,720p有1个,480p有1个)"
    for grandchild in result.children:
        for gg_child in grandchild.children:
            assert gg_child.type == 'media', "第三层类型应为media"
            assert gg_child.is_vod == True, "第三层应为VOD"
    print("✓ 第三层验证通过")
    
    # 验证TS片段
    ts_counts = []
    for grandchild in result.children:
        for gg_child in grandchild.children:
            ts_counts.append(len(gg_child.ts_list))
    
    print(f"✓ 第三层TS片段数量: {ts_counts}")
    assert ts_counts == [5, 3, 2, 2], "各流TS片段数量应为5,3,2,2"
    
    print("\n" + "=" * 60)
    print("所有测试通过!")
    print("=" * 60)

async def main1():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'res_data')
    client = M3u8TestClient(data_dir)
    res = await client.parse("第一层_master.m3u8")
    # while res.type == 'master':
    #     children = res.children[0]
    #     stream = res.streams[0]
    #     print(children)
    #     print(stream)
    #     res = children
    # print("\n" + "=" * 60)
    # ts = res.ts_list
    # print(ts)
    # print()
    res = client.download_stream(res)
    print(res)
    # for i in res.children:
    #     print(i)
    #     for j in i.children:
    #         print(j)


if __name__ == '__main__':
    asyncio.run(main1())
