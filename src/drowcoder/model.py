from dataclasses import dataclass
from typing import List

from config_morpher import ConfigMorpher


@dataclass(frozen=True)
class ModelRole:
    chatcompletions :str = 'chat-completions'
    postcompletions :str = 'post-completions'


class ModelDispatcher:
    def __init__(self, models:List[dict], morph:bool=True):
        self.models = models
        self.morph =  morph
        self.for_chatcompletions = {'models': []}
        self.for_postcompletions = {'models': []}
        self.dispatch(morph=morph)

    def dispatch(self, morph:bool=True):
        for model in self.models:
            role_dict = {}
            if 'roles' in model:
                for i in range(len(model['roles'])):
                    if isinstance(model['roles'][i], str):
                        role_dict[model['roles'][i]] = None
                    elif isinstance(model['roles'][i], dict):
                        role_dict.update(model['roles'][i])

                if ModelRole.chatcompletions in role_dict:
                    self.for_chatcompletions['models'].append(model)
                if ModelRole.postcompletions in role_dict:
                    self.for_postcompletions['models'].append(model)

        if morph:
            self.for_chatcompletions = ConfigMorpher(self.for_chatcompletions)
            self.for_postcompletions = ConfigMorpher(self.for_postcompletions)