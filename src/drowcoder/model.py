from dataclasses import dataclass
from typing import List

from config_morpher import ConfigMorpher


@dataclass(frozen=True)
class ModelRoleType:
    chatcompletions :str = 'chatcompletions'
    postcompletions :str = 'postcompletions'


class ModelDispatcher:
    def __init__(self, models:List[dict], morph:bool=True):
        self.models = models
        self.morph =  morph
        self.for_chatcompletions = {'models': []}
        self.for_postcompletions = {'models': []}
        self.dispatch(morph=morph)

    def dispatch(self, morph:bool=True):
        for model in self.models:
            # Use 'or' instead of get() default to handle None and empty list cases
            # get() only uses default when key is missing, not when value is None/[]
            roles = model.get('roles') or [ModelRoleType.chatcompletions]

            for i in range(len(roles)):
                if isinstance(roles[i], str):
                    role, task = roles[i], None
                elif isinstance(roles[i], dict):
                    role, task = next(iter(roles[i].items()))

                _model = {**model} # shallow copy
                _model['roles'] = {role:task}
                if role == ModelRoleType.chatcompletions:
                    self.for_chatcompletions['models'].append(_model)
                elif role == ModelRoleType.postcompletions:
                    self.for_postcompletions['models'].append(_model)

        if morph:
            self.for_chatcompletions = ConfigMorpher(self.for_chatcompletions)
            self.for_postcompletions = ConfigMorpher(self.for_postcompletions)