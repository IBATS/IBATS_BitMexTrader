# -*- coding: utf-8 -*-
"""
Created on 2017/10/3
@author: MG
"""
import logging
from collections import OrderedDict
from datetime import datetime, timedelta, date
from ibats_bitmex_trader.config import config
from ibats_common.utils.db import with_db_session, get_db_session
from ibats_common.backend import engines
from ibats_common.common import Direction, Action, BacktestTradeMode, PositionDateType, RunMode, ExchangeName
from ibats_common.trade import TraderAgentBase, trader_agent, BacktestTraderAgentBase
from ibats_bitmex_feeder.backend import engine_md
from ibats_bitmex_feeder.backend.other_tables import instrument_info_table
from bitmex import bitmex
from collections import defaultdict
from enum import Enum
import math

engine_ibats = engines.engine_ibats
logger = logging.getLogger()


class OrderType(Enum):
    """
    buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖, buy-ioc：IOC买单, sell-ioc：IOC卖单
    """
    buy_market = 'buy-market'
    sell_market = 'sell-market'
    buy_limit = 'buy-limit'
    sell_limit = 'sell-limit'
    buy_ioc = 'buy-ioc'
    sell_ioc = 'sell-ioc'


@trader_agent(RunMode.Backtest, ExchangeName.BitMex, is_default=False)
class BacktestTraderAgent(BacktestTraderAgentBase):
    """
    供调用模拟交易接口使用
    """

    def __init__(self, stg_run_id, **kwargs):
        super().__init__(stg_run_id, **kwargs)


