from typing import Any, Dict, Optional, Callable

from pygeomodels.api import submit_model_task


class ModelCaller:
    def __init__(self, metadata: Dict[str, Dict[str, Optional[Any]]]):
        self.model_functions = self._generate_model_functions(metadata)

    def _generate_model_functions(self, metadata):
        model_functions = dict()

        for m_id in metadata.keys():
            model_name = metadata[m_id]['model_unique_abbr']
            def create_model_function(model_id):
                def model_function(_inputs: Dict[str, Optional[Any]],
                                   _params: Dict[str, Optional[Any]],
                                   _outputs: Dict[str, Optional[Any]],
                                   _taskname: str = '') -> Dict[str, Optional[Any]]:
                    return submit_model_task(model_id, _inputs, _params, _outputs, _taskname)

                return model_function

            model_function = create_model_function(m_id)
            model_function.__name__ = model_name
            model_function.__annotations__ = {
                'inputs': Dict[str, Any],
                'params': Dict[str, Any],
                'outputs': Dict[str, Any],
                'return': Dict[str, Any]
            }

            model_functions[model_name] = model_function

        return model_functions

    def __getattr__(self, name: str) -> Callable:
        if name in self.model_functions:
            return self.model_functions[name]
        raise AttributeError(f"No such model: {name}")


