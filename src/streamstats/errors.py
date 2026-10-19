# Общая ошибка программы.
class StreamStatsError(Exception):
    pass


class FormatError(StreamStatsError):
    pass


class EventError(StreamStatsError):
    pass


class TimeError(StreamStatsError):
    pass


class ConfigError(StreamStatsError):
    pass
