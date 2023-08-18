import datetime


class TimeConverter:
    __format: str = "%Y-%m-%dT%H:%M:%SZ"
    __mili_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"

    @staticmethod
    def to_date(time: str) -> datetime.datetime:
        if not time:
            return datetime.datetime.now()
        try:
            return datetime.datetime.strptime(time, TimeConverter.__format)
        except ValueError:
            return datetime.datetime.strptime(time, TimeConverter.__mili_format)
        except Exception as e:
            raise e

    @staticmethod
    def to_str(time: datetime.datetime) -> str:
        if not time:
            return datetime.datetime.now().strftime(TimeConverter.__format)
        try:
            return time.strftime(TimeConverter.__format)
        except ValueError:
            return time.strftime(TimeConverter.__mili_format)
        except Exception as e:
            raise e
