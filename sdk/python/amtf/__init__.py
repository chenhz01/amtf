# -*- coding: utf-8 -*-
"""AMTF Python SDK — 零第三方依赖（纯标准库），冷启动友好。
真相源：../spec/SPEC.md；本包任何行为与 spec 冲突以 spec 为准并视为 bug。"""
from .types import VERSION, REQUIRED, ZmfMemory
from .validate import validate, validate_file
from .migrate import migrate, migrate_file

__version__ = "0.1.0"
__all__ = ["VERSION", "REQUIRED", "ZmfMemory", "validate", "validate_file",
           "migrate", "migrate_file", "__version__"]
