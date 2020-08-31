import operator
import numbers
import sys
from datetime import datetime, timedelta
from collections.abc import Iterable
from typing import Callable, NewType
from datatypes_timex_expression import Timex
from dateutil import tz
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from .memory_interface import MemoryInterface
from .options import Options
from .return_type import ReturnType
from .expression_type import ACCESSOR, ELEMENT
from .convert_format import FormatDatetime

VerifyExpression = NewType("VerifyExpression", Callable[[object, object, int], str])

# pylint: disable=unused-argument
class FunctionUtils:
    verify_expression = VerifyExpression
    default_date_time_format = "yyyy-MM-ddTHH:mm:ss.fffZ"

    @staticmethod
    def validate_arity_and_any_type(
        expression: object,
        min_arity: int,
        max_arity: int,
        return_type: ReturnType = ReturnType.Object,
    ):
        if len(expression.children) < min_arity:
            raise Exception(
                expression.to_string()
                + " should have at least "
                + str(min_arity)
                + " children."
            )

        if len(expression.children) > max_arity:
            raise Exception(
                expression.to_string()
                + " can't have more than "
                + str(max_arity)
                + " children."
            )

        if return_type & ReturnType.Object == 0:
            for child in expression.children:
                if (child.return_type & ReturnType.Object == 0) and (
                    return_type & child.return_type == 0
                ):
                    raise Exception(
                        FunctionUtils.build_type_validator_error(
                            return_type, child, expression
                        )
                    )

    @staticmethod
    def validate_binary(expression: object):
        FunctionUtils.validate_arity_and_any_type(expression, 2, 2)

    @staticmethod
    def validate_two_or_more_than_two_numbers(expression: object):
        FunctionUtils.validate_arity_and_any_type(
            expression, 2, sys.maxsize, ReturnType.Number
        )

    @staticmethod
    def validate_binary_number_or_string(expression: object):
        FunctionUtils.validate_arity_and_any_type(
            expression, 2, 2, ReturnType.Number | ReturnType.String
        )

    @staticmethod
    def validate_at_least_one(expression: object):
        return FunctionUtils.validate_arity_and_any_type(expression, 1, sys.maxsize)

    @staticmethod
    def validate_unary(expression: object):
        return FunctionUtils.validate_arity_and_any_type(expression, 1, 1)

    @staticmethod
    def validate_binary_number(expression: object):
        return FunctionUtils.validate_arity_and_any_type(
            expression, 2, 2, ReturnType.Number
        )

    @staticmethod
    def validate_order(expression: object, optional: list, *types: object):
        if optional is None:
            optional = []
        if len(expression.children) < len(types) or len(expression.children) > len(
            types
        ) + len(optional):
            if len(optional) == 0:

                raise Exception(
                    "{"
                    + expression.to_string()
                    + "} should have {"
                    + str(len(types))
                    + "} children."
                )

            raise Exception(
                "{"
                + expression.to_string()
                + "} should have between {"
                + str(len(types))
                + "} and {"
                + str(len(types) + len(optional))
                + "} children."
            )

        for i, child_type in enumerate(types):
            child = expression.children[i]
            child_return_type = child.return_type

            if (
                child_type & ReturnType.Object == 0
                and child_return_type & ReturnType.Object == 0
                and child_type & child_return_type == 0
            ):

                raise Exception(
                    FunctionUtils.build_type_validator_error(
                        child_type, child, expression
                    )
                )
        for i, child_type in enumerate(optional):
            i_c = i + len(types)
            if i_c >= len(expression.children):
                break
            child = expression.children[i_c]
            child_return_type = child.return_type

            if (
                child_type & ReturnType.Object == 0
                and child_return_type & ReturnType.Object == 0
                and child_type & child_return_type == 0
            ):

                raise Exception(
                    FunctionUtils.build_type_validator_error(
                        child_type, child, expression
                    )
                )

    @staticmethod
    def validate_unary_number(expression: object):
        return FunctionUtils.validate_arity_and_any_type(
            expression, 1, 1, ReturnType.Number
        )

    @staticmethod
    def validate_unary_or_binary_number(expression: object):
        return FunctionUtils.validate_arity_and_any_type(
            expression, 1, 2, ReturnType.Number
        )

    @staticmethod
    def validate_unary_or_binary_string(expression: object):
        return FunctionUtils.validate_arity_and_any_type(
            expression, 1, 2, ReturnType.String
        )

    @staticmethod
    def validate_unary_string(expression: object):
        return FunctionUtils.validate_arity_and_any_type(
            expression, 1, 1, ReturnType.String
        )

    @staticmethod
    def validate_foreach(expression: object):
        if len(expression.children) != 3:
            raise Exception(
                "foreach expect 3 parameters, found " + str(len(expression.children))
            )

        second = expression.children[1]
        if not (second.expr_type == ACCESSOR and len(second.children) == 1):
            raise Exception(
                "Second parameter of foreach is not an identifier: "
                + second.to_string()
            )

    @staticmethod
    def verify_string(value: object, expression: object, number: int):
        error: str = None
        if not isinstance(value, str):
            error = expression.to_string() + " is not a string."
        return error

    @staticmethod
    def verify_string_or_null(value: object, expression: object, number: int):
        error: str = None
        if not isinstance(value, str) and value is not None:
            error = expression.to_string() + " is neither a string nor a null object."
        return error

    @staticmethod
    def verify_number_or_string_or_null(value: object, expression: object, number: int):
        error: str = None
        if (
            value is not None
            and (isinstance(value, bool) or not isinstance(value, numbers.Number))
            and not isinstance(value, str)
        ):
            error = expression.to_string() + " is neither a number nor string."

        return error

    @staticmethod
    def verify_number_or_string(value: object, expression: object, number: int):
        error: str = None
        if value is None or (
            not isinstance(value, numbers.Number) and not isinstance(value, str)
        ):
            error = expression.to_string() + " is not string or number"

        return error

    @staticmethod
    def verify_number(value: object, expression: object, pos: int):
        error: str = None
        if not isinstance(value, numbers.Number):
            error = expression.to_string() + " is not a number."

        return error

    @staticmethod
    def verify_numeric_list_or_number(value: object, expression: object, number: int):
        error: str = None
        if isinstance(value, numbers.Number):
            return error

        if not isinstance(value, list):
            error = expression.to_string() + " is neither a list nor a number."
        else:
            for elt in value:
                if not isinstance(elt, numbers.Number):
                    error = elt + " is not a number in " + expression
                    break

        return error

    @staticmethod
    def verify_integer(value: object, expression: object, number: int):
        error: str = None
        if not FunctionUtils.is_integer(value):
            error = expression.to_string() + " is not an integer."

        return error

    @staticmethod
    def verify_list(value: object, expression: object, number: int):
        error: str = None
        if not isinstance(value, list):
            error = expression.to_string() + " is not a list."

        return error

    @staticmethod
    def verify_numeric_list(value: object, expression: object, number: int):
        error: str = None
        if not isinstance(value, list):
            error = expression.to_string() + " is not a list."
        else:
            for elt in value:
                if not isinstance(elt, numbers.Number):
                    error = elt + " is not a number in " + expression
                    break

        return error

    @staticmethod
    def verify_not_null(value: object, expression, number: int):
        error: str = None
        if value is None:
            error = expression.to_string() + " is null."
        return error

    @staticmethod
    def verify_container(value: object, expression: object, number: int):
        error: str = None
        if not isinstance(value, str) and not isinstance(value, Iterable):
            error = expression.to_string() + " must be a string or list."

        return error

    @staticmethod
    def apply_sequence_with_error(
        function: Callable[[list], object], verify: VerifyExpression = None
    ):
        def anonymous_function(args: []) -> object:
            binary_args = [None, None]
            so_far = args[0]
            value: object
            error: str
            for arg in args[1:]:
                binary_args[0] = so_far
                binary_args[1] = arg
                value, error = function(binary_args)
                if error:
                    return value, error

                so_far = value

            value = so_far
            error = None
            return value, error

        return FunctionUtils.apply_with_error(anonymous_function, verify)

    @staticmethod
    def apply_with_error(
        function: Callable[[list], object], verify: VerifyExpression = None
    ):
        def anonymous_function(
            expression: object, state: MemoryInterface, options: Options
        ):
            value: object = None
            error: str = None
            args: []
            args, error = FunctionUtils.evaluate_children(
                expression, state, options, verify
            )
            if error is None:
                try:
                    value, error = function(args)
                except Exception as err:
                    error = str(err)

            return value, error

        return anonymous_function

    @staticmethod
    def apply_sequence(
        function: Callable[[list], object], verify: VerifyExpression = None
    ):
        def anonymous_function(args: list):
            binary_args = [None, None]
            so_far = args[0]
            for arg in args[1:]:
                binary_args[0] = so_far
                binary_args[1] = arg
                so_far = function(binary_args)

            return so_far

        return FunctionUtils.apply(anonymous_function, verify)

    @staticmethod
    def apply(function: Callable[[list], object], verify: VerifyExpression = None):
        def anonymous_function(
            expression: object, state: MemoryInterface, options: Options
        ):
            value: object = None
            error: str
            args: []
            args, error = FunctionUtils.evaluate_children(
                expression, state, options, verify
            )
            if error is None:
                try:
                    value = function(args)
                except Exception as err:
                    error = str(err)

            return value, error

        return anonymous_function

    @staticmethod
    def evaluate_children(
        expression: object,
        state: MemoryInterface,
        options: Options,
        verify: VerifyExpression = None,
    ):
        args = []
        value: object
        error: str = None
        pos = 0

        for child in expression.children:
            res = child.try_evaluate(state, options)
            value = res[0]
            error = res[1]
            if error:
                break

            if verify:
                error = verify(value, child, pos)

            if error:
                break

            args.append(value)
            pos = pos + 1

        return args, error

    @staticmethod
    def access_index(instance: object, index: int):
        value: object = None
        error: str = None

        if instance is None:
            return value, error

        if isinstance(instance, list):
            if 0 <= index < len(instance):
                value = instance[index]
            else:
                error = str(index) + " is out of range for " + str(instance)
        else:
            error = instance + " is not a collection."

        return value, error

    @staticmethod
    def access_property(instance: object, property: str):
        value: object = None
        error: str = None

        if instance is None:
            return value, error

        if isinstance(instance, dict):
            value = instance.get(property)
            if value is None:
                prop = list(
                    filter(lambda x: (x.lower() == property.lower()), instance.keys())
                )
                if len(prop) > 0:
                    value = instance.get(prop[0])

        return value, error

    @staticmethod
    def set_property(instance: object, property: str, val: object):
        result = val
        instance[property] = val
        value = result
        error = None
        return value, error

    @staticmethod
    def parse_int(obj: object):
        result: int = 0
        error: str = None
        if FunctionUtils.is_integer(obj):
            result = int(obj)
        else:
            error = str(obj) + " must be a integer."

        return result, error

    @staticmethod
    def is_integer(obj: object):
        if (obj is not None) and (
            isinstance(obj, int) or (isinstance(obj, float) and obj.is_integer())
        ):
            return True
        return False

    @staticmethod
    def is_logic_true(instance: object):
        result = True
        if isinstance(instance, bool):
            result = instance
        elif instance is None:
            result = False
        return result

    @staticmethod
    def date_time_converter(interval: int, time_unit: str, is_past: bool = True):
        converter: Callable[[datetime], datetime] = None
        error: str = None
        multi_flag = -1 if is_past else 1
        if time_unit.lower() == "second":

            def anonymous_function(date_time: datetime):
                return date_time + timedelta(seconds=multi_flag * interval)

            converter = anonymous_function
        elif time_unit.lower() == "minute":

            def anonymous_function(date_time: datetime):
                return date_time + timedelta(minutes=multi_flag * interval)

            converter = anonymous_function
        elif time_unit.lower() == "hour":

            def anonymous_function(date_time: datetime):
                return date_time + timedelta(hours=multi_flag * interval)

            converter = anonymous_function
        elif time_unit.lower() == "day":

            def anonymous_function(date_time: datetime):
                return date_time + timedelta(days=multi_flag * interval)

            converter = anonymous_function
        elif time_unit.lower() == "week":

            def anonymous_function(date_time: datetime):
                return date_time + timedelta(weeks=multi_flag * interval)

            converter = anonymous_function
        elif time_unit.lower() == "month":

            def anonymous_function(date_time: datetime):
                return date_time + relativedelta(months=multi_flag * interval)

            converter = anonymous_function
        elif time_unit.lower() == "year":

            def anonymous_function(date_time: datetime):
                return date_time + relativedelta(years=multi_flag * interval)

            converter = anonymous_function
        else:
            error = "{" + time_unit + "} is not a valid time unit."
            print(error)

        return converter, error

    @staticmethod
    def normalize_to_date_time(
        timestamp: object, transform: Callable[[datetime], object] = None
    ):
        result: object = None
        error: str = None
        if isinstance(timestamp, str):
            result, error = FunctionUtils.parse_iso_timestamp(timestamp, transform)
        elif isinstance(timestamp, datetime):
            if transform is not None:
                result, error = transform(timestamp)
            else:
                result, error = timestamp, None
        else:
            error = (
                "{"
                + str(timestamp)
                + "} should be a standard ISO format string or a DateTime object."
            )
        return result, error

    @staticmethod
    def parse_iso_timestamp(
        timestamp: str, transform: Callable[[datetime], object] = None
    ):
        result: object = None
        error: str = None
        parsed = None
        try:
            parsed = parse(timestamp)
            if (
                FormatDatetime.format(
                    parsed, FunctionUtils.default_date_time_format
                ).upper()
                == timestamp
            ):
                if transform is not None:
                    result, error = transform(parsed)
                else:
                    result = parsed
                    error = None
            else:
                error = "{" + timestamp + "} is not standard ISO format."
        except:
            error = "Could not parse {" + timestamp + "}"
        return result, error

    @staticmethod
    def try_accumulate_path(
        expression: object, state: MemoryInterface, options: Options
    ):
        path: str = ""
        error: str = None
        left = expression
        while left is not None:
            if left.expr_type == ACCESSOR:
                path = str(left.children[0].get_value()) + "." + path
                left = left.children[1] if len(left.children) == 2 else None
            elif left.expr_type == ELEMENT:
                value, error = left.children[1].try_evaluate(state, options)

                if error is not None:
                    path = None
                    left = None
                    return path, left, error

                if isinstance(value, numbers.Number) and FunctionUtils.is_integer(
                    value
                ):
                    path = "[" + str(int(value)) + "]." + path
                elif isinstance(value, str):
                    path = "['" + value + "']." + path
                else:
                    path = None
                    left = None
                    error = (
                        left.children[1].to_string()
                        + " doesn't return an int or string"
                    )
                    return path, left, error

                left = left.children[0]
            else:
                break

        path = path.rstrip(".").replace(".[", "[")
        if path == "":
            path = None

        return path, left, error

    @staticmethod
    def wrap_get_value(state: MemoryInterface, path: str, options: Options):
        result = state.get_value(path)
        if result is not None:
            return result

        if options.null_substitution is not None:
            return options.null_substitution(path)

        return None

    @staticmethod
    def build_type_validator_error(
        return_type: ReturnType, child_expr: object, expr: object
    ):
        result: str
        names: str
        if return_type == (1,):
            names = "Boolean"
        elif return_type == (2,):
            names = "Number"
        elif return_type == (4,):
            names = "Object"
        elif return_type == (8,):
            names = "String"
        else:
            names = "Array"
        if not "," in names:
            result = (
                "{"
                + child_expr.to_string()
                + "} is not a {"
                + names
                + "} expression in {"
                + expr.to_string()
                + "}."
            )
        else:
            result = (
                "{"
                + child_expr.to_string()
                + "} in {"
                + expr.to_string()
                + "} is not any of [{"
                + names
                + "}]."
            )
        return result

    @staticmethod
    # pylint: disable=import-outside-toplevel
    def foreach(expression: object, state: MemoryInterface, options: Options):
        result: list
        error: str = None
        instance: object

        res = expression.children[0].try_evaluate(state, options)
        instance = res[0]
        error = res[1]
        if instance is None:
            error = expression.children[0].to_string() + " evaluated to null."

        if error is None:
            iterator_name = str(expression.children[1].children[0].get_value())
            arr = []
            if isinstance(instance, (list, set)):
                arr = list(instance)
            elif isinstance(instance, dict):
                for ele in instance:
                    arr.append({"key": ele, "value": instance[ele]})
            else:
                error = (
                    expression.children[0].to_string()
                    + " is not a collection or structure object to run foreach"
                )

            if error is None:
                from .memory.stacked_memory import StackedMemory

                stacked_memory = StackedMemory.wrap(state)
                result = []
                for item in arr:
                    local = {iterator_name: item}

                    from .memory.simple_object_memory import SimpleObjectMemory

                    stacked_memory.append(SimpleObjectMemory.wrap(local))
                    res = expression.children[2].try_evaluate(stacked_memory, options)
                    stacked_memory.pop()
                    if res[1] is not None:
                        value = None
                        error = res[1]
                        return value, error

                    result.append(res[0])

        value = result

        return value, error

    @staticmethod
    def parse_timex_property(timex_expr):
        parsed: object = None
        if isinstance(timex_expr, Timex):
            parsed = timex_expr
        elif isinstance(timex_expr, str):
            parsed = Timex(timex=timex_expr)
        else:
            return (
                None,
                "${timexExpr} requires a TimexProperty or a string as a argument.",
            )
        return parsed, None

    @staticmethod
    def sort_by(is_descending: bool):
        def anonymous_function(
            expression: object, state: MemoryInterface, options: Options
        ):
            result: object = None
            error: str = None

            res = expression.children[0].try_evaluate(state, options)
            arr = res[0]
            error = res[1]

            if error is None:
                if isinstance(arr, list):
                    if len(expression.children) == 1:
                        if is_descending:
                            result = sorted(arr, key=str, reverse=True)
                        else:
                            result = sorted(arr, key=str)
                    else:
                        property_name: str = None
                        res = expression.children[1].try_evaluate(state, options)
                        property_name = res[0]
                        error = res[1]

                        if error is None:
                            property_name = (
                                "" if property_name is None else property_name
                            )

                        if is_descending:
                            result = sorted(
                                arr, key=lambda x: x[property_name], reverse=True
                            )
                        else:
                            result = sorted(arr, key=lambda x: x[property_name])
                else:
                    error = expression.children[0].to_string() + " is not an array"

            value = result

            return value, error

        return anonymous_function

    @staticmethod
    def ticks_with_error(timestamp: object):
        result: object = None
        parsed: object = None
        error: str = None
        parsed, error = FunctionUtils.normalize_to_date_time(timestamp)
        if error is None:
            result = (
                parsed.astimezone(tz.gettz("UTC"))
            ).timestamp() * 10000000 + 621355968000000000
        return result, error

    @staticmethod
    def is_equal(args: list) -> bool:
        if len(args) == 0:
            return False
        if args[0] is None or args[1] is None:
            return args[0] is None and args[1] is None
        if (isinstance(args[0], list) and len(args[0]) == 0) and (
            isinstance(args[1], list) and len(args[1]) == 0
        ):
            return True
        if (isinstance(args[0], dict) and len(args[0]) == 0) and (
            isinstance(args[1], dict) and len(args[1]) == 0
        ):
            return True
        if isinstance(args[0], numbers.Number) and isinstance(args[1], numbers.Number):
            if abs(float(args[0]) - float(args[1])) < 0.00000001:
                return True
        return operator.eq(args[0], args[1])
