#!/usr/bin/env python3
"""
Comprehensive UI Rendering and Styling Tests

This test suite focuses on the UI layout, style application, and rendering aspects
of the Truth Table Educational Tool. It performs checks on:

1. Layout spacing and widget sizing to prevent UI crowding
2. Global style application across components
3. Font handling and rendering without causing crashes
4. UI element visibility and proper hierarchical arrangement
5. Style editor integration with the main application
6. Theme consistency throughout the application
"""

import sys
import os
import pytest
import re
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLineEdit, QPushButton, 
    QLabel, QGroupBox, QDockWidget, QTabWidget, QTableView, 
    QComboBox, QSpinBox, QScrollArea, QVBoxLayout
)
from PyQt6.QtCore import Qt, QSize, QRect, QPoint, QMargins
from PyQt6.QtGui import QColor, QFont, QPalette

# Import application components
from Visual_Truth_Table import (
    TruthTableApp, StyleEditor, FuturisticUI, AppTheme,
    IdentifierLineEdit, ExpressionWidget, FloatingSymbolToolbar
)

# Define placeholder classes for testing
class EnhancedStyleEditor(QWidget):
    """Placeholder for the enhanced style editor"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EnhancedStyleEditor")

class AdvancedTestApp(QMainWindow):
    """Placeholder for the advanced test app"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AdvancedTestApp")

# Test fixtures
@pytest.fixture
def app():
    """PyQt QApplication fixture"""
    application = QApplication(sys.argv)
    # Enable high DPI scaling
    application.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # Force consistent font rendering
    application.setFont(QFont("Arial", 12))
    yield application
    application.quit()

@pytest.fixture
def truth_table_app(app):
    """Create a truth table app instance for testing"""
    tt_app = TruthTableApp()
    yield tt_app
    tt_app.deleteLater()

@pytest.fixture
def advanced_test_app(app):
    """Create an advanced test app instance"""
    adv_app = AdvancedTestApp()
    yield adv_app
    adv_app.deleteLater()

@pytest.fixture
def enhanced_style_editor(app):
    """Create an enhanced style editor for testing"""
    editor = EnhancedStyleEditor()
    yield editor
    editor.deleteLater()

@pytest.fixture
def style_editor(app):
    """Create a standard style editor for testing"""
    editor = StyleEditor()
    yield editor
    editor.deleteLater()

# Test utilities
def get_widget_tree(widget, level=0, max_depth=3):
    """Generate a hierarchical tree of widgets for analysis"""
    if level > max_depth:
        return []
    
    result = [f"{'  ' * level}{widget.__class__.__name__}: {widget.objectName() or 'unnamed'}"]
    
    for child in widget.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
        result.extend(get_widget_tree(child, level + 1, max_depth))
    
    return result

def check_layout_spacing(layout):
    """Check that a layout has reasonable spacing and margins"""
    if not layout:
        return False, "No layout found"
    
    # Check spacing
    spacing = layout.spacing()
    if spacing < 0:
        return False, f"Layout spacing is negative: {spacing}"
    if spacing > 20:
        return False, f"Layout spacing is too large: {spacing}"
    
    # Check margins
    margins = layout.contentsMargins()
    if any(m < 0 for m in [margins.left(), margins.top(), margins.right(), margins.bottom()]):
        return False, f"Layout has negative margins: {margins.left()}, {margins.top()}, {margins.right()}, {margins.bottom()}"
    if any(m > 30 for m in [margins.left(), margins.top(), margins.right(), margins.bottom()]):
        return False, f"Layout has excessively large margins: {margins.left()}, {margins.top()}, {margins.right()}, {margins.bottom()}"
    
    return True, "Layout spacing is reasonable"

def check_widget_sizes(widget_list, min_size=30, max_size=500):
    """Verify that widgets have reasonable sizes (not too small or large)"""
    results = []
    
    for widget in widget_list:
        size = widget.size()
        if size.width() < min_size or size.height() < min_size:
            results.append(f"{widget.__class__.__name__} is too small: {size.width()}x{size.height()}")
        elif size.width() > max_size or size.height() > max_size:
            results.append(f"{widget.__class__.__name__} is too large: {size.width()}x{size.height()}")
    
    return results

