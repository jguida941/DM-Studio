#!/usr/bin/env python3
"""
Unit Tests for Truth Table Model

This script contains pytest-based tests that verify:
1. TruthTableModel data generation and manipulation
2. DisplayConfig functionality
3. Basic expression evaluation logic
"""

import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtGui import QColor

# Import the components to test
from Visual_Truth_Table import (
    TruthTableModel,
    DisplayConfig,
    ExpressionEvaluator
)

# Test fixtures
@pytest.fixture
def app():
    """PyQt QApplication fixture"""
    application = QApplication(sys.argv)
    yield application
    application.quit()

@pytest.fixture
def truth_table_model(app):
    """Create a truth table model for testing"""
    model = TruthTableModel()
    yield model

@pytest.fixture
def display_config():
    """Create a display config for testing"""
    config = DisplayConfig()
    yield config

# TruthTableModel Tests
class TestTruthTableModel:
    """Test suite for the TruthTableModel class"""
    
    def test_model_initialization(self, truth_table_model):
        """Test the model's default initialization"""
        # Check default variables and expressions
        assert truth_table_model.variable_names == ["p", "q"]
        assert truth_table_model.expressions == ["p and q"]
        
        # Check dimensions
        assert truth_table_model.rowCount() == 4  # 2^2 = 4 rows for 2 variables
        assert truth_table_model.columnCount() == 3  # 2 variables + 1 expression
        
        # Check truth values were generated
        assert len(truth_table_model.truth_values) == 4
        assert len(truth_table_model.results) == 4
    
    def test_update_variables(self, truth_table_model):
        """Test updating variable names"""
        # Update to three variables
        truth_table_model.set_variable_names(["p", "q", "r"])
        
        # Check dimensions
        assert truth_table_model.rowCount() == 8  # 2^3 = 8 rows for 3 variables
        assert truth_table_model.columnCount() == 4  # 3 variables + 1 expression
        
        # Check truth values were regenerated
        assert len(truth_table_model.truth_values) == 8
        assert len(truth_table_model.results) == 8
    
    def test_update_expressions(self, truth_table_model):
        """Test updating expressions"""
        # Update to two expressions
        truth_table_model.set_expressions(["p and q", "p or q"])
        
        # Check dimensions
        assert truth_table_model.columnCount() == 4  # 2 variables + 2 expressions
        
        # Check results were recalculated
        assert len(truth_table_model.results) == 4  # Still 4 rows with 2 variables
        assert len(truth_table_model.results[0]) == 2  # 2 results per row (for 2 expressions)
    
    def test_expression_colors(self, truth_table_model):
        """Test setting expression colors"""
        # Set colors
        colors = [QColor(255, 0, 0), QColor(0, 255, 0)]
        truth_table_model.set_expressions(["p and q", "p or q"])
        truth_table_model.set_expression_colors(colors)
        
        # Check colors were set
        assert len(truth_table_model.expr_colors) == 2
        assert truth_table_model.expr_colors[0].name() == QColor(255, 0, 0).name()
        assert truth_table_model.expr_colors[1].name() == QColor(0, 255, 0).name()
    
    def test_header_data(self, truth_table_model):
        """Test header display"""
        # Check variable header
        header = truth_table_model.headerData(0, Qt.Orientation.Horizontal)
        assert header == "p"
        
        # Check expression header
        header = truth_table_model.headerData(2, Qt.Orientation.Horizontal)
        assert header == "p and q"
        
        # Invalid section should return None
        header = truth_table_model.headerData(10, Qt.Orientation.Horizontal)
        assert header is None

# DisplayConfig Tests
class TestDisplayConfig:
    """Test suite for the DisplayConfig class"""
    
    def test_display_modes(self, display_config):
        """Test display modes"""
        # Check that essential attributes and methods exist
        assert hasattr(display_config, 'format_variable')
        assert hasattr(display_config, 'format_expression')
        assert hasattr(display_config, 'set_variable_display')
        assert hasattr(display_config, 'set_expression_display')
        
        # Store initial outputs
        initial_true_var = display_config.format_variable(True)
        initial_false_var = display_config.format_variable(False)
        
        # Should be either T/F or 1/0 format
        assert initial_true_var in ["T", "1"]
        assert initial_false_var in ["F", "0"]
        
        # Set to T/F mode explicitly
        display_config.set_variable_display(DisplayConfig.TF_MODE)
        assert display_config.format_variable(True) == "T"
        assert display_config.format_variable(False) == "F"
        
        # Set to 1/0 mode explicitly 
        display_config.set_variable_display(DisplayConfig.BINARY_MODE)
        assert display_config.format_variable(True) == "1"
        assert display_config.format_variable(False) == "0"
        
        # Test expression format - set explicitly to T/F
        display_config.set_expression_display(DisplayConfig.TF_MODE)
        assert display_config.format_expression(True) == "T"
        assert display_config.format_expression(False) == "F"
        
        # Change expression format to binary
        display_config.set_expression_display(DisplayConfig.BINARY_MODE)
        assert display_config.format_expression(True) == "1"
        assert display_config.format_expression(False) == "0"
    
    def test_row_order(self, display_config):
        """Test row order settings"""
        # Check default row order
        assert display_config.row_order == DisplayConfig.STANDARD_ORDER
        assert not display_config.should_reverse_rows()
        
        # Set reversed order
        display_config.set_row_order(DisplayConfig.REVERSED_ORDER)
        assert display_config.row_order == DisplayConfig.REVERSED_ORDER
        assert display_config.should_reverse_rows()

# ExpressionEvaluator Tests
class TestExpressionEvaluator:
    """Test suite for ExpressionEvaluator class"""
    
    def test_normalize_expression(self):
        """Test symbol normalization"""
        test_cases = [
            ("p ∧ q", "p and q"),
            ("p ∨ q", "p or q"),
            ("¬p", "not p"),
            ("p → q", "p <= q"),
            ("p ↔ q", "p == q")
        ]
        
        for input_expr, expected in test_cases:
            result = ExpressionEvaluator._normalize_expression(input_expr)
            assert result == expected, f"Failed to normalize '{input_expr}'"
    
    def test_expression_validation(self):
        """Test expression validation"""
        valid_expressions = [
            "p and q",
            "p or q",
            "not p",
            "p or (q and r)"
        ]
        
        invalid_expressions = [
            "",  # Empty
            "p +",  # Syntax error
            "print(p)",  # Function call
            "p = True"  # Assignment
        ]
        
        for expr in valid_expressions:
            is_valid, _ = ExpressionEvaluator.is_valid_expression(expr)
            assert is_valid, f"Expression '{expr}' should be valid"
        
        for expr in invalid_expressions:
            is_valid, _ = ExpressionEvaluator.is_valid_expression(expr)
            assert not is_valid, f"Expression '{expr}' should be invalid"
    
    def test_evaluate_expression(self):
        """Test expression evaluation"""
        var_dict = {"p": True, "q": False}
        
        # Test basic expressions
        assert ExpressionEvaluator.evaluate("p and q", var_dict) == False
        assert ExpressionEvaluator.evaluate("p or q", var_dict) == True
        assert ExpressionEvaluator.evaluate("not p", var_dict) == False
        
        # Test with logical symbols
        assert ExpressionEvaluator.evaluate("p ∧ q", var_dict) == False
        assert ExpressionEvaluator.evaluate("p ∨ q", var_dict) == True
        assert ExpressionEvaluator.evaluate("¬p", var_dict) == False

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 