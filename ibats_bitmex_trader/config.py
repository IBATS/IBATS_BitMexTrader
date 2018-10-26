# -*- coding: utf-8 -*-
"""
Created on 2017/6/9
@author: MG
"""
import logging
from ibats_common.config import ConfigBase as ConBase
from ibats_common.common import ExchangeName

logger = logging.getLogger()


class ConfigBase(ConBase):
    # 交易所名称
    MARKET_NAME = ExchangeName.BitMex.name

    # api configuration
    # https://testnet.bitmex.com/app/apiKeys
    TEST_NET = True
    EXCHANGE_PUBLIC_KEY = "kRGATSGD9QRhSRvY0Ih58t5z"
    EXCHANGE_SECRET_KEY = "tYJwFJeFe5SxzWETFEvoI_HxDaUbtF2fCNwxXd8SZyPNL-1J"

    # mysql db info
    DB_SCHEMA_MD = 'md_bitmex'
    DB_URL_DIC = {
        DB_SCHEMA_MD: 'mysql://mg:****@localhost/' + DB_SCHEMA_MD,
        ConBase.DB_SCHEMA_IBATS: 'mysql://mg:****@localhost/' + ConBase.DB_SCHEMA_IBATS,
    }

    # redis info
    REDIS_INFO_DIC = {'REDIS_HOST': 'localhost',
                      'REDIS_PORT': '6379',
                      }

    # 每一次实务均产生数据库插入或更新动作（默认：否）
    UPDATE_OR_INSERT_PER_ACTION = False


config = ConfigBase()


def update_config(config_new: ConfigBase):
    global config
    config = config_new
    logger.info('更新默认配置信息 %s < %s', ConfigBase, config_new.__class__)
