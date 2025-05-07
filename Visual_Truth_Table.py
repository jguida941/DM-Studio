#!/usr/bin/env python3

"""
Truth Table Educational Tool

This application generates truth tables for logical expressions and provides
educational content about logic operators and expressions.
"""

import sys
import re
import ast
import functools
from itertools import product

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableView, QSpinBox, QScrollArea, QCheckBox,
    QComboBox, QFileDialog, QColorDialog, QFontDialog, QInputDialog, QDialog,
    QTabWidget, QTextEdit, QGroupBox, QSplitter, QMessageBox, QHeaderView, 
    QToolBar, QStatusBar, QGridLayout, QFrame, QSizePolicy, QSpacerItem, 
    QToolTip, QMenu, QDockWidget, QStyle, QStyleFactory, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QSize, QAbstractTableModel, pyqtSignal, QModelIndex, QRegularExpression, 
    QRect, QPoint, QPropertyAnimation, QEasingCurve, QTimer, QObject, pyqtProperty
)
from PyQt6.QtGui import (
    QColor, QBrush, QFont, QPainter, QPen, QIcon, QPixmap, QAction, QPalette, 
    QRegularExpressionValidator, QLinearGradient, QRadialGradient, QConicalGradient,
    QCursor
)

# Import the KarnaughMapWidget
from karnaugh_map_widget import KarnaughMapWidget


