#!/usr/bin/env python2.7
# coding=utf-8

import sys
import re
import time
import random
import httplib
import traceback
import StringIO
import gzip
import subprocess

rd = random.Random()


class Stock(object):
    decimal_digit = 2

    name = None
    detail_url = None
    time = None
    date = None
    # 显示价格
    show_price = None
    # 升跌百分比
    change_percent = None
    # 买价
    buy_price = None
    # 卖价
    sell_price = None
    # 最高价
    highest_price = None
    # 最低价
    lowest_price = None
    # 今天开盘价
    open_price = None
    # 昨天收盘价
    close_price = None
    # 持仓量
    open_interest = None
    # 买量
    buy_quantity = None
    # 卖量
    sell_quantity = None
    # 交易量
    trade_volume = None

    def display_format(self, rename=None, href=True):
        return '%s %s %s %s %.2f%% | color=%s %s' % (
            '▲' if self.change_percent > 0 else '▼' if self.change_percent < 0 else '◆',
            rename if rename is not None else self.name,
            format(self.show_price, '.%df' % self.decimal_digit),
            format(self.close_price * self.change_percent / 100, '.%df' % self.decimal_digit),
            self.change_percent,
            'red' if self.change_percent > 0 else 'green' if self.change_percent < 0 else 'gray',
            ('href=%s' % self.detail_url) if href else '',
        )

    @staticmethod
    def external_futures_make(f, detail_url):
        # var hq_str_hf_CL="54.05,1.3881,54.05,54.06,54.11,53.09,22:51:58,53.31,53.26,23805,0,0,2019-01-30,纽约原油";
        assert len(f) == 14
        s = Stock()
        s.show_price = float(f[0])
        s.change_percent = float(f[1])
        s.buy_price = float(f[2])
        s.sell_price = float(f[3])
        s.highest_price = float(f[4])
        s.lowest_price = float(f[5])
        s.time = f[6]
        s.open_price = float(f[7])
        s.close_price = float(f[8])
        s.open_interest = int(f[9])
        s.buy_quantity = int(f[10])
        s.sell_quantity = int(f[11])
        s.date = f[12].replace('/', '-')
        s.name = f[13]
        s.detail_url = detail_url
        return s

    @staticmethod
    def internal_futures_make(f, detail_url):
        # var hq_str_nf_AU0="黄金连续,235835,287.00,287.00,286.40,287.55,286.65,286.70,286.65,286.69,287.25,95,35,305306,58532,沪,黄金,2019-01-30,0,287.950,282.650,287.950,282.300,291.600,282.300,291.600,274.550,1.693";
        assert len(f) > 16
        s = Stock()
        s.name = f[0]
        s.time = re.sub(r"(\d{2})(\d{2})(\d{2})", r"\1:\2:\3", f[1])
        s.open_price = float(f[2])
        s.highest_price = float(f[3])
        s.lowest_price = float(f[4])
        # <-- ?
        s.buy_price = float(f[6])
        s.show_price = float(f[7])
        s.sell_price = float(f[8])
        # <-- 动态结算价
        s.close_price = float(f[10])
        s.buy_quantity = int(f[11])
        s.sell_quantity = int(f[12])
        s.trade_volume = int(f[13])
        s.open_interest = int(f[14])
        s.date = f[16].replace('/', '-')

        s.change_percent = (s.show_price - s.close_price) * 100 / s.close_price
        s.detail_url = detail_url
        return s

    @staticmethod
    def cn_stock_make(f, detail_url):
        # var hq_str_sz002155="湖南黄金,8.080,7.970,8.040,8.110,7.910,8.040,8.050,18087276,145144866.670,22670,8.040,116000,8.030,165202,8.020,23900,8.010,64345,8.000,248137,8.050,139702,8.060,122400,8.070,225179,8.080,233200,8.090,2019-01-30,15:00:03,00";
        assert len(f) > 31
        s = Stock()
        s.name = f[0]
        s.open_price = float(f[1])
        s.close_price = float(f[2])
        s.show_price = float(f[3])
        s.highest_price = float(f[4])
        s.lowest_price = float(f[5])
        s.sell_price = float(f[6])
        s.buy_price = float(f[7])
        s.trade_volume = int(f[8])
        # <-- 成交额
        # 买1数量
        # 买1价格
        # 买2数量
        # 买2价格
        # ... 买5
        # 卖1数量
        # 卖1价格
        # ... 卖5
        s.date = f[30].replace('/', '-')
        s.time = f[31]
        s.buy_quantity = int(f[10])  # 买1数量
        s.sell_quantity = int(f[20])  # 卖1数量

        s.change_percent = (s.show_price - s.close_price) * 100 / s.close_price
        s.detail_url = detail_url
        return s

    @staticmethod
    def hk_stock_make(f, detail_url):
        # var hq_str_rt_hk00217="CHINA CHENGTONG,中国诚通发展集团,0.180,0.194,0.194,0.180,0.185,-0.009,-4.639,0.183,0.185,46762.200,250200,37.000,0.000,0.495,0.160,2019/01/30,16:09:30,100|0,N|N|N,0.185|0.000|0.000,0|||0.000|0.000|0.000,|0,N";
        assert len(f) > 19
        s = Stock()
        s.name = f[1]
        s.open_price = float(f[2])
        s.close_price = float(f[3])
        s.highest_price = float(f[4])
        s.lowest_price = float(f[5])
        s.show_price = float(f[6])
        # <--价格浮动增量(涨幅)
        s.change_percent = float(f[8])
        s.sell_price = float(f[9])
        s.buy_price = float(f[10])
        # <--成交额
        s.trade_volume = int(f[12])
        # <--市盈率
        # <-- ?
        # <-- 52周最高
        # <-- 52周最低
        s.date = f[17].replace('/', '-')
        s.time = f[18]
        s.detail_url = detail_url
        return s

    @staticmethod
    def us_stock_make(f, detail_url):
        # var hq_str_gb_amd="AMD,23.0900,19.95,2019-01-31 09:17:52,3.8400,21.4900,23.1300,21.3700,34.1400,9.0400,211421150,93051235,23066910000,0.36,64.14,0.00,0.00,0.00,0.00,999000000,73.00,23.3700,1.21,0.28,Jan 30 08:00PM EST,Jan 30 04:00PM EST,19.2500,3782954.00";
        assert len(f) == 28
        s = Stock()
        s.name = f[0]
        s.show_price = float(f[1])
        s.change_percent = float(f[2])
        (s.date, s.time) = f[3].split(' ')
        # <-- 价格浮动增量（涨幅）
        s.open_price = float(f[5])
        s.highest_price = float(f[6])
        s.lowest_price = float(f[7])
        # <-- 52周最高价
        # <-- 52周最低价
        s.trade_volume = int(f[10])
        # <-- 10日均量
        # <-- 市值
        # <-- 每股收益
        # <-- 市盈率
        # <-- ?
        # <-- ?
        # <-- ?
        # <-- ?
        # <-- 股本
        # <-- ?
        # <-- 盘后价
        # <-- 盘后价格浮动增量（涨幅）
        # <-- 盘后价格浮动增量百分比（涨幅百分比）
        # <-- 盘后价时间(美国时间)
        # <-- 收盘时间(美国时间)
        s.close_price = float(f[26])
        # <-- 盘后成交量
        s.detail_url = detail_url
        return s

    @staticmethod
    def exchange_rate_make(f, detail_url):
        # var hq_str_fx_susdhkd="02:32:00,7.845,7.8451,7.8461,109.9,7.846,7.8461,7.83511,7.845,美元兑港元即期汇率,-0.01,-0.0011,0.001401,Kantonalbank. Zurich,7.8507,7.7915,++-+--++,2019-01-31";
        assert len(f) == 18
        s = Stock()
        s.decimal_digit = 4
        s.time = f[0]
        s.buy_price = float(f[1])
        s.sell_price = float(f[2])
        s.close_price = float(f[3])
        # <-- 波幅
        s.open_price = float(f[5])
        s.highest_price = float(f[6])
        s.lowest_price = float(f[7])
        s.show_price = float(f[8])
        s.name = f[9]
        # <-- ?
        s.change_percent = float(f[11]) * 100 / s.close_price
        # <-- 振幅
        # <-- 报价银行（变化）
        # <-- 52周最高
        # <-- 52周最低
        # <-- ?
        s.date = f[17].replace('/', '-')
        s.detail_url = detail_url
        return s


