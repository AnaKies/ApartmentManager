from enum import Enum


class CrudState(Enum):
    """
    CRUD states that can be required by the user in his question.
    """
    SHOW = 1
    UPDATE = 2
    DELETE = 3
    CREATE = 4
    NONE = 5

class ConversationState():
    def __init__(self):
        self.state = CrudState.NONE

    def set_state(self, state: CrudState):
        self.state = state

    def reset(self):
        self.state = CrudState.NONE

    @property
    def is_create(self) -> bool:
        return self.state is CrudState.CREATE

    @property
    def is_update(self) -> bool:
        return self.state is CrudState.UPDATE

    @property
    def is_delete(self) -> bool:
        return self.state is CrudState.DELETE

    @property
    def is_show(self) -> bool:
        return self.state is CrudState.SHOW

    @property
    def is_none(self) -> bool:
        return self.state is CrudState.NONE