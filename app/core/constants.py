from enum import Enum

email_regex = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,4})+$"

class Environment(str, Enum):
    development = "development"
    production = "production"

class Role(str, Enum):
    admin = "admin"
    user = "user"

class Modules(str, Enum):
    auth = "auth"

class AppLogType(str, Enum):
    add = "add"
    update = "update"
    delete = "delete"
    login = "login"

class WsResponseMsgType(str, Enum):
    notification = "notification"

class WsStatusType(str, Enum):
    success = "success"
    failed = "failed"


class NotificationType(str, Enum):
    error = "error"
    success = "success"