def extract_stylesheet_properties(stylesheet, property_name):
    """Extract all values of a specific property from a stylesheet"""
    pattern = r'(?:^|\s)' + property_name + r'\s*:\s*([^;]+);'
    matches = re.findall(pattern, stylesheet)
    return matches

def analyze_style_consistency(widget):
    """Analyze style consistency across a widget and its children"""
    # Extract styles from the widget and all children
    stylesheet = widget.styleSheet()
    
    # Get all unique background colors
    bg_colors = set(extract_stylesheet_properties(stylesheet, "background-color"))
    font_families = set(extract_stylesheet_properties(stylesheet, "font-family"))
    font_sizes = set(extract_stylesheet_properties(stylesheet, "font-size"))
    
    return {
        "background_colors": list(bg_colors),
        "font_families": list(font_families),
        "font_sizes": list(font_sizes)
    }

# UI Layout Tests
class TestUILayout:
    """Test suite for UI layout and spacing"""
    
    def test_main_app_sizing(self, truth_table_app):
        """Test main app has appropriate dimensions"""
        # Get the main window size
        size = truth_table_app.size()
        
        # Check reasonable size constraints
        assert size.width() >= 800, "Main window should be at least 800px wide"
        assert size.height() >= 600, "Main window should be at least 600px tall"
        
        # Check not excessively large
        assert size.width() <= 1920, "Main window should not exceed 1920px wide"
        assert size.height() <= 1080, "Main window should not exceed 1080px tall"
    
    def test_dock_widget_proportions(self, truth_table_app):
        """Test that dock widgets have appropriate proportions"""
        # Get dock widgets
        dock_widgets = truth_table_app.findChildren(QDockWidget)
        assert len(dock_widgets) >= 2, "App should have at least 2 dock widgets"
        
        # Check individual dock sizes
        for dock in dock_widgets:
            size = dock.size()
            
            # Docks should have reasonable dimensions
            assert size.width() >= 200, f"Dock '{dock.windowTitle()}' width should be at least 200px"
            assert size.height() >= 100, f"Dock '{dock.windowTitle()}' height should be at least 100px"
            
            # Width should not be insanely large compared to the main window
            assert size.width() <= truth_table_app.width() * 0.8, f"Dock '{dock.windowTitle()}' width should not exceed 80% of main window"
    
    def test_central_widget_visibility(self, truth_table_app):
        """Test that the central widget (truth table) has appropriate visibility"""
        # Get the central widget
        central_widget = truth_table_app.centralWidget()
        assert central_widget is not None, "Central widget should exist"
        
        # Table view should be visible in central area
        table_view = central_widget.findChild(QTableView)
        assert table_view is not None, "Table view should exist in central widget"
        
        # Table should have reasonable dimensions
        assert table_view.width() >= 400, "Table view should be at least 400px wide"
        assert table_view.height() >= 300, "Table view should be at least 300px tall"
    
    def test_button_sizing(self, truth_table_app):
        """Test that buttons have appropriate and consistent sizing"""
        # Get all buttons
        buttons = truth_table_app.findChildren(QPushButton)
        assert len(buttons) > 0, "App should have buttons"
        
        # Check button sizes
        button_heights = [btn.height() for btn in buttons]
        min_height = min(button_heights)
        max_height = max(button_heights)
        
        # Buttons should have reasonable heights
        assert min_height >= 25, f"Smallest button is too small: {min_height}px"
        assert max_height <= 60, f"Largest button is too large: {max_height}px"
        
        # Check consistency - height variation should not be extreme
        assert max_height / min_height <= 2.0, "Button height variation is excessive"
    
    def test_input_field_sizing(self, truth_table_app):
        """Test that input fields have appropriate sizing"""
        # Get all line edits
        line_edits = truth_table_app.findChildren(QLineEdit)
        assert len(line_edits) > 0, "App should have input fields"
        
        # Check line edit sizes
        for edit in line_edits:
            # Input fields should have reasonable dimensions
            assert edit.height() >= 20, f"Line edit height too small: {edit.height()}px"
            assert edit.width() >= 100, f"Line edit width too small: {edit.width()}px"
            assert edit.height() <= 50, f"Line edit height too large: {edit.height()}px"
    
    def test_layout_spacing(self, truth_table_app):
        """Test layout spacing is reasonable throughout the app"""
        # Check a sample of widgets with layouts
        widgets_with_layouts = []
        
        # Get variable config widget
        variable_config = truth_table_app.variable_config
        if variable_config and variable_config.layout():
            widgets_with_layouts.append(variable_config)
        
        # Get expression widget
        expression_widget = truth_table_app.expression_widget
        if expression_widget and expression_widget.layout():
            widgets_with_layouts.append(expression_widget)
        
        # Check layouts for reasonable spacing
        for widget in widgets_with_layouts:
            layout = widget.layout()
            is_reasonable, message = check_layout_spacing(layout)
            assert is_reasonable, f"Layout issues in {widget.__class__.__name__}: {message}"
    
    def test_scroll_areas(self, truth_table_app):
        """Test scroll areas function correctly and are properly sized"""
        # Get scroll areas
        scroll_areas = truth_table_app.findChildren(QScrollArea)
        
        for scroll_area in scroll_areas:
            # Scroll areas should be visible
            assert scroll_area.isVisibleTo(truth_table_app), "Scroll area should be visible"
            
            # Should have appropriate minimum size
            assert scroll_area.minimumWidth() <= scroll_area.width(), "Scroll area width constrained by minimum width"
            assert scroll_area.minimumHeight() <= scroll_area.height(), "Scroll area height constrained by minimum height"
            
            # Should have a viewport with content
            viewport = scroll_area.viewport()
            assert viewport is not None, "Scroll area should have a viewport"
            
            # Content widget should exist
            content_widget = scroll_area.widget()
            assert content_widget is not None, "Scroll area should have content widget"
    
    def test_tab_widget_proportions(self, truth_table_app):
        """Test that tab widgets have appropriate proportions"""
        # Get tab widgets
        tab_widgets = truth_table_app.findChildren(QTabWidget)
        
        for tab_widget in tab_widgets:
            # Should have appropriate height
            assert tab_widget.height() >= 200, f"Tab widget too short: {tab_widget.height()}px"
            
            # Should have at least one tab
            assert tab_widget.count() > 0, "Tab widget should have at least one tab"
            
            # Tabs should be visible
            tab_bar = tab_widget.tabBar()
            assert tab_bar.isVisible(), "Tab bar should be visible"
            assert tab_bar.count() > 0, "Tab bar should have tabs"

