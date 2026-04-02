from lxml import etree
from typing import Any
class Html:
    """Small HTML helper collection retained for backwards compatibility."""

    @staticmethod
    def html_drop_script(html_content: str) -> str:
        html_content = html_content.replace("<script", "<!-- <script")
        html_content = html_content.replace("</script>", "</script> -->")
        return html_content

    @staticmethod
    def save_file(html_content: str, path: str = "test.html") -> None:
        with open(path, "w", encoding="utf-8") as file_handle:
            file_handle.write(Html.html_drop_script(html_content))

    @staticmethod
    def strip(text: str) -> str:
        return (
            text.strip()
            .replace("\xa0", "")
            .replace("\r", "")
            .replace("\n", "")
            .replace("\t", "")
        )

    @staticmethod
    def ls_strip(values: list[str]) -> str:
        return "\n".join(
            Html.strip(item)
            for item in values
            if item is not None and isinstance(item, str) and Html.strip(item)
        )

    @staticmethod
    def str_to_html(res: str) -> Any:
        return etree.HTML(res)

    @staticmethod
    def drop_xml(html_str: str) -> Any:
        html = html_str.replace('<?xml version="1.0" encoding="UTF-8" ?>', "")
        return Html.str_to_html(html)

    @staticmethod
    def xpath_ls(html: Any, xpath: str) -> str:
        return "\n".join(html.xpath(xpath))

