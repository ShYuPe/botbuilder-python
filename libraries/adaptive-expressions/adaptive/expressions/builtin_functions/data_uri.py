import base64
from ..expression_evaluator import ExpressionEvaluator, EvaluateExpressionDelegate
from ..expression_type import DATAURI
from ..function_utils import FunctionUtils
from ..return_type import ReturnType


class DataUri(ExpressionEvaluator):
    def __init__(self):
        super().__init__(
            DATAURI,
            DataUri.evaluator(),
            ReturnType.String,
            FunctionUtils.validate_unary,
        )

    @staticmethod
    def evaluator() -> EvaluateExpressionDelegate:
        def anonymous_function(args: []):
            bytes_string = str(args[0]).encode(encoding="utf-8")
            return (
                "data:text/plain;charset=utf-8;base64,"
                + base64.b64encode(bytes_string).decode()
            )

        return FunctionUtils.apply(anonymous_function, FunctionUtils.verify_string)
