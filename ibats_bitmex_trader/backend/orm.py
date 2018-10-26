#! /usr/bin/env python
# -*- coding:utf-8 -*-
"""
@author  : MG
@Time    : 2018/6/12 13:02
@File    : orm.py
@contact : mmmaaaggg@163.com
@desc    :
"""
from sqlalchemy import Column, Integer, String, UniqueConstraint, TIMESTAMP
from sqlalchemy.dialects.mysql import DOUBLE
from sqlalchemy.ext.declarative import declarative_base
from ibats_common.utils.db import with_db_session
from ibats_bitmex_trader.backend import engine_md
from ibats_bitmex_trader.config import config
import logging
logger = logging.getLogger()
BaseModel = declarative_base()


def init(alter_table=False):
    BaseModel.metadata.create_all(engine_md)
    if alter_table:
        pass

    logger.info("所有表结构建立完成")


if __name__ == "__main__":
    init()
