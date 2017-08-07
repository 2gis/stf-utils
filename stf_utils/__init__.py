# -*- coding: utf-8 -*-
import logging


def init_console_logging(level):
    logging.basicConfig(level=getattr(logging, level.upper()))