# Style Application Tests
class TestStyleApplication:
    """Test suite for style application and consistency"""
    
    def test_global_stylesheet_application(self, truth_table_app):
        """Test that global stylesheet is applied to the entire application"""
        # Apply a distinctive test stylesheet
        test_style = """
        QWidget { background-color: #223344; color: #AABBCC; }
        QPushButton { background-color: #445566; }
        QLineEdit { background-color: #667788; }
        """
        
        # Apply the style
        truth_table_app.setStyleSheet(test_style)
        
        # Check main application has style
        assert "#223344" in truth_table_app.styleSheet(), "Main window should have the test background color"
        
        # Check major components have inherited the style
        # Note: We're not directly checking widget.styleSheet() as it might be empty
        # because styles are often inherited from parents
        
        # Instead, check that palette colors reflect our styling
        central_widget = truth_table_app.centralWidget()
        assert central_widget is not None, "Central widget should exist"
        
        # The effective stylesheet should cascade to children
        dock_widgets = truth_table_app.findChildren(QDockWidget)
        for dock in dock_widgets:
            style = dock.styleSheet()
            # Either has own style or inherits from parent
            assert dock.styleSheet() == test_style or dock.styleSheet() == "", "Dock widget stylesheet issue"
    
    def test_style_editor_changes_propagate(self, truth_table_app, style_editor):
        """Test that style changes from StyleEditor propagate correctly"""
        # Create a distinctive test stylesheet
        test_style = """
        QWidget { background-color: #345678; color: white; }
        QPushButton { border-radius: 8px; background-color: #567890; }
        QLineEdit { border: 2px solid #789012; background-color: #123456; }
        """
        
        # Directly call apply_style_changes method instead of signal
        truth_table_app.apply_style_changes(test_style)
        
        # Verify style was applied to main window
        assert truth_table_app.styleSheet() == test_style, "Style should be applied to main window"
        
        # Check that key components have the style applied or inherited
        central_widget = truth_table_app.centralWidget()
        assert central_widget is not None, "Central widget should exist"
        assert central_widget.styleSheet() == "" or "#345678" in central_widget.styleSheet(), "Central widget should inherit style"
        
        # Check all buttons should either have no style (inheriting) or the test style
        buttons = truth_table_app.findChildren(QPushButton)
        for button in buttons:
            assert button.styleSheet() == "" or "#567890" in button.styleSheet(), "Button should inherit style"
    
    def test_style_consistency(self, truth_table_app):
        """Test style consistency across different UI components"""
        # Set baseline styles
        truth_table_app.setStyleSheet("")  # Clear any existing styles
        AppTheme.get_main_stylesheet()  # Apply app theme
        
        # Apply consistent styling
        buttons = truth_table_app.findChildren(QPushButton)
        line_edits = truth_table_app.findChildren(QLineEdit)
        labels = truth_table_app.findChildren(QLabel)
        
        # Verify consistent button styling
        button_heights = {button.height() for button in buttons}
        assert len(button_heights) <= 3, f"Too many different button heights: {button_heights}"
        
        # Verify consistent input field styling
        line_edit_heights = {edit.height() for edit in line_edits}
        assert len(line_edit_heights) <= 3, f"Too many different line edit heights: {line_edit_heights}"
        
        # Verify consistent font usage
        label_fonts = {label.font().family() for label in labels}
        assert len(label_fonts) <= 3, f"Too many different fonts: {label_fonts}"
    
    def test_futuristic_ui_style(self, truth_table_app):
        """Test application of FuturisticUI style"""
        # Apply futuristic style
        FuturisticUI.set_futuristic_style(QApplication.instance())
        
        # Main window should have dark background
        app_style = QApplication.instance().styleSheet()
        assert "#121212" in app_style or "rgb(18, 18, 18)" in app_style, "FuturisticUI style not properly applied"
        
        # Add a test button and apply gradient
        test_button = QPushButton("Test Button")
        FuturisticUI.create_gradient_button(
            test_button,
            start_color=FuturisticUI.SURFACE,
            end_color=FuturisticUI.PRIMARY,
            hover_color=FuturisticUI.ACCENT
        )
        
        # Check button style
        assert "qlineargradient" in test_button.styleSheet(), "Gradient not applied to button"
        assert FuturisticUI.SURFACE.name() in test_button.styleSheet() or str(FuturisticUI.SURFACE.rgba()) in test_button.styleSheet(), "Surface color not in button style"

