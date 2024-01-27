import os
from datetime import date
import hashlib
from dotenv import load_dotenv
from supabase import create_client, Client
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def create_document(data):
    result = supabase.table('stock_data')\
        .select('*')\
        .eq('hash', data['hash'])\
        .execute().data
    if len(result) > 0:
        print("document found")
        return 1
    else:
        print("inserting document")
    d, count = supabase.table("stock_data").insert(data).execute()
    return 0
# todo 
def get_documents():
    docs = supabase.table("stock_data").select("*").order("date", desc=True).execute()
    return docs
def clean_and_convert(value):
    # Remove unwanted characters (like commas) and convert to the appropriate data type
    cleaned_value = value.replace(',', '').replace('(', '').replace(')', '') if isinstance(value, str) else value
    return int(cleaned_value) if isinstance(cleaned_value, int) else float(cleaned_value)

def generate_dict(date, instrument, bid_qty, bid_price, ask_price, ask_qty, last_trade_price, net_change,
                  closing_price, total_turnover, average_price, last_traded_size, week_52_high, week_52_low,
                  opening_price, change, previous_closing_price, total_trades, trade_volume, foreign_buys,
                  foreign_sells):
    md5_hash = hashlib.md5(f"{instrument}{str(date)}".encode()).hexdigest()
    stock_data_dict = {
        "hash": md5_hash,
        'date': date,
        'instrument': instrument,
        'bid_qty': clean_and_convert(bid_qty),
        'bid_price': clean_and_convert(bid_price),
        'ask_price': clean_and_convert(ask_price),
        'ask_qty': clean_and_convert(ask_qty),
        'last_trade_price': clean_and_convert(last_trade_price),
        'net_change': clean_and_convert(net_change),
        'closing_price': clean_and_convert(closing_price),
        'total_turnover': clean_and_convert(total_turnover),
        'average_price': clean_and_convert(average_price),
        'last_traded_size': clean_and_convert(last_traded_size),
        'week_52_high': clean_and_convert(week_52_high),
        'week_52_low': clean_and_convert(week_52_low),
        'opening_price': clean_and_convert(opening_price),
        'change': clean_and_convert(change),
        'previous_closing_price': clean_and_convert(previous_closing_price),
        'total_trades': clean_and_convert(total_trades),
        'trade_volume': clean_and_convert(trade_volume),
        'foreign_buys': clean_and_convert(foreign_buys),
        'foreign_sells': clean_and_convert(foreign_sells),
    }
    return stock_data_dict


