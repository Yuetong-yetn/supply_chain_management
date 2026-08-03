"""核心基础层 — app 内的基础设施。

提供 config / database / auth / response / exceptions / event 等模块的统一入口。
这些模块复用 kernel.common 下的实现（不重复，仅转发），
保证 engine、SessionLocal、get_settings 等单例唯一。
"""
