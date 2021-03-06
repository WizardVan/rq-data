import re
import socket
import zlib
import struct
from pymongo import MongoClient
import pymongo
import datetime
from rpc.rpc import RpcClient

freq_int = {
    '1m': 1,
    '5m': 2,
    '10m': 3,
    '15m': 4,
    '30m': 5,
    '60m': 6,
    '1d': 7
}


###公司mysql数据库格式
def get_future_price1(code, start_date, end_date, frequency):
    df = get_price(code.upper(), start_date=start_date, end_date=end_date, frequency=frequency)
    df['dateInt'] = [int(i.strftime("%Y%m%d")) for i in df.index]
    df['timeInt'] = [int(i.strftime("%H%M%S")) for i in df.index]
    df['realDate'] = range(df.shape[0])
    df['vol'] = df['volume']
    df['openInt'] = df['open_interest']
    df['contract'] = re.match('[a-zA-Z]+', code).group()
    df['cycle'] = freq_int[frequency]
    del df['total_turnover']
    del df['volume']
    del df['trading_date']
    del df['limit_up']
    del df['limit_down']
    del df['basis_spread']
    del df['open_interest']
    return df


###vnpy回测mongodb格式
def get_future_price2(code, start_date, end_date, frequency):
    contract = code + '0000'
    df = get_price(code.upper() + '88', start_date=start_date, end_date=end_date, frequency=frequency,
                   adjust_type='post')
    df['vtSymbol'] = contract
    df['symbol'] = contract
    df['date'] = [int(i.strftime("%Y%m%d")) for i in df.index]
    df['time'] = [int(i.strftime("%H%M%S")) for i in df.index]
    df['datetime'] = df.index
    df['openInterest'] = df.open_interest

    del df['total_turnover']
    del df['trading_date']
    del df['limit_up']
    del df['limit_down']
    del df['basis_spread']
    del df['open_interest']
    return df


###插入到vnpy回测数据库中
def insert_mongo2(client, code, frequency):
    start_date = client.latest_date(code + '0000', type='future')
    if not start_date:
        start_date = '20100104'
        print(code, "no begin_date, set default: 20100104")

    else:
        print("\r{}, start date: {}".format(code, start_date), end='')
    start_date = datetime.datetime.strptime(str(start_date), "%Y%m%d") + datetime.timedelta(1)

    end_date = datetime.datetime.now().date()
    if start_date.date() > end_date:
        return
    df = get_future_price2(code, start_date, end_date, frequency)
    if df.empty:
        return
    client.insert(code + '0000', df.to_dict('record'), type="future")


codes = ["IC", "IF", "IH", "T", "TF", "CF", "FG", "MA", "OI", "RM", "SR",
         "TA", "ZC", "a", "c", "i", "j", "jd", "jm", "l", "m", "p", "pp",
         "v", "y", "ag", "al", "au", "bu", "cu", "hc", "ni", "pb", "rb",
         "ru", "sn", "zn"]

code = 'rb'
frequency = '1m'
host = "carniejq.cn"
port = 31245
client = RpcClient(host, port)
# insert_mongo2(client,code,frequency)
for code in codes:
    insert_mongo2(client, code, frequency)
print("\rfinished, stoping", end='')
client.stop_all()