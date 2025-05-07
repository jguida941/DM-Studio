#!/usr/bin/env python3
"""
Component Test Script for Truth Table Educational Tool

This script tests individual components of the Truth Table tool to ensure they work correctly.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QPushButton, QLabel, QLineEdit, QToolBar, QStatusBar,
    QGraphicsDropShadowEffect, QTabWidget
)
from PyQt6.QtCore import Qt, QSize, QPoint, QRect
from PyQt6.QtGui import QColor

# Import the components to test
try:
    from Visual_Truth_Table import (
        IdentifierLineEdit, 
        ExpressionEvaluator,
        FloatingSymbolToolbar
    )
except ImportError:
    # Define a simplified version for isolated testing
    from PyQt6.QtWidgets import QLineEdit, QToolTip
    
    class IdentifierLineEdit(QLineEdit):
        """Simplified version for testing"""
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setToolTip("Enter a valid variable name")
            self.base_style = "QLineEdit { padding: 8px; border: 1px solid #aaa; }"
            self.setStyleSheet(self.base_style)
            self.textChanged.connect(self._validate_text)
            
        def keyPressEvent(self, event):
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                event.accept()
                return
                
            if event.text() and event.text() in ['∧', '∨', '¬', '→', '↔', '⊕']:
                event.accept()
                QToolTip.showText(self.mapToGlobal(QPoint(0, -30)), 
                                "Logical symbols cannot be used in variable names", 
                                self)
                return
                
            super().keyPressEvent(event)
            
        def _validate_text(self, text):
            if not text:
                self.setStyleSheet(self.base_style)
                return
                
            valid = text.isidentifier()
            if valid:
                self.setStyleSheet(self.base_style + 
                                  "QLineEdit { background-color: #eeffee; }")
            else:
                self.setStyleSheet(self.base_style + 
                                  "QLineEdit { background-color: #ffeeee; }")


class TestApp(QMainWindow):
    """Simple application to test the components"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Component Test")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create a status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create a tab widget to organize our tests
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create test widgets for different features
        id_widget = self._create_identifier_test()
        symbols_widget = self._create_symbol_test()
        button_style_widget = self._create_button_style_test()
        
        # Add tabs
        self.tabs.addTab(id_widget, "IdentifierLineEdit")
        self.tabs.addTab(symbols_widget, "Symbol Insertion")
        self.tabs.addTab(button_style_widget, "Button Styling")
        
    def _create_identifier_test(self):
        """Create test tab for IdentifierLineEdit"""
        id_section = QWidget()
        id_layout = QVBoxLayout(id_section)
        id_layout.addWidget(QLabel("<h2>Test IdentifierLineEdit</h2>"))
        id_layout.addWidget(QLabel("Test typing in variable field:"))
        self.id_edit = IdentifierLineEdit()
        id_layout.addWidget(self.id_edit)
        id_layout.addWidget(QLabel("Try to type special characters, symbols, and hit Enter"))
        id_layout.addStretch()
        return id_section
        
    def _create_symbol_test(self):
        """Create test tab for symbol insertion"""
        symbol_section = QWidget()
        symbol_layout = QVBoxLayout(symbol_section)
        symbol_layout.addWidget(QLabel("<h2>Test Symbol Insertion</h2>"))
        
        # Create a symbol toolbar
        symbol_bar = QToolBar("Symbols")
        symbol_bar.setMovable(False)
        symbols = ['∧', '∨', '¬', '→', '↔', '⊕', '^', '&', '|', '~']
        for sym in symbols:
            btn = QPushButton(sym)
            btn.setFixedSize(40, 40)
            btn.clicked.connect(lambda _, s=sym: self.insert_symbol(s))
            symbol_bar.addWidget(btn)
            
        symbol_layout.addWidget(symbol_bar)
        
        symbol_layout.addWidget(QLabel("Expression field (regular QLineEdit):"))
        self.expr_edit = QLineEdit()
        symbol_layout.addWidget(self.expr_edit)
        symbol_layout.addWidget(QLabel("Click in this field and use the symbol buttons above"))
        symbol_layout.addStretch()
        return symbol_section
    
    def _create_button_style_test(self):
        """Create test tab for button styling comparison"""
        style_section = QWidget()
        style_layout = QVBoxLayout(style_section)
        style_layout.addWidget(QLabel("<h2>Test Improved Button Styling</h2>"))
        style_layout.addWidget(QLabel("Button Size and Contrast Comparison:"))
        
        # Compare old and new button styles
        comparison_layout = QHBoxLayout()
        
        # Old style section
        old_style_layout = QVBoxLayout()
        old_style_layout.addWidget(QLabel("Original Style (30x30):"))
        
        old_symbol_layout = QHBoxLayout()
        old_symbols = ['∧', '∨', '¬', '→', '↔', '⊕']
        for sym in old_symbols:
            btn = QPushButton(sym)
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("""
                QPushButton {
                    background: #252525;
                    border: 1px solid #444;
                    border-radius: 15px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #00FFAA;
                    color: #000;
                }
            """)
            old_symbol_layout.addWidget(btn)
        
        old_style_layout.addLayout(old_symbol_layout)
        comparison_layout.addLayout(old_style_layout)
        
        # New style section
        new_style_layout = QVBoxLayout()
        new_style_layout.addWidget(QLabel("Improved Style (42x42):"))
        
        new_symbol_layout = QHBoxLayout()
        new_symbols = ['∧', '∨', '¬', '→', '↔', '⊕']
        for sym in new_symbols:
            btn = QPushButton(sym)
            btn.setFixedSize(42, 42)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2A2A2A;
                    border: 1px solid #777;
                    border-radius: 21px;
                    font-size: 20px;
                    font-weight: bold;
                    color: #FFFFFF;
                }
                QPushButton:hover {
                    background: #00FFAA;
                    color: #000000;
                    border: 2px solid #00FFFF;
                }
            """)
            
            # Add glow effect
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(12)
            glow.setColor(QColor(0, 255, 170, 130))
            glow.setOffset(0)
            btn.setGraphicsEffect(glow)
            
            new_symbol_layout.addWidget(btn)
        
        new_style_layout.addLayout(new_symbol_layout)
        comparison_layout.addLayout(new_style_layout)
        
        style_layout.addLayout(comparison_layout)
        
        # Add a label explaining the improvements
        improvements_label = QLabel(
            """
            <p><strong>Improvements Made:</strong></p>
            <ul>
                <li>Increased button size from 30x30 to 42x42 for better visibility and touch targets</li>
                <li>Improved contrast with lighter background (#2A2A2A vs #252525)</li>
                <li>Increased font size from 16px to 20px for better legibility</li>
                <li>Added explicit white color for symbols to ensure visibility</li>
                <li>Enhanced hover state with wider 2px borders and contrasting colors</li>
                <li>Added glow effect for visual emphasis</li>
            </ul>
            """
        )
        improvements_label.setTextFormat(Qt.TextFormat.RichText)
        style_layout.addWidget(improvements_label)
        
        style_layout.addStretch()
        return style_section
        
    def insert_symbol(self, sym):
        """Symbol insertion method"""
        focused_widget = QApplication.focusWidget()
        
        if isinstance(focused_widget, QLineEdit):
            # Special handling for IdentifierLineEdit
            if isinstance(focused_widget, IdentifierLineEdit):
                self.status_bar.showMessage(
                    "Cannot insert logical symbol in variable name field", 3000)
                return
                
            # Insert the symbol in regular line edit
            pos = focused_widget.cursorPosition()
            current_text = focused_widget.text()
            new_text = current_text[:pos] + sym + current_text[pos:]
            focused_widget.setText(new_text)
            focused_widget.setCursorPosition(pos + len(sym))
            self.status_bar.showMessage(f"Inserted symbol: {sym}", 1500)
        else:
            self.status_bar.showMessage(
                "Please click in an expression field before inserting symbols", 3000)


def main():
    app = QApplication(sys.argv)
    
    # Apply dark theme for better testing of contrast
    app.setStyleSheet("""
        QWidget {
            background-color: #121212;
            color: #FFFFFF;
        }
        QTabWidget::pane {
            border: 1px solid #444;
        }
        QTabBar::tab {
            background-color: #252525;
            padding: 8px 12px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #2980B9;
        }
        QLabel {
            color: #DDDDDD;
        }
    """)
    
    window = TestApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 