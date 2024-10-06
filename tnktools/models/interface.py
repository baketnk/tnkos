from abc import ABC, abstractmethod
from typing import Dict, Any

class ModelInterface(ABC):
    @abstractmethod
    def load_model(self) -> None:
        pass

    @abstractmethod
    def unload_model(self) -> None:
        pass

    @abstractmethod
    async def run_inference(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_parameter_info(self) -> Dict[str, Any]:
        pass
