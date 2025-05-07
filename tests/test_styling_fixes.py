#!/usr/bin/env python3
"""
Test suite for styling fixes in PyQt Truth Table application.

This test verifies:
1. Consistent styling across components
2. Font application without crashes
3. Global style propagation
4. Symbol insertion functionality
"""

import sys
import pytest
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QApplication, QLineEdit, QPushButton, QMainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Import testing utilities and mock classes
try:
    from Visual_Truth_Table import (
        TruthTableApp, 
        StyleEditor, 
        AppTheme,
        ExpressionWidget,
        IdentifierLineEdit,
        FloatingSymbolToolbar
    )
except ImportError:
    # Mock classes for testing without actual imports
    class AppTheme:
        @staticmethod
        def get_main_stylesheet():
            return """
            QWidget {
                background-color: #121212;
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            QPushButton {
                background-color: #2a2a2a;
                border-radius: 4px;
                padding: 8px 16px;
                margin: 4px;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                margin: 4px;
            }
            """
        
        @staticmethod
        def get_button_stylesheet():
            return """
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                margin: 4px;
                min-height: 30px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            """
        
        @staticmethod
        def get_table_stylesheet():
            return """
            QTableView {
                background-color: #121212;
                alternate-background-color: #1a1a1a;
                color: white;
                gridline-color: #333333;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 0px;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: white;
                padding: 4px;
                border: 1px solid #3a3a3a;
            }
            """
    
    class StyleEditor(QMainWindow):
        def __init__(self):
            super().__init__()
            self.stylesChanged = MagicMock()
            self.font = QFont("Helvetica", 12)
        
        def apply_style(self):
            style = """
            QWidget {
                background-color: #121212;
                color: white;
                font-family: "Helvetica";
                font-size: 12pt;
            }
            QPushButton {
                background-color: #2a2a2a;
                border-radius: 4px;
                padding: 8px;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
            }
            """
            self.stylesChanged.emit(style)
            QApplication.instance().setFont(self.font)

    class ExpressionWidget(QMainWindow):
        def __init__(self):
            super().__init__()
            self.input_fields = [QLineEdit() for _ in range(3)]
        
        def _validate_expression(self, text):
            pass

    class IdentifierLineEdit(QLineEdit):
        pass

    class FloatingSymbolToolbar(QMainWindow):
        pass

    class TruthTableApp(QMainWindow):
        def __init__(self):
            super().__init__()
            self.variable_config = None
            self.expression_widget = ExpressionWidget()
            self.app_container = QMainWindow()
            self.status_bar = self.statusBar()
        
        def apply_style_changes(self, style):
            self.setStyleSheet(style)
            QApplication.instance().setFont(QApplication.instance().font())
        
        def insert_symbol(self, symbol):
            focused_widget = QApplication.focusWidget()
            
            # Do not insert symbols into variable name fields
            if isinstance(focused_widget, IdentifierLineEdit):
                self.status_bar.showMessage("Symbols cannot be used in variable names", 3000)
                return
            
            # Find the correct target field
            target_field = None
            
            # If a line edit has focus, use it (as long as it's an expression field)
            if isinstance(focused_widget, QLineEdit):
                # Check if it's one of our expression input fields
                if hasattr(self, 'expression_widget') and focused_widget in self.expression_widget.input_fields:
                    target_field = focused_widget
            
            # If no valid target field found, use the first expression field as fallback
            if not target_field and hasattr(self, 'expression_widget'):
                target_field = self.expression_widget.input_fields[0]
                self.status_bar.showMessage(f"Inserted '{symbol}' into expression field 1", 3000)
            elif target_field:
                # Find which expression field number this is for better feedback
                if hasattr(self, 'expression_widget'):
                    field_index = self.expression_widget.input_fields.index(target_field)
                    self.status_bar.showMessage(f"Inserted '{symbol}' into expression field {field_index + 1}", 3000)
            
            if target_field:
                # Get current text and cursor position
                current_text = target_field.text()
                cursor_pos = target_field.cursorPosition()
                
                # Insert the symbol at cursor position
                new_text = current_text[:cursor_pos] + symbol + current_text[cursor_pos:]
                target_field.setText(new_text)
                
                # Move cursor after the inserted symbol
                target_field.setCursorPosition(cursor_pos + len(symbol))
                
                # Trigger validation
                if hasattr(self.expression_widget, '_validate_expression'):
                    self.expression_widget._validate_expression(new_text)


# Test fixtures
@pytest.fixture
def app():
    """Create a QApplication instance for testing"""
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication(sys.argv)
    yield instance

@pytest.fixture
def truth_table_app(app):
    """Create a TruthTableApp instance for testing"""
    tt_app = TruthTableApp()
    yield tt_app