# Font Handling Tests
class TestFontHandling:
    """Test suite for font handling and rendering"""
    
    def test_font_application(self, truth_table_app):
        """Test that fonts can be applied without crashes"""
        # Apply a basic font with reasonable settings (avoid exotic fonts that might not exist)
        test_font = QFont("Arial", 12)
        
        # Set font and verify no crash
        try:
            truth_table_app.setFont(test_font)
            assert truth_table_app.font().family() == "Arial", "Font family should be set"
            assert truth_table_app.font().pointSize() == 12, "Font size should be set"
        except Exception as e:
            pytest.fail(f"Font application caused an error: {str(e)}")
        
        # Setting font size through CSS should also work
        try:
            truth_table_app.setStyleSheet("QWidget { font-size: 13px; }")
        except Exception as e:
            pytest.fail(f"Font size CSS caused an error: {str(e)}")
    
    def test_custom_font_loading(self, truth_table_app):
        """Test loading custom fonts (or reasonable fallbacks)"""
        # Test applying a style with custom font family
        custom_font_style = """
        QWidget { font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; }
        """
        
        try:
            truth_table_app.setStyleSheet(custom_font_style)
            # Success is not crashing
        except Exception as e:
            pytest.fail(f"Custom font style caused an error: {str(e)}")
    
    def test_font_size_changes(self, truth_table_app):
        """Test changing font sizes doesn't break layout"""
        # Get initial sizes of some key widgets
        central_widget = truth_table_app.centralWidget()
        initial_central_height = central_widget.height()
        
        # Apply larger font size
        large_font_style = """
        QWidget { font-size: 16px; }
        QLabel { font-size: 16px; }
        QPushButton { font-size: 16px; }
        """
        
        try:
            truth_table_app.setStyleSheet(large_font_style)
            
            # Verify no crash and sizes adjusted reasonably
            new_central_height = central_widget.height()
            
            # Height might change slightly but shouldn't change dramatically
            height_ratio = abs(new_central_height / initial_central_height)
            assert 0.5 <= height_ratio <= 1.5, f"Font size change caused dramatic layout change. Ratio: {height_ratio}"
        except Exception as e:
            pytest.fail(f"Font size change caused an error: {str(e)}")

