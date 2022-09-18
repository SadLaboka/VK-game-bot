import enum


class BaseEnum(enum.Enum):
    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))


class CommandKind(BaseEnum):

    START = "start"
    JOIN = "join"
    FINISH = "finish"
    SHOW_INFO = "show_info"
    CHOICE = "choice"
    ANSWER = "answer"


class SessionStatusKind(BaseEnum):

    ACTIVE = "Active"
    FINISHED = "Finished"
    INTERRUPTED = "Interrupted"
    PREPARED = "Prepared"
