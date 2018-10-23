# -*- coding: utf-8 -*-
"""
Created on 2017/6/9
@author: MG
"""
import logging
from logging.config import dictConfig
from ibats_trader.config import update_config

logger = logging.getLogger()


class ConfigBase:
    # 交易所名称
    MARKET_NAME = '***'

    # api configuration
    EXCHANGE_ACCESS_KEY = ""
    EXCHANGE_SECRET_KEY = ""

    # mysql db info
    DB_SCHEMA_IBATS = 'ibats'
    DB_SCHEMA_MD = 'bc_md'
    DB_URL_DIC = {
        DB_SCHEMA_MD: 'mysql://mg:****@localhost/' + DB_SCHEMA_MD,
        DB_SCHEMA_IBATS: 'mysql://mg:****@localhost/' + DB_SCHEMA_IBATS,
    }

    # redis info
    REDIS_INFO_DIC = {'REDIS_HOST': 'localhost',
                      'REDIS_PORT': '6379',
                      }

    # evn configuration
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(filename)s.%(funcName)s:%(lineno)d|%(message)s'

    # 每一次实务均产生数据库插入或更新动作（默认：否）
    UPDATE_OR_INSERT_PER_ACTION = False

    # log settings
    logging_config = dict(
        version=1,
        formatters={
            'simple': {
                'format': LOG_FORMAT}
        },
        handlers={
            'file_handler':
                {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': 'logger.log',
                    'maxBytes': 1024 * 1024 * 10,
                    'backupCount': 5,
                    'level': 'DEBUG',
                    'formatter': 'simple',
                    'encoding': 'utf8'
                },
            'console_handler':
                {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',
                    'formatter': 'simple'
                }
        },

        root={
            'handlers': ['console_handler', 'file_handler'],
            'level': logging.DEBUG,
        }
    )
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)
    dictConfig(logging_config)


# 开发配置（SIMNOW MD + Trade）
config = ConfigBase()
# 测试配置（测试行情库）
# Config = ConfigTest()
# 生产配置
# Config = ConfigProduct()

update_config(config)
