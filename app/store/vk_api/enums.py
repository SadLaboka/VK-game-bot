import enum


class CommandKind(enum.Enum):

    START = "start"
    JOIN = "join"
    FINISH = "finish"
    SHOW_INFO = "show_info"

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))


class SessionStatusKind(enum.Enum):

    ACTIVE = "Active"
    FINISHED = "Finished"
    INTERRUPTED = "Interrupted"
    PREPARED = "Prepared"

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))
