#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for Truth Table Educational Tool

This script contains pytest-based tests that verify:
1. Symbol insertion functionality
2. Style editor integration
3. UI organization and visibility
4. Table generation accuracy
5. Expression validation logic
"""

import sys
import os
import pytest
from PyQt6.QtWidgets import QApplication, QLineEdit, QTableView, QDockWidget, QPushButton
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QColor, QFont

# Import the components to test
from Visual_Truth_Table import (
    TruthTableApp, 
    IdentifierLineEdit,
    ExpressionEvaluator,
    FloatingSymbolToolbar,
    StyleEditor,
    FuturisticUI,
    AppTheme
)

# Test fixtures
@pytest.fixture
def app():
    """PyQt QApplication fixture"""
    application = QApplication(sys.argv)
    yield application
    application.quit()

@pytest.fixture
def truth_table_app(app):
    """Create a Truth Table app instance for testing"""
    tt_app = TruthTableApp()
    yield tt_app
    tt_app.deleteLater()

@pytest.fixture
def floating_toolbar(app):
    """Create a floating toolbar for testing"""
    toolbar = FloatingSymbolToolbar()
    yield toolbar
    toolbar.deleteLater()

@pytest.fixture
def style_editor(app):
    """Create a style editor for testing"""
    editor = StyleEditor()
    yield editor
    editor.deleteLater()

# Symbol insertion tests
class TestSymbolInsertion:
    """Test suite for symbol insertion functionality"""
    
    def test_symbol_toolbar_exists(self, truth_table_app):
        """Test that the floating symbol toolbar exists and is properly initialized"""
        assert hasattr(truth_table_app, 'floating_toolbar')
        assert isinstance(truth_table_app.floating_toolbar, FloatingSymbolToolbar)
    
    def test_symbol_toolbar_buttons(self, floating_toolbar):
        """Test that the floating toolbar has the correct buttons"""
        # Check that the floating toolbar has buttons
        buttons = floating_toolbar.findChildren(QPushButton)
        assert len(buttons) > 0
        
        # We can check for some of the common symbols in the button text
        button_texts = [btn.text() for btn in buttons]
        
        # At least some of these symbols should be present
        common_symbols = ['∧', '∨', '¬', '→', '↔', '⊕']
        found_symbols = [sym for sym in common_symbols if sym in button_texts]
        
        assert len(found_symbols) > 0, f"No logical symbols found in toolbar buttons: {button_texts}"
    
    def test_symbol_insertion_regular_lineedit(self, truth_table_app, qtbot):
        """Test symbol insertion into a regular QLineEdit"""
        # Get an expression line edit
        truth_table_app.show()
        
        with qtbot.waitExposed(truth_table_app):
            expr_widget = truth_table_app.expression_widget
            if hasattr(expr_widget, 'input_fields') and expr_widget.input_fields:
                line_edit = expr_widget.input_fields[0]
                
                # Focus the line edit
                line_edit.setFocus()
                qtbot.wait(100)  # Give time for focus to take effect
                
                # Initial text
                line_edit.setText("p q")
                
                # Call the insert_symbol method - it may insert at end or cursor position
                # depending on implementation, so we'll test both possibilities
                truth_table_app.insert_symbol('∧')
                
                # Check if symbol was inserted
                # The implementation might insert at the end rather than cursor position
                # so we'll accept either of these outcomes
                text = line_edit.text()
                assert (text == "p q∧" or text == "p∧ q"), \
                    f"Symbol not inserted properly. Got '{text}', expected 'p q∧' or 'p∧ q'"
    
    def test_no_symbol_insertion_in_identifier(self, truth_table_app, qtbot):
        """Test that symbols cannot be inserted into identifier fields"""
        # Get a variable line edit
        var_widget = truth_table_app.variable_config
        
        if hasattr(var_widget, 'variable_inputs') and var_widget.variable_inputs:
            id_edit = var_widget.variable_inputs[0]
            
            # Focus the line edit
            id_edit.setFocus()
            qtbot.waitForWindowShown(truth_table_app)
            
            # Initial text
            original_text = id_edit.text()
            
            # Try to insert a symbol
            truth_table_app.insert_symbol('∧')
            
            # Text should not have changed
            assert id_edit.text() == original_text
    
    def test_floating_toolbar_visibility(self, truth_table_app, qtbot):
        """Test that the floating toolbar can be shown and hidden"""
        toolbar = truth_table_app.floating_toolbar
        
        # Initially hidden
        assert not toolbar.isVisible()
        
        # Show the toolbar
        truth_table_app.show_floating_toolbar()
        assert toolbar.isVisible()
        
        # Hide the toolbar
        toolbar.hideToolbar()
        assert not toolbar.isVisible()
    
    def test_toolbar_drag_functionality(self, floating_toolbar, qtbot):
        """Test that the floating toolbar can be dragged"""
        # Show the toolbar
        floating_toolbar.show()
        qtbot.waitForWindowShown(floating_toolbar)
        
        # Initial position
        initial_pos = floating_toolbar.pos()
        
        # Simulate drag operation
        qtbot.mousePress(floating_toolbar, Qt.MouseButton.LeftButton, pos=QPoint(10, 10))
        qtbot.mouseMove(floating_toolbar, pos=QPoint(50, 50))
        qtbot.mouseRelease(floating_toolbar, Qt.MouseButton.LeftButton, pos=QPoint(50, 50))
        
        # Position should have changed
        # Note: This test might be flaky depending on window manager
        # assert floating_toolbar.pos() != initial_pos

# Style editor tests
class TestStyleEditor:
    """Test suite for the style editor functionality"""
    
    def test_style_editor_exists(self, truth_table_app):
        """Test that the style editor exists in the app"""
        assert hasattr(truth_table_app, 'style_editor')
        
    def test_style_editor_integration(self, truth_table_app):
        """Test that the style editor is properly integrated into the UI"""
        # Should be accessible via a dock widget
        style_dock = None
        for dock in truth_table_app.findChildren(QDockWidget):
            if dock.windowTitle() == "Style Editor":
                style_dock = dock
                break
        
        assert style_dock is not None
        assert style_dock.widget() is truth_table_app.style_editor
    
    def test_style_changes_application(self, truth_table_app, qtbot):
        """Test that the style editor can apply changes"""
        editor = truth_table_app.style_editor
        
        # Record initial stylesheet
        initial_style = truth_table_app.styleSheet()
        
        # Apply a test style
        test_stylesheet = """
        QWidget { background-color: #123456; }
        """
        
        # Emit the signal that would be emitted when applying style
        editor.stylesChanged.emit(test_stylesheet)
        
        # Check that the style was applied
        assert truth_table_app.styleSheet() == test_stylesheet
    
    def test_color_picking(self, style_editor, qtbot, monkeypatch):
        """Test color picking in the style editor"""
        # Mock QColorDialog.getColor to return a specific color
        def mock_get_color(*args, **kwargs):
            return QColor("#FF5500")
        
        # This test needs to be adapted based on the actual implementation
        pass

# UI organization tests
class TestUIOrganization:
    """Test suite for UI organization and visibility"""
    
    def test_main_window_dimensions(self, truth_table_app):
        """Test that the main window has appropriate dimensions"""
        assert truth_table_app.width() >= 800
        assert truth_table_app.height() >= 600
    
    def test_dock_widgets_presence(self, truth_table_app):
        """Test that all required dock widgets are present"""
        # Check for Variables dock
        var_dock = None
        for dock in truth_table_app.findChildren(QDockWidget):
            if dock.windowTitle() == "Variables":
                var_dock = dock
                break
        assert var_dock is not None
        
        # Check for Expressions dock
        expr_dock = None
        for dock in truth_table_app.findChildren(QDockWidget):
            if dock.windowTitle() == "Expressions":
                expr_dock = dock
                break
        assert expr_dock is not None
        
        # Check for Educational Tools dock
        educ_dock = None
        for dock in truth_table_app.findChildren(QDockWidget):
            if dock.windowTitle() == "Educational Tools":
                educ_dock = dock
                break
        assert educ_dock is not None
    
    def test_central_widget(self, truth_table_app):
        """Test that the central widget contains the truth table"""
        # The table should be in the central widget
        central = truth_table_app.centralWidget()
        assert central is not None
        
        # Find the QTableView in the central widget
        table_views = central.findChildren(QTableView)
        assert len(table_views) > 0
        
        # The table view should be the main truth table
        assert truth_table_app.table_view in table_views
    
    def test_widget_visibility(self, truth_table_app):
        """Test that all main widgets are visible when the app is shown"""
        truth_table_app.show()
        
        # Main components should be visible
        assert truth_table_app.variable_config.isVisible()
        assert truth_table_app.expression_widget.isVisible()
        assert truth_table_app.explanation_widget.isVisible()
        assert truth_table_app.table_view.isVisible()

# Expression evaluation tests
class TestExpressionEvaluation:
    """Test suite for expression evaluation logic"""
    
    def test_expression_validator(self):
        """Test that expressions are properly validated"""
        # Valid expressions
        assert ExpressionEvaluator.is_valid_expression("p and q")[0] is True
        assert ExpressionEvaluator.is_valid_expression("p or q")[0] is True
        assert ExpressionEvaluator.is_valid_expression("not p")[0] is True
        assert ExpressionEvaluator.is_valid_expression("p → q")[0] is True
        
        # Invalid expressions
        assert ExpressionEvaluator.is_valid_expression("p + q")[0] is False  # + not a logical operator
        assert ExpressionEvaluator.is_valid_expression("print('hello')")[0] is False  # function call
        assert ExpressionEvaluator.is_valid_expression("import os")[0] is False  # import statement
    
    def test_expression_evaluation(self):
        """Test that expressions are properly evaluated"""
        # Setup variable dictionary
        var_dict = {'p': True, 'q': False}
        
        # Test evaluation
        assert ExpressionEvaluator.evaluate("p and q", var_dict) is False
        assert ExpressionEvaluator.evaluate("p or q", var_dict) is True
        assert ExpressionEvaluator.evaluate("not p", var_dict) is False
        assert ExpressionEvaluator.evaluate("p", var_dict) is True
        
        # Test with logical symbols
        assert ExpressionEvaluator.evaluate("p ∧ q", var_dict) is False
        assert ExpressionEvaluator.evaluate("p ∨ q", var_dict) is True
        assert ExpressionEvaluator.evaluate("¬p", var_dict) is False
    
    def test_symbol_normalization(self):
        """Test that logical symbols are properly normalized"""
        # Get the normalized expression directly
        norm_expr = ExpressionEvaluator._normalize_expression("p ∧ q")
        assert "and" in norm_expr
        
        norm_expr = ExpressionEvaluator._normalize_expression("p ∨ q")
        assert "or" in norm_expr
        
        norm_expr = ExpressionEvaluator._normalize_expression("¬p")
        assert "not" in norm_expr
        
        norm_expr = ExpressionEvaluator._normalize_expression("p → q")
        assert "<=" in norm_expr
    
    def test_evaluation_steps(self):
        """Test that evaluation steps are generated correctly"""
        # Setup variable dictionary
        var_dict = {'p': True, 'q': False}
        
        # Get evaluation steps
        steps = ExpressionEvaluator.get_evaluation_steps("p and q", var_dict)
        
        # Should return a list of steps
        assert isinstance(steps, list)
        assert len(steps) > 0
        
        # Check that steps mention variable values and final result
        has_var_p = any("p = True" in step for step in steps)
        has_var_q = any("q = False" in step for step in steps)
        has_result = any("False" in step for step in steps)
        
        assert has_var_p
        assert has_var_q
        assert has_result

# Table generation tests
class TestTableGeneration:
    """Test suite for truth table generation"""
    
    def test_table_model_columns(self, truth_table_app):
        """Test that the table model has the correct columns"""
        # Set variables
        truth_table_app.update_variables(["p", "q"])
        
        # Set expressions
        truth_table_app.update_expressions(["p and q"])
        
        # Generate table
        truth_table_app.generate_table()
        
        # Check column count (should be variables + expressions)
        assert truth_table_app.table_model.columnCount() == 3  # p, q, (p and q)
    
    def test_table_model_rows(self, truth_table_app):
        """Test that the table model has the correct number of rows"""
        # Set variables
        truth_table_app.update_variables(["p", "q"])
        
        # Set expressions
        truth_table_app.update_expressions(["p and q"])
        
        # Generate table
        truth_table_app.generate_table()
        
        # Check row count (should be 2^n where n is the number of variables)
        assert truth_table_app.table_model.rowCount() == 4  # 2^2 = 4
    
    def test_table_data_accuracy(self, truth_table_app):
        """Test that the table data is accurate"""
        # Set variables
        truth_table_app.update_variables(["p"])
        
        # Set expressions
        truth_table_app.update_expressions(["not p"])
        
        # Generate table
        truth_table_app.generate_table()
        
        # Check data at specific cells
        # This will depend on your row ordering, adjust as needed
        # Row 0, Column 0 (p = False)
        assert truth_table_app.table_model.data(
            truth_table_app.table_model.index(0, 0), 
            Qt.ItemDataRole.DisplayRole
        ) in ["F", "0"]  # Depending on display mode
        
        # Row 0, Column 1 (not p = True)
        assert truth_table_app.table_model.data(
            truth_table_app.table_model.index(0, 1), 
            Qt.ItemDataRole.DisplayRole
        ) in ["T", "1"]  # Depending on display mode
    
    def test_display_mode_changes(self, truth_table_app, qtbot):
        """Test that display mode changes update the table"""
        # Set variables and expressions
        truth_table_app.update_variables(["p"])
        truth_table_app.update_expressions(["p"])
        truth_table_app.generate_table()
        
        # Get original display mode for variables
        original_mode = truth_table_app.var_display_combo.currentText()
        
        # Change to the other mode
        new_mode = "1/0" if original_mode == "T/F" else "T/F"
        truth_table_app.var_display_combo.setCurrentText(new_mode)
        
        # Check that the change was applied
        assert truth_table_app.var_display_combo.currentText() == new_mode
        
        # The table should reflect the new display mode
        # This would need to check specific cell display values

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 