#!/usr/bin/env python3
"""大A祖训 · 构建脚本
用法：
  python3 build.py            # 仅用本地 data.json 生成 index.html
  python3 build.py --fetch    # 先从东财拉取最新日K（全量 2016-11-24 至今），再生成
"""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_JSON = os.path.join(HERE, 'data.json')
TEMPLATE = os.path.join(HERE, 'template.html')
OUT = os.path.join(HERE, 'index.html')

INDICES = {
    '000001': ('1.000001', '上证指数'),
    '399001': ('0.399001', '深圳成指'),
    '399006': ('0.399006', '创业板指'),
    '000688': ('1.000688', '科创50'),
    '000300': ('1.000300', '沪深300'),
    '000905': ('1.000905', '中证500'),
    '000852': ('1.000852', '中证1000'),
}

def fetch_all():
    data = {'meta': {'source': 'Eastmoney daily K-line', 'updated': '', 'indices': {}}}
    latest = ''
    for code, (secid, name) in INDICES.items():
        url = ('https://push2his.eastmoney.com/api/qt/stock/kline/get'
               f'?secid={secid}&klt=101&fqt=1&beg=20161124&end=29991231'
               '&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55,f56,f57,f58')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.load(resp)
        kl = d.get('data', {}).get('klines', [])
        bars = []
        for s in kl:
            p = s.split(',')
            bars.append([int(p[0].replace('-', '')), round(float(p[1]), 2),
                         round(float(p[3]), 2), round(float(p[4]), 2), round(float(p[2]), 2)])
        bars.sort(key=lambda b: b[0])
        data['meta']['indices'][code] = name
        data[code] = bars
        if bars:
            last = f"{str(bars[-1][0])[:4]}-{str(bars[-1][0])[4:6]}-{str(bars[-1][0])[6:]}"
            latest = max(latest, last)
        print(code, name, 'bars:', len(bars), 'last:', bars[-1][0] if bars else None)
    data['meta']['updated'] = latest
    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print('wrote', DATA_JSON, os.path.getsize(DATA_JSON), 'bytes; updated =', latest)
    return data

def build(data):
    with open(TEMPLATE, 'r', encoding='utf-8') as f:
        tpl = f.read()
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    html = tpl.replace('__DATA_JSON__', payload, 1)
    assert '__DATA_JSON__' not in html, 'template placeholder not replaced'
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print('wrote', OUT, os.path.getsize(OUT), 'bytes')

if __name__ == '__main__':
    if '--fetch' in sys.argv:
        data = fetch_all()
    else:
        with open(DATA_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print('loaded', DATA_JSON, 'updated =', data.get('meta', {}).get('updated'))
    build(data)