# Custom QLineEdit subclass that restricts input to valid Python identifiers
class IdentifierLineEdit(QLineEdit):
    """
    A QLineEdit subclass for variable names that ensures input is a valid Python identifier.
    
    Features:
    - Restricts input to valid identifier characters (letters, numbers, underscore)
    - Changes background color to provide visual feedback on validity
    - Shows tooltip with validation error messages
    - Prevents Enter key from triggering form submission
    - Avoids overwriting user input when possible
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup tooltip
        self.setToolTip("Enter a valid variable name (letters, numbers, underscore)")
        
        # Set validator for Python identifiers
        validator = QRegularExpressionValidator(QRegularExpression(r'[A-Za-z_][A-Za-z0-9_]*'))
        self.setValidator(validator)
        
        # Connect text change signal to validation method
        self.textChanged.connect(self._validate_text)
        
        # Base stylesheet for this widget
        self.base_style = """
            QLineEdit {
                padding: 8px;
                border: 1px solid #aaa;
                border-radius: 4px;
                font-size: 14px;
            }
        """
        self.setStyleSheet(self.base_style)
    
    def keyPressEvent(self, event):
        """
        Override keyPressEvent to control key handling

        Specifically:
        - Prevents Enter/Return from triggering form submission
        - Only allows valid identifier characters
        """
        # Don't let Enter/Return keys bubble up
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.accept()
            return

        # For standard keys, check if the key is a valid identifier character
        if event.text():
            key_char = event.text()
            current_text = self.text()
            cursor_pos = self.cursorPosition()

            # Allow any character if the identifier rules are met overall
            potential_text = current_text[:cursor_pos] + key_char + current_text[cursor_pos:]
            matches_pattern = bool(re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', potential_text))

            # Special handling for logical symbols - never allowed in identifiers
            if key_char in ['∧', '∨', '¬', '→', '↔', '⊕']:
                event.accept()  # Accept but don't process
                # Show a tooltip explaining why symbol isn't allowed
                self.setToolTip("Logical symbols cannot be used in variable names")
                QToolTip.showText(self.mapToGlobal(QPoint(0, -30)),
                                 "Logical symbols cannot be used in variable names",
                                 self,
                                 QRect(),
                                 2000)  # Show for 2 seconds
                return

            # If character would make identifier invalid, don't accept it
            if not matches_pattern and cursor_pos == 0 and not key_char.isalpha() and key_char != '_':
                event.accept()  # Accept but don't process
                # Show a tooltip explaining the issue
                self.setToolTip("Variable names must start with a letter or underscore")
                QToolTip.showText(self.mapToGlobal(QPoint(0, -30)),
                                 "Variable names must start with a letter or underscore",
                                 self,
                                 QRect(),
                                 2000)
                return
            elif not matches_pattern and not (key_char.isalnum() or key_char == '_'):
                event.accept()  # Accept but don't process
                # Show a tooltip explaining the issue
                self.setToolTip("Variable names can only contain letters, numbers, and underscores")
                QToolTip.showText(self.mapToGlobal(QPoint(0, -30)),
                                 "Variable names can only contain letters, numbers, and underscores",
                                 self,
                                 QRect(),
                                 2000)
                return

        # Process the key event normally
        super().keyPressEvent(event)
    
    def _validate_text(self, text):
        """
        Validate the text and provide visual feedback
        
        This method:
        - Checks if the text is a valid Python identifier
        - Changes background color based on validity
        - Shows appropriate tooltip
        """
        if not text:
            # Empty text is fine (visually neutral)
            self.setStyleSheet(self.base_style)
            self.setToolTip("Enter a valid variable name (letters, numbers, underscore)")
            return
            
        # Check if the text is a valid Python identifier
        valid = text.isidentifier()
        
        if valid:
            # Valid - green tint
            self.setStyleSheet(self.base_style + """
                QLineEdit {
                    background-color: #eeffee;
                    border-color: #5cb85c;
                }
            """)
            self.setToolTip("Valid variable name")
        else:
            # Invalid - red tint
            self.setStyleSheet(self.base_style + """
                QLineEdit {
                    background-color: #ffeeee;
                    border-color: #d9534f;
                }
            """)
            # More specific error messages
            if not text[0].isalpha() and text[0] != '_':
                self.setToolTip("Variable names must start with a letter or underscore")
            else:
                self.setToolTip("Variable names can only contain letters, numbers, and underscores")


# FuturisticUI class for advanced styling and animations
class FuturisticUI:
    """
    Advanced UI styling and animation utilities for a modern, futuristic look.
    Provides methods for creating glowing buttons, gradient backgrounds, and animations.
    """
    
    # Color constants
    PRIMARY = QColor(41, 128, 185)      # Blue
    SECONDARY = QColor(142, 68, 173)    # Purple
    ACCENT = QColor(0, 255, 170)        # Neon green
    HIGHLIGHT = QColor(255, 69, 0)      # Orange-red
    
    BACKGROUND = QColor(18, 18, 18)     # Nearly black
    SURFACE = QColor(30, 30, 30)        # Dark gray
    
    TEXT_PRIMARY = QColor(255, 255, 255)  # White
    TEXT_SECONDARY = QColor(180, 180, 180)  # Light gray
    
    @staticmethod
    def set_futuristic_style(app):
        """Apply futuristic style to the entire application"""
        if isinstance(app, QApplication):
            app.setStyleSheet("""
            QWidget { 
                background: #121212; 
                color: #EEE; 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            }
            QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                               stop:0 #1E1E1E, stop:1 #2D2D2D); 
                border: 1px solid #333;
                border-radius: 8px; 
                padding: 8px 16px;
                color: #EEE;
                font-weight: bold;
                min-height: 24px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                               stop:0 #2D2D2D, stop:1 #3D3D3D);
                border: 1px solid #00FFAA;
            }
            QPushButton:pressed { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                               stop:0 #1A1A1A, stop:1 #2A2A2A);
            }
            QLineEdit, QTextEdit, QSpinBox { 
                background: #1E1E1E; 
                border: 1px solid #333; 
                border-radius: 4px;
                padding: 4px 8px;
                color: #EEE;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus { 
                border: 1px solid #00FFAA;
                background: #252525;
            }
            QTableView {
                background: #1E1E1E;
                border: 1px solid #333;
                border-radius: 4px;
                alternate-background-color: #252525;
                gridline-color: #333;
            }
            QHeaderView::section {
                background: #2980B9;
                color: white;
                font-weight: bold;
                padding: 4px;
                border: none;
            }
            QDockWidget::title {
                background: #2980B9;
                color: white;
                padding: 6px;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #333;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #1E1E1E;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #2980B9;
                color: white;
            }
            QScrollBar:vertical {
                background: #1E1E1E;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #333;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00FFAA;
            }
            QComboBox {
                background: #1E1E1E;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 4px 8px;
                color: #EEE;
            }
            QComboBox:focus {
                border: 1px solid #00FFAA;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #333;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #555;
                background: #1E1E1E;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #00FFAA;
                background: #00FFAA;
                border-radius: 2px;
            }
            QLabel {
                color: #EEE;
            }
            QGroupBox {
                border: 1px solid #333;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 3px;
                color: #00FFAA;
            }
            QToolBar {
                background: #121212;
                border-bottom: 1px solid #333;
                spacing: 4px;
            }
            QStatusBar {
                background: #1A1A1A;
                color: #CCC;
            }
            """)
    
    @staticmethod
    def create_neon_effect(widget, color=None, blur_radius=10, offset=0):
        """Add a neon glow effect to a widget"""
        if color is None:
            color = FuturisticUI.ACCENT
            
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(blur_radius)
        glow.setColor(color)
        glow.setOffset(offset)
        widget.setGraphicsEffect(glow)
        return glow
    
    @staticmethod
    def create_gradient_button(button, start_color=None, end_color=None, hover_color=None):
        """Apply a gradient background to a button"""
        if start_color is None:
            start_color = FuturisticUI.SURFACE
        if end_color is None:
            end_color = FuturisticUI.PRIMARY
        if hover_color is None:
            hover_color = FuturisticUI.ACCENT
            
        # Create stylesheets for normal and hover states
        normal_style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 {start_color.name()}, stop:1 {end_color.name()});
                border: 1px solid #333;
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 {end_color.name()}, stop:1 {start_color.name()});
            }}
        """

        hover_style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 {start_color.name()}, stop:1 {end_color.name()});
                border: 2px solid {hover_color.name()};
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 {end_color.name()}, stop:1 {start_color.name()});
            }}
        """

        # Apply normal style initially
        button.setStyleSheet(normal_style)

        # Set up event filters for hover effect
        class HoverFilter(QObject):
            def eventFilter(self, obj, event):
                if event.type() == event.Type.Enter:
                    obj.setStyleSheet(hover_style)
                    return True
                elif event.type() == event.Type.Leave:
                    obj.setStyleSheet(normal_style)
                    return True
                return False

        hover_filter = HoverFilter(button)
        button.installEventFilter(hover_filter)

        # Keep a reference to prevent garbage collection
        button._hover_filter = hover_filter

        return button
    
    @staticmethod
    def create_animation(widget, property_name, start_value, end_value, duration=300, easing_curve=QEasingCurve.Type.OutCubic):
        """Create an animation for a widget property"""
        animation = QPropertyAnimation(widget, property_name)
        animation.setDuration(duration)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setEasingCurve(easing_curve)
        return animation
    
    @staticmethod
    def pulse_effect(widget, color=None):
        """Create a pulsing glow effect for a widget"""
        if color is None:
            color = FuturisticUI.ACCENT
        
        # Create initial glow effect
        glow = FuturisticUI.create_neon_effect(widget, color, blur_radius=5)
        
        # Set up timer for pulsing
        timer = QTimer(widget)
        timer.timeout.connect(lambda: FuturisticUI._update_pulse(glow))
        timer.start(50)  # Update every 50ms
        
        # Store pulse parameters
        widget._pulse_data = {
            'effect': glow,
            'timer': timer,
            'direction': 1,
            'min_blur': 3,
            'max_blur': 15,
            'current': 5
        }
        
        return timer
    
    @staticmethod
    def _update_pulse(effect):
        """Update the pulsing effect (internal use)"""
        widget = effect.parent()
        
        # Safety check - make sure widget exists and has _pulse_data
        if widget is None or not hasattr(widget, '_pulse_data'):
            return
            
        data = widget._pulse_data
        
        # Update blur radius
        data['current'] += 0.5 * data['direction']
        
        # Change direction if at min/max
        if data['current'] >= data['max_blur']:
            data['direction'] = -1
        elif data['current'] <= data['min_blur']:
            data['direction'] = 1
            
        # Apply new blur radius
        effect.setBlurRadius(data['current'])

# Define modern theme and styling
class AppTheme:
    # This class serves as a centralized repository for all styling-related constants and utility methods.
    # Its purpose is to ensure a consistent visual theme throughout the application and to make
    # global style changes easier by modifying values in one place.
    # It defines colors for various UI elements, text, states, and specific truth table elements,
    # as well as common styling parameters like border radius.
    # It also provides static methods to generate CSS-like stylesheet strings for different PyQt6 widgets.
    """Modern application theme and styling"""
    # Main colors - These are the foundational colors for the application's branding and primary interactions.
    PRIMARY = QColor(41, 128, 185)  # Blue: Used for primary actions, headers, and important highlights. QColor object.
    SECONDARY = QColor(142, 68, 173)  # Purple: Used for secondary accents or alternative theming. QColor object.
    ACCENT = QColor(231, 76, 60)  # Red: Used for calls to action or to draw strong attention. QColor object.

    # UI colors - These define the colors for the general user interface chrome.
    BACKGROUND = QColor(248, 249, 250)  # Light gray: Used for the main window background. QColor object.
    SURFACE = QColor(255, 255, 255)  # White: Used for surfaces of widgets like input fields, cards. QColor object.
    PANEL = QColor(240, 242,
                   245)  # Off-white/Light gray: Used for panels, group box backgrounds, status bar. QColor object.

    # Text colors - Define the colors for text elements to ensure readability against UI backgrounds.
    TEXT_PRIMARY = QColor(33, 37, 41)  # Dark gray: Used for primary text content. QColor object.
    TEXT_SECONDARY = QColor(108, 117,
                            125)  # Medium gray: Used for secondary or less important text, descriptions. QColor object.

    # State colors - Colors used to indicate application states or feedback to the user.
    SUCCESS = QColor(40, 167, 69)  # Green: Indicates successful operations or valid states. QColor object.
    ERROR = QColor(220, 53, 69)  # Red: Indicates errors or invalid states. QColor object.
    WARNING = QColor(255, 193, 7)  # Yellow: Indicates warnings or cautionary messages. QColor object.

    # Truth table specific - Colors specifically for rendering the truth table cells.
    TRUE_COLOR = QColor(40, 167, 69)  # Green: Represents 'True' values in the table. Same as SUCCESS. QColor object.
    FALSE_COLOR = QColor(220, 53, 69)  # Red: Represents 'False' values in the table. Same as ERROR. QColor object.

    # Styling constants - Common numerical values for styling.
    BORDER_RADIUS = 6  # Integer: Defines the radius for rounded corners on buttons, inputs, etc.

    @staticmethod
    # This decorator indicates that get_button_stylesheet is a static method.
    # Static methods belong to the class rather than an instance of the class.
    # They can be called on the class itself (e.g., AppTheme.get_button_stylesheet()).
    def get_button_stylesheet(primary=True):
        # This method generates and returns a PyQt6 stylesheet string for QPushButton widgets.
        # Parameter:
        #   primary (bool): If True, returns stylesheet for a primary button (e.g., main action).
        #                   If False, returns stylesheet for a secondary/default button.
        # Returns:
        #   str: A CSS-like stylesheet string.
        # Concepts: PyQt6 stylesheets, f-strings for dynamic string formatting.
        # Connection: Used by various parts of the application (e.g., ExpressionWidget, TruthTableApp)
        #             to apply consistent styling to buttons.
        """Get stylesheet for buttons"""
        if primary:
            # Stylesheet for primary buttons (stronger visual hierarchy).
            return f"""
                QPushButton {{
                    background-color: {AppTheme.PRIMARY.name()}; /* Uses the defined PRIMARY color name (e.g., '#2980b9') */
                    color: white; /* Text color for primary buttons */
                    border: none; /* No border */
                    border-radius: {AppTheme.BORDER_RADIUS}px; /* Applies rounded corners */
                    padding: 8px 16px; /* Inner spacing */
                    font-weight: bold; /* Makes text bold */
                }}
                QPushButton:hover {{ /* Style when the mouse hovers over the button */
                    background-color: {QColor(AppTheme.PRIMARY.red() + 20, AppTheme.PRIMARY.green() + 20, AppTheme.PRIMARY.blue() + 20).name()}; /* Slightly lighter shade of primary */
                }}
                QPushButton:pressed {{ /* Style when the button is being pressed */
                    background-color: {QColor(AppTheme.PRIMARY.red() - 20, AppTheme.PRIMARY.green() - 20, AppTheme.PRIMARY.blue() - 20).name()}; /* Slightly darker shade of primary */
                }}
            """
        else:
            # Stylesheet for secondary/default buttons.
            return f"""
                QPushButton {{
                    background-color: {AppTheme.SURFACE.name()}; /* Uses the SURFACE color */
                    color: {AppTheme.TEXT_PRIMARY.name()}; /* Uses primary text color */
                    border: 1px solid {AppTheme.PANEL.name()}; /* Light border */
                    border-radius: {AppTheme.BORDER_RADIUS}px;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {AppTheme.PANEL.name()}; /* Changes background on hover */
                    border: 1px solid {AppTheme.PRIMARY.name()}; /* Highlights border with primary color on hover */
                }}
                QPushButton:pressed {{
                    background-color: {QColor(AppTheme.PRIMARY.red(), AppTheme.PRIMARY.green(), AppTheme.PRIMARY.blue(), 50).name()}; /* Primary color with alpha transparency on press */
                }}
            """

    @staticmethod
    # Static method to generate stylesheet for QLineEdit widgets.
    def get_lineedit_stylesheet():
        # Returns:
        #   str: A CSS-like stylesheet string for QLineEdit.
        # Concepts: PyQt6 stylesheets, QLineEdit styling, focus pseudo-state.
        # Connection: Used in VariableConfigWidget and ExpressionWidget for styling text input fields.
        """Get stylesheet for line edits"""
        return f"""
            QLineEdit {{
                background-color: {AppTheme.SURFACE.name()};
                border: 1px solid {AppTheme.PANEL.name()};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: 8px; /* Padding inside the line edit */
            }}
            QLineEdit:focus {{ /* Style when the line edit has keyboard focus */
                border: 2px solid {AppTheme.PRIMARY.name()}; /* Highlights border with primary color */
                background-color: {QColor(AppTheme.PRIMARY.red(), AppTheme.PRIMARY.green(), AppTheme.PRIMARY.blue(), 10).name()}; /* Very light primary background tint */
            }}
        """

    @staticmethod
    # Static method to generate stylesheet for QTableView widgets.
    def get_table_stylesheet():
        # Returns:
        #   str: A CSS-like stylesheet string for QTableView and its QHeaderView sections.
        # Concepts: PyQt6 stylesheets, QTableView styling, QHeaderView::section pseudo-state.
        # Connection: Used in TruthTableApp to style the main truth table display.
        """Get stylesheet for tables"""
        return f"""
            QTableView {{
                background-color: {AppTheme.SURFACE.name()};
                border: 1px solid {AppTheme.PANEL.name()};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                gridline-color: {AppTheme.PANEL.name()}; /* Color of the grid lines */
                selection-background-color: {QColor(AppTheme.PRIMARY.red(), AppTheme.PRIMARY.green(), AppTheme.PRIMARY.blue(), 70).name()}; /* Background of selected cells, primary with alpha */
            }}
            QHeaderView::section {{ /* Style for the header sections (column and row headers) */
                background-color: {AppTheme.PRIMARY.name()};
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }}
            QTableView::item {{ /* Style for individual cells/items in the table */
                padding: 4px; /* Padding within each cell */
            }}
        """

    @staticmethod
    # Static method to generate stylesheet for QDockWidget title bars.
    def get_dock_stylesheet():
        # Returns:
        #   str: A CSS-like stylesheet string for the title bar of QDockWidget.
        # Concepts: PyQt6 stylesheets, QDockWidget::title pseudo-state.
        # Connection: Used in TruthTableApp to style the "Variables" and "Expressions" dock widgets.
        """Get stylesheet for dock widgets"""
        return f"""
            QDockWidget::title {{ /* Style for the title bar of the dock widget */
                background: {AppTheme.PRIMARY.name()};
                color: white;
                padding: 8px;
                font-weight: bold;
            }}
        """

    @staticmethod
    # Static method to generate stylesheet for QTabWidget and QTabBar.
    def get_tab_stylesheet():
        # Returns:
        #   str: A CSS-like stylesheet string for QTabWidget panes and QTabBar tabs.
        # Concepts: PyQt6 stylesheets, QTabWidget::pane, QTabBar::tab, QTabBar::tab:selected pseudo-states.
        # Connection: Used in TruthTableApp to style the QTabWidget in the right panel (ExplanationWidget).
        """Get stylesheet for tab widgets"""
        return f"""
            QTabWidget::pane {{ /* The area where tab pages are shown */
                border: 1px solid {AppTheme.PANEL.name()};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                border-top-left-radius: 0px; /* To make the top edge flush with the selected tab */
                top: -1px; /* Minor adjustment to align with tab bar */
            }}
            QTabBar::tab {{ /* Style for individual tabs */
                background-color: {AppTheme.SURFACE.name()};
                color: {AppTheme.TEXT_SECONDARY.name()};
                border: 1px solid {AppTheme.PANEL.name()};
                border-bottom: none; /* No bottom border for unselected tabs, making selected tab appear connected to pane */
                border-top-left-radius: {AppTheme.BORDER_RADIUS}px;
                border-top-right-radius: {AppTheme.BORDER_RADIUS}px;
                padding: 8px 12px;
                margin-right: 2px; /* Small space between tabs */
            }}
            QTabBar::tab:selected {{ /* Style for the currently selected tab */
                background-color: {AppTheme.PRIMARY.name()};
                color: white;
                border-bottom: none; /* Ensures the selected tab visually merges with the pane */
                font-weight: bold;
            }}
        """

    @staticmethod
    # Static method to generate stylesheet for QSpinBox widgets.
    def get_spinbox_stylesheet():
        # Returns:
        #   str: A CSS-like stylesheet string for QSpinBox.
        # Concepts: PyQt6 stylesheets, QSpinBox styling, focus pseudo-state.
        # Connection: Used in VariableConfigWidget for the variable count spinbox.
        """Get stylesheet for spinboxes"""
        return f"""
            QSpinBox {{
                background-color: {AppTheme.SURFACE.name()};
                border: 1px solid {AppTheme.PANEL.name()};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                padding: 6px;
            }}
            QSpinBox:focus {{ /* Style when the spinbox has keyboard focus */
                border: 2px solid {AppTheme.PRIMARY.name()}; /* Highlights border with primary color */
            }}
        """

    @staticmethod
    # Static method to generate a global stylesheet for the main application window and common widgets.
    def get_main_stylesheet():
        # Returns:
        #   str: A CSS-like stylesheet string for QMainWindow, QDialog, QToolBar, QStatusBar, QLabel,
        #        QGroupBox, QScrollArea, and QTextEdit.
        # Concepts: PyQt6 stylesheets, global styling, styling various common widgets.
        # Connection: Applied to the main TruthTableApp instance to set a base theme for the application.
        """Get stylesheet for main window"""
        return f"""
            QMainWindow, QDialog {{ /* Style for main window and dialogs */
                background-color: {AppTheme.BACKGROUND.name()};
            }}
            QToolBar {{
                background-color: {AppTheme.PRIMARY.name()};
                spacing: 10px; /* Spacing between items in the toolbar */
                padding: 8px;
                border: none;
            }}
            QStatusBar {{
                background-color: {AppTheme.PANEL.name()};
                color: {AppTheme.TEXT_PRIMARY.name()};
            }}
            QLabel {{ /* Default style for all QLabels */
                color: {AppTheme.TEXT_PRIMARY.name()};
            }}
            QGroupBox {{ /* Style for QGroupBox frames */
                font-weight: bold;
                border: 1px solid {AppTheme.PANEL.name()};
                border-radius: {AppTheme.BORDER_RADIUS}px;
                margin-top: 20px; /* Margin above the group box to make space for its title */
                padding-top: 16px; /* Padding inside the group box, below the title */
            }}
            QGroupBox::title {{ /* Style for the title of a QGroupBox */
                subcontrol-origin: margin; /* Positions the title relative to the margin */
                left: 10px; /* Offset from the left */
                padding: 0 5px; /* Padding around the title text */
                color: {AppTheme.PRIMARY.name()}; /* Title text color */
            }}
            QScrollArea {{
                border: none; /* No border for scroll areas by default */
                background-color: transparent; /* Transparent background */
            }}
            QTextEdit {{ /* Default style for QTextEdit widgets */
                background-color: {AppTheme.SURFACE.name()};
                border: 1px solid {AppTheme.PANEL.name()};
                border-radius: {AppTheme.BORDER_RADIUS}px;
            }}
        """


class ExpressionEvaluator:
    # This class is designed for the safe parsing and evaluation of logical expressions provided by the user.
    # It uses Python's Abstract Syntax Tree (ast) module to analyze the structure of an expression
    # before evaluation. This is a crucial security measure to prevent the execution of arbitrary
    # or malicious code, as it allows only a whitelisted set of Python language features typical
    # of logical expressions.
    # It also handles the normalization of common logical symbols (e.g., '→', '∧') into their
    # Python equivalents (e.g., '<=', 'and').
    # This class does not have a UI component itself but provides the backend logic for expression handling.
    """Safe AST-based parser and evaluator for logical expressions"""

    # Allowed AST node types for safe evaluation - add ast.Expression
    # This set defines all Python AST node types that are permitted within a user-submitted expression.
    # If an expression, when parsed, contains any node type not in this set (e.g., function calls,
    # import statements, loops), it will be considered invalid or unsafe.
    # This whitelist is fundamental to the security of the expression evaluation.
    ALLOWED_NODES = {
        ast.Module,  # Represents a_module (usually the root of a script, but relevant if parsing with mode='exec')
        ast.Expr,
        # Represents an expression that is evaluated and its result discarded (e.g., a standalone literal or operation)
        ast.BoolOp,  # Represents boolean operations like 'and' and 'or'. Specific ops are ast.And, ast.Or.
        ast.UnaryOp,  # Represents unary operations like 'not'. Specific op is ast.Not.
        ast.Name,  # Represents a variable name (e.g., 'p', 'q'). Used with ast.Load when reading the variable.
        ast.And,  # Specific AST node for the 'and' boolean operation.
        ast.Or,  # Specific AST node for the 'or' boolean operation.
        ast.Not,  # Specific AST node for the 'not' unary operation.
        ast.Compare,  # Represents comparison operations (e.g., ==, !=, <, <=, >, >=).
        ast.Eq,  # Specific AST node for equality comparison (==).
        ast.NotEq,  # Specific AST node for inequality comparison (!=).
        ast.Lt,  # Specific AST node for less than comparison (<).
        ast.LtE,  # Specific AST node for less than or equal to comparison (<=).
        ast.Gt,  # Specific AST node for greater than comparison (>).
        ast.GtE,  # Specific AST node for greater than or equal to comparison (>=).
        ast.Load,  # Indicates that a variable name (ast.Name) is being read/loaded.
        ast.Constant,
        # Represents literal constants like True, False, numbers, strings. (Replaced ast.Num, ast.Str, ast.NameConstant in newer Python).
        ast.Expression  # The root node for an expression parsed with mode='eval'. This is important.
    }

    # Symbol mapping for display and parsing
    # This dictionary maps common logical symbols to their Python string equivalents.
    # This allows users to input expressions using familiar mathematical/logical notation,
    # which are then translated by _normalize_expression before AST parsing.
    SYMBOL_MAP = {
        '→': '<=',
        # Implication (p → q is equivalent to not p or q; for booleans 0/1, p <= q also works: 0<=0, 0<=1, 1<=1 are True, 1<=0 is False)
        '↔': '==',  # Equivalence (biconditional)
        '⊕': '!=',  # XOR (exclusive OR)
        '∧': 'and',  # Conjunction (AND)
        '∨': 'or',  # Disjunction (OR)
        '¬': 'not '  # NOT (negation). Note the trailing space to ensure correct parsing (e.g. 'not p' vs 'notp')
    }

    @classmethod
    # This decorator indicates that is_valid_expression is a class method.
    # It can be called on the class itself (e.g., ExpressionEvaluator.is_valid_expression()).
    # It receives the class (cls) as its first argument automatically.
    def is_valid_expression(cls, expr):
        # Purpose: Checks if a given expression string is syntactically valid Python for a logical expression
        #          and, more importantly, if it only contains allowed operations (AST nodes).
        # Parameters:
        #   expr (str): The expression string to validate.
        # Returns:
        #   tuple (bool, str): A boolean indicating validity (True if valid, False otherwise),
        #                      and a string message explaining the status or error.
        # Concepts: AST parsing (ast.parse), AST traversal (ast.walk), error handling (try-except).
        # Connection: Called by ExpressionWidget._validate_expression to provide real-time feedback to the user
        #             as they type an expression into a QLineEdit.
        """Check if expression is syntactically valid and safe"""
        if not expr.strip():  # Check if the expression is empty or only whitespace.
            return False, "Expression cannot be empty"

        try:
            # Step 1: Normalize the expression (replace symbols with Python operators).
            py_expr = cls._normalize_expression(expr)

            # Step 2: Parse the normalized expression into an Abstract Syntax Tree (AST).
            # mode='eval' is used because we expect a single expression that returns a value.
            # If parsing fails (e.g., syntax error), a SyntaxError will be raised.
            tree = ast.parse(py_expr, mode='eval')

            # Step 3: Traverse the AST to check if all nodes are allowed.
            # ast.walk(tree) generates all nodes in the tree in no specific order.
            for node in ast.walk(tree):
                if type(node) not in cls.ALLOWED_NODES:  # Check node type against the whitelist.
                    # If an unsupported node type is found, the expression is deemed unsafe/invalid.
                    return False, f"Unsupported operation: {type(node).__name__}"

            # If parsing and all node checks pass, the expression is considered valid.
            return True, "Valid expression"
        except SyntaxError as e:
            # Catch Python syntax errors during parsing.
            return False, f"Syntax error: {str(e)}"
        except Exception as e:
            # Catch any other unexpected errors during validation.
            return False, f"Error: {str(e)}"

    @classmethod
    # Class method for evaluating a pre-validated logical expression.
    def evaluate(cls, expr, var_dict):
        # Purpose: Evaluates a given logical expression string using a dictionary of variable values.
        #          This method assumes the expression has already been somewhat validated for safety by
        #          is_valid_expression or similar checks, but it re-validates AST nodes as a safeguard.
        # Parameters:
        #   expr (str): The logical expression string to evaluate.
        #   var_dict (dict): A dictionary mapping variable names (str) to their boolean values (bool).
        #                    Example: {'p': True, 'q': False}
        # Returns:
        #   bool: The boolean result of the evaluated expression.
        # Raises:
        #   ValueError: If the expression is empty, contains unsupported operations, or other evaluation issues occur.
        #   NameError: If the expression uses variables not defined in var_dict.
        # Concepts: AST parsing, AST compilation (compile), restricted evaluation (eval with limited globals/locals),
        #           error handling, string normalization.
        # Connection: Primarily called by TruthTableModel._generate_data to calculate the truth values for each
        #             expression column in the truth table for every row of variable assignments.
        """Evaluate a logical expression with the given variable values"""
        if not expr.strip():  # Ensure the expression is not empty.
            raise ValueError("Expression cannot be empty")

        try:
            # Debug output - useful during development, can be removed or made conditional for production.
            print(f"Evaluating expression: '{expr}'")
            print(f"Variables available: {var_dict}")

            # Step 1: Normalize the expression (replace symbols with Python operators).
            py_expr = cls._normalize_expression(expr)
            print(f"Normalized expression: '{py_expr}'")

            # Step 2: Parse the normalized expression into an AST.
            tree = ast.parse(py_expr, mode='eval')

            # Step 3: Walk the AST to check for allowed nodes and identify all variable names used.
            # This is a reinforcement of the safety check and helps identify required variables.
            variables_in_expr = set()  # Using a set to store unique variable names found.
            for node in ast.walk(tree):
                node_type = type(node)
                print(f"Node type: {node_type.__name__}")  # Debugging: shows AST node types being processed.
                if node_type not in cls.ALLOWED_NODES:
                    raise ValueError(f"Unsupported operation: {node_type.__name__}")
                if isinstance(node, ast.Name):  # If the node is a variable name identifier.
                    variables_in_expr.add(node.id)  # Add its name (id) to the set.
                    print(f"Found variable reference: {node.id}")  # Debugging.

            print(f"Variables in expression: {variables_in_expr}")  # Debugging.

            # Step 4: Ensure all variables used in the expression are provided in var_dict.
            # This prevents NameError during evaluation if a variable is used but not defined.
            missing_vars = [v for v in variables_in_expr if v not in var_dict]
            if missing_vars:
                # This is a critical error if the expression refers to variables not in the context.
                print(f"CRITICAL ERROR: Variables missing from dictionary: {missing_vars}")
                print(f"Available keys: {list(var_dict.keys())}")
                raise NameError(f"Undefined variable(s): {{', '.join(missing_vars)}}")

            # Step 5: Compile the AST into a code object.
            # '<string>' is a placeholder for the filename in tracebacks.
            # 'eval' mode indicates the code object should represent a single expression.
            code = compile(tree, '<string>', 'eval')

            # Step 6: Create a safe evaluation environment (locals for eval).
            # It includes Python's True/False and the user-provided variables from var_dict.
            # All variable names (keys) from var_dict are explicitly cast to str, and values to bool,
            # to ensure consistency, though var_dict keys should already be strings from variable names.
            safe_globals = {"__builtins__": {}}  # CRITICAL: Restrict access to built-in functions.
            safe_locals = {'True': True, 'False': False}
            for key, value in var_dict.items():
                safe_locals[str(key)] = bool(value)

            print(f"Safe evaluation dictionary: {safe_locals}")  # Debugging.

            # Step 7: Execute the compiled code.
            # The first argument to eval is the code object.
            # The second (globals) is restricted to prevent access to unsafe built-ins.
            # The third (locals) provides the context (True, False, and variable values).
            result = eval(code, safe_globals, safe_locals)

            # Step 8: Ensure the result is always a boolean.
            bool_result = bool(result)
            print(f"Result: {bool_result}")  # Debugging.
            return bool_result

        except Exception as e:
            # Catch any error during evaluation (e.g., NameError if somehow missed, TypeError for operations on wrong types)
            # and re-raise it as a ValueError to be handled by the caller (e.g., TruthTableModel).
            print(f"Error evaluating expression '{expr}': {e}")
            raise ValueError(f"Error evaluating '{expr}': {str(e)}")

    @classmethod
    # Helper class method to convert an expression string with custom logical symbols
    # into a standard Python expression string.
    def _normalize_expression(cls, expr):
        # Purpose: To allow users to input expressions using common logical symbols (like '→', '∧')
        #          and have them automatically converted to Python's equivalent operators ('and', 'or', etc.)
        #          before parsing and evaluation.
        # Parameters:
        #   expr (str): The raw expression string from the user.
        # Returns:
        #   str: The expression string with symbols replaced by Python keywords/operators.
        # Concepts: String manipulation (strip, replace), iteration over a dictionary.
        # Connection: Called internally by is_valid_expression and evaluate as a preprocessing step.
        """Convert expression with various notations to Python syntax"""
        py_expr = expr.strip()  # Remove leading/trailing whitespace.

        # Iterate through the SYMBOL_MAP dictionary.
        for symbol, op_keyword in cls.SYMBOL_MAP.items():
            # Replace each occurrence of the symbol (e.g., '∧') with its Python operator string (e.g., 'and').
            py_expr = py_expr.replace(symbol, op_keyword)

        return py_expr

    @classmethod
    # Class method to generate a simplified, human-readable step-by-step explanation of an expression's evaluation.
    def get_evaluation_steps(cls, expr, var_dict):
        # Purpose: To provide users with a textual breakdown of how an expression is evaluated,
        #          which is useful for educational purposes.
        # Parameters:
        #   expr (str): The original expression string.
        #   var_dict (dict): A dictionary of variable names to their boolean values for a specific scenario (e.g., a truth table row).
        # Returns:
        #   list[str]: A list of strings, where each string is a step in the evaluation explanation.
        #              Returns a list with an error message if an issue occurs.
        # Concepts: String manipulation, calling cls.evaluate for the final result.
        # Connection: Called by ExplanationWidget.update_step_evaluation to display these steps in the UI.
        # Note: This provides a simplified, high-level view of evaluation, not a true AST-based step-by-step evaluation.
        """Generate step-by-step explanation for expression evaluation"""
        if not expr.strip():  # Handle empty expression case.
            return ["Error: Expression is empty"]

        try:
            # Store the original expression for evaluation
            orig_expr = expr

            # Create a display version of the expression, replacing Python keywords with logical symbols
            display_expr = orig_expr
            # Create a reversed symbol map to convert Python operators back to logical symbols
            reversed_map = {}
            for symbol, op in cls.SYMBOL_MAP.items():
                # Special handling for 'not ' because it has a space
                if op == 'not ':
                    reversed_map['not'] = symbol
                else:
                    reversed_map[op] = symbol
            
            # Apply the reversed map to create a more readable display version
            for op, symbol in reversed_map.items():
                # Use regex with word boundaries to only replace whole operators
                import re
                display_expr = re.sub(r'\b' + re.escape(op) + r'\b', symbol, display_expr)
            
            steps = [f"Starting with expression: {display_expr}"]
            
            # 1. Substitute variable values with their boolean values
            steps.append("1. Substitute variable values:")
            substituted_expr = display_expr
            for var_name, var_value in var_dict.items():
                # Use regex with word boundaries to avoid partial replacements
                substituted_expr = re.sub(r'\b' + re.escape(var_name) + r'\b', 
                                         f"<b>{str(var_value).lower()}</b>", 
                                         substituted_expr)
            steps.append(f"   {substituted_expr}")
            
            # 2. Evaluate negations (¬) - highest precedence
            steps.append("2. Evaluate negations (¬):")
            # Find all patterns like "¬<b>true</b>" or "¬<b>false</b>" and evaluate them
            negation_pattern = r'¬\s*<b>(true|false)</b>'
            
            negation_match = re.search(negation_pattern, substituted_expr)
            if negation_match:
                # Process all negations
                negation_step = substituted_expr
                while negation_match:
                    neg_expr = negation_match.group(0)
                    value_str = negation_match.group(1)
                    result = not (value_str.lower() == "true")
                    result_str = f"<b>{str(result).lower()}</b>"
                    
                    # Replace just this specific negation
                    negation_step = negation_step.replace(neg_expr, result_str, 1)
                    
                    # Look for next negation
                    negation_match = re.search(negation_pattern, negation_step)
                
                steps.append(f"   {negation_step}")
            else:
                steps.append("   No negations to evaluate")
                negation_step = substituted_expr
            
            # 3. Evaluate AND operations (∧) - second precedence
            steps.append("3. Evaluate AND operations (∧):")
            # Find all patterns like "<b>true</b> ∧ <b>false</b>" and evaluate them
            and_pattern = r'<b>(true|false)</b>\s*∧\s*<b>(true|false)</b>'
            
            and_match = re.search(and_pattern, negation_step)
            if and_match:
                # Process all AND operations
                and_step = negation_step
                while and_match:
                    and_expr = and_match.group(0)
                    left_value = and_match.group(1).lower() == "true"
                    right_value = and_match.group(2).lower() == "true"
                    result = left_value and right_value
                    result_str = f"<b>{str(result).lower()}</b>"
                    
                    # Replace just this AND operation
                    and_step = and_step.replace(and_expr, result_str, 1)
                    
                    # Look for next AND operation
                    and_match = re.search(and_pattern, and_step)
                
                steps.append(f"   {and_step}")
            else:
                steps.append("   No AND operations to evaluate")
                and_step = negation_step
            
            # 4. Evaluate OR operations (∨) - lowest precedence
            steps.append("4. Evaluate OR operations (∨):")
            # Find all patterns like "<b>true</b> ∨ <b>false</b>" and evaluate them
            or_pattern = r'<b>(true|false)</b>\s*∨\s*<b>(true|false)</b>'
            
            or_match = re.search(or_pattern, and_step)
            if or_match:
                # Process all OR operations
                or_step = and_step
                while or_match:
                    or_expr = or_match.group(0)
                    left_value = or_match.group(1).lower() == "true"
                    right_value = or_match.group(2).lower() == "true"
                    result = left_value or right_value
                    result_str = f"<b>{str(result).lower()}</b>"
                    
                    # Replace just this OR operation
                    or_step = or_step.replace(or_expr, result_str, 1)
                    
                    # Look for next OR operation
                    or_match = re.search(or_pattern, or_step)
                
                steps.append(f"   {or_step}")
            else:
                steps.append("   No OR operations to evaluate")
                or_step = and_step
            
            # 5. Evaluate other operations (→, ↔, ⊕) if present
            # Implication (→)
            implies_pattern = r'<b>(true|false)</b>\s*→\s*<b>(true|false)</b>'
            implies_match = re.search(implies_pattern, or_step)
            if implies_match:
                steps.append("5. Evaluate implications (→):")
                implies_step = or_step
                
                while implies_match:
                    implies_expr = implies_match.group(0)
                    left_value = implies_match.group(1).lower() == "true"
                    right_value = implies_match.group(2).lower() == "true"
                    # p → q is equivalent to (not p) or q
                    result = (not left_value) or right_value
                    result_str = f"<b>{str(result).lower()}</b>"
                    
                    implies_step = implies_step.replace(implies_expr, result_str, 1)
                    implies_match = re.search(implies_pattern, implies_step)
                
                steps.append(f"   {implies_step}")
                final_step = implies_step
            else:
                final_step = or_step
            
            # Get the actual final result using the evaluator
            final_result_bool = cls.evaluate(orig_expr, var_dict)
            steps.append(f"Final result: <b>{str(final_result_bool).lower()}</b>")
            
            return steps
        except Exception as e:
            return [f"Error generating steps: {str(e)}"]


class VariableConfigWidget(QWidget):
    # This class defines a custom QWidget responsible for the UI section where users configure
    # the number of variables and their names for the truth table.
    # It includes a QSpinBox for the variable count and dynamically generated QLineEdits for names.
    # It emits a custom signal `variablesChanged` when the configuration is altered by the user.
    # Visual Layout:
    #   - Appears in the left QDockWidget titled "Variables" in the main application window.
    #   - Contains a title "Variables", a description, a QGroupBox "Number of Variables" (with a QSpinBox),
    #     and a QGroupBox "Variable Names" (with a QScrollArea containing QLineEdits for each variable name).
    #   - Also includes a QCheckBox "Auto-generate table when variables change".
    """Widget for configuring variables"""

    # Define custom signals
    # pyqtSignal is the PyQt mechanism for creating custom signals that QObject-derived classes can emit.
    # This signal will be emitted whenever the list of variable names is considered to have changed
    # (either by count or by content of the names).
    # The `list` argument indicates that the signal will carry a Python list (of variable names) as its payload.
    variablesChanged = pyqtSignal(list)

    def __init__(self, parent=None):
        # Constructor for VariableConfigWidget.
        # Parameters:
        #   parent (QWidget, optional): The parent widget. Defaults to None.
        # Purpose: Initializes the widget, sets default variable count and names, and builds the UI.
        # Concepts: QWidget initialization, instance attributes, calling UI setup method.
        super().__init__(parent)  # Call the constructor of the parent class (QWidget).

        # Default number of variables when the application starts.
        self.variable_count = 3
        # Default names for the initial variables.
        self.variable_names = ['p', 'q', 'r']
        # List to hold references to the QLineEdit widgets for variable names.
        # This is populated in _create_variable_inputs.
        self.variable_inputs = []

        self._build_ui()  # Call the method to construct the UI elements of this widget.

    def _build_ui(self):
        # Purpose: Constructs and arranges all the UI elements (widgets and layouts) for this widget.
        #          This method is called once during initialization.
        # Concepts: PyQt6 layouts (QVBoxLayout, QHBoxLayout), QWidget creation (QLabel, QGroupBox, QSpinBox,
        #           QScrollArea, QCheckBox), signal-slot connections, applying stylesheets.
        # Visual Layout: Sets up the main vertical structure, group boxes for count and names, and the auto-generate option.

        # Main layout for this widget: arranges child widgets vertically.
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 20)  # External margins: left, top, right, bottom.
        layout.setSpacing(18)  # Spacing between widgets/layouts added to this QVBoxLayout.

        # Title Label for the variable configuration section.
        title_label = QLabel("Variables")  # QLabel used to display static text.
        title_font = QFont()  # QFont object to customize the font.
        title_font.setBold(True)  # Make the title font bold.
        title_font.setPointSize(13)  # Set font size.
        title_label.setFont(title_font)
        layout.addWidget(title_label)  # Add the title label to the main layout.

        # Description Label providing context to the user.
        description_label = QLabel("Configure the variables used in your expressions:")
        description_label.setWordWrap(True)  # Allow text to wrap to multiple lines if it exceeds widget width.
        description_label.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY.name()};")  # Style using AppTheme.
        layout.addWidget(description_label)

        # GroupBox for "Number of Variables" controls.
        # QGroupBox provides a frame and a title, visually grouping related widgets.
        count_group = QGroupBox("Number of Variables")
        count_layout = QHBoxLayout()  # Horizontal layout for label and spinbox within this group box.
        count_layout.setContentsMargins(15, 20, 15, 20)  # Internal margins for the group box content.
        count_layout.setSpacing(15)  # Spacing between "Variables:" label and the spinbox.

        # QSpinBox for selecting the number of variables.
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(1, 8)  # Allow user to select between 1 and 8 variables (increased from 6).
        self.count_spinbox.setValue(self.variable_count)  # Set initial value from self.variable_count.
        self.count_spinbox.setStyleSheet(AppTheme.get_spinbox_stylesheet())  # Apply custom styling.
        self.count_spinbox.setMinimumHeight(36)  # Set minimum height for consistent UI.
        self.count_spinbox.setMinimumWidth(80)  # Set minimum width.
        # Signal-Slot Connection:
        # When the value of the spinbox changes (valueChanged signal), the _update_variable_count method (slot) is called.
        self.count_spinbox.valueChanged.connect(self._update_variable_count)

        count_layout.addWidget(QLabel("Variables:"))  # Label for the spinbox.
        count_layout.addWidget(self.count_spinbox)
        count_layout.addStretch()  # Adds stretchable space, pushing label and spinbox to the left.
        count_group.setLayout(count_layout)  # Set the QHBoxLayout as the layout for the QGroupBox.
        layout.addWidget(count_group)  # Add the group box to the main vertical layout.

        # GroupBox for "Variable Names" input fields.
        names_group = QGroupBox("Variable Names")
        names_layout = QVBoxLayout()  # Vertical layout for the scroll area within this group box.
        names_layout.setContentsMargins(15, 20, 15, 20)
        names_layout.setSpacing(10)

        # QScrollArea to contain variable name QLineEdits, allowing scrolling if there are many variables.
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # Allows the widget set in setWidget() to resize with the scroll area.
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)  # Remove the default frame of the scroll area for a cleaner look.
        self.scroll_area.setMinimumHeight(200)  # Ensure the scroll area has a reasonable minimum height
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Make the scroll area expand vertically

        self.variables_widget = QWidget()  # A container widget to hold the layout of variable inputs.
        self.variables_layout = QVBoxLayout()  # This layout will hold individual variable input rows (label + QLineEdit).
        self.variables_layout.setSpacing(15)
        self.variables_layout.setContentsMargins(5, 5, 5, 5)
        self.variables_widget.setLayout(self.variables_layout)
        self.scroll_area.setWidget(self.variables_widget)  # Set this container as the content of the scroll area.

        names_layout.addWidget(self.scroll_area)  # Add scroll area to the names_group layout.
        names_group.setLayout(names_layout)
        names_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Make the group box expand vertically
        layout.addWidget(names_group)  # Add the variable names group box to the main layout.

        # Layout for the "Auto-generate" checkbox.
        auto_layout = QHBoxLayout()
        auto_layout.setContentsMargins(5, 10, 5, 5)
        self.auto_generate = QCheckBox("Auto-generate table when variables change")  # QCheckBox for user toggle.
        self.auto_generate.setStyleSheet(f"font-size: 13px; color: {AppTheme.TEXT_PRIMARY.name()};")
        self.auto_generate.setChecked(True)  # Default state is checked (auto-generation enabled).
        # This checkbox's state is checked by `should_auto_generate()`.
        # Its `stateChanged` signal could be connected if direct action on change is needed beyond polling.
        auto_layout.addWidget(self.auto_generate)
        layout.addLayout(auto_layout)

        # Add stretchable space at the bottom of the main layout.
        # This pushes all content above it towards the top if space is available.
        layout.addStretch()

        self._create_variable_inputs()  # Populate the variable name input fields initially.
        self.setLayout(layout)  # Set the QVBoxLayout as the main layout for this VariableConfigWidget.

    def should_auto_generate(self):
        # Purpose: Provides a convenient way to check the state of the auto-generate checkbox.
        # Returns:
        #   bool: True if the "Auto-generate table when variables change" checkbox is checked, False otherwise.
        # Connection: Called by TruthTableApp.update_variables and TruthTableApp.update_expressions
        #             to decide whether to immediately regenerate the truth table after changes.
        """Check if auto-generate is enabled"""
        return self.auto_generate.isChecked()

    def _create_variable_inputs(self):
        # Purpose: Dynamically creates or recreates the QLineEdit widgets for entering variable names
        #          based on the current `self.variable_count`.
        #          This method is called initially and whenever the variable count changes.
        # Concepts: Dynamic widget creation and deletion, layout management, QLineEdit, QLabel.
        # Visual Layout: Populates the `self.variables_layout` (inside the QScrollArea) with rows,
        #              each containing a label ("Variable X:") and a QLineEdit for the name.

        # Clear existing QLineEdit inputs from self.variables_layout to prevent duplication or old widgets.
        # Iterate in reverse to safely remove items from the layout.
        for i in reversed(range(self.variables_layout.count())):
            item = self.variables_layout.itemAt(i)  # Get item at index i (can be widget or layout).
            if item.layout():  # If the item is a sub-layout.
                # Clear items from the sub-layout first.
                for j in reversed(range(item.layout().count())):
                    sub_item = item.layout().itemAt(j)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()  # Schedule widget for deletion.
                # Then remove the layout itself from self.variables_layout.
                self.variables_layout.removeItem(item)
            elif item.widget():  # If the item is a widget.
                item.widget().deleteLater()  # Schedule widget for deletion.

        # Reset the list that stores references to the QLineEdit widgets.
        self.variable_inputs = []

        # Create new QLineEdit input fields based on self.variable_count.
        for i in range(self.variable_count):
            # Create a container QWidget for each variable row (label + QLineEdit) for better styling and grouping.
            var_row_widget = QWidget()
            var_row_widget.setStyleSheet(
                "background-color: rgba(40, 40, 40, 0.8); border-radius: 8px;")  # Darker background, rounded corners
            input_layout = QHBoxLayout(var_row_widget)  # Horizontal layout for the row.
            input_layout.setContentsMargins(15, 15, 15, 15)  # Increased padding
            input_layout.setSpacing(20)  # Increased spacing

            # Label for the variable input field (e.g., "Variable 1:").
            label = QLabel(f"Variable {i + 1}:")
            label.setMinimumWidth(150)  # Increased width for alignment
            label_font = QFont()
            label_font.setBold(True)
            label_font.setPointSize(14)  # Larger font size
            label.setFont(label_font)
            # Align text to the right and vertically centered within the label area.
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            input_layout.addWidget(label)

            # Use IdentifierLineEdit instead of QLineEdit for entering the variable name.
            # This ensures only valid Python identifiers can be entered.
            # Set initial text from self.variable_names if available, otherwise generate a default (e.g., "var1").
            initial_name = self.variable_names[i] if i < len(self.variable_names) else f"var{i + 1}"
            input_box = IdentifierLineEdit()
            input_box.setText(initial_name)  # Set text after creating the widget
            
            # Enhanced styling for better visibility and usability
            input_box.setStyleSheet("""
                QLineEdit {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 2px solid #3a3a3a;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 14px;
                    selection-background-color: #2980b9;
                }
                QLineEdit:focus {
                    border: 2px solid #00ffaa;
                    background-color: #333333;
                }
                QLineEdit:hover {
                    border: 2px solid #4a4a4a;
                }
            """)
            
            input_box.setMinimumWidth(200)  # Increased width
            input_box.setMinimumHeight(40)  # Increased height
            
            # Ensure the widget is enabled and can receive input
            input_box.setEnabled(True)
            input_box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            
            # Add context menu for logical symbols
            input_box.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            input_box.customContextMenuRequested.connect(self._show_context_menu)

            # Signal-Slot Connection:
            # When the text in this QLineEdit changes (textChanged signal), the _variables_updated method (slot) is called.
            # This triggers validation and emits the `variablesChanged` signal if appropriate.
            input_box.textChanged.connect(self._variables_updated)
            self.variable_inputs.append(input_box)  # Store a reference to the QLineEdit.
            input_layout.addWidget(input_box)

            input_layout.addStretch()  # Pushes label and line_edit to the left within their row.

            self.variables_layout.addWidget(var_row_widget)  # Add the styled row widget to the vertical layout.

            # Add a small QSpacerItem between variable input rows for visual separation, except after the last one.
            if i < self.variable_count - 1:
                # QSizePolicy.Policy.Fixed means the spacer has a fixed vertical size.
                spacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
                self.variables_layout.addSpacerItem(spacer)

        # Increase spacing between variable input rows for better editor spacing
        self.variables_layout.setSpacing(15)
        
        # Update scroll area and group box size policies
        self.scroll_area.setMinimumHeight(300)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        
        # Find the parent group box (names_group) and set its size policy if possible
        parent = self.scroll_area.parent()
        while parent is not None:
            if isinstance(parent, QGroupBox):
                parent.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
                break
            parent = parent.parent()


# --- Symbol insertion context menu for variable name inputs ---
    def _show_context_menu(self, position):
        sender = self.sender()
        if not isinstance(sender, QLineEdit):
            return

        menu = QMenu()
        insert_and = QAction("Insert ∧", self)
        insert_or = QAction("Insert ∨", self)
        insert_not = QAction("Insert ¬", self)
        insert_implies = QAction("Insert →", self)
        insert_equiv = QAction("Insert ↔", self)
        insert_xor = QAction("Insert ⊕", self)

        for action, symbol in [(insert_and, "∧"), (insert_or, "∨"), (insert_not, "¬"),
                                (insert_implies, "→"), (insert_equiv, "↔"), (insert_xor, "⊕")]:
            action.triggered.connect(lambda _, s=symbol: self._insert_symbol(sender, s))
            menu.addAction(action)

        menu.exec(sender.mapToGlobal(position))

    def _insert_symbol(self, line_edit, symbol):
        cursor_pos = line_edit.cursorPosition()
        text = line_edit.text()
        line_edit.setText(text[:cursor_pos] + symbol + text[cursor_pos:])
        line_edit.setCursorPosition(cursor_pos + len(symbol))

    def _update_variable_count(self, count):
        # Slot method called when the value of `self.count_spinbox` changes.
        # Parameters:
        #   count (int): The new value from the spinbox (the desired number of variables).
        # Purpose: Updates `self.variable_count`, adjusts `self.variable_names` list to match the new count,
        #          recreates the variable input fields, and signals that variables have changed.
        # Concepts: Slot, list manipulation, calling other methods to update UI and emit signals.

        self.variable_count = count  # Update the internal count.

        # Adjust the self.variable_names list to match the new count.
        # If count is greater, append new default names (e.g., "var4", "var5").
        while len(self.variable_names) < count:
            self.variable_names.append(f"var{len(self.variable_names) + 1}")
        # If count is smaller, truncate the list.
        self.variable_names = self.variable_names[:count]

        self._create_variable_inputs()  # Re-generate the QLineEdit widgets for variable names.
        self._variables_updated()  # Call to validate names and emit the variablesChanged signal.

    def _variables_updated(self):
        # Slot method called when the text in any variable name QLineEdit changes, or when variable count changes.
        # Purpose: Updates `self.variable_names` from the QLineEdits, performs basic validation on names,
        #          and emits the `variablesChanged` signal with the current list of names.
        #          It also provides a simple warning mechanism via the main window's status bar if a name is invalid.
        # Concepts: Signal emission, basic string validation (isidentifier), status bar updates (indirectly).

        # Get current names from all QLineEdit input fields.
        current_names = self.get_variable_names()
        
        # Update internal list without enforcing validation (the IdentifierLineEdit already enforces valid identifiers)
        self.variable_names = current_names  # Update the internal list of names.

        # Check for empty names - these will be allowed during typing, but we'll show a warning
        has_empty_names = False
        
        # Check for duplicate names
        has_duplicate_names = len(current_names) != len(set(current_names))
        
        # Show warnings in the status bar if needed
        if has_empty_names or has_duplicate_names:
            main_window = self.parent()  # Assuming this widget is directly on a dock, get the dock.
            if main_window and hasattr(main_window, 'parent') and callable(main_window.parent):
                main_app_window = main_window.parent()  # Get the QMainWindow from the QDockWidget.
                if hasattr(main_app_window, "status_bar") and hasattr(main_app_window.status_bar, "showMessage"):
                    if has_empty_names:
                        main_app_window.status_bar.showMessage(
                            f"Warning: Empty variable names will be replaced with defaults when generating the table", 
                            3000)  # Show for 3s
                    elif has_duplicate_names:
                        main_app_window.status_bar.showMessage(
                            f"Warning: Duplicate variable names will be made unique when generating the table", 
                            3000)  # Show for 3s

        # Emit the variablesChanged signal, passing the current list of variable names.
        # The TruthTableApp will handle final validation when actually generating the table.
        self.variablesChanged.emit(self.variable_names)

    def get_variable_names(self):
        # Purpose: Retrieves the current text from all variable name QLineEdit input fields.
        # Returns:
        #   list[str]: A list of strings, where each string is the current text of a variable name input field.
        # Connection: Called by _variables_updated to get current names, and potentially by TruthTableApp
        #             to fetch names directly before generating the table.
        return [input_field.text() for input_field in self.variable_inputs]


class ExpressionWidget(QWidget):
    # This class defines a custom QWidget for managing a list of logical expressions.
    # Users can add, edit, and delete expressions, and also assign a unique color to each.
    # It provides QLineEdits for expression input, buttons for actions, and a help section for operators.
    # Visual Layout:
    #   - Appears in the left QDockWidget titled "Expressions" in the main application window, typically below VariableConfigWidget.
    #   - Contains a title "Logical Expressions", a description.
    #   - A QGroupBox "Expressions" houses:
    #       - A QScrollArea that dynamically displays input rows for each expression.
    #         Each row includes: a color indicator, an expression number label, a QLineEdit for the expression,
    #         a "Change Color" button, and a "Delete" button.
    #       - An "Add Expression" QPushButton below the scroll area.
    #   - A QGroupBox "Operator Reference" displays help text for logical operators and examples.
    # Interactivity:
    #   - Users type expressions into QLineEdits (with real-time validation feedback).
    #   - "Add Expression" button: adds a new expression input row.
    #   - "Delete" button (per expression): removes that expression.
    #   - "Change Color" button (per expression): opens a QColorDialog to pick a color for the expression's results in the table.
    # Styling: Uses AppTheme for QLineEdit, QPushButton, and QGroupBox styling.
    """Widget for managing multiple logical expressions"""

    # Define custom signals
    # Emitted when the list of expression strings changes (added, removed, or text edited and validated).
    # Carries a list of the current expression strings.
    expressionsChanged = pyqtSignal(list)
    # Emitted when the color associated with any expression changes.
    # Carries a list of QColor objects, corresponding to the order of expressions.
    expressionColorsChanged = pyqtSignal(list)

    def __init__(self, parent=None):
        # Constructor for ExpressionWidget.
        # Parameters:
        #   parent (QWidget, optional): The parent widget. Defaults to None.
        # Purpose: Initializes the widget, sets up default expressions and their colors, and builds the UI.
        # Concepts: QWidget initialization, default data, signal emission, UI construction.
        
        super().__init__(parent)
        
        # List to store expression strings
        self.expressions = ["p and q"]
        
        # List to store colors for expressions - will be applied to truth table cells
        self.expr_colors = [QColor(91, 192, 222)]
        
        # List to track expression input fields
        self.input_fields = []
        
        # Build the UI
        self._build_ui()
        
        # Emit initial signals
        self._expressions_updated()
        self._colors_updated()
        
    def test_expressions(self, var_names):
        """
        Test if the expressions are valid with the given variable names
        
        If an expression is invalid with the current variables, it will be
        replaced with a simpler valid expression.
        
        Parameters:
            var_names (list[str]): List of variable names to use for testing
        """
        print(f"Testing expressions with variables: {var_names}")  # Debug
        
        # Create a test dictionary with all values False
        test_dict = {name: False for name in var_names}
        
        # Test each expression and replace invalid ones
        updated = False
        valid_expressions = []
        
        for expr in self.expressions:
            try:
                # Try to evaluate the expression
                ExpressionEvaluator.evaluate(expr, test_dict)
                valid_expressions.append(expr)
            except Exception as e:
                # If evaluation fails, replace with a simple valid expression
                updated = True
                print(f"Invalid expression: {expr} - Error: {e}")
                
                if var_names:
                    # Use the first variable as a simple expression
                    new_expr = var_names[0]
                    valid_expressions.append(new_expr)
                else:
                    # No variables - use True
                    valid_expressions.append("True")
        
        # Update expressions if needed
        if updated:
            self.expressions = valid_expressions
            self._create_expression_inputs()
            self._expressions_updated()
                
    def _build_ui(self):
        # Purpose: Constructs and arranges all UI elements for the ExpressionWidget.
        #          Called once during initialization.
        # Concepts: PyQt6 layouts (QVBoxLayout, QHBoxLayout), QWidget creation (QLabel, QGroupBox, QScrollArea, QPushButton),
        #           applying stylesheets, rich text display.
        # Visual Layout: Organizes the title, description, the main expressions input area (scrollable),
        #              the "Add Expression" button, and the operator reference help section.

        layout = QVBoxLayout()  # Main vertical layout for this widget.
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(18)

        # Title Label for the expressions section.
        title_label = QLabel("Logical Expressions")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(13)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Description Label.
        description_label = QLabel("Create Boolean expressions to evaluate in the truth table:")
        description_label.setWordWrap(True)
        description_label.setStyleSheet(f"color: {AppTheme.TEXT_SECONDARY.name()};")
        layout.addWidget(description_label)

        # GroupBox for the main expression input area.
        expr_group = QGroupBox("Expressions")
        expr_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Allow the group box to expand
        expr_group_layout = QVBoxLayout()  # Vertical layout for content inside the group box.
        expr_group_layout.setContentsMargins(15, 20, 15, 15)
        expr_group_layout.setSpacing(20)

        # QScrollArea for dynamically added expression input rows.
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # Allows the inner widget to resize with the scroll area.
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)  # No border for the scroll area itself.
        self.scroll_area.setMinimumHeight(200)  # Ensure reasonable minimum height
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Allow the scroll area to expand

        self.expressions_widget_container = QWidget()  # Container widget for the scroll area's content.
        self.expressions_rows_layout = QVBoxLayout()  # This layout will hold individual expression input rows.
        self.expressions_rows_layout.setSpacing(20)
        self.expressions_rows_layout.setContentsMargins(5, 5, 5, 5)
        self.expressions_widget_container.setLayout(self.expressions_rows_layout)
        self.scroll_area.setWidget(self.expressions_widget_container)  # Set this container as the content of the scroll area.
        expr_group_layout.addWidget(self.scroll_area, 1)  # Add scroll area to the expr_group layout with a stretch factor of 1.

        # Layout for the "Add Expression" button.
        add_button_layout = QHBoxLayout()
        add_button_layout.setContentsMargins(5, 15, 5, 5)
        add_button_layout.setSpacing(15)

        self.add_expr_btn = QPushButton("Add Expression")
        self.add_expr_btn.setStyleSheet(AppTheme.get_button_stylesheet(True))  # Primary button style.
        self.add_expr_btn.setMinimumHeight(44)
        # QIcon.fromTheme attempts to load a standard system icon. If "list-add" is not found,
        # it might not display an icon or display a fallback.
        # For cross-platform consistency, embedding icons as resources is often preferred.
        self.add_expr_btn.setIcon(QIcon.fromTheme("list-add"))
        # Signal-Slot Connection: When clicked, calls the _add_expression method.
        self.add_expr_btn.clicked.connect(self._add_expression)
        add_button_layout.addWidget(self.add_expr_btn)
        add_button_layout.addStretch()  # Pushes button to the left.
        expr_group_layout.addLayout(add_button_layout)

        expr_group.setLayout(expr_group_layout)
        layout.addWidget(expr_group, 1)  # Add with stretch factor of 1 to make it expand

        # GroupBox for the "Operator Reference" help text.
        help_group = QGroupBox("Operator Reference")
        help_layout = QVBoxLayout()
        help_layout.setContentsMargins(15, 20, 15, 15)
        help_layout.setSpacing(15)

        # QLabel to display basic and symbolic operators. Uses RichText for bolding.
        operators_info_label = QLabel(
            "<b>Basic operators:</b> and, or, not<br>"
            "<b>Symbolic operators:</b> ∧ (AND), ∨ (OR), ¬ (NOT)<br>"
            "<b>Additional operators:</b> → (IMPLIES), ↔ (EQUIVALENT), ⊕ (XOR)"
        )
        operators_info_label.setTextFormat(Qt.TextFormat.RichText)  # Allows HTML-like formatting.
        operators_info_label.setWordWrap(True)
        operators_info_label.setStyleSheet("font-size: 13px;")
        help_layout.addWidget(operators_info_label)

        # QLabel to display examples of expressions. Uses RichText.
        examples_info_label = QLabel(
            "<b>Examples:</b><br>"
            "- p and q<br>"
            "- not p or q<br>"
            "- (p and q) or r<br>"
            "- p → q"
        )
        examples_info_label.setTextFormat(Qt.TextFormat.RichText)
        examples_info_label.setStyleSheet("font-size: 13px;")
        help_layout.addWidget(examples_info_label)

        help_group.setLayout(help_layout)
        help_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)  # Don't allow excessive vertical expansion
        layout.addWidget(help_group)

        layout.addStretch()  # Pushes all content to the top.

        self._create_expression_inputs()  # Populate initial expression input fields.
        self.setLayout(layout)  # Set the main layout for this widget.

    def _create_expression_inputs(self):
        # Purpose: Dynamically creates or recreates the UI elements for each expression in `self.expressions`.
        #          This includes labels, QLineEdits for input, and buttons for color change and deletion.
        #          Called initially and whenever expressions are added, deleted, or need a full UI refresh (e.g., after test_expressions).
        # Concepts: Dynamic widget creation/deletion, layout management, signal-slot connections with functools.partial.
        # Visual Layout: Populates `self.expressions_rows_layout` (inside the QScrollArea) with styled rows for each expression.

        # Clear existing expression input widgets from self.expressions_rows_layout.
        # Iterating in reverse is important for safe removal from layouts.
        for i in reversed(range(self.expressions_rows_layout.count())):
            # Get the layout item and the corresponding widget/layout
            item = self.expressions_rows_layout.itemAt(i)
            
            # If it's a widget, remove and delete it
            if item.widget():
                item.widget().deleteLater()
            # If it's a layout, need to clear it first
            elif item.layout():
                # Clear the nested layout
                nested_layout = item.layout()
                for j in reversed(range(nested_layout.count())):
                    nested_item = nested_layout.itemAt(j)
                    if nested_item.widget():
                        nested_item.widget().deleteLater()
                
                # Delete the layout itself
                nested_layout.deleteLater()
                
            # Remove the item from the layout
            self.expressions_rows_layout.removeItem(item)
        
        # Clear the input fields list
        self.input_fields = []
        
        # Create a UI row for each expression
        for idx, expr in enumerate(self.expressions):
            # Create a horizontal layout for this expression row
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(5, 10, 5, 10)  # Increased vertical padding
            
            # Create a container widget for better styling
            row_container = QWidget()
            row_container.setStyleSheet("background-color: rgba(40, 40, 40, 0.8); border-radius: 8px;")
            container_layout = QHBoxLayout(row_container)
            container_layout.setContentsMargins(15, 15, 15, 15)  # Increased padding
            container_layout.setSpacing(20)  # Increased spacing
            
            # Add color swatch
            color_swatch = QFrame()
            color_swatch.setFixedSize(QSize(32, 32))  # Larger color swatch
            
            # Set the swatch color from our list, with a fallback to default
            swatch_color = self.expr_colors[idx] if idx < len(self.expr_colors) else QColor(100, 100, 100)
            color_swatch.setStyleSheet(f"background-color: {swatch_color.name()}; border: 2px solid #555; border-radius: 4px;")
            container_layout.addWidget(color_swatch)
            
            # Add expression number label with larger font
            expr_label = QLabel(f"Expression {idx + 1}:")
            expr_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
            expr_label.setMinimumWidth(150)  # Fixed width for alignment
            container_layout.addWidget(expr_label)
            
            # Add line edit for the expression
            line_edit = QLineEdit(expr)
            line_edit.setStyleSheet("""
                QLineEdit {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 2px solid #3a3a3a;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 14px;
                    selection-background-color: #2980b9;
                }
                QLineEdit:focus {
                    border: 2px solid #00ffaa;
                    background-color: #333333;
                }
                QLineEdit:hover {
                    border: 2px solid #4a4a4a;
                }
            """)
            line_edit.setPlaceholderText("Enter a logical expression...")
            line_edit.setMinimumHeight(40)  # Taller input field
            line_edit.setEnabled(True)  # Ensure it's enabled
            line_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Strong focus policy
            
            # Connect the textChanged signal with a lambda that captures the current line_edit and index
            line_edit.textChanged.connect(
                lambda text, le=line_edit, i=idx: self._validate_expression(text, le, i)
            )
            
            # Add to input fields list for context menu setup
            self.input_fields.append(line_edit)
            container_layout.addWidget(line_edit, 1)  # Give stretch factor for reasonable width
            
            # Add color button with improved styling
            color_btn = QPushButton("Change Color")
            color_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 2px solid #3a3a3a;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    border: 2px solid #00ffaa;
                }
                QPushButton:pressed {
                    background-color: #202020;
                }
            """)
            color_btn.setFixedWidth(130)
            color_btn.setMinimumHeight(40)
            color_btn.clicked.connect(lambda _, i=idx: self._select_color(i))
            container_layout.addWidget(color_btn)
            
            # Add delete button with improved styling
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #802020;
                    color: #ffffff;
                    border: 2px solid #a03030;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #a02020;
                    border: 2px solid #ff3030;
                }
                QPushButton:pressed {
                    background-color: #601010;
                }
            """)
            delete_btn.setFixedWidth(90)
            delete_btn.setMinimumHeight(40)
            delete_btn.clicked.connect(lambda _, i=idx: self._delete_expression(i))
            delete_btn.setEnabled(len(self.expressions) > 1)  # Disable if only one expression
            container_layout.addWidget(delete_btn)
            
            # Add the container to the row layout
            row_layout.addWidget(row_container)
            
            # Add the row to the main expressions layout
            self.expressions_rows_layout.addLayout(row_layout)
            
            # Add spacing between rows
            if idx < len(self.expressions) - 1:
                spacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
                self.expressions_rows_layout.addSpacerItem(spacer)

    def _add_expression(self):
        # Slot method called when the "Add Expression" button is clicked.
        # Purpose: Adds a new default expression ("p or q") to the list and a new default color,
        #          then rebuilds the expression input UI and emits signals.
        #          Limits the total number of expressions to 5.
        # Concepts: List manipulation, UI update, signal emission, QMessageBox for warning.
        # Behavior: User clicks "Add Expression", a new input row appears if limit not reached.

        if len(self.expressions) < 5:  # Enforce a maximum of 5 expressions.
            self.expressions.append("p or q")  # Add a new default expression.

            # Add a new default color for the new expression.
            # This uses the same color generation logic as in _create_expression_inputs.
            new_color_idx = len(self.expr_colors)
            self.expr_colors.append(QColor(
                min(255, 100 + (new_color_idx * 50) % 155),
                min(255, 100 + (new_color_idx * 80) % 155),
                min(255, 100 + (new_color_idx * 120) % 155)
            ))

            self._create_expression_inputs()  # Regenerate the UI for expression inputs.
            self._expressions_updated()  # Emit signal that the list of expressions has changed.
            self._colors_updated()  # Emit signal that the list of colors has changed.
        else:
            # Show a warning message if the maximum number of expressions is reached.
            QMessageBox.warning(self, "Limit Reached", "Maximum of 5 expressions allowed.")

    def _delete_expression(self, idx):
        # Slot method called when a "Delete" button for a specific expression is clicked.
        # Parameters:
        #   idx (int): The index of the expression to delete.
        # Purpose: Removes the expression and its corresponding color from the lists,
        #          then rebuilds the UI and emits signals. Ensures at least one expression remains.
        # Concepts: List manipulation (del), UI update, signal emission, QMessageBox for warning.
        # Behavior: User clicks a "Delete" button, the corresponding expression row is removed if not the last one.

        if len(self.expressions) > 1:  # Ensure at least one expression remains.
            del self.expressions[idx]  # Remove expression at the given index.
            if idx < len(self.expr_colors):  # Safety check before deleting color.
                del self.expr_colors[idx]  # Remove corresponding color.

            self._create_expression_inputs()  # Regenerate UI.
            self._expressions_updated()  # Emit signal: expressions changed.
            self._colors_updated()  # Emit signal: colors changed.
        else:
            # Show warning if user tries to delete the last remaining expression.
            QMessageBox.warning(self, "Action Not Allowed", "At least one expression is required.")

    def _select_color(self, idx):
        # Slot method called when a "Change Color" button for an expression is clicked.
        # Parameters:
        #   idx (int): The index of the expression whose color is to be changed.
        # Purpose: Opens a QColorDialog to allow the user to pick a new color for the specified expression.
        #          If a valid color is chosen, updates the color list, rebuilds the UI (to show new color swatch),
        #          and emits the `expressionColorsChanged` signal.
        # Concepts: QColorDialog, UI update, signal emission.
        # Behavior: User clicks "Change Color", a color picker dialog appears. If a color is selected,
        #           the swatch for that expression updates, and the change is stored.
        """Open color dialog for expression"""
        current_color = self.expr_colors[idx]  # Get the current color for initial dialog selection.
        # QColorDialog.getColor() is a static method that shows the dialog and returns the selected QColor.
        # It's modal, meaning it blocks interaction with other parts of the app until closed.
        new_color = QColorDialog.getColor(current_color, self, f"Select Color for Expression {idx + 1}")

        if new_color.isValid():  # Check if the user selected a color (and didn't cancel).
            self.expr_colors[idx] = new_color  # Update the color in the list.
            # Recreate UI inputs to reflect the new color in the color indicator label.
            # A more optimized approach might be to find the specific QLabel for the color swatch
            # and update its stylesheet directly, avoiding a full UI rebuild for this widget.
            self._create_expression_inputs()
            self._colors_updated()  # Emit signal that colors have changed.

    def _validate_expression(self, text, line_edit_widget, idx):
        # Slot method called when the text in an expression QLineEdit changes.
        # Parameters:
        #   text (str): The new text from the QLineEdit.
        #   line_edit_widget (QLineEdit): The QLineEdit instance that emitted the signal.
        #   idx (int): The index of the expression being edited.
        # Purpose: Validates the syntax of the entered expression text using ExpressionEvaluator.
        #          Updates the QLineEdit's style (e.g., background color) and tooltip to give feedback.
        #          If valid, updates the expression in `self.expressions` and emits `expressionsChanged`.
        # Concepts: Real-time validation, UI feedback (styling, tooltip), signal emission.
        # Behavior: As user types in an expression field, its border/background might change and a tooltip
        #           appears indicating if it's valid or describing an error.

        # Update the stored expression string immediately, even if invalid
        # This prevents losing user input during typing
        if idx < len(self.expressions):
            self.expressions[idx] = text
        
        # Only perform validation if there's actual text to validate
        if not text.strip():
            # For empty expressions, show a neutral state
            line_edit_widget.setStyleSheet(AppTheme.get_lineedit_stylesheet())  # Reset to default style
            line_edit_widget.setToolTip("Enter a logical expression")
            return

        # Use ExpressionEvaluator to check if the expression is valid and safe.
        is_valid, message = ExpressionEvaluator.is_valid_expression(text)

        if is_valid:
            # If valid, reset stylesheet (remove error styling) and set a positive tooltip.
            line_edit_widget.setStyleSheet(AppTheme.get_lineedit_stylesheet())  # Back to default style
            line_edit_widget.setToolTip("Valid expression")
            # Emit signal that expressions have changed (now that we have a valid expression)
            self._expressions_updated()
        else:
            # If invalid, apply an error style (e.g., light red background) and set tooltip to the error message.
            # Use a light red background to indicate error but still allow readability
            line_edit_widget.setStyleSheet(
                AppTheme.get_lineedit_stylesheet() + "background-color: rgba(255, 200, 200, 0.7);")  # Lighter, more transparent error style
            line_edit_widget.setToolTip(message)

    def _expressions_updated(self):
        # Helper method to emit the expressionsChanged signal.
        # Purpose: Centralizes the emission of the signal.
        # Connection: Called after expressions are added, deleted, edited (and valid), or modified by test_expressions.
        """Emit the expressionsChanged signal when expressions change"""
        self.expressionsChanged.emit(self.expressions)

    def _colors_updated(self):
        # Helper method to emit the expressionColorsChanged signal.
        # Purpose: Centralizes the emission of the signal.
        # Connection: Called after colors are changed via _select_color or new expressions (with new colors) are added/removed.
        """Emit the expressionColorsChanged signal when colors change"""
        self.expressionColorsChanged.emit(self.expr_colors)

    def get_expression_colors(self):
        # Public accessor method to get the current list of expression colors.
        # Returns:
        #   list[QColor]: The current list of QColor objects for expressions.
        # Connection: (Potentially) Called by TruthTableApp if it needed direct access to colors, though currently
        #             the model gets colors via its own `set_expression_colors` which is triggered by the signal.
        return self.expr_colors

    def get_expressions(self):
        # Public accessor method to get the current list of expression strings.
        # Returns:
        #   list[str]: The current list of expressions managed by this widget.
        # Connection: Called by TruthTableApp.generate_table to get expressions for the TruthTableModel.
        return self.expressions


class ExplanationWidget(QWidget):
    # This class provides educational content and real-time expression evaluations.
    # It consists of two main components:
    #   1. A "Learning Resources" section with a dropdown of topics and HTML content display
    #   2. A "Expression Evaluation" section that shows step-by-step evaluation of expressions
    # Visual Layout:
    #   - Appears in the right panel of the main application window, inside a QTabWidget.
    #   - Contains a title, two QGroupBoxes with their own internal layouts.
    #   - The second group box (Expression Evaluation) dynamically updates based on truth table data.
    # Interactivity:
    #   - Users can select learning topics from a dropdown to view educational content.
    #   - Users can toggle a checkbox to show/hide step-by-step expression evaluation.
    """Widget for explaining truth table steps and providing educational resources"""

    def __init__(self, parent=None):
        # Constructor for ExplanationWidget.
        # Parameters:
        #   parent (QWidget, optional): The parent widget. Defaults to None.
        # Purpose: Initializes the widget and builds the UI.
        # Concepts: QWidget initialization, calling UI setup method.
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        # Purpose: Constructs and arranges the UI elements for this widget.
        # Concepts: QVBoxLayout, QGroupBox, QComboBox, QTextEdit, QCheckBox.
        # Visual Layout: Vertical arrangement of title and two group boxes.
        
        # Main layout for this widget
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)  # Increased spacing

        # Title
        title = QLabel("Educational Tools")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)  # Larger font
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align
        layout.addWidget(title)

        # Learning resources group box
        resources_group = QGroupBox("Learning Resources")
        resources_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #00ffaa;
            }
        """)
        resources_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        resources_layout = QVBoxLayout()
        resources_layout.setContentsMargins(15, 25, 15, 15)  # Increased top padding
        resources_layout.setSpacing(15)

        # Topic selection dropdown
        topic_label = QLabel("Choose a topic to learn about:")
        topic_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        resources_layout.addWidget(topic_label)
        
        self.tutorials_combo = QComboBox()
        self.tutorials_combo.addItems([
            "Select a topic to learn",
            "Basic Logic Operations",
            "Truth Tables Explained",
            "Boolean Algebra Rules",
            "Logical Equivalences",
            "Conditional Statements"
        ])
        self.tutorials_combo.setMinimumHeight(40)  # Taller dropdown
        self.tutorials_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 2px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox:hover {
                border: 2px solid #00ffaa;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #3a3a3a;
            }
        """)
        # Signal-Slot Connection: When an item is selected, show the corresponding tutorial
        self.tutorials_combo.currentIndexChanged.connect(self._show_tutorial)
        resources_layout.addWidget(self.tutorials_combo)

        # Text area for displaying tutorial content
        tutorial_label = QLabel("Tutorial Content:")
        tutorial_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        resources_layout.addWidget(tutorial_label)
        
        self.tutorial_text = QTextEdit()
        self.tutorial_text.setReadOnly(True)
        self.tutorial_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                selection-background-color: #2980b9;
            }
            QTextEdit:focus {
                border: 2px solid #00ffaa;
            }
        """)
        self.tutorial_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tutorial_text.setMinimumHeight(250)  # Taller content area
        resources_layout.addWidget(self.tutorial_text)
        resources_group.setLayout(resources_layout)
        layout.addWidget(resources_group, 3) # Give more space to learning resources

        # Step-by-step evaluation group box
        eval_group = QGroupBox("Expression Evaluation")
        eval_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #00ffaa;
            }
        """)
        eval_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        eval_layout = QVBoxLayout()
        eval_layout.setContentsMargins(15, 25, 15, 15)  # Increased top padding 
        eval_layout.setSpacing(15)

        # Checkbox to toggle step-by-step evaluation display
        self.show_steps_check = QCheckBox("Show step-by-step evaluation")
        self.show_steps_check.setChecked(True)
        self.show_steps_check.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #ffffff;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2a2a2a;
                border: 2px solid #3a3a3a;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #00ffaa;
                border: 2px solid #00aa7f;
                border-radius: 4px;
            }
        """)
        eval_layout.addWidget(self.show_steps_check)

        # Text area for displaying evaluation steps
        steps_label = QLabel("Evaluation Steps:")
        steps_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        eval_layout.addWidget(steps_label)
        
        self.step_text = QTextEdit()
        self.step_text.setReadOnly(True)
        self.step_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                selection-background-color: #2980b9;
            }
            QTextEdit:focus {
                border: 2px solid #00ffaa;
            }
        """)
        self.step_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.step_text.setMinimumHeight(200)  # Taller content area
        eval_layout.addWidget(self.step_text)
        eval_group.setLayout(eval_layout)
        layout.addWidget(eval_group, 2) # Slightly less space for evaluation section

        self.setLayout(layout)

    def _show_tutorial(self, index):
        # Slot method called when a topic is selected in the tutorials_combo.
        # Parameters:
        #   index (int): The index of the selected item in the QComboBox.
        # Purpose: Displays the corresponding tutorial HTML content in tutorial_text.
        # Concepts: HTML content in QTextEdit, dictionary lookup by key.
        # Connection: Connected to the QComboBox.currentIndexChanged signal.
        
        # Dictionary mapping tutorial indices to HTML content
        tutorials = {
            1: """
            <html>
            <head>
            <style>
                body { color: white; font-size: 15px; line-height: 1.5; }
                h3 { color: #00ffaa; font-size: 18px; margin-top: 15px; margin-bottom: 10px; }
                p { margin: 10px 0; }
                b { color: #2980b9; }
            </style>
            </head>
            <body>
            <h3>Basic Logic Operations</h3>
            <p><b>AND (∧):</b> True only when both inputs are true</p>
            <p><b>OR (∨):</b> True when at least one input is true</p>
            <p><b>NOT (¬):</b> Inverts the truth value</p>
            <p><b>XOR (⊕):</b> True when inputs have different values</p>
            <p><b>IMPLICATION (→):</b> False only when antecedent is true and consequent is false</p>
            <p><b>EQUIVALENCE (↔):</b> True when both inputs have the same value</p>
            </body>
            </html>""",

            2: """
            <html>
            <head>
            <style>
                body { color: white; font-size: 15px; line-height: 1.5; }
                h3 { color: #00ffaa; font-size: 18px; margin-top: 15px; margin-bottom: 10px; }
                p { margin: 10px 0; }
                b { color: #2980b9; }
                ul { margin-top: 10px; padding-left: 25px; }
                li { margin-bottom: 8px; }
            </style>
            </head>
            <body>
            <h3>Truth Tables Explained</h3>
            <p>Truth tables show all possible combinations of input values and the resulting output values for logical expressions.</p>
            <p>For n variables, a truth table has 2ⁿ rows representing all possible combinations.</p>
            <p>Each row evaluates the expression with specific values for each variable.</p>
            <p>Truth tables are useful for:</p>
            <ul>
            <li>Verifying logical equivalence between expressions</li>
            <li>Finding satisfying assignments</li>
            <li>Designing digital circuits</li>
            </ul>
            </body>
            </html>""",

            3: """
            <html>
            <head>
            <style>
                body { color: white; font-size: 15px; line-height: 1.5; }
                h3 { color: #00ffaa; font-size: 18px; margin-top: 15px; margin-bottom: 10px; }
                p { margin: 10px 0; }
                b { color: #2980b9; }
                ul { margin-top: 5px; padding-left: 25px; }
                li { margin-bottom: 8px; }
            </style>
            </head>
            <body>
            <h3>Boolean Algebra Rules</h3>
            <p><b>Identity laws:</b></p>
            <ul>
            <li>p ∧ True = p</li>
            <li>p ∨ False = p</li>
            </ul>
            <p><b>Domination laws:</b></p>
            <ul>
            <li>p ∧ False = False</li>
            <li>p ∨ True = True</li>
            </ul>
            <p><b>Idempotent laws:</b></p>
            <ul>
            <li>p ∧ p = p</li>
            <li>p ∨ p = p</li>
            </ul>
            <p><b>Complement laws:</b></p>
            <ul>
            <li>p ∧ ¬p = False</li>
            <li>p ∨ ¬p = True</li>
            </ul>
            <p><b>Double negation:</b> ¬(¬p) = p</p>
            </body>
            </html>""",

            4: """
            <html>
            <head>
            <style>
                body { color: white; font-size: 15px; line-height: 1.5; }
                h3 { color: #00ffaa; font-size: 18px; margin-top: 15px; margin-bottom: 10px; }
                p { margin: 10px 0; }
                b { color: #2980b9; }
                ul { margin-top: 5px; padding-left: 25px; }
                li { margin-bottom: 8px; }
            </style>
            </head>
            <body>
            <h3>Logical Equivalences</h3>
            <p><b>De Morgan's Laws:</b></p>
            <ul>
            <li>¬(p ∧ q) = ¬p ∨ ¬q</li>
            <li>¬(p ∨ q) = ¬p ∧ ¬q</li>
            </ul>
            <p><b>Distributive Laws:</b></p>
            <ul>
            <li>p ∧ (q ∨ r) = (p ∧ q) ∨ (p ∧ r)</li>
            <li>p ∨ (q ∧ r) = (p ∨ q) ∧ (p ∨ r)</li>
            </ul>
            <p><b>Absorption Laws:</b></p>
            <ul>
            <li>p ∧ (p ∨ q) = p</li>
            <li>p ∨ (p ∧ q) = p</li>
            </ul>
            </body>
            </html>""",

            5: """
            <html>
            <head>
            <style>
                body { color: white; font-size: 15px; line-height: 1.5; }
                h3 { color: #00ffaa; font-size: 18px; margin-top: 15px; margin-bottom: 10px; }
                p { margin: 10px 0; }
                b { color: #2980b9; }
                ul { margin-top: 5px; padding-left: 25px; }
                li { margin-bottom: 8px; }
                table { border-collapse: collapse; margin: 15px 0; }
                th, td { border: 1px solid #555; padding: 8px 15px; text-align: center; }
                th { background-color: #2a2a2a; }
                td { background-color: #1e1e1e; }
            </style>
            </head>
            <body>
            <h3>Conditional Statements</h3>
            <p><b>Implication (p → q):</b> "If p then q" or "p implies q"</p>
            <p>Truth table for p → q:</p>
            <table border="1" cellpadding="5">
            <tr><th>p</th><th>q</th><th>p → q</th></tr>
            <tr><td>T</td><td>T</td><td>T</td></tr>
            <tr><td>T</td><td>F</td><td>F</td></tr>
            <tr><td>F</td><td>T</td><td>T</td></tr>
            <tr><td>F</td><td>F</td><td>T</td></tr>
            </table>
            <p><b>Equivalent forms:</b></p>
            <ul>
            <li>p → q ≡ ¬p ∨ q</li>
            <li>p → q ≡ ¬(p ∧ ¬q)</li>
            </ul>
            </body>
            </html>"""
        }

        # If a valid topic is selected, display its HTML content
        if index > 0 and index in tutorials:
            self.tutorial_text.setHtml(tutorials[index])
        else:
            # Clear the content if "Select a topic to learn" is chosen
            self.tutorial_text.setHtml("""
            <html>
            <head>
            <style>
                body { color: #aaaaaa; font-size: 15px; text-align: center; margin-top: 50px; }
            </style>
            </head>
            <body>
            <p>Select a topic from the dropdown to learn about logic concepts.</p>
            </body>
            </html>
            """)

    def update_step_evaluation(self, variable_names, expressions, truth_values):
        # Purpose: Updates the step-by-step evaluation display with the current truth table data.
        # Parameters:
        #   variable_names (list[str]): List of variable names used in the truth table.
        #   expressions (list[str]): List of logical expressions being evaluated.
        #   truth_values (list[tuple]): List of tuples, each containing the True/False values for variables in a row.
        # Concepts: HTML content generation, conditional display, ExpressionEvaluator.get_evaluation_steps.
        # Connection: Called by TruthTableApp.update_step_evaluation when the table data changes.
        
        # If step evaluation is turned off, clear the text and exit
        if not self.show_steps_check.isChecked():
            self.step_text.setHtml("""
            <html>
            <head>
            <style>
                body { color: #aaaaaa; font-size: 15px; text-align: center; margin-top: 50px; }
            </style>
            </head>
            <body>
            <p>Step-by-step evaluation is turned off.</p>
            <p>Enable it using the checkbox above to see detailed evaluation steps.</p>
            </body>
            </html>
            """)
            return

        # No expressions or no variables
        if not expressions or not variable_names:
            self.step_text.setHtml("""
            <html>
            <head>
            <style>
                body { color: #aaaaaa; font-size: 15px; text-align: center; margin-top: 50px; }
            </style>
            </head>
            <body>
            <p>No expressions or variables to evaluate.</p>
            <p>Add variables and expressions in the Variables & Expressions tab.</p>
            </body>
            </html>
            """)
            return

        # Generate HTML content with improved styling
        html = """
        <html>
        <head>
        <style>
            body { color: white; font-size: 15px; line-height: 1.5; }
            h3 { color: #00ffaa; font-size: 18px; margin-top: 15px; margin-bottom: 10px; }
            p { margin: 10px 0; }
            b { color: #2980b9; }
            ol { margin-top: 10px; padding-left: 25px; }
            li { margin-bottom: 8px; }
            table { border-collapse: collapse; margin: 15px 0; width: 100%; }
            th, td { border: 1px solid #555; padding: 8px 10px; }
            th { background-color: #2a2a2a; }
            td { background-color: #1e1e1e; }
            hr { border: 0; height: 1px; background-color: #3a3a3a; margin: 20px 0; }
        </style>
        </head>
        <body>
        <h3>Step-by-Step Evaluation</h3>
        """
        
        # Show first row of truth table for simplicity
        if len(truth_values) > 0:
            first_row = truth_values[0]
            
            # Create variable dictionary for the first row
            var_dict = {}
            for i, name in enumerate(variable_names):
                if i < len(first_row):
                    var_dict[name] = first_row[i]
            
            # Label for this row
            html += "<p>For the first row of the truth table, where:</p>"
            html += "<table>"
            for name, value in var_dict.items():
                html += f"<tr><td><b>{name}</b></td><td>{str(value)}</td></tr>"
            html += "</table>"
            
            # Explain evaluation of each expression
            for expr in expressions:
                html += f"<p><b>Evaluating:</b> {expr}</p>"
                steps = ExpressionEvaluator.get_evaluation_steps(expr, var_dict)
                
                html += "<ol>"
                for step in steps:
                    html += f"<li>{step}</li>"
                html += "</ol>"

                # Add a separator between expressions
                html += "<hr>"
        
        html += """
        </body>
        </html>
        """
        
        # Set the HTML content
        self.step_text.setHtml(html)


class DisplayConfig:
    """
    Configuration class for managing truth table display formats.
    
    This class defines the available display modes for the truth table and provides
    methods to control how the data is displayed.
    """
    
    # Display mode constants
    TF_MODE = "T/F"       # True as "T", False as "F" 
    BINARY_MODE = "1/0"   # True as "1", False as "0"
    
    # Row order constants
    STANDARD_ORDER = "Standard"    # FFF, FFT, FTF, FTT, etc.
    REVERSED_ORDER = "Reversed"    # TTT, TTF, TFT, TFF, etc.
    
    # Available display modes
    AVAILABLE_DISPLAY_MODES = [TF_MODE, BINARY_MODE]
    
    # Available row orders
    AVAILABLE_ROW_ORDERS = [STANDARD_ORDER, REVERSED_ORDER]
    
    def __init__(self):
        """Initialize display configuration with default settings"""
        # Default display modes
        self.variable_display = self.BINARY_MODE
        self.expression_display = self.TF_MODE
        
        # Default row order
        self.row_order = self.STANDARD_ORDER
    
    def format_variable(self, value):
        """
        Format a boolean value for variable display based on current mode
        
        Parameters:
            value (bool): The boolean value to format
            
        Returns:
            str: Formatted string representation
        """
        if self.variable_display == self.TF_MODE:
            return "T" if value else "F"
        elif self.variable_display == self.BINARY_MODE:
            return "1" if value else "0"
        # Fallback
        return str(value)
    
    def format_expression(self, value):
        """
        Format a boolean value for expression display based on current mode
        
        Parameters:
            value (bool): The boolean value to format
            
        Returns:
            str: Formatted string representation
        """
        if self.expression_display == self.TF_MODE:
            return "T" if value else "F"
        elif self.expression_display == self.BINARY_MODE:
            return "1" if value else "0"
        # Fallback
        return str(value)
    
    def set_variable_display(self, mode):
        """Set display mode for variables"""
        if mode in self.AVAILABLE_DISPLAY_MODES:
            self.variable_display = mode
            return True
        return False
    
    def set_expression_display(self, mode):
        """Set display mode for expressions"""
        if mode in self.AVAILABLE_DISPLAY_MODES:
            self.expression_display = mode
            return True
        return False
        
    def set_row_order(self, order):
        """Set the row order for the truth table"""
        if order in self.AVAILABLE_ROW_ORDERS:
            self.row_order = order
            return True
        return False
        
    def should_reverse_rows(self):
        """Check if rows should be displayed in reverse order"""
        return self.row_order == self.REVERSED_ORDER


class TruthTableModel(QAbstractTableModel):
    """
    Model for handling truth table data and displaying it in a QTableView.
    
    This class manages all data related to the truth table, including variable names,
    expressions, and calculation of all possible truth value combinations. It implements
    the Qt Model-View architecture through QAbstractTableModel, providing methods that
    the view (QTableView) will call to request data for display.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the truth table model.
        
        Parameters:
            parent (QObject, optional): The parent object. Defaults to None.
        
        Attributes:
            variable_names (list[str]): List of variable names (e.g., ["p", "q"]).
            expressions (list[str]): List of logical expressions to evaluate.
            expr_colors (list[QColor]): List of colors for expression columns.
            truth_values (list[tuple]): List of all possible truth value combinations.
            results (list[list[bool]]): Results of evaluating expressions for each row.
        """
        super().__init__(parent)
        self.variable_names = ["p", "q"]  # Default variable names
        self.expressions = ["p and q"]  # Default expression
        self.expr_colors = [QColor(91, 192, 222)]  # Default color for expression
        self.truth_values = []  # Will store all combinations of True/False
        self.results = []  # Will store evaluation results
        
        # Display configuration
        self.display_config = DisplayConfig()
        
        # Initialize the data
        self._generate_data()
    
    def rowCount(self, parent=QModelIndex()):
        """
        Return the number of rows in the model.
        
        This is determined by the number of possible truth value combinations,
        which is 2^n where n is the number of variables.
        
        Parameters:
            parent (QModelIndex): Parent index (unused in this implementation).
        
        Returns:
            int: Number of rows in the truth table.
        """
        return len(self.truth_values)
    
    def columnCount(self, parent=QModelIndex()):
        """
        Return the number of columns in the model.
        
        This includes columns for the variables and the expressions.
        
        Parameters:
            parent (QModelIndex): Parent index (unused in this implementation).
        
        Returns:
            int: Number of columns in the truth table.
        """
        return len(self.variable_names) + len(self.expressions)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """
        Return the data for a given cell based on the specified role.
        
        This method handles multiple roles:
        - DisplayRole: The actual value to display (True/False)
        - BackgroundRole: The background color of the cell
        - TextAlignmentRole: How to align the text
        
        Parameters:
            index (QModelIndex): The index of the cell for which data is requested.
            role (Qt.ItemDataRole): The role of the data (display, background, etc.)
        
        Returns:
            Various: The data appropriate for the role, or None if no data for the role.
        """
        if not index.isValid():
            return None
        
        row, col = index.row(), index.column()
        
        # Alignment role - center all values
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        
        # Display role - what to show in the cell
        if role == Qt.ItemDataRole.DisplayRole:
            # Variable columns - use display format from config
            if col < len(self.variable_names):
                value = self.truth_values[row][col]
                return self.display_config.format_variable(value)
            
            # Expression columns - use display format from config
            expr_idx = col - len(self.variable_names)
            if expr_idx < len(self.results[row]):
                value = self.results[row][expr_idx]
                if value is None:
                    return "Error"
                return self.display_config.format_expression(value)
        
        # Background role - cell background color based on actual truth values, not display format
        if role == Qt.ItemDataRole.BackgroundRole:
            # Variable columns - light gray background
            if col < len(self.variable_names):
                return QBrush(AppTheme.PANEL)
            
            # Expression columns - colored background based on result
            expr_idx = col - len(self.variable_names)
            if expr_idx < len(self.results[row]):
                value = self.results[row][expr_idx]
                
                if value is None:
                    return QBrush(AppTheme.PANEL)  # Neutral color for None/error
                elif value:  # If TRUE (regardless of display mode)
                    # True value - use AppTheme.TRUE_COLOR
                    return QBrush(AppTheme.TRUE_COLOR.lighter(140))  # Slightly lighter for readability
                else:  # If FALSE (regardless of display mode)
                    # False value - use AppTheme.FALSE_COLOR
                    return QBrush(AppTheme.FALSE_COLOR.lighter(140))  # Slightly lighter for readability
        
        # Foreground role - text color based on actual truth values, not display format
        if role == Qt.ItemDataRole.ForegroundRole:
            # Expression columns - use darker shade of the background for better contrast
            if col >= len(self.variable_names):
                expr_idx = col - len(self.variable_names)
                if expr_idx < len(self.results[row]):
                    value = self.results[row][expr_idx]
                    
                    if value is None:
                        return QBrush(AppTheme.ERROR)  # Error text color
                    elif value:  # If TRUE (regardless of display mode)
                        return QBrush(AppTheme.TRUE_COLOR.darker(150))  # Darker green for text
                    else:  # If FALSE (regardless of display mode)
                        return QBrush(AppTheme.FALSE_COLOR.darker(150))  # Darker red for text
            
            # Default text color for variables
            return QBrush(AppTheme.TEXT_PRIMARY)
        
        # Font role - make expression columns bold
        if role == Qt.ItemDataRole.FontRole:
            font = QFont()
            font.setBold(True)
            return font
        
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """
        Return the header data for rows and columns.
        
        Parameters:
            section (int): Row or column number.
            orientation (Qt.Orientation): Horizontal (column) or Vertical (row).
            role (Qt.ItemDataRole): The role of the data (display, font, etc.)
        
        Returns:
            Various: The header data for the role, or None if no data for the role.
        """
        # Display role - what text to show
        if role == Qt.ItemDataRole.DisplayRole:
            # Column headers: variable names and expressions
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self.variable_names):
                    return self.variable_names[section]
                else:
                    expr_idx = section - len(self.variable_names)
                    if expr_idx < len(self.expressions):
                        return self.expressions[expr_idx]
            
            # Row headers: just use row numbers
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        
        # Alignment role - center headers
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        
        # Background role - make headers stand out
        if role == Qt.ItemDataRole.BackgroundRole:
            if orientation == Qt.Orientation.Horizontal:
                # Variable columns get a distinct header color
                if section < len(self.variable_names):
                    return QBrush(AppTheme.SECONDARY)
                
                # Expression headers get their specific colors
                expr_idx = section - len(self.variable_names)
                if expr_idx < len(self.expr_colors):
                    return QBrush(self.expr_colors[expr_idx])
                return QBrush(AppTheme.PRIMARY)
            else:
                # Row headers
                return QBrush(AppTheme.SECONDARY.lighter(140))
        
        # Foreground role - white text for headers
        if role == Qt.ItemDataRole.ForegroundRole:
            return QBrush(QColor(255, 255, 255))
        
        # Font role - bold headers
        if role == Qt.ItemDataRole.FontRole:
            font = QFont()
            font.setBold(True)
            # Slightly larger font for variable headers
            if orientation == Qt.Orientation.Horizontal and section < len(self.variable_names):
                font.setPointSize(11)
            else:
                font.setPointSize(10)
            return font
        
        return None
    
    def set_variable_names(self, names):
        """
        Update the variable names used in the model.
        
        Parameters:
            names (list[str]): List of new variable names.
        
        This method updates the variable names and regenerates the truth table data.
        """
        self.variable_names = names
        self._generate_data()
        self.layoutChanged.emit()
    
    def set_expressions(self, expressions):
        """
        Update the expressions used in the model.
        
        Parameters:
            expressions (list[str]): List of new expressions to evaluate.
        
        This method updates the expressions and regenerates the results.
        """
        self.expressions = expressions
        
        # Ensure we have colors for all expressions
        while len(self.expr_colors) < len(self.expressions):
            # Generate a new color different from existing ones
            new_color = QColor(
                min(255, max(50, 100 + hash(expressions[-1]) % 155)),
                min(255, max(50, 150 + hash(expressions[-1] + "a") % 105)),
                min(255, max(50, 200 + hash(expressions[-1] + "b") % 55))
            )
            self.expr_colors.append(new_color)
        
        # Trim colors if we have fewer expressions
        while len(self.expr_colors) > len(self.expressions):
            self.expr_colors.pop()
        
        self._generate_data()
        self.dataChanged.emit(
            self.index(0, len(self.variable_names)),
            self.index(self.rowCount() - 1, self.columnCount() - 1)
        )
    
    def set_expression_colors(self, colors):
        """
        Update the colors used for expression columns.
        
        Parameters:
            colors (list[QColor]): List of colors for expressions.
        
        This method updates the colors without regenerating the data.
        """
        self.expr_colors = colors
        # Only need to update the columns for expressions
        self.dataChanged.emit(
            self.index(0, len(self.variable_names)),
            self.index(self.rowCount() - 1, self.columnCount() - 1)
        )
    
    def _generate_data(self):
        """
        Generate truth table data for all combinations of variable values.
        
        This method:
        1. Creates all possible combinations of True/False for the variables.
        2. Evaluates each expression for each combination.
        3. Stores the results in self.results.
        """
        # Create all possible combinations of True/False values
        truth_values = list(product([False, True], repeat=len(self.variable_names)))
        
        # Check if we should reverse the order of rows
        if self.display_config.should_reverse_rows():
            truth_values.reverse()
        
        # Store the truth values
        self.truth_values = truth_values

        # For debugging
        print(f"Variable names: {self.variable_names}")
        print(f"Expressions: {self.expressions}")

        # Evaluate each expression for each row
        self.results = []
        for row_values in self.truth_values:
            row_results = []

            # Debug print first row
            if len(self.results) == 0:
                print(f"First row values: {row_values}")

            # Create variable dictionary - MAKE SURE THIS IS CORRECT
            # Fixed: Use string values 'p', 'q', 'r' as keys exactly as they appear in expressions
            # Remove any type conversion to ensure variable names match exactly
            var_dict = {}
            for i, name in enumerate(self.variable_names):
                if i < len(row_values):
                    var_dict[name] = row_values[i]

            # Debug print first row
            if len(self.results) == 0:
                print(f"First row var_dict: {var_dict}")

            for expr in self.expressions:
                try:
                    # Debug print for first expression in first row
                    if len(self.results) == 0 and len(row_results) == 0:
                        print(f"Evaluating '{expr}' with {var_dict}")

                    result = ExpressionEvaluator.evaluate(expr, var_dict)
                    row_results.append(result)
                except ValueError as e:
                    print(f"Error evaluating '{expr}': {e}")
                    row_results.append(None)

            self.results.append(row_results)


class TruthTableApp(QMainWindow):
    """
    Main application window for the Truth Table Educational Tool
    
    Implements a modern, dockable UI with macOS-style unified toolbar
    and floating, resizable panels for better usability.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Truth Table Educational Tool")
        self.setMinimumSize(1200, 800)

        # Apply futuristic styling
        FuturisticUI.set_futuristic_style(QApplication.instance())
        
        # --- Status Bar (bottom of window) ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Welcome to Truth Table Educational Tool")
        self.status_bar.setStyleSheet("padding: 8px; font-size: 13px;")
        
        # Create floating toolbar for symbol insertion
        self.floating_toolbar = FloatingSymbolToolbar(self)
        self.floating_toolbar.symbolClicked.connect(self.insert_symbol)
        self.floating_toolbar.hide()  # Start hidden
        
        # --- Set up central widget (Truth Table) ---
        self.setup_central_widget()
        
        # --- Set up docks ---
        self.setup_docks()
        
        # --- Set up toolbar ---
        self.setup_toolbar()
        
        # Create data model for truth table
        self.table_model = TruthTableModel()
        self.table_view.setModel(self.table_model)
        self.update_table_column_sizes()
        
        # Connect signals
        self.variable_config.variablesChanged.connect(self.on_variables_changed)
        self.expression_widget.expressionsChanged.connect(self.on_expressions_changed)
        self.expression_widget.expressionColorsChanged.connect(self.on_colors_changed)
        
        # Initialize
        self.generate_table()
        
    def setup_central_widget(self):
        """Set up the central widget with the truth table view"""
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(15, 15, 15, 15)
        central_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Truth Table Results")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_layout.addWidget(title_label)
        
        # Table view
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setStyleSheet("""
            QTableView {
                background-color: #1e1e1e;
                alternate-background-color: #262626;
                color: #ffffff;
                gridline-color: #444444;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                font-size: 14px;
            }
            QTableView::item {
                padding: 5px;
            }
            QTableView::item:selected {
                background-color: #00aa7f;
                color: white;
            }
            QHeaderView::section {
                background-color: #006644;
                color: white;
                padding: 10px;
                border: 1px solid #005533;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.table_view.verticalHeader().setDefaultSectionSize(40)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        central_layout.addWidget(self.table_view, 1)  # Give stretch factor of 1
        
        # Add Karnaugh Map button
        karnaugh_button = QPushButton("Show Karnaugh Map")
        karnaugh_button.setStyleSheet("""
            QPushButton {
                background-color: #00aa7f;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ffaa;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #008f60;
            }
        """)
        karnaugh_button.setMinimumHeight(40)
        karnaugh_button.clicked.connect(self.show_karnaugh_map)
        
        # Create a container for the button with some padding
        karnaugh_container = QWidget()
        karnaugh_layout = QHBoxLayout(karnaugh_container)
        karnaugh_layout.setContentsMargins(5, 5, 5, 15)
        karnaugh_layout.addStretch()
        karnaugh_layout.addWidget(karnaugh_button)
        karnaugh_layout.addStretch()
        
        central_layout.addWidget(karnaugh_container)
        
        # Display options
        options_group = QGroupBox("Display Options")
        options_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #00ffaa;
            }
        """)
        options_layout = QHBoxLayout()
        
        # Variable display mode
        var_display_label = QLabel("Variables:")
        var_display_label.setStyleSheet("font-size: 14px; color: #ffffff;")
        self.var_display_combo = QComboBox()
        self.var_display_combo.addItems(DisplayConfig.AVAILABLE_DISPLAY_MODES)
        self.var_display_combo.setCurrentText(DisplayConfig.TF_MODE)
        self.var_display_combo.currentTextChanged.connect(self.update_variable_display_mode)
        self.var_display_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 6px;
                min-width: 80px;
                font-size: 14px;
            }
        """)
        
        # Expression display mode
        expr_display_label = QLabel("Expressions:")
        expr_display_label.setStyleSheet("font-size: 14px; color: #ffffff;")
        self.expr_display_combo = QComboBox()
        self.expr_display_combo.addItems(DisplayConfig.AVAILABLE_DISPLAY_MODES)
        self.expr_display_combo.setCurrentText(DisplayConfig.TF_MODE)
        self.expr_display_combo.currentTextChanged.connect(self.update_expression_display_mode)
        self.expr_display_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 6px;
                min-width: 80px;
                font-size: 14px;
            }
        """)
        
        # Row order
        row_order_label = QLabel("Row Order:")
        row_order_label.setStyleSheet("font-size: 14px; color: #ffffff;")
        self.row_order_combo = QComboBox()
        self.row_order_combo.addItems(DisplayConfig.AVAILABLE_ROW_ORDERS)
        self.row_order_combo.setCurrentText(DisplayConfig.STANDARD_ORDER)
        self.row_order_combo.currentTextChanged.connect(self.update_row_order)
        self.row_order_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 6px;
                min-width: 120px;
                font-size: 14px;
            }
        """)
        
        # Add to layout
        options_layout.addWidget(var_display_label)
        options_layout.addWidget(self.var_display_combo)
        options_layout.addSpacing(20)
        options_layout.addWidget(expr_display_label)
        options_layout.addWidget(self.expr_display_combo)
        options_layout.addSpacing(20)
        options_layout.addWidget(row_order_label)
        options_layout.addWidget(self.row_order_combo)
        options_layout.addStretch()
        
        # Export buttons
        export_btn = QPushButton("Export as CSV")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 1px solid #00ffaa;
            }
        """)
        export_btn.clicked.connect(self.export_csv)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 1px solid #00ffaa;
            }
        """)
        copy_btn.clicked.connect(self.copy_table)
        
        options_layout.addWidget(export_btn)
        options_layout.addWidget(copy_btn)
        
        options_group.setLayout(options_layout)
        central_layout.addWidget(options_group)
        
        self.setCentralWidget(central_widget)
    
    def setup_docks(self):
        """Set up all dock widgets"""
        # Variables dock
        self.variables_dock = QDockWidget("Variables", self)
        self.variable_config = VariableConfigWidget()
        self.variables_dock.setWidget(self.variable_config)
        self.variables_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                         QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.variables_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                           Qt.DockWidgetArea.RightDockWidgetArea)
        self.variables_dock.setStyleSheet("""
            QDockWidget {
                font-size: 14px;
                font-weight: bold;
            }
            QDockWidget::title {
                background-color: #006644;
                color: white;
                padding: 8px;
                text-align: center;
            }
        """)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.variables_dock)
        
        # Expressions dock
        self.expressions_dock = QDockWidget("Expressions", self)
        self.expression_widget = ExpressionWidget()
        self.expressions_dock.setWidget(self.expression_widget)
        self.expressions_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                         QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.expressions_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                                           Qt.DockWidgetArea.RightDockWidgetArea)
        self.expressions_dock.setStyleSheet("""
            QDockWidget {
                font-size: 14px;
                font-weight: bold;
            }
            QDockWidget::title {
                background-color: #006644;
                color: white;
                padding: 8px;
                text-align: center;
            }
        """)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.expressions_dock)
        
        # Learning resources dock
        self.learning_dock = QDockWidget("Learning Resources", self)
        self.explanation_widget = ExplanationWidget()
        self.learning_dock.setWidget(self.explanation_widget)
        self.learning_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                     QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.learning_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | 
                                         Qt.DockWidgetArea.LeftDockWidgetArea)
        self.learning_dock.setStyleSheet("""
            QDockWidget {
                font-size: 14px;
                font-weight: bold;
            }
            QDockWidget::title {
                background-color: #006644;
                color: white;
                padding: 8px;
                text-align: center;
            }
        """)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.learning_dock)
        
        # Style editor dock (hidden by default)
        self.style_dock = QDockWidget("UI Appearance", self)
        self.style_editor = StyleEditor()
        self.style_editor.stylesChanged.connect(self.apply_style_changes)
        self.style_dock.setWidget(self.style_editor)
        self.style_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                   QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.style_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | 
                                       Qt.DockWidgetArea.LeftDockWidgetArea)
        self.style_dock.setStyleSheet("""
            QDockWidget {
                font-size: 14px;
                font-weight: bold;
            }
            QDockWidget::title {
                background-color: #006644;
                color: white;
                padding: 8px;
                text-align: center;
            }
        """)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.style_dock)
        self.style_dock.hide()  # Hidden by default
        
        # Set size constraints
        self.resizeDocks([self.variables_dock, self.expressions_dock], [250, 250], Qt.Orientation.Horizontal)
        self.resizeDocks([self.learning_dock], [350], Qt.Orientation.Horizontal)
    
    def setup_toolbar(self):
        """Set up the unified macOS-style toolbar"""
        # Main toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #1a1a1a;
                border-bottom: 1px solid #3a3a3a;
                spacing: 10px;
                padding: 5px;
            }
            QToolButton {
                background-color: transparent;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 12px;
            }
            QToolButton:hover {
                background-color: #3a3a3a;
            }
            QToolButton:pressed {
                background-color: #006644;
            }
        """)
        
        # Generate button
        generate_action = QAction("Generate", self)
        generate_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        generate_action.triggered.connect(self.generate_table)
        generate_action.setToolTip("Generate or update the truth table")
        self.toolbar.addAction(generate_action)
        
        # Symbol toolbar toggle
        symbols_action = QAction("Symbols", self)
        symbols_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ToolBarHorizontalExtensionButton))
        symbols_action.triggered.connect(self.toggle_symbol_toolbar)
        symbols_action.setToolTip("Show/hide the symbol insertion toolbar")
        self.toolbar.addAction(symbols_action)
        
        self.toolbar.addSeparator()
        
        # View actions
        self.vars_action = QAction("Variables", self)
        self.vars_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.vars_action.setCheckable(True)
        self.vars_action.setChecked(True)
        self.vars_action.triggered.connect(lambda checked: self.variables_dock.setVisible(checked))
        self.toolbar.addAction(self.vars_action)
        
        self.expr_action = QAction("Expressions", self)
        self.expr_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.expr_action.setCheckable(True)
        self.expr_action.setChecked(True)
        self.expr_action.triggered.connect(lambda checked: self.expressions_dock.setVisible(checked))
        self.toolbar.addAction(self.expr_action)
        
        self.learn_action = QAction("Learning", self)
        self.learn_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton))
        self.learn_action.setCheckable(True)
        self.learn_action.setChecked(True)
        self.learn_action.triggered.connect(lambda checked: self.learning_dock.setVisible(checked))
        self.toolbar.addAction(self.learn_action)
        
        self.style_action = QAction("Appearance", self)
        self.style_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.style_action.setCheckable(True)
        self.style_action.setChecked(False)
        self.style_action.triggered.connect(lambda checked: self.style_dock.setVisible(checked))
        self.toolbar.addAction(self.style_action)
        
        self.toolbar.addSeparator()
        
        # Auto-generate toggle
        self.auto_generate = QCheckBox("Auto-generate")
        self.auto_generate.setChecked(True)
        self.auto_generate.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                spacing: 5px;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #00ffaa;
                border: 1px solid #008f60;
                border-radius: 3px;
            }
        """)
        self.toolbar.addWidget(self.auto_generate)
        
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        # Connect dockwidget visibility to toolbar button states
        self.variables_dock.visibilityChanged.connect(lambda visible: self.vars_action.setChecked(visible))
        self.expressions_dock.visibilityChanged.connect(lambda visible: self.expr_action.setChecked(visible))
        self.learning_dock.visibilityChanged.connect(lambda visible: self.learn_action.setChecked(visible))
        self.style_dock.visibilityChanged.connect(lambda visible: self.style_action.setChecked(visible))
    
    def toggle_symbol_toolbar(self):
        """Toggle the visibility of the symbol toolbar"""
        if self.floating_toolbar.isVisible():
            self.floating_toolbar.hide()
        else:
            self.floating_toolbar.show()
            # Position it near the center of the window
            toolbar_size = self.floating_toolbar.size()
            window_rect = self.geometry()
            centered_pos = window_rect.center() - QPoint(toolbar_size.width() // 2, toolbar_size.height() // 2)
            self.floating_toolbar.move(centered_pos)
    
    def update_table_column_sizes(self):
        """Adjust the column widths in the truth table"""
        if not hasattr(self, 'table_view') or not hasattr(self, 'table_model'):
            return
            
        header = self.table_view.horizontalHeader()
        for column in range(self.table_model.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
    
    def generate_table(self):
        """Generate the truth table based on current variables and expressions"""
        # Get variable names and expressions
        var_names = self.variable_config.get_variable_names()
        expressions = self.expression_widget.get_expressions()
        
        # Update the model
        self.table_model.set_variable_names(var_names)
        self.table_model.set_expressions(expressions)
        
        # Update column widths
        self.update_table_column_sizes()
        
        # Update step evaluation in explanation widget
        self.update_step_evaluation()
        
        # Show status message
        self.status_bar.showMessage("Truth table generated successfully", 3000)
    
    def on_variables_changed(self, var_names):
        """Handle variable name changes"""
        if self.auto_generate.isChecked():
            self.table_model.set_variable_names(var_names)
            self.update_step_evaluation()
    
    def on_expressions_changed(self, expressions):
        """Handle expression changes"""
        if self.auto_generate.isChecked():
            self.table_model.set_expressions(expressions)
            self.update_step_evaluation()
    
    def on_colors_changed(self, colors):
        """Handle expression color changes"""
        self.table_model.set_expression_colors(colors)
    
    def update_variable_display_mode(self, mode):
        """Update the display mode for variables"""
        if self.table_model.display_config.set_variable_display(mode):
            var_count = len(self.table_model.variable_names)
            self.table_model.dataChanged.emit(
                self.table_model.index(0, 0),
                self.table_model.index(self.table_model.rowCount() - 1, var_count - 1)
            )
    
    def update_expression_display_mode(self, mode):
        """Update the display mode for expressions"""
        if self.table_model.display_config.set_expression_display(mode):
            var_count = len(self.table_model.variable_names)
            expr_count = len(self.table_model.expressions)
            self.table_model.dataChanged.emit(
                self.table_model.index(0, var_count),
                self.table_model.index(self.table_model.rowCount() - 1, var_count + expr_count - 1)
            )
    
    def update_row_order(self, order):
        """Update the row order for the truth table"""
        if self.table_model.display_config.set_row_order(order):
            self.table_model._generate_data()
            self.table_model.layoutChanged.emit()
    
    def insert_symbol(self, symbol):
        """Insert a symbol at the cursor position in the currently focused QLineEdit"""
        focused_widget = QApplication.focusWidget()
        
        if isinstance(focused_widget, QLineEdit):
            # Get cursor position and text
            pos = focused_widget.cursorPosition()
            text = focused_widget.text()
            
            # Insert the symbol
            focused_widget.setText(text[:pos] + symbol + text[pos:])
            
            # Move cursor after the inserted symbol
            focused_widget.setCursorPosition(pos + len(symbol))
            
            # Show message
            self.status_bar.showMessage(f"Inserted symbol '{symbol}'", 2000)
        else:
            self.status_bar.showMessage("Please click in an expression field first", 3000)
    
    def update_step_evaluation(self):
        """Update the step-by-step evaluation in the explanation widget"""
        var_names = self.table_model.variable_names
        expressions = self.table_model.expressions
        truth_values = self.table_model.truth_values
        
        self.explanation_widget.update_step_evaluation(var_names, expressions, truth_values)
    
    def copy_table(self):
        """Copy the truth table to clipboard"""
        text = ""
        
        # Add header row
        for col in range(self.table_model.columnCount()):
            header = self.table_model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            text += f"{header}\t"
        text = text.strip() + "\n"
        
        # Add data rows
        for row in range(self.table_model.rowCount()):
            for col in range(self.table_model.columnCount()):
                value = self.table_model.data(self.table_model.index(row, col), Qt.ItemDataRole.DisplayRole)
                text += f"{value}\t"
            text = text.strip() + "\n"
        
        # Copy to clipboard
        QApplication.clipboard().setText(text)
        self.status_bar.showMessage("Truth table copied to clipboard", 3000)
    
    def export_csv(self):
        """Export the truth table to a CSV file"""
        import csv
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Truth Table as CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as file:
                    writer = csv.writer(file)
                    
                    # Write header row
                    headers = []
                    for col in range(self.table_model.columnCount()):
                        headers.append(self.table_model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole))
                    writer.writerow(headers)
                    
                    # Write data rows
                    for row in range(self.table_model.rowCount()):
                        row_data = []
                        for col in range(self.table_model.columnCount()):
                            value = self.table_model.data(self.table_model.index(row, col), Qt.ItemDataRole.DisplayRole)
                            row_data.append(value)
                        writer.writerow(row_data)
                
                self.status_bar.showMessage(f"Truth table exported to {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Error exporting CSV: {str(e)}")
    
    def apply_style_changes(self, qss):
        """Apply stylesheet changes from the style editor"""
        QApplication.instance().setStyleSheet(qss)
        self.status_bar.showMessage("Style updated successfully", 3000)

    def show_karnaugh_map(self):
        """Show a Karnaugh map for the current truth table"""
        # Get variable names and minterms from the current table model
        variable_names = self.table_model.variable_names
        
        # Check if we have a valid number of variables for K-map (2-5)
        if not 2 <= len(variable_names) <= 5:
            QMessageBox.warning(
                self, 
                "Karnaugh Map Error",
                f"Karnaugh maps support 2 to 5 variables. Found {len(variable_names)} variables."
            )
            return
            
        # Identify minterms (where the result is 1)
        minterms = []
        dont_cares = []
        
        # For simplicity, use the first expression results
        for row in range(self.table_model.rowCount()):
            truth_values = self.table_model.truth_values[row]
            
            # Convert row of truth values to a minterm index
            # For example, [False, True] would be index 2 (binary 10)
            idx = 0
            for i, val in enumerate(truth_values):
                if val:
                    idx |= (1 << (len(truth_values) - 1 - i))
                    
            # Get the first expression result for this row
            if row < len(self.table_model.results) and len(self.table_model.results[row]) > 0:
                if self.table_model.results[row][0]:
                    minterms.append(idx)
        
        # Create and show the Karnaugh map dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Karnaugh Map")
        dialog.setMinimumSize(800, 600)
        dialog_layout = QVBoxLayout(dialog)
        
        # Create the Karnaugh map widget and pass the data
        k_map_widget = KarnaughMapWidget()
        k_map_widget.update_from_truth_table(variable_names, minterms, dont_cares)
        dialog_layout.addWidget(k_map_widget)
        
        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 1px solid #00ffaa;
            }
        """)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        dialog_layout.addLayout(button_layout)
        
        # Show the dialog
        dialog.exec()


class FloatingSymbolToolbar(QWidget):
    """
    A floating toolbar that provides quick access to logical symbols
    which can be inserted into expressions.
    
    Signals:
        symbolClicked (str): Emitted when a symbol button is clicked with the symbol character.
    """
    # Signal emitted when a symbol is clicked (contains the symbol character)
    symbolClicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the floating toolbar with logical symbols"""
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()
    
    def _build_ui(self):
        """Build the UI for the symbol toolbar"""
        # Main layout with shadow effect
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create a container with rounded corners and background
        container = QWidget()
        container.setObjectName("symbol_container")
        container.setStyleSheet("""
            #symbol_container {
                background-color: #1a1a1a;
                border: 2px solid #3a3a3a;
                border-radius: 12px;
            }
        """)
        
        # Apply shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 3)
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(12)
        
        # Title 
        title = QLabel("Logical Symbol Toolbar")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #00ffaa;
            padding: 5px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)
        
        # Symbol buttons layout
        symbol_layout = QGridLayout()
        symbol_layout.setSpacing(8)
        
        # Symbol definitions with descriptions
        symbols = [
            ("∧", "AND", "Logical AND (conjunction)"),
            ("∨", "OR", "Logical OR (disjunction)"),
            ("¬", "NOT", "Logical NOT (negation)"),
            ("→", "IF-THEN", "Implication (if-then)"),
            ("↔", "IFF", "Equivalence (if and only if)"),
            ("⊕", "XOR", "Exclusive OR"),
            ("⊤", "TRUE", "Logical constant true"),
            ("⊥", "FALSE", "Logical constant false"),
            ("(", "OPEN", "Open parenthesis"),
            (")", "CLOSE", "Close parenthesis")
        ]
        
        # Create buttons for each symbol with improved styling
        row, col = 0, 0
        for symbol, name, tooltip in symbols:
            btn = QPushButton(f"{symbol} {name}")
            btn.setToolTip(tooltip)
            btn.setMinimumSize(105, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 1px solid #3a3a3a;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    border: 1px solid #00ffaa;
                }
                QPushButton:pressed {
                    background-color: #202020;
                }
            """)
            # Capture the symbol value in a lambda using default argument
            btn.clicked.connect(lambda checked, s=symbol: self.symbolClicked.emit(s))
            
            # Arrange buttons in 2 columns
            symbol_layout.addWidget(btn, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        container_layout.addLayout(symbol_layout)
        
        # Help text 
        help_text = QLabel("Click on a symbol to insert it into the focused expression field")
        help_text.setStyleSheet("""
            font-size: 12px;
            color: #aaaaaa;
            padding: 5px;
        """)
        help_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_text.setWordWrap(True)
        container_layout.addWidget(help_text)
        
        # Drag handle
        drag_handle = QLabel("≡ Drag to move ≡")
        drag_handle.setStyleSheet("""
            font-size: 12px;
            color: #888888;
            background-color: #222222;
            border-radius: 6px;
            padding: 4px;
        """)
        drag_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(drag_handle)
        
        main_layout.addWidget(container)
        
        # Make it draggable
        self.drag_position = None
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging the toolbar"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.position().toPoint()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging the toolbar"""
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_position:
            self.move(self.pos() + event.position().toPoint() - self.drag_position)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release after dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None

class StyleEditor(QWidget):
    """Interactive style editor for customizing UI appearance"""
    
    stylesChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        """Build the UI with a tabbed interface for better organization"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)  # Increased spacing
        
        # Create a tab widget for better organization
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #cccccc;
                border: 1px solid #3a3a3a;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
                color: #00ffaa;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3a3a3a;
            }
        """)
        
        # Colors tab
        colors_tab = QWidget()
        colors_layout = QVBoxLayout(colors_tab)
        colors_layout.setContentsMargins(15, 15, 15, 15)
        colors_layout.setSpacing(20)
        
        colors_group = QGroupBox("Theme Colors")
        colors_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #00ffaa;
            }
        """)
        colors_group_layout = QGridLayout()
        colors_group_layout.setVerticalSpacing(15)
        colors_group_layout.setHorizontalSpacing(15)
        
        # Create a label class for consistent styling
        color_label_style = "font-size: 14px; color: #ffffff;"
        
        # Primary Color
        colors_group_layout.addWidget(QLabel("Primary Color:"), 0, 0)
        colors_group_layout.itemAt(0).widget().setStyleSheet(color_label_style)
        
        self.primary_btn = QPushButton()
        self.primary_btn.setFixedSize(60, 40)  # Larger color button
        self.primary_btn.setStyleSheet(f"background-color: {FuturisticUI.PRIMARY.name()}; border: 2px solid #555; border-radius: 6px;")
        self.primary_btn.setCursor(Qt.CursorShape.PointingHandCursor)  # Hand cursor for better UX
        self.primary_btn.setToolTip("Click to change the primary accent color")
        self.primary_btn.clicked.connect(lambda: self._pick_color("primary"))
        colors_group_layout.addWidget(self.primary_btn, 0, 1)
        
        # Accent Color
        colors_group_layout.addWidget(QLabel("Accent Color:"), 1, 0)
        colors_group_layout.itemAt(2).widget().setStyleSheet(color_label_style)
        
        self.accent_btn = QPushButton()
        self.accent_btn.setFixedSize(60, 40)  # Larger color button
        self.accent_btn.setStyleSheet(f"background-color: {FuturisticUI.ACCENT.name()}; border: 2px solid #555; border-radius: 6px;")
        self.accent_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.accent_btn.setToolTip("Click to change the accent highlight color")
        self.accent_btn.clicked.connect(lambda: self._pick_color("accent"))
        colors_group_layout.addWidget(self.accent_btn, 1, 1)
        
        # Background Color
        colors_group_layout.addWidget(QLabel("Background:"), 2, 0)
        colors_group_layout.itemAt(4).widget().setStyleSheet(color_label_style)
        
        self.bg_btn = QPushButton()
        self.bg_btn.setFixedSize(60, 40)  # Larger color button
        self.bg_btn.setStyleSheet(f"background-color: {FuturisticUI.BACKGROUND.name()}; border: 2px solid #555; border-radius: 6px;")
        self.bg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bg_btn.setToolTip("Click to change the background color")
        self.bg_btn.clicked.connect(lambda: self._pick_color("background"))
        colors_group_layout.addWidget(self.bg_btn, 2, 1)
        
        # Text Color
        colors_group_layout.addWidget(QLabel("Text Color:"), 3, 0)
        colors_group_layout.itemAt(6).widget().setStyleSheet(color_label_style)
        
        self.text_btn = QPushButton()
        self.text_btn.setFixedSize(60, 40)  # Larger color button
        self.text_btn.setStyleSheet(f"background-color: {FuturisticUI.TEXT_PRIMARY.name()}; border: 2px solid #555; border-radius: 6px;")
        self.text_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.text_btn.setToolTip("Click to change the text color")
        self.text_btn.clicked.connect(lambda: self._pick_color("text"))
        colors_group_layout.addWidget(self.text_btn, 3, 1)
        
        colors_group.setLayout(colors_group_layout)
        colors_layout.addWidget(colors_group)
        
        # Add color preview
        preview_group = QGroupBox("Preview")
        preview_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #00ffaa;
            }
        """)
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(10, 15, 10, 10)
        
        self.color_preview = QWidget()
        self.color_preview.setMinimumHeight(120)  # Taller preview
        self.color_preview.setStyleSheet(f"background-color: {FuturisticUI.BACKGROUND.name()}; border-radius: 6px;")
        
        # Sample elements for preview
        preview_inner = QVBoxLayout(self.color_preview)
        preview_inner.setContentsMargins(15, 15, 15, 15)
        preview_inner.setSpacing(15)
        
        preview_label = QLabel("Sample Text")
        preview_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        preview_inner.addWidget(preview_label)
        
        sample_btn = QPushButton("Sample Button")
        sample_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                font-size: 14px;
                border-radius: 6px;
            }
        """)
        preview_inner.addWidget(sample_btn)
        
        preview_layout.addWidget(self.color_preview)
        preview_group.setLayout(preview_layout)
        colors_layout.addWidget(preview_group)
        
        # Add stretch
        colors_layout.addStretch()
        
        # Typography tab
        typography_tab = QWidget()
        typography_layout = QVBoxLayout(typography_tab)
        typography_layout.setContentsMargins(15, 15, 15, 15)
        typography_layout.setSpacing(20)
        
        font_group = QGroupBox("Application Font")
        font_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #00ffaa;
            }
        """)
        font_layout = QVBoxLayout()
        font_layout.setContentsMargins(15, 15, 15, 15)
        font_layout.setSpacing(15)
        
        font_description = QLabel("Change the font used throughout the application:")
        font_description.setStyleSheet("font-size: 14px; color: #ffffff;")
        font_layout.addWidget(font_description)
        
        font_btn = QPushButton("Choose Font...")
        font_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 2px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 2px solid #00ffaa;
            }
            QPushButton:pressed {
                background-color: #202020;
            }
        """)
        font_btn.setMinimumHeight(45)  # Taller button
        font_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        font_btn.clicked.connect(self._pick_font)
        font_layout.addWidget(font_btn)
        
        self.font_label = QLabel("Current Font: Default")
        self.font_label.setStyleSheet("font-size: 14px; color: #cccccc; padding: 10px; background-color: #1e1e1e; border-radius: 6px;")
        self.font_label.setMinimumHeight(40)
        font_layout.addWidget(self.font_label)
        
        # Store the font object as an instance variable
        self.selected_font = None
        
        font_group.setLayout(font_layout)
        typography_layout.addWidget(font_group)
        
        # Add stretch
        typography_layout.addStretch()
        
        # Effects tab
        effects_tab = QWidget()
        effects_layout = QVBoxLayout(effects_tab)
        effects_layout.setContentsMargins(15, 15, 15, 15)
        effects_layout.setSpacing(20)
        
        glow_group = QGroupBox("Button Glow Effects")
        glow_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #00ffaa;
            }
        """)
        glow_layout = QVBoxLayout()
        glow_layout.setContentsMargins(15, 15, 15, 15)
        glow_layout.setSpacing(15)
        
        glow_description = QLabel("Configure glow effects for interactive elements:")
        glow_description.setStyleSheet("font-size: 14px; color: #ffffff;")
        glow_layout.addWidget(glow_description)
        
        self.glow_check = QCheckBox("Enable Glow Effect")
        self.glow_check.setChecked(True)
        self.glow_check.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #ffffff;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2a2a2a;
                border: 2px solid #3a3a3a;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #00ffaa;
                border: 2px solid #00aa7f;
                border-radius: 4px;
            }
        """)
        glow_layout.addWidget(self.glow_check)
        
        glow_color_layout = QHBoxLayout()
        glow_color_label = QLabel("Glow Color:")
        glow_color_label.setStyleSheet("font-size: 14px; color: #ffffff;")
        glow_color_layout.addWidget(glow_color_label)
        
        self.glow_color_btn = QPushButton()
        self.glow_color_btn.setFixedSize(60, 30)
        self.glow_color_btn.setStyleSheet("background-color: #00ffaa; border: 2px solid #00aa7f; border-radius: 6px;")
        self.glow_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.glow_color_btn.clicked.connect(lambda: self._pick_color("glow"))
        glow_color_layout.addWidget(self.glow_color_btn)
        glow_color_layout.addStretch()
        
        glow_layout.addLayout(glow_color_layout)
        glow_group.setLayout(glow_layout)
        effects_layout.addWidget(glow_group)
        
        # Add stretch
        effects_layout.addStretch()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(colors_tab, "Colors")
        self.tab_widget.addTab(typography_tab, "Typography")
        self.tab_widget.addTab(effects_tab, "Effects")
        
        main_layout.addWidget(self.tab_widget)
        
        # Apply button
        apply_btn = QPushButton("Apply Styles")
        apply_btn.clicked.connect(self.apply_style)
        apply_btn.setMinimumHeight(50)  # Taller button
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #00aa7f;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ffaa;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #008f60;
            }
        """)
        FuturisticUI.create_neon_effect(apply_btn, QColor(0, 255, 170, 150), blur_radius=10)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        main_layout.addWidget(apply_btn)
    
    def _pick_font(self):
        """Open font dialog to pick a new font"""
        # Get current font or use default
        current_font = QApplication.font()
        
        # Show font dialog - this returns a tuple of (font, ok)
        font, ok = QFontDialog.getFont(current_font, self, "Choose Application Font")
        
        # If user selected a font (clicked OK), store it and update label
        if ok:
            self.selected_font = font  # Store the QFont object
            self.font_label.setText(f"Current Font: {font.family()}, {font.pointSize()}pt")
            
            # Preview the font in the label
            preview_font = QFont(font)
            self.font_label.setFont(preview_font)
    
    def apply_style(self):
        """Generate and apply custom stylesheet"""
        # Extract colors from the buttons
        primary_color = QColor(self.primary_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
        accent_color = QColor(self.accent_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
        bg_color = QColor(self.bg_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
        text_color = QColor(self.text_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
        
        # Check if font is selected
        font_family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        font_size = "12px"
        
        # Use the selected font if available
        if hasattr(self, 'selected_font') and self.selected_font is not None:
            font_family = self.selected_font.family()
            font_size = f"{self.selected_font.pointSize()}pt"
        
        # Generate stylesheet
        stylesheet = f"""
            QWidget {{ 
                background: {bg_color.name()}; 
                color: {text_color.name()};
                font-family: {font_family};
                font-size: {font_size};
            }}
            QPushButton {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 {bg_color.lighter(120).name()}, stop:1 {primary_color.darker(120).name()}); 
                color: {text_color.name()};
                border-radius: 6px;
                padding: 10px 18px;
                font-family: {font_family};
                font-size: {font_size};
            }}
            QPushButton:hover {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 {bg_color.lighter(140).name()}, stop:1 {primary_color.name()}); 
                border: 1px solid {accent_color.name()};
            }}
            QPushButton:pressed {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 {bg_color.darker(110).name()}, stop:1 {primary_color.darker(130).name()}); 
            }}
            QLineEdit {{ 
                background: {bg_color.lighter(110).name()}; 
                color: {text_color.name()};
                border: 1px solid {accent_color.darker(120).name()};
                border-radius: 6px;
                padding: 8px;
                font-family: {font_family};
                font-size: {font_size};
            }}
            QLineEdit:focus {{ 
                border: 2px solid {accent_color.name()};
                background: {bg_color.lighter(120).name()};
            }}
            QTableView {{
                background: {bg_color.name()};
                alternate-background-color: {bg_color.lighter(110).name()};
                color: {text_color.name()};
                gridline-color: {bg_color.lighter(120).name()};
                border: 1px solid {accent_color.darker(120).name()};
                font-family: {font_family};
                font-size: {font_size};
            }}
            QHeaderView::section {{
                background: {primary_color.name()};
                color: white;
                padding: 5px;
                font-family: {font_family};
                font-size: {font_size};
                font-weight: bold;
            }}
            QGroupBox {{
                border: 1px solid {accent_color.darker(120).name()};
                border-radius: 8px;
                margin-top: 1.2em;
                padding-top: 1em;
                font-family: {font_family};
                font-size: {font_size};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {accent_color.lighter(130).name()};
                font-family: {font_family};
                font-size: {font_size};
                font-weight: bold;
            }}
            QLabel {{
                background: transparent;
                color: {text_color.name()};
                font-family: {font_family};
                font-size: {font_size};
            }}
            QTabWidget::pane {{
                border: 1px solid {bg_color.lighter(130).name()};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background: {bg_color.lighter(110).name()};
                color: {text_color.name()};
                border: 1px solid {bg_color.lighter(130).name()};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 12px;
                font-family: {font_family};
                font-size: {font_size};
            }}
            QTabBar::tab:selected {{
                background: {primary_color.name()};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background: {bg_color.lighter(130).name()};
            }}
            QTextEdit {{
                background: {bg_color.lighter(110).name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.darker(120).name()};
                border-radius: 6px;
                padding: 5px;
                font-family: {font_family};
                font-size: {font_size};
            }}
            QComboBox {{
                background: {bg_color.lighter(110).name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.darker(120).name()};
                border-radius: 6px;
                padding: 5px;
                font-family: {font_family};
                font-size: {font_size};
            }}
        """
        
        # Apply the selected font directly to QApplication
        if hasattr(self, 'selected_font') and self.selected_font is not None:
            QApplication.instance().setFont(self.selected_font)
        
        # Show a temporary status message
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QMainWindow) and hasattr(parent, 'statusBar'):
                parent.statusBar().showMessage("Applying new style...", 1000)
                break
            parent = parent.parent()
        
        # Emit the signal with new stylesheet
        self.stylesChanged.emit(stylesheet)
        
        # Show a message box confirmation
        QMessageBox.information(self, "Styles Applied", "The new style has been applied to the application.")
    
    def _pick_color(self, name):
        """Open color dialog to pick a new color"""
        if name == "primary":
            current_color = QColor(self.primary_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
            new_color = QColorDialog.getColor(current_color, self, "Choose Primary Color")
            if new_color.isValid():
                self.primary_btn.setStyleSheet(f"background-color: {new_color.name()}; border: 2px solid #555; border-radius: 6px;")
                self._update_preview()
        elif name == "accent":
            current_color = QColor(self.accent_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
            new_color = QColorDialog.getColor(current_color, self, "Choose Accent Color")
            if new_color.isValid():
                self.accent_btn.setStyleSheet(f"background-color: {new_color.name()}; border: 2px solid #555; border-radius: 6px;")
                self._update_preview()
        elif name == "background":
            current_color = QColor(self.bg_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
            new_color = QColorDialog.getColor(current_color, self, "Choose Background Color")
            if new_color.isValid():
                self.bg_btn.setStyleSheet(f"background-color: {new_color.name()}; border: 2px solid #555; border-radius: 6px;")
                self.color_preview.setStyleSheet(f"background-color: {new_color.name()}; border-radius: 6px;")
                self._update_preview()
        elif name == "text":
            current_color = QColor(self.text_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
            new_color = QColorDialog.getColor(current_color, self, "Choose Text Color")
            if new_color.isValid():
                self.text_btn.setStyleSheet(f"background-color: {new_color.name()}; border: 2px solid #555; border-radius: 6px;")
                self._update_preview()
        elif name == "glow":
            current_color = QColor(self.glow_color_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
            new_color = QColorDialog.getColor(current_color, self, "Choose Glow Color")
            if new_color.isValid():
                self.glow_color_btn.setStyleSheet(f"background-color: {new_color.name()}; border: 2px solid #555; border-radius: 6px;")
    
    def _update_preview(self):
        """Update the color preview with current selections"""
        # Get the current colors
        try:
            bg_color = QColor(self.bg_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
            primary_color = QColor(self.primary_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
            text_color = QColor(self.text_btn.styleSheet().split("background-color:")[1].split(";")[0].strip())
            
            # Update the preview background
            self.color_preview.setStyleSheet(f"background-color: {bg_color.name()}; border-radius: 6px;")
            
            # Update the sample text and button
            for child in self.color_preview.children():
                if isinstance(child, QLabel):
                    child.setStyleSheet(f"color: {text_color.name()}; font-size: 14px; font-weight: bold; background: transparent;")
                elif isinstance(child, QPushButton):
                    child.setStyleSheet(f"""
                        QPushButton {{
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                    stop:0 {bg_color.lighter(120).name()}, stop:1 {primary_color.darker(120).name()});
                            color: {text_color.name()};
                            border-radius: 6px;
                            padding: 8px 15px;
                            font-size: 14px;
                        }}
                    """)
        except:
            # Fallback if any errors occur during preview update
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TruthTableApp()
    window.show()
    sys.exit(app.exec())