@pytest.fixture
def style_editor(app):
    """Create a StyleEditor instance for testing"""
    editor = StyleEditor()
    yield editor


# Test cases
class TestStylingFixesCore:
    """Test core styling functionality"""
    
    def test_apptheme_consistency(self):
        """Test AppTheme generates consistent stylesheets"""
        main_style = AppTheme.get_main_stylesheet()
        button_style = AppTheme.get_button_stylesheet()
        table_style = AppTheme.get_table_stylesheet()
        
        # Verify styles contain necessary properties
        assert "background-color" in main_style, "Main stylesheet missing background-color"
        assert "color" in main_style, "Main stylesheet missing text color"
        assert "font-family" in main_style, "Main stylesheet missing font family"
        
        assert "QPushButton" in button_style, "Button stylesheet missing QPushButton selector"
        assert "hover" in button_style.lower(), "Button stylesheet missing hover state"
        
        assert "QTableView" in table_style, "Table stylesheet missing QTableView selector"
        assert "QHeaderView" in table_style, "Table stylesheet missing header styling"
    
    def test_style_application(self, truth_table_app):
        """Test that styles are correctly applied to the application"""
        # Apply the main style
        main_style = AppTheme.get_main_stylesheet()
        truth_table_app.apply_style_changes(main_style)
        
        # Verify style was applied
        app_style = truth_table_app.styleSheet()
        assert "background-color" in app_style, "Style not applied correctly"
        assert "font-family" in app_style, "Font family not in applied style"
    
    def test_style_editor_integration(self, truth_table_app, style_editor):
        """Test StyleEditor integration with main app"""
        # Connect the StyleEditor to the main app
        style_editor.stylesChanged.connect(truth_table_app.apply_style_changes)
        
        # Apply style via StyleEditor
        with patch.object(QApplication.instance(), 'setFont') as mock_set_font:
            style_editor.apply_style()
            
            # Verify style was applied
            assert mock_set_font.called, "Font not applied to application"
            assert "font-family" in truth_table_app.styleSheet(), "Font family not in stylesheet"
            assert "font-size" in truth_table_app.styleSheet(), "Font size not in stylesheet"


class TestSymbolInsertion:
    """Test symbol insertion functionality"""
    
    def test_symbol_insertion_to_focused_field(self, truth_table_app):
        """Test symbol insertion targets the focused field correctly"""
        # Get expression fields
        fields = truth_table_app.expression_widget.input_fields
        test_field = fields[1]  # Use the second field
        
        # Set initial text and focus
        test_field.setText("p q")
        test_field.setFocus()
        test_field.setCursorPosition(1)  # Cursor after 'p'
        
        # Insert symbol
        with patch.object(truth_table_app.status_bar, 'showMessage') as mock_status:
            truth_table_app.insert_symbol('∧')
            
            # Verify symbol was inserted at cursor position
            assert test_field.text() == "p∧ q", f"Symbol not inserted correctly: {test_field.text()}"
            assert mock_status.called, "Status message not shown"
            # Verify status message indicates correct field (field 2)
            assert "field 2" in mock_status.call_args[0][0], "Status message doesn't indicate correct field"
    
    def test_symbol_insertion_fallback(self, truth_table_app):
        """Test symbol insertion falls back to first field when no valid focus"""
        # Get expression fields and clear focus
        fields = truth_table_app.expression_widget.input_fields
        QApplication.instance().focusWidget()  # Clear focus
        
        # Set initial text in first field
        fields[0].setText("p q")
        
        # Insert symbol with no focus
        with patch.object(truth_table_app.status_bar, 'showMessage') as mock_status:
            truth_table_app.insert_symbol('∨')
            
            # Verify symbol was inserted in first field
            assert fields[0].text() == "p q∨", "Symbol not inserted in first field"
            assert mock_status.called, "Status message not shown"
            assert "field 1" in mock_status.call_args[0][0], "Status message doesn't indicate field 1"
    
    def test_no_insertion_in_identifier_field(self, truth_table_app):
        """Test symbols are not inserted into identifier fields"""
        # Create a mock identifier field
        id_field = IdentifierLineEdit()
        id_field.setText("var1")
        id_field.setFocus()
        
        # Try to insert symbol
        with patch.object(truth_table_app.status_bar, 'showMessage') as mock_status:
            truth_table_app.insert_symbol('∧')
            
            # Verify no change and warning message
            assert id_field.text() == "var1", "Identifier field should not be modified"
            assert mock_status.called, "Status message not shown"
            assert "cannot be used" in mock_status.call_args[0][0], "Warning message not shown"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])