from dataclasses import fields


class From_dic:
    @classmethod
    def from_dict(cls, data):
        fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in fields}
        return cls(**filtered)

    def update(self, **kwargs) -> None:
        """动态更新字段"""
        class_fields = {f.name for f in fields(self)}
        for k, v in kwargs.items():
            if k in class_fields:
                setattr(self, k, v)