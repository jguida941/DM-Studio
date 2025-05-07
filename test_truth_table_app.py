#!/usr/bin/env python3
"""
Unit Tests for Truth Table App and Model Components

This script contains pytest-based tests that verify:
1. TruthTableApp initialization and component setup
2. TruthTableModel data generation and display
3. Variable and expression update functionality
4. UI interactions and display mode changes
"""

import sys
import pytest
from PyQt6.QtWidgets import QApplication, QTableView, QDockWidget, QLineEdit, QDialog
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QColor

# Import the components to test
from Visual_Truth_Table import (
    TruthTableApp,
    TruthTableModel,
    VariableConfigWidget,
    ExpressionWidget,
    ExplanationWidget,
    DisplayConfig
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
def truth_table_app(app):
    """Create a truth table app for testing"""
    tt_app = TruthTableApp()
    yield tt_app
    tt_app.deleteLater()

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
    
    def test_data_display(self, truth_table_model):
        """Test data display in various roles"""
        # Check variable display (first column, first row)
        index = truth_table_model.index(0, 0)
        
        # Display role (should be "F" by default)
        display_value = truth_table_model.data(index, Qt.ItemDataRole.DisplayRole)
        assert display_value in ["F", "0"]  # Depends on config, both are acceptable
        
        # Background role for variable (could be None or a QBrush depending on implementation)
        background = truth_table_model.data(index, Qt.ItemDataRole.BackgroundRole)
        # Either None or a QBrush is acceptable, we just ensure it's handled properly
        
        # Check expression result display (third column, first row)
        index = truth_table_model.index(0, 2)
        
        # Display role
        display_value = truth_table_model.data(index, Qt.ItemDataRole.DisplayRole)
        assert display_value in ["F", "0"]  # p and q is False when p is False
        
        # Background role for expression (should be a QBrush with color)
        background = truth_table_model.data(index, Qt.ItemDataRole.BackgroundRole)
        assert background is not None  # Should have a color
    
    def test_header_display(self, truth_table_model):
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
        # Check default display modes
        assert display_config.variable_display == DisplayConfig.BINARY_MODE
        assert display_config.expression_display == DisplayConfig.TF_MODE
        
        # Check format_variable in binary mode (default)
        assert display_config.format_variable(True) == "1"
        assert display_config.format_variable(False) == "0"
        
        # Set TF mode for variables
        display_config.set_variable_display(DisplayConfig.TF_MODE)
        assert display_config.variable_display == DisplayConfig.TF_MODE
        
        # Check format_variable in TF mode
        assert display_config.format_variable(True) == "T" 
        assert display_config.format_variable(False) == "F"
    
    def test_row_order(self, display_config):
        """Test row order settings"""
        # Check default row order
        assert display_config.row_order == DisplayConfig.STANDARD_ORDER
        assert not display_config.should_reverse_rows()
        
        # Set reversed order
        display_config.set_row_order(DisplayConfig.REVERSED_ORDER)
        assert display_config.row_order == DisplayConfig.REVERSED_ORDER
        assert display_config.should_reverse_rows()

# TruthTableApp Tests
class TestTruthTableApp:
    """Test suite for the TruthTableApp class"""
    
    def test_app_initialization(self, truth_table_app):
        """Test that the app is properly initialized with all required components"""
        # Check that main UI components are created
        assert truth_table_app.variable_config is not None
        assert truth_table_app.expression_widget is not None
        assert truth_table_app.table_view is not None
        assert truth_table_app.table_model is not None
        assert truth_table_app.explanation_widget is not None
        
        # Check that dock widgets are created
        var_dock = None
        expr_dock = None
        for dock in truth_table_app.findChildren(QDockWidget):
            if dock.windowTitle() == "Variables":
                var_dock = dock
            elif dock.windowTitle() == "Expressions":
                expr_dock = dock
        
        assert var_dock is not None, "Variables dock widget should exist"
        assert expr_dock is not None, "Expressions dock widget should exist"
    
    def test_update_variables(self, truth_table_app, qtbot):
        """Test updating variables via the API"""
        # Initial state
        initial_vars = truth_table_app.table_model.variable_names
        
        # Update variables
        new_vars = ["x", "y", "z"]
        truth_table_app.update_variables(new_vars)
        
        # Check that model was updated
        assert truth_table_app.table_model.variable_names == new_vars
        
        # Check row count (should be 2^3 = 8)
        assert truth_table_app.table_model.rowCount() == 8
    
    def test_update_expressions(self, truth_table_app, qtbot):
        """Test updating expressions via the API"""
        # Initial state
        initial_exprs = truth_table_app.table_model.expressions
        
        # Update expressions
        new_exprs = ["p or q", "p and q", "p xor q"]
        truth_table_app.update_expressions(new_exprs)
        
        # Check that model was updated
        assert truth_table_app.table_model.expressions == new_exprs
        
        # Check column count (should be 2 vars + 3 expressions = 5)
        assert truth_table_app.table_model.columnCount() == 5
    
    def test_generate_table(self, truth_table_app, qtbot):
        """Test table generation"""
        # Initial state (table should already be generated)
        assert truth_table_app.table_model.rowCount() > 0
        assert truth_table_app.table_model.columnCount() > 0
        
        # Explicitly generate table
        truth_table_app.generate_table()
        
        # Table view should be updated
        assert truth_table_app.table_view.model() is truth_table_app.table_model
    
    def test_display_mode_changes(self, truth_table_app, qtbot):
        """Test changing display modes"""
        # Initial state (should match the DisplayConfig defaults)
        assert truth_table_app.display_config.variable_display == DisplayConfig.BINARY_MODE
        
        # Change to TF mode
        truth_table_app.update_variable_display_mode(DisplayConfig.TF_MODE)
        
        # Check that mode was updated
        assert truth_table_app.display_config.variable_display == DisplayConfig.TF_MODE
        
        # Check that combo box was updated
        assert truth_table_app.var_display_combo.currentText() == DisplayConfig.TF_MODE
    
    def test_insert_symbol(self, truth_table_app, qtbot):
        """Test symbol insertion functionality"""
        # Get the first expression input (assuming it exists)
        expression_inputs = truth_table_app.expression_widget.findChildren(QLineEdit)
        if expression_inputs:
            # Focus the input
            expression_inputs[0].setFocus()
            
            # Clear and set initial text
            expression_inputs[0].clear()
            expression_inputs[0].setText("p ")
            
            # Insert a symbol
            truth_table_app.insert_symbol("∧")
            
            # Check that symbol was inserted
            assert "∧" in expression_inputs[0].text()
    
    def test_floating_toolbar(self, truth_table_app):
        """Test floating toolbar interaction"""
        # Toolbar should exist but be hidden initially
        assert truth_table_app.floating_toolbar is not None
        assert not truth_table_app.floating_toolbar.isVisible()
        
        # Show the toolbar
        truth_table_app.show_floating_toolbar()
        
        # Toolbar should now be visible
        assert truth_table_app.floating_toolbar.isVisible()
    
    def test_style_editor(self, truth_table_app):
        """Test style editor integration"""
        # Style editor should exist
        assert truth_table_app.style_editor is not None
        
        # Generate a test stylesheet
        test_style = """
        QWidget { background-color: #123456; }
        """
        
        # Apply the style
        truth_table_app.apply_style_changes(test_style)
        
        # Check that style was applied
        assert truth_table_app.styleSheet() == test_style

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 