def fetch(url, headers=None):
    request_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:56.0) Gecko/20100101 Firefox/64.0',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Accept': '*/*',
    }
    if headers is not None:
        request_headers.update(headers)

    common_connection = httplib.HTTPSConnection if url.lower().startswith('https://') else httplib.HTTPConnection
    conn = common_connection(re.search(r'^(?:https?://)?([^/\?#=%]+)', url, re.I).group(1), timeout=3)
    conn.request('GET', re.search(r'^(?:https?://)?(?:[^/\?#=%]+)([^#]*)', url, re.I).group(1) or '/', headers=request_headers)

    resp = conn.getresponse()
    status_code = resp.status
    if status_code < 400:
        raw_data = resp.read()

        if 'gzip' in resp.getheader('content-encoding', '').lower():
            gz = gzip.GzipFile(fileobj=StringIO.StringIO(raw_data))
            raw_data = gz.read()
            gz.close()

        conn.close()
        return status_code, raw_data
    else:
        return status_code, None


external_futures_check_code = {
    'NID': '伦镍',
    'PBD': '伦铅',
    'SND': '伦锡',
    'ZSD': '伦锌',
    'AHD': '伦铝',
    'CAD': '伦铜',
    'S': '美国大豆',
    'W': '美国小麦',
    'C': '美国玉米',
    'BO': '美黄豆油',
    'SM': '美黄豆粉',
    'TRB': '日本橡胶',
    'HG': '美铜',
    'NG': '美国天然气',
    'CL': '纽约原油',
    'SI': '纽约白银',
    'GC': '纽约黄金',
    'LHC': '美瘦猪肉',
    'OIL': '布伦特原油',
    'XAU': '伦敦金',
    'XAG': '伦敦银',
    'XPT': '伦敦铂金',
    'ES': '标普期货',
    'DXF': '美元指数期货',
    'SF': '瑞郎期货',
    'CD': '加元期货',
    'JY': '日元期货',
    'BP': '英镑期货',
    'EC': '欧元期货',
}


def external_futures(page_stock_code):
    if page_stock_code not in external_futures_check_code:
        raise ValueError('Unknown stock code.')
    
    url = 'https://hq.sinajs.cn/etag.php?_=%d&list=hf_%s' % (int(time.time() * 1000), page_stock_code)
    #url = 'https://hq.sinajs.cn/?_=%f&list=hf_%s' % (rd.random(), page_stock_code)
    detail_url = 'https://finance.sina.com.cn/futures/quotes/%s.shtml' % page_stock_code
    (status_code, data) = fetch(url, {'Referer': detail_url})
    if status_code < 400 and data is not None:
        return Stock.external_futures_make(re.sub(r'^var\s+[^=]+="', '', str(data)).rstrip('";\n').split(','), detail_url)


inner_future_check_code = {
    'FU0': '燃油连续',
    'SC0': '原油连续',
    'AL0': '沪铝连续',
    'RU0': '橡胶连续',
    'ZN0': '沪锌连续',
    'CU0': '沪铜连续',
    'AU0': '黄金连续',
    'RB0': '螺纹钢连续',
    'WR0': '线材连续',
    'PB0': '沪铅连续',
    'AG0': '白银连续',
    'BU0': '沥青连续',
    'HC0': '热轧卷板连续',
    'SN0': '沪锡连续',
    'NI0': '沪镍连续',
    'SP0': '纸浆连续',
    'V0': 'PVC连续',
    'P0': '棕榈连续',
    'B0': '豆二连续',
    'M0': '豆粕连续',
    'I0': '铁矿石连续',
    'JD0': '鸡蛋连续',
    'L0': '塑料连续',
    'PP0': 'PP连续',
    'FB0': '纤维板连续',
    'BB0': '胶合板连续',
    'Y0': '豆油连续',
    'C0': '玉米连续',
    'A0': '豆一连续',
    'J0': '焦炭连续',
    'JM0': '焦煤连续',
    'CS0': '玉米淀粉连续',
    'EG0': '乙二醇连续',
    'TA0': 'PTA连续',
    'OI0': '菜油连续',
    'RS0': '菜籽连续',
    'RM0': '菜粕连续',
    'ZC0': '动力煤连续',
    'WH0': '强麦连续',
    'JR0': '粳稻连续',
    'SR0': '白糖连续',
    'CF0': '棉花连续',
    'RI0': '早籼稻连续',
    'MA0': '郑醇连续',
    'FG0': '玻璃连续',
    'LR0': '晚籼稻连续',
    'SF0': '硅铁连续',
    'SM0': '锰硅连续',
    'CY0': '棉纱连续',
    'AP0': '鲜苹果连续',
    'IF0': '期指0',
    'TF0': 'TF0',
    'IH0': 'IH0',
    'IC0': 'IC0',
    'TS0': 'TS0',
}


def inner_future(page_stock_code):
    if page_stock_code not in inner_future_check_code:
        raise ValueError('Unknown stock code.')

    url = 'https://hq.sinajs.cn/etag.php?_=%d&list=%s' % (int(time.time() * 1000), page_stock_code)
    #url = 'https://hq.sinajs.cn/?_=%f&list=%s' % (rd.random(), page_stock_code)
    detail_url = 'https://finance.sina.com.cn/futures/quotes/%s.shtml' % page_stock_code
    (status_code, data) = fetch(url, {'Referer': detail_url})
    if status_code < 400 and data is not None:
        return Stock.internal_futures_make(re.sub(r'^var\s+[^=]+="', '', str(data)).rstrip('";\n').split(','), detail_url)


def cn_stock(page_stock_code):
    if not re.match(r'^(sz|sh)', page_stock_code):
        raise ValueError('Unknown stock code.')

    url = 'https://hq.sinajs.cn/etag.php?_=%d&list=%s' % (int(time.time() * 1000), page_stock_code)
    #url = 'https://hq.sinajs.cn/?_=%f&list=%s' % (rd.random(), page_stock_code)
    detail_url = 'https://finance.sina.com.cn/realstock/company/%s/nc.shtml' % page_stock_code
    (status_code, data) = fetch(url, {'Referer': detail_url})
    if status_code < 400 and data is not None:
        return Stock.cn_stock_make(re.sub(r'^var\s+[^=]+="', '', str(data)).rstrip('";\n').split(','), detail_url)


def hk_stock(page_stock_code):
    # 港股指数形式不定
    # if not re.match(r'^(\d{5}$', page_stock_code):
    #     raise ValueError('Unknown stock code.')

    url = 'https://hq.sinajs.cn/etag.php?_=%d&list=rt_hk%s' % (int(time.time() * 1000), page_stock_code.lower())
    #url = 'https://hq.sinajs.cn/?_=%f&list=rt_hk%s' % (rd.random(), page_stock_code.lower())
    detail_url = 'http://stock.finance.sina.com.cn/hkstock/quotes/%s.html' % page_stock_code
    (status_code, data) = fetch(url, {'Referer': detail_url})
    if status_code < 400 and data is not None:
        return Stock.hk_stock_make(re.sub(r'^var\s+[^=]+="', '', str(data)).rstrip('";\n').split(','), detail_url)


def us_stock(page_stock_code):
    if not re.match(r'^[A-Z0-9]{3,4}$', page_stock_code):
         raise ValueError('Unknown stock code.')

    url = 'https://hq.sinajs.cn/etag.php?_=%d&list=gb_%s' % (int(time.time() * 1000), page_stock_code.lower())
    #url = 'https://hq.sinajs.cn/?_=%f&list=gb_%s' % (rd.random(), page_stock_code.lower())
    detail_url = 'https://stock.finance.sina.com.cn/usstock/quotes/%s.html' % page_stock_code
    (status_code, data) = fetch(url, {'Referer': detail_url})
    if status_code < 400 and data is not None:
        print data
        return Stock.us_stock_make(re.sub(r'^var\s+[^=]+="', '', str(data)).rstrip('";\n').split(','), detail_url)


def exchange_rate_stock(page_stock_code):
    if not re.match(r'^[A-Z]{6}$', page_stock_code):
        raise ValueError('Unknown stock code.')

    url = 'https://hq.sinajs.cn/etag.php?_=%d&list=fx_s%s' % (int(time.time() * 1000), page_stock_code.lower())
    #url = 'https://hq.sinajs.cn/?_=%f&list=fx_s%s' % (rd.random(), page_stock_code.lower())
    detail_url = 'https://finance.sina.com.cn/money/forex/hq/%s.shtml' % page_stock_code
    (status_code, data) = fetch(url, {'Referer': detail_url})
    if status_code < 400 and data is not None:
        return Stock.exchange_rate_make(re.sub(r'^var\s+[^=]+="', '', str(data)).rstrip('";\n').split(','), detail_url)