@trader_agent(RunMode.Realtime, ExchangeName.BitMex, is_default=False)
class RealTimeTraderAgent(TraderAgentBase):
    """
    供调用实时交易接口使用
    """

    def __init__(self, stg_run_id, **run_mode_params):
        super().__init__(stg_run_id, **run_mode_params)
        self.trader_api = bitmex(test=config.TEST_NET,
                                 api_key=config.EXCHANGE_PUBLIC_KEY, api_secret=config.EXCHANGE_SECRET_KEY)
        self.currency_balance_dic = {}
        self.currency_balance_last_get_datetime = None
        self.symbol_currency_dic = None
        self.symbol_precision_dic = None
        self._datetime_last_rtn_trade_dic = {}
        self._datetime_last_update_position_dic = {}

    def connect(self):
        if instrument_info_table is None:
            raise EnvironmentError("instrument_info_table 为 None，请先加载 dynamic_load_table_model 再重新 import")
        with with_db_session(engine_md) as session:
            data = session.query(
                instrument_info_table.columns['symbol'],
                instrument_info_table.columns['underlying'],
                instrument_info_table.columns['tickSize'],
            ).filter(instrument_info_table.c.state == 'open').all()
            self.symbol_currency_dic = {
                row[0]: row[1]
                for row in data}
            self.symbol_precision_dic = {
                # row[0]: (int(sym.price_precision), int(sym.amount_precision))
                row[0]: row[2]
                for row in data}

    # @try_n_times(times=3, sleep_time=2, logger=logger)
    def open_long(self, symbol, price, vol):
        """买入多头"""
        # 0.5 XBTUSD 100 XBTJPY 最小价格变动单位
        price_precision, amount_precision = self.symbol_precision_dic[symbol], 1
        if isinstance(price, float):
            # 剔除价格后面的尾数
            price = price - price % price_precision
        if isinstance(vol, float):
            if vol < 1:
                logger.warning('%s open_long 订单量 %f 太小，忽略', symbol, vol)
                return
            vol = math.ceil(vol)
        result, _ = self.trader_api.Order.Order_new(symbol=symbol, side='Buy', orderQty=vol, price=price).result()
        self._datetime_last_rtn_trade_dic[symbol] = datetime.now()

    def close_long(self, symbol, price, vol):
        """卖出多头"""
        price_precision, amount_precision = self.symbol_precision_dic[symbol], 1
        if isinstance(price, float):
            # 剔除价格后面的尾数
            price = price - price % price_precision
        if isinstance(vol, float):
            if vol < 1:
                logger.warning('%s open_long 订单量 %f 太小，忽略', symbol, vol)
                return
            vol = math.ceil(vol)
        result, _ = self.trader_api.Order.Order_new(symbol=symbol, side='Sell', orderQty=vol, price=price).result()
        self._datetime_last_rtn_trade_dic[symbol] = datetime.now()

    def open_short(self, symbol, price, vol):
        """开空单"""
        price_precision, amount_precision = self.symbol_precision_dic[symbol], 1
        if isinstance(price, float):
            # 剔除价格后面的尾数
            price = price - price % price_precision
        if isinstance(vol, float):
            if vol < 1:
                logger.warning('%s open_long 订单量 %f 太小，忽略', symbol, vol)
                return
            vol = math.ceil(vol)
        result, _ = self.trader_api.Order.Order_new(symbol=symbol, side='Sell', orderQty=vol, price=price).result()
        self._datetime_last_rtn_trade_dic[symbol] = datetime.now()

    def close_short(self, symbol, price, vol):
        """平空单"""
        price_precision, amount_precision = self.symbol_precision_dic[symbol], 1
        if isinstance(price, float):
            # 剔除价格后面的尾数
            price = price - price % price_precision
        if isinstance(vol, float):
            if vol < 1:
                logger.warning('%s open_long 订单量 %f 太小，忽略', symbol, vol)
                return
            vol = math.ceil(vol)
        result, _ = self.trader_api.Order.Order_new(symbol=symbol, side='Buy', orderQty=vol, price=price).result()
        self._datetime_last_rtn_trade_dic[symbol] = datetime.now()

    def get_position(self, symbol, force_refresh=False) -> dict:
        """
        symbol（相当于 symbol )
        symbol ethusdt, btcusdt
        currency eth, btc
        :param symbol:
        :param force_refresh:
        :return:
        """
        currency = self.get_currency(symbol)
        # self.logger.debug('symbol:%s force_refresh=%s', symbol, force_refresh)
        position_date_inv_pos_dic = self.get_balance(currency=currency, force_refresh=force_refresh)
        return position_date_inv_pos_dic

    def get_currency(self, symbol):
        """
        根据 symbol 找到对应的 currency
        symbol: ethusdt, btcusdt
        currency: eth, btc
        :param symbol:
        :return:
        """
        return self.symbol_currency_dic[symbol]

    def get_balance(self, non_zero_only=False, trade_type_only=True, currency=None, force_refresh=False):
        """
        调用接口 查询 各个币种仓位
        :param non_zero_only: 只保留非零币种
        :param trade_type_only: 只保留 trade 类型币种，frozen 类型的不保存
        :param currency: 只返回制定币种 usdt eth 等
        :param force_refresh: 强制刷新，默认没30秒允许重新查询一次
        :return: {'usdt': {<PositionDateType.History: 2>: {'currency': 'usdt', 'type': 'trade', 'balance': 144.09238}}}
        """
        if force_refresh or self.currency_balance_last_get_datetime is None or \
                self.currency_balance_last_get_datetime < datetime.now() - timedelta(seconds=30):
            # trader_api.Position.Position_get
            # result, _ = self.trader_api.Position.Position_get().result()
            result, _ = self.trader_api.User.User_getWallet().result()
            self.logger.debug('更新持仓数据： %d 条', len(result))
            acc_balance_new_dic = defaultdict(dict)
            for data_dic in result:
                currency_curr = data_dic['currency']
                self._datetime_last_update_position_dic[currency_curr] = datetime.now()

                if non_zero_only and data_dic['amount'] == '0':
                    continue

                data_dic['amount'] = float(data_dic['amount'])
                # self.logger.debug(data_dic)
                if PositionDateType.History in acc_balance_new_dic[currency_curr]:
                    balance_dic_old = acc_balance_new_dic[currency_curr][PositionDateType.History]
                    balance_dic_old['balance'] += data_dic['balance']
                    # TODO: 日后可以考虑将 PositionDateType.History 替换为 type
                    acc_balance_new_dic[currency_curr][PositionDateType.History] = data_dic
                else:
                    acc_balance_new_dic[currency_curr] = {PositionDateType.History: data_dic}

            self.currency_balance_dic = acc_balance_new_dic
            self.currency_balance_last_get_datetime = datetime.now()

        if currency is not None:
            if currency in self.currency_balance_dic:
                ret_data = self.currency_balance_dic[currency]
                # for position_date_type, data in self.currency_balance_dic[currency].items():
                #     if data['currency'] == currency:
                #         ret_data = data
                #         break
            else:
                ret_data = None
        else:
            ret_data = self.currency_balance_dic
        return ret_data

    @property
    def datetime_last_update_position(self) -> datetime:
        return self.currency_balance_last_get_datetime

    @property
    def datetime_last_rtn_trade_dic(self) -> dict:
        return self._datetime_last_rtn_trade_dic

    @property
    def datetime_last_update_position_dic(self) -> dict:
        return self._datetime_last_update_position_dic

    @property
    def datetime_last_send_order_dic(self) -> dict:
        raise NotImplementedError()

    def get_order(self, symbol, states='submitted') -> list:
        """

        :param symbol:
        :param states:
        :return: 格式如下：
        [{'id': 603164274, 'symbol': 'ethusdt', 'account-id': 909325, 'amount': '4.134700000000000000',
'price': '983.150000000000000000', 'created-at': 1515166787246, 'type': 'buy-limit',
'field-amount': '4.134700000000000000', 'field-cash-amount': '4065.030305000000000000',
'field-fees': '0.008269400000000000', 'finished-at': 1515166795669, 'source': 'web',
'state': 'filled', 'canceled-at': 0},
 ... ]
        """
        symbol = symbol
        ret_data = self.trader_api.get_orders_info(symbol=symbol, states=states)
        return ret_data['data']

    def cancel_order(self, symbol):
        symbol = symbol
        order_list = self.get_order(symbol)
        order_id_list = [data['id'] for data in order_list]
        return self.trader_api.batchcancel_order(order_id_list)

    def release(self):
        pass


def _test_only():
    # 测试交易 下单接口及撤单接口
    # symbol, vol, price = 'ocnusdt', 1, 0.00004611  # OCN/USDT
    symbol, vol, price = 'eosusdt', 1.0251, 4.1234  # OCN/USDT

    td = RealTimeTraderAgent(stg_run_id=1, run_mode_params={})
    td.open_long(symbol=symbol, price=price, vol=vol)
    order_dic_list = td.get_order(symbol=symbol)
    print('after open_long', order_dic_list)
    assert len(order_dic_list) == 1
    td.cancel_order(symbol=symbol)
    time.sleep(1)
    order_dic_list = td.get_order(symbol=symbol)
    print('after cancel', order_dic_list)
    assert len(order_dic_list) == 0


if __name__ == "__main__":
    import time
    _test_only()
