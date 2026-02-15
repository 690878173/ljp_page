import json
from Xs.xs import Xs_UI
from ljp_page.request import Html

class YY(Xs_UI):
    def parse_p1(self,res_html,url):
        html = Html.str_to_html(res_html)
        li = html.xpath('//div[@class="bd"]/ul/li/div/a/@href')
        return li,None


    def parse_p2(self,res_html,url:str):
        html = Html.str_to_html(res_html)

        title = html.xpath('//div[@class="right"]/h1/text()')[0]
        author = html.xpath('//div[@class="right"]/p//text()')[0]
        author = Html.strip(author)
        dres = '\n'.join(html.xpath('//div[@class="mod book-intro"]/div/text()'))
        li = html.xpath('//div[@class="mod block update chapter-list"]//ul')[1].xpath('.//li/a/@href')
        ls = [('',f'{self.config.base_url}{i}') for i in li]
        next_url = self.config.base_url+html.xpath('//a[@class="nextPage"]/@href')[0]
        if next_url == url:
            next_url = None

        return title,author,dres,ls,next_url

    def parse_p3(self,res_html,url) ->tuple[str,str,str|None]:
        html = Html.str_to_html(res_html)
        title = html.xpath('//h1[@class="page-title"]/text()')[0]
        content1 = html.xpath('//div[@class="page-content font-large"]//text()')
        content = Html.ls_strip(content1)
        ls = html.xpath('//center[@class="chapterPages"]/a[@class="curr"]/following-sibling::*[1][name()="a"]/@href')
        if ls:
            a = ls[0]
            if a.startswith('/'):
                next_url = self.config.base_url+ls[0]
            else:
                next_url = '/'.join(url.split('/')[:-1]) + '/'+a
        else:
            next_url = None
        return title,content,next_url



if __name__ == '__main__':
    cookies = {
        'cf_clearance': 'aEUObqkhStGMyt41kZ4xvaS8wOpvsDGWummuVRk.hYI-1768928693-1.2.1.1-B2Z5bOIW9.flddQKMwZzx5SGVsIhjDmuTeFSabDJdswEwyM0LVuQoFJ.CN8ghsaUAxMe781jqds4yCTnXxtdcAgB7trj1oqjtZWGvudlUG1gH26tZUjp2gv6zaGA4qoQd6fg7EjpUkO0dr7okxUiuAP.jFT3LIHHbgBI7G8vQp8yeJ6Ysr.CdPGgcepiavrBiAjug1fKTjMKjWIL7OXNNIzmwTDw7XUQ8iWUOZDFOsANMS._7RuLWp1555n2rRta',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'if-modified-since': 'Mon, 19 Jan 2026 17:35:16 GMT',
        'origin': 'https://www.bz777777.net',
        'priority': 'u=0, i',
        'referer': 'https://www.bz777777.net/7/7943/?__cf_chl_tk=XLSRNRxKY.or_hwIyCxVbLJL0i6d3Y5ka82AQqRPWNo-1768846119-1.0.1.1-Z.HJ4omn1_FvquVxTQ._E1KKm0sioKWLrNw9FjdweDU',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version': '"144.0.3719.82"',
        'sec-ch-ua-full-version-list': '"Not(A:Brand";v="8.0.0.0", "Chromium";v="144.0.7559.60", "Microsoft Edge";v="144.0.3719.82"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"15.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0',
        # 'cookie': 'cf_clearance=MymIAXMOMWmWJvpWnuF9piXzfYxfIEfOFO8RP8qIqaM-1768846130-1.2.1.1-nGy1BsLagrMntqsr9u51EkcaHFqBh6PJttYzdhckW3Lou4rpmtyK3ftFA5wLEiTyRkFlQBJ8JlDklnmxj7kUVMiN0TeoVPGfcUl2CCbkkyVTE9i7f0DQEsgzdPxWSvlbe7VR2f35x41Y2tz46LtSNXOiG8qKE1uSgwbxckvnZm0ox.VmB.0li5.QlqbbcxzjjDjlPRHfEFWyscevCl6JsNEy_XUDJTUT8riSAzrvTlF3ldbV.Is1nf3rNmYzbqtD',
    }
    config = YY.Config(
        base_url=r'https://www.bz777777.net',
        p1_url=r'https://www.bz777777.net/shuku/6-size-0-{}.html',
        p2_url=r'https://www.bz777777.net{}',
        mode='mode2',
        headers=headers,
        cookies=cookies,
        save_path=r'E:/爬虫/test',
        start_id=9,
        end_id=30,
        max_workers=5,
        max_retries=5,
    )
    # from ljp_page.logger import Logger
    # logger = Logger(log_level='DEBUG')
    xs = YY(config)
    UI = xs.UI(xs)
    UI.run()