def display(msg):
    if isinstance(msg, list):
        msg = '\n'.join(msg)

    sys.stdout.write(str(msg))
    sys.stdout.write('\n~~~\n')
    sys.stdout.flush()


def check_bitbar_running(process_id):
    return ('%s BitBar' % process_id) == str(subprocess.Popen(['ps -xco pid=,command= -p %s' % process_id], shell=True, executable='/bin/sh', stdout=subprocess.PIPE, universal_newlines=True).communicate()[0]).strip()


def get_active_display_number():
    return int(str(subprocess.Popen(['ioreg -n IODisplayWrangler | grep IODisplayConnect | grep " active," | wc -l'], shell=True, executable='/bin/sh', stdout=subprocess.PIPE, universal_newlines=True).communicate()[0]).strip())


def get_bitbar_process_id():
    p1 = subprocess.Popen(['ps -axco pid=,command='], shell=True, executable='/bin/sh', stdout=subprocess.PIPE, universal_newlines=True)
    p1.wait()
    p2 = subprocess.Popen(['grep BitBar'], shell=True, executable='/bin/sh', stdout=subprocess.PIPE, stdin=p1.stdout, universal_newlines=True)
    p = str(p2.communicate()[0]).strip().split(' ')
    if len(p) >= 2 and p[0].isdigit():
        return p[0]
    else:
        display('Can not get bitbar process ID! | color=red')
    return None


def get_bitbar_version():
    return str(subprocess.Popen(["""osascript -e 'get version of application "BitBar"'"""], shell=True, executable='/bin/sh', stdout=subprocess.PIPE, universal_newlines=True).communicate()[0])


def restart_bitbar():
    subprocess.Popen(["""osascript -e 'tell application "BitBar" to quit' -e 'delay 3' -e 'tell application "BitBar" to activate' &>/dev/null &"""], shell=True, executable='/bin/sh')


def test():
    print external_futures('CL').display_format()
    # print inner_future('AU0').display_format()
    # print cn_stock('sz300582').display_format()
    # print hk_stock('01810').display_format()
    # print us_stock('AMD').display_format()
    # print exchange_rate_stock('USDCNY').display_format()


def run():
    bitbar_version = get_bitbar_version()
    if not (len(bitbar_version) > 0 and bitbar_version[0].isdigit() and int(bitbar_version[0]) >= 2):
        display('The program only supports Bitbar V2 and later versions.')
        exit(1)

    bitbar_process_id = get_bitbar_process_id()
    active_display_number = get_active_display_number()

    if bitbar_process_id is not None:
        # restart bitbar every day for release memory
        restart_bitbar_time = int(time.time()) + 86400
        check_interval_second = 60
        next_check_time = int(time.time()) + check_interval_second
        which_display = 0
        while True:
            try:
                output = list()
                # (stock, long_display_name, short_display_name)
                stocks = [(external_futures('CL'), 'USOL', 'OL'), (exchange_rate_stock('USDCNY'), 'USDCNY', 'UC')]

                output.append(stocks[which_display][0].display_format(stocks[which_display][2], href=False))
                # 状态栏轮流切换模式显示stocks
                # which_display = (which_display + 1) % len(stocks)
                # 状态栏固定模式显示某个stocks
                which_display = 0

                output.append('---')
                for s in stocks:
                    output.append(s[0].display_format(s[1]))

                # output.append(inner_future('AU0').display_format('CNAU'))
                # output.append(inner_future('AG0').display_format('CNAG'))

                # output.append('pid: %s | color=blue' % bitbar_process_id)

                display(output)
                time.sleep(3)
            except Exception:
                output = list()
                output.append('Runtime error! | color=red')
                output.append('---')

                c = StringIO.StringIO()
                traceback.print_exc(file=c)
                c.seek(0)
                output.append(c.read())
                c.close()

                display(output)
                # don't know what's error cause, sleep more long
                time.sleep(10)

            t = int(time.time())
            if t > next_check_time:
                next_check_time = t + check_interval_second

                if t > restart_bitbar_time or get_active_display_number() != active_display_number:
                    restart_bitbar()
                    # after restart bitbar, exit program
                    exit(0)
                elif not check_bitbar_running(bitbar_process_id):
                    # if bitbar not running, exit program
                    exit(0)


if __name__ == '__main__':
    # test()
    run()
