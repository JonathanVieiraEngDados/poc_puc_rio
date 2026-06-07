import math
from typing import List, Union, Dict, Any
import pandas as pd

from langchain_core.tools import StructuredTool


Number = Union[int, float]


class MathOperatorTools:
    """
    Utility math tools to assist the agent with basic numeric operations.
    Exposes each operation as a StructuredTool via as_tools().
    """

    # ---------- Implementation functions (no self in signature) ---------- #
    @staticmethod
    def sum_list(numbers: List[Number]) -> float:
        if numbers is None or not isinstance(numbers, list) or len(numbers) == 0:
            raise ValueError("'numbers' must be a non-empty list of numbers.")
        total = 0.0
        for n in numbers:
            if n is None:
                continue
            total += float(n)
        return float(total)

    @staticmethod
    def max_list(numbers: List[Number]) -> float:
        if numbers is None or not isinstance(numbers, list) or len(numbers) == 0:
            raise ValueError("'numbers' must be a non-empty list of numbers.")
        vals = [float(n) for n in numbers if n is not None]
        if not vals:
            raise ValueError("'numbers' contains no valid numeric values.")
        return float(max(vals))

    @staticmethod
    def min_list(numbers: List[Number]) -> float:
        if numbers is None or not isinstance(numbers, list) or len(numbers) == 0:
            raise ValueError("'numbers' must be a non-empty list of numbers.")
        vals = [float(n) for n in numbers if n is not None]
        if not vals:
            raise ValueError("'numbers' contains no valid numeric values.")
        return float(min(vals))

    @staticmethod
    def mean_list(numbers: List[Number]) -> float:
        if numbers is None or not isinstance(numbers, list) or len(numbers) == 0:
            raise ValueError("'numbers' must be a non-empty list of numbers.")
        vals = [float(n) for n in numbers if n is not None]
        if not vals:
            raise ValueError("'numbers' contains no valid numeric values.")
        return float(sum(vals) / len(vals))

    @staticmethod
    def add(a: Number, b: Number) -> float:
        return float(a) + float(b)

    @staticmethod
    def subtract(a: Number, b: Number) -> float:
        return float(a) - float(b)

    @staticmethod
    def multiply(a: Number, b: Number) -> float:
        return float(a) * float(b)

    @staticmethod
    def divide(a: Number, b: Number) -> float:
        b = float(b)
        if b == 0.0:
            raise ZeroDivisionError("Division by zero is not allowed.")
        return float(float(a) / b)

    @staticmethod
    def group_and_aggregate(
        data: List[Dict[str, Any]], 
        group_by: List[str], 
        value_column: str, 
        operation: str = "sum"
    ) -> List[Dict[str, Any]]:
        """
        Group data by categorical variables and apply aggregation operation.
        
        Args:
            data: List of dictionaries representing rows
            group_by: List of column names to group by (e.g., ["CLIENTE", "Cidade"])
            value_column: Column name to aggregate (e.g., "Vr Frete Contab Prev")
            operation: Aggregation operation - "sum", "mean", "max", "min", "count"
        
        Returns:
            List of dictionaries with grouped results
        """
        if not data or not isinstance(data, list):
            raise ValueError("'data' must be a non-empty list of dictionaries.")
        
        if not group_by or not isinstance(group_by, list):
            raise ValueError("'group_by' must be a non-empty list of column names.")
        
        if not value_column or not isinstance(value_column, str):
            raise ValueError("'value_column' must be a non-empty string.")
        
        valid_operations = ["sum", "mean", "max", "min", "count"]
        if operation not in valid_operations:
            raise ValueError(f"'operation' must be one of: {valid_operations}")
        
        # Convert to DataFrame
        try:
            df = pd.DataFrame(data)
        except Exception as e:
            raise ValueError(f"Failed to convert data to DataFrame: {e}")
        
        # Validate columns exist
        missing_group_cols = [col for col in group_by if col not in df.columns]
        if missing_group_cols:
            raise ValueError(f"Group columns not found in data: {missing_group_cols}")
        
        if value_column not in df.columns:
            raise ValueError(f"Value column '{value_column}' not found in data.")
        
        # Convert value column to numeric, coercing errors
        df[value_column] = pd.to_numeric(df[value_column], errors='coerce')
        
        # Group and aggregate
        try:
            if operation == "sum":
                result = df.groupby(group_by)[value_column].sum().reset_index()
            elif operation == "mean":
                result = df.groupby(group_by)[value_column].mean().reset_index()
            elif operation == "max":
                result = df.groupby(group_by)[value_column].max().reset_index()
            elif operation == "min":
                result = df.groupby(group_by)[value_column].min().reset_index()
            elif operation == "count":
                result = df.groupby(group_by)[value_column].count().reset_index()
            
            # Rename the aggregated column
            result = result.rename(columns={value_column: f"{operation}_{value_column}"})
            
            # Convert back to list of dictionaries
            return result.to_dict(orient='records')
            
        except Exception as e:
            raise ValueError(f"Failed to perform group aggregation: {e}")

    # ---------- Exposure helpers ---------- #
    @classmethod
    def as_tools(cls) -> List[StructuredTool]:
        """Return all math operations as StructuredTool instances."""
        return [
            StructuredTool.from_function(
                func=cls.sum_list,
                name="math_sum",
                description="Sum a list of numbers and return the total as float.",
            ),
            StructuredTool.from_function(
                func=cls.max_list,
                name="math_max",
                description="Return the maximum value from a list of numbers.",
            ),
            StructuredTool.from_function(
                func=cls.min_list,
                name="math_min",
                description="Return the minimum value from a list of numbers.",
            ),
            StructuredTool.from_function(
                func=cls.mean_list,
                name="math_mean",
                description="Return the arithmetic mean of a list of numbers.",
            ),
            StructuredTool.from_function(
                func=cls.add,
                name="math_add",
                description="Add two numbers and return the result.",
            ),
            StructuredTool.from_function(
                func=cls.subtract,
                name="math_subtract",
                description="Subtract b from a and return the result.",
            ),
            StructuredTool.from_function(
                func=cls.multiply,
                name="math_multiply",
                description="Multiply two numbers and return the result.",
            ),
            StructuredTool.from_function(
                func=cls.divide,
                name="math_divide",
                description="Divide a by b and return the result; raises error on division by zero.",
            ),
            StructuredTool.from_function(
                func=cls.group_and_aggregate,
                name="math_group_aggregate",
                description="Group data by categorical variables and apply aggregation (sum, mean, max, min, count). "
                           "Input: data (list of dicts), group_by (list of column names), value_column (string), operation (string). "
                           "Example: group by ['CLIENTE', 'Cidade'] and sum 'Vr Frete Contab Prev'.",
            ),
        ]


