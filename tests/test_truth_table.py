#!/usr/bin/env python3
import unittest
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor

# Create a QApplication instance for the tests
app = QApplication(sys.argv)

# Import the required classes from our application
from Visual_Truth_Table import (
    ExpressionEvaluator,
    TruthTableModel,
    IdentifierLineEdit
)

class ExpressionEvaluatorTests(unittest.TestCase):
    """Test cases for the ExpressionEvaluator class"""
    
    def test_normalize_expression(self):
        """Test symbol normalization for logic expressions"""
        test_cases = [
            ("p ∧ q", "p and q"),
            ("p ∨ q", "p or q"),
            ("¬p", "not p"),
            ("p → q", "p <= q"),
            ("p ↔ q", "p == q"),
            ("p ⊕ q", "p != q"),
            ("p ∧ q ∨ ¬r", "p and q or not r")
        ]
        
        for input_expr, expected_output in test_cases:
            result = ExpressionEvaluator._normalize_expression(input_expr)
            self.assertEqual(result, expected_output, 
                            f"Failed to normalize '{input_expr}' correctly")
    
    def test_is_valid_expression(self):
        """Test expression validation"""
        valid_expressions = [
            "p and q",
            "p or q",
            "not p",
            "p and (q or r)",
            "(p or q) and (r or s)",
            "p == q",
            "p != q",
            "p <= q",
            "p or True",
            "False and q"
        ]
        
        invalid_expressions = [
            "",  # Empty
            "p +",  # Syntax error
            "print(p)",  # Function call - not allowed
            "p = True",  # Assignment - not allowed
            "import sys",  # Import - not allowed
            "p if q else r",  # Conditional expression - not allowed
            "lambda x: x",  # Lambda - not allowed
            "[p for p in [True, False]]"  # List comprehension - not allowed
        ]
        
        for expr in valid_expressions:
            is_valid, message = ExpressionEvaluator.is_valid_expression(expr)
            self.assertTrue(is_valid, f"Expression '{expr}' should be valid but got: {message}")
        
        for expr in invalid_expressions:
            is_valid, message = ExpressionEvaluator.is_valid_expression(expr)
            self.assertFalse(is_valid, f"Expression '{expr}' should be invalid")
    
    def test_evaluate(self):
        """Test expression evaluation with variable dictionaries"""
        test_cases = [
            # (expression, var_dict, expected_result)
            ("p and q", {"p": True, "q": True}, True),
            ("p and q", {"p": True, "q": False}, False),
            ("p or q", {"p": False, "q": True}, True),
            ("not p", {"p": False}, True),
            ("p and q or r", {"p": False, "q": True, "r": True}, True),
            ("p and (q or r)", {"p": True, "q": False, "r": False}, False),
            ("p <= q", {"p": True, "q": False}, False),
            ("p <= q", {"p": False, "q": True}, True)
        ]
        
        for expr, var_dict, expected in test_cases:
            result = ExpressionEvaluator.evaluate(expr, var_dict)
            self.assertEqual(result, expected, 
                             f"'{expr}' with {var_dict} should evaluate to {expected}")
    
    def test_evaluation_with_missing_variables(self):
        """Test that evaluation raises error when variables are missing"""
        with self.assertRaises(Exception):
            ExpressionEvaluator.evaluate("p and q", {"p": True})
            
    def test_get_evaluation_steps(self):
        """Test step-by-step evaluation generation"""
        var_dict = {"p": True, "q": False}
        steps = ExpressionEvaluator.get_evaluation_steps("p and q", var_dict)
        
        self.assertTrue(isinstance(steps, list))
        self.assertTrue(len(steps) > 2)  # Should have multiple explanation steps
        
        # Check that the final step includes the correct result (false for p and q where q is false)
        self.assertTrue("false" in steps[-1].lower())


class TruthTableModelTests(unittest.TestCase):
    """Test cases for the TruthTableModel class"""
    
    def setUp(self):
        """Set up a new model for each test"""
        self.model = TruthTableModel()
    
    def test_default_initialization(self):
        """Test the model's default state"""
        self.assertEqual(self.model.variable_names, ["p", "q"])
        self.assertEqual(self.model.expressions, ["p and q"])
        self.assertEqual(self.model.rowCount(), 4)  # 2^2 combinations
        self.assertEqual(self.model.columnCount(), 3)  # 2 vars + 1 expr
    
    def test_set_variable_names(self):
        """Test updating variable names"""
        self.model.set_variable_names(["x", "y", "z"])
        self.assertEqual(self.model.variable_names, ["x", "y", "z"])
        self.assertEqual(self.model.rowCount(), 8)  # 2^3 combinations
        self.assertEqual(self.model.columnCount(), 4)  # 3 vars + 1 expr
    
    def test_set_expressions(self):
        """Test updating expressions"""
        new_expressions = ["p or q", "p and q", "not p"]
        self.model.set_expressions(new_expressions)
        self.assertEqual(self.model.expressions, new_expressions)
        self.assertEqual(self.model.columnCount(), 5)  # 2 vars + 3 expr
    
    def test_set_expression_colors(self):
        """Test updating expression colors"""
        new_colors = [QColor(255, 0, 0), QColor(0, 255, 0)]
        self.model.set_expressions(["p or q", "p and q"])  # Make sure we have 2 expressions
        self.model.set_expression_colors(new_colors)
        self.assertEqual(len(self.model.expr_colors), 2)
        self.assertEqual(self.model.expr_colors[0].name(), QColor(255, 0, 0).name())
        self.assertEqual(self.model.expr_colors[1].name(), QColor(0, 255, 0).name())
    
    def test_truth_table_generation(self):
        """Test that truth values are correctly generated"""
        # Set simple case with 2 variables
        self.model.set_variable_names(["p", "q"])
        self.model.set_expressions(["p and q"])
        
        # Truth table should have all combinations
        self.assertEqual(len(self.model.truth_values), 4)
        
        # Check specific combinations
        combinations = set()
        for row in self.model.truth_values:
            combinations.add(tuple(row))
            
        expected_combinations = {
            (False, False), (False, True), (True, False), (True, True)
        }
        self.assertEqual(combinations, expected_combinations)
    
    def test_expression_evaluation(self):
        """Test that expressions are evaluated correctly for each row"""
        self.model.set_variable_names(["p", "q"])
        self.model.set_expressions(["p and q", "p or q"])
        
        # Find row index for (False, False)
        row_ff_idx = None
        for i, row in enumerate(self.model.truth_values):
            if row == (False, False):
                row_ff_idx = i
                break
                
        # Find row index for (True, True)
        row_tt_idx = None
        for i, row in enumerate(self.model.truth_values):
            if row == (True, True):
                row_tt_idx = i
                break
        
        # Check results for False, False
        self.assertEqual(self.model.results[row_ff_idx], [False, False])  # p and q, p or q
        
        # Check results for True, True
        self.assertEqual(self.model.results[row_tt_idx], [True, True])  # p and q, p or q


if __name__ == "__main__":
    unittest.main() 