# Enhanced Style Editor Tests
class TestEnhancedStyleEditor:
    """Test suite for the EnhancedStyleEditor from advanced_test.py"""
    
    def test_tab_organization(self, enhanced_style_editor):
        """Test proper tab organization in enhanced style editor"""
        # Find the tab widget
        tab_widget = enhanced_style_editor.findChild(QTabWidget)
        assert tab_widget is not None, "Tab widget not found in EnhancedStyleEditor"
        
        # Check all required tabs exist
        tab_count = tab_widget.count()
        assert tab_count >= 4, f"Expected at least 4 tabs, found {tab_count}"
        
        # Check all required tab titles
        expected_tabs = ["Colors", "Typography", "Components", "Effects"]
        tab_titles = [tab_widget.tabText(i) for i in range(tab_count)]
        
        for expected in expected_tabs:
            assert expected in tab_titles, f"Missing tab: {expected}"
    
    def test_color_configuration(self, enhanced_style_editor):
        """Test color configuration tab in enhanced style editor"""
        # Find the tab widget and select Colors tab
        tab_widget = enhanced_style_editor.findChild(QTabWidget)
        assert tab_widget is not None, "Tab widget not found"
        
        # Find Colors tab index
        colors_tab_index = -1
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i) == "Colors":
                colors_tab_index = i
                break
        
        assert colors_tab_index >= 0, "Colors tab not found"
        
        # Set current tab to Colors
        tab_widget.setCurrentIndex(colors_tab_index)
        
        # Check for color pickers
        assert hasattr(enhanced_style_editor, 'color_pickers'), "No color_pickers attribute"
        assert len(enhanced_style_editor.color_pickers) > 0, "No color pickers found"
        
        # Check for theme colors group
        theme_colors_group = None
        for group in enhanced_style_editor.findChildren(QGroupBox):
            if "Theme Colors" in group.title():
                theme_colors_group = group
                break
        
        assert theme_colors_group is not None, "Theme Colors group not found"
        
        # Check for preview section
        preview_group = None
        for group in enhanced_style_editor.findChildren(QGroupBox):
            if "Preview" in group.title():
                preview_group = group
                break
        
        assert preview_group is not None, "Preview section not found"
    
    def test_typography_configuration(self, enhanced_style_editor):
        """Test typography configuration tab in enhanced style editor"""
        # Find the tab widget and select Typography tab
        tab_widget = enhanced_style_editor.findChild(QTabWidget)
        
        # Find Typography tab index
        typography_tab_index = -1
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i) == "Typography":
                typography_tab_index = i
                break
        
        assert typography_tab_index >= 0, "Typography tab not found"
        
        # Set current tab to Typography
        tab_widget.setCurrentIndex(typography_tab_index)
        
        # Check for font selection group
        font_group = None
        for group in enhanced_style_editor.findChildren(QGroupBox):
            if "Font" in group.title():
                font_group = group
                break
        
        assert font_group is not None, "Font selection group not found"
        
        # Check for text size settings group
        size_group = None
        for group in enhanced_style_editor.findChildren(QGroupBox):
            if "Size" in group.title():
                size_group = group
                break
        
        assert size_group is not None, "Text size group not found"
        
        # Check for combo boxes (size options)
        combos = size_group.findChildren(QComboBox)
        assert len(combos) > 0, "No size selection combo boxes found"
    
    def test_style_generation(self, enhanced_style_editor):
        """Test style generation and application in enhanced style editor"""
        # Find apply button
        apply_button = None
        for button in enhanced_style_editor.findChildren(QPushButton):
            if button.text() == "Apply Styles":
                apply_button = button
                break
        
        assert apply_button is not None, "Apply Styles button not found"
        
        # Create a mock slot to receive the style signal
        mock_receiver = MagicMock()
        
        # Connect to the signal
        enhanced_style_editor.stylesChanged.connect(mock_receiver)
        
        # Trigger apply_style method
        enhanced_style_editor.apply_style()
        
        # Check that the signal was emitted
        assert mock_receiver.called, "stylesChanged signal was not emitted"
        
        # Check that generated style contains essential elements
        generated_style = mock_receiver.call_args[0][0]
        assert "QWidget" in generated_style, "Generated style missing QWidget section"
        assert "QPushButton" in generated_style, "Generated style missing QPushButton section"
        assert "QLineEdit" in generated_style, "Generated style missing QLineEdit section"
        assert "QTableView" in generated_style, "Generated style missing QTableView section"
    
    def test_style_clearing_and_rebuilding(self, enhanced_style_editor):
        """Test that UI structure can be cleared and rebuilt without errors"""
        # Count widgets before clearing
        initial_button_count = len(enhanced_style_editor.findChildren(QPushButton))
        initial_tab_count = len(enhanced_style_editor.findChildren(QTabWidget))
        
        assert initial_button_count > 0, "No buttons found before clearing"
        assert initial_tab_count > 0, "No tab widgets found before clearing"
        
        # Clear the UI
        enhanced_style_editor._clear_current_layout()
        
        # Count widgets after clearing
        clearing_button_count = len(enhanced_style_editor.findChildren(QPushButton))
        clearing_tab_count = len(enhanced_style_editor.findChildren(QTabWidget))
        
        # Now rebuild
        enhanced_style_editor._rebuild_ui()
        
        # Count widgets after rebuilding
        rebuilt_button_count = len(enhanced_style_editor.findChildren(QPushButton))
        rebuilt_tab_count = len(enhanced_style_editor.findChildren(QTabWidget))
        
        # Verify rebuilding created similar structure
        assert rebuilt_button_count > 0, "No buttons after rebuilding UI"
        assert rebuilt_tab_count > 0, "No tab widgets after rebuilding UI"
        assert abs(rebuilt_button_count - initial_button_count) <= 2, "Significant difference in button count after rebuilding"
        assert rebuilt_tab_count == initial_tab_count, "Tab count changed after rebuilding"

# Advanced Application Tests
class TestAdvancedApplication:
    """Test suite for AdvancedTestApp and complex UI interactions"""
    
    def test_app_initialization(self, advanced_test_app):
        """Test proper initialization of advanced test app"""
        # Check window dimensions
        size = advanced_test_app.size()
        assert size.width() >= 800, "Advanced app window should be reasonably wide"
        assert size.height() >= 600, "Advanced app window should be reasonably tall"
        
        # Check tab structure
        tabs = advanced_test_app.tabs
        assert tabs is not None, "Tabs widget not found"
        assert tabs.count() >= 4, "Expected at least 4 test tabs"
        
        # Check for main components
        assert hasattr(advanced_test_app, 'status_bar'), "Status bar not created"
        assert advanced_test_app.status_bar is not None, "Status bar is None"
    
    def test_symbol_test_tab(self, advanced_test_app):
        """Test symbol insertion test tab organization"""
        # Find symbol test tab
        symbol_tab_index = -1
        for i in range(advanced_test_app.tabs.count()):
            if "Symbol" in advanced_test_app.tabs.tabText(i):
                symbol_tab_index = i
                break
        
        assert symbol_tab_index >= 0, "Symbol Insertion tab not found"
        
        # Set current tab
        advanced_test_app.tabs.setCurrentIndex(symbol_tab_index)
        
        # Check for test input fields
        assert hasattr(advanced_test_app, 'regular_edit'), "Regular edit field not found"
        assert hasattr(advanced_test_app, 'id_edit'), "Identifier edit field not found"
        assert hasattr(advanced_test_app, 'expr_edit'), "Expression edit field not found"
        
        # Check for symbol buttons
        symbol_groups = [g for g in advanced_test_app.findChildren(QGroupBox) if "Symbol" in g.title()]
        assert len(symbol_groups) > 0, "Symbol buttons group not found"
        
        symbol_buttons = []
        for group in symbol_groups:
            symbol_buttons.extend(group.findChildren(QPushButton))
        
        assert len(symbol_buttons) > 0, "No symbol buttons found"
        
        # Check for floating toolbar
        assert hasattr(advanced_test_app, 'floating_toolbar'), "Floating toolbar not found"
        assert advanced_test_app.floating_toolbar is not None, "Floating toolbar is None"
    
    def test_styling_test_tab(self, advanced_test_app):
        """Test style editor test tab organization"""
        # Find styling test tab
        style_tab_index = -1
        for i in range(advanced_test_app.tabs.count()):
            if "Style" in advanced_test_app.tabs.tabText(i):
                style_tab_index = i
                break
        
        assert style_tab_index >= 0, "Style Editor tab not found"
        
        # Set current tab
        advanced_test_app.tabs.setCurrentIndex(style_tab_index)
        
        # Check for enhanced style editor
        assert hasattr(advanced_test_app, 'style_editor'), "Style editor not found"
        assert advanced_test_app.style_editor is not None, "Style editor is None"
        assert isinstance(advanced_test_app.style_editor, EnhancedStyleEditor), "Style editor is not enhanced version"
    
    def test_legibility_test_tab(self, advanced_test_app):
        """Test legibility test tab organization"""
        # Find legibility test tab
        legibility_tab_index = -1
        for i in range(advanced_test_app.tabs.count()):
            if "Legibility" in advanced_test_app.tabs.tabText(i):
                legibility_tab_index = i
                break
        
        assert legibility_tab_index >= 0, "Text Legibility tab not found"
        
        # Set current tab
        advanced_test_app.tabs.setCurrentIndex(legibility_tab_index)
        
        # Check for legibility matrix
        matrix_groups = [g for g in advanced_test_app.findChildren(QGroupBox) if "Matrix" in g.title()]
        assert len(matrix_groups) > 0, "Legibility matrix group not found"
        
        # Check for a reasonable number of test cells
        labels = matrix_groups[0].findChildren(QLabel)
        assert len(labels) >= 12, "Not enough legibility test cells"  # 3 backgrounds * 4 sizes + headers
    
    def test_launch_main_app(self, advanced_test_app):
        """Test launching main app from advanced test app"""
        # Find app test tab
        app_tab_index = -1
        for i in range(advanced_test_app.tabs.count()):
            if "Main Application" == advanced_test_app.tabs.tabText(i):
                app_tab_index = i
                break
        
        assert app_tab_index >= 0, "Main Application tab not found"
        
        # Set current tab
        advanced_test_app.tabs.setCurrentIndex(app_tab_index)
        
        # Find launch button
        launch_buttons = [btn for btn in advanced_test_app.findChildren(QPushButton) if "Launch" in btn.text()]
        assert len(launch_buttons) > 0, "Launch button not found"
        
        # Check container exists
        assert hasattr(advanced_test_app, 'app_container'), "App container not found"
        
        # Mock the truth table app creation to avoid potential crashes
        with patch('advanced_test.TruthTableApp') as mock_app:
            # Create a mock truth table app
            mock_instance = MagicMock()
            mock_app.return_value = mock_instance
            
            # Launch the app
            advanced_test_app.launch_main_app()
            
            # Verify TruthTableApp was instantiated
            assert mock_app.called, "TruthTableApp constructor not called"
            
            # Verify it was added to the container
            assert hasattr(advanced_test_app, 'truth_table_app'), "truth_table_app attribute not set"

# Global Style Integration Tests
class TestGlobalStyleIntegration:
    """Test integration of different styling components"""
    
    def test_style_editor_to_app_integration(self, truth_table_app, style_editor):
        """Test that style editor changes properly apply to the main app"""
        # Create a custom style with a distinct color
        sample_color = "#A1B2C3"
        test_style = f"""
        QWidget {{ background-color: {sample_color}; }}
        QPushButton {{ background-color: #D4E5F6; color: black; }}
        """
        
        # Mock sending the style signal
        style_editor.stylesChanged.emit(test_style)
        
        # Check that main app received and applied the style
        assert sample_color in truth_table_app.styleSheet() or sample_color.lower() in truth_table_app.styleSheet().lower(), "Style change not applied to main app"
    
    def test_futuristic_to_advanced_integration(self, advanced_test_app):
        """Test FuturisticUI style integration with the advanced app"""
        # Apply futuristic style
        FuturisticUI.set_futuristic_style(QApplication.instance())
        
        # Check for dark theme in app
        app_style = QApplication.instance().styleSheet()
        assert "#121212" in app_style or "rgb(18, 18, 18)" in app_style, "FuturisticUI style not applied to application"
        
        # Create a test button with gradient effect
        with patch.object(advanced_test_app, 'setStyleSheet') as mock_set_style:
            # Simulate applying new styles
            advanced_test_app.apply_style_changes(app_style)
            
            # Check that the style was applied
            assert mock_set_style.called, "setStyleSheet not called on advanced app"
    
    def test_consistency_across_components(self, advanced_test_app):
        """Test style consistency across different UI components in a complex app"""
        # Get colors from various components
        background_colors = set()
        button_colors = set()
        text_colors = set()
        
        # Extract stylesheet components
        app_style = advanced_test_app.styleSheet()
        bg_colors = extract_stylesheet_properties(app_style, "background-color")
        for color in bg_colors:
            background_colors.add(color.strip())
        
        # Check button styling to see if consistent
        buttons = advanced_test_app.findChildren(QPushButton)
        for button in buttons:
            btn_style = button.styleSheet()
            bg_colors = extract_stylesheet_properties(btn_style, "background-color")
            for color in bg_colors:
                button_colors.add(color.strip())
        
        # Check reasonable number of colors (theme consistency)
        assert len(background_colors) <= 10, f"Too many background colors ({len(background_colors)}), suggests inconsistent theme"
        assert len(button_colors) <= 5, f"Too many button colors ({len(button_colors)}), suggests inconsistent styling"
    
    def test_theme_cascade(self, truth_table_app):
        """Test that theme changes cascade properly to all components"""
        # Apply a custom stylesheet with easily identifiable colors
        custom_theme = """
        QWidget { background-color: #222222; color: white; }
        QPushButton { background-color: #444444; }
        QLineEdit { background-color: #333333; }
        QLabel { color: #EEEEEE; }
        """
        
        truth_table_app.setStyleSheet(custom_theme)
        
        # Check specific component types have the theme applied
        dock_widgets = truth_table_app.findChildren(QDockWidget)
        
        for dock in dock_widgets:
            # Should either have empty style (inherited) or match parent
            assert dock.styleSheet() == "" or dock.styleSheet() == custom_theme, "Dock widget does not have correct style"
            
            # Check children within the dock
            dock_content = dock.widget()
            if dock_content:
                assert dock_content.styleSheet() == "" or dock_content.styleSheet() == custom_theme, "Dock content does not have correct style"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 