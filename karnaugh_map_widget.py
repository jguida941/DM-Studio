"""
Karnaugh Map Widget for Truth Table Educational Tool

This widget provides interactive Karnaugh map visualization and Boolean expression simplification.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTextEdit, QFrame, QGridLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox,
    QSpacerItem, QSizePolicy, QToolTip
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPixmap

import logic_simplification as ls


class KarnaughCellWidget(QFrame):
    """
    A custom widget to represent a cell in the Karnaugh map.
    
    This provides interactive features like hover highlighting and click selection.
    """
    
    clicked = pyqtSignal(int, int)  # row, col
    
    def __init__(self, value, row, col, parent=None):
        super().__init__(parent)
        self.value = value
        self.row = row
        self.col = col
        self.is_highlighted = False
        self.groups = {}  # Map group_id to is_essential
        
        # Configure appearance
        self.setMinimumSize(50, 50)
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Plain)
        
        # Setup the layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        # Value label
        self.value_label = QLabel(str(value))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Set initial appearance
        self._update_appearance()
        
    def add_group(self, group_id, is_essential):
        """Add this cell to a group."""
        self.groups[group_id] = is_essential
        self._update_appearance()
        
    def clear_groups(self):
        """Remove cell from all groups."""
        self.groups.clear()
        self._update_appearance()
        
    def _update_appearance(self):
        """Update the cell's visual styling based on its state."""
        if self.value == 'X':
            # Don't care cell
            bg_color = "#E0E0E0"
            text_color = "#707070"
        elif self.value == 1:
            # Minterm (True)
            bg_color = "#D0FFD0"  # Light green
            text_color = "#006000"
        else:
            # Maxterm (False)
            bg_color = "#FFD0D0"  # Light red
            text_color = "#600000"
        
        # If cell belongs to any group, use a custom highlight color
        if self.groups:
            # If cell belongs to an essential prime implicant, use a brighter highlight
            if any(is_essential for is_essential in self.groups.values()):
                border_color = "#FF00FF"  # Magenta for essential
                border_width = 3
            else:
                border_color = "#1E90FF"  # Blue for regular prime implicant
                border_width = 2
                
            # Adjust background for grouped cells
            if self.value == 1:
                bg_color = "#90EE90"  # Brighter green for grouped 1s
            elif self.value == 'X':
                bg_color = "#C0C0C0"  # Darker gray for grouped don't cares
        else:
            border_color = "#A0A0A0"
            border_width = 1
            
        if self.is_highlighted:
            # Brighten the background when highlighted
            border_color = "#FF5500"  # Orange highlight
            border_width = 3
            
        # Apply the styling
        self.setStyleSheet(f"""
            KarnaughCellWidget {{
                background-color: {bg_color};
                border: {border_width}px solid {border_color};
            }}
            QLabel {{
                color: {text_color};
                font-weight: bold;
                font-size: 14px;
                background-color: transparent;
            }}
        """)
        
    def enterEvent(self, event):
        """Handle mouse hover enter."""
        self.is_highlighted = True
        self._update_appearance()
        
        # Show tooltip with cell information
        groups_info = []
        for group_id, is_essential in self.groups.items():
            groups_info.append(f"Group {group_id}{' (Essential)' if is_essential else ''}")
            
        tooltip = f"Value: {self.value}<br>Position: ({self.row}, {self.col})"
        if groups_info:
            tooltip += "<br>Groups: " + ", ".join(groups_info)
            
        QToolTip.showText(event.globalPosition().toPoint(), tooltip, self)
        
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse hover leave."""
        self.is_highlighted = False
        self._update_appearance()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.row, self.col)
        super().mousePressEvent(event)


class KMapGrouping:
    """Helper class to represent a visual grouping in the Karnaugh map."""
    
    def __init__(self, cells, term, is_essential=False, color=None):
        """
        Initialize a K-map grouping.
        
        Args:
            cells: List of (row, col) tuples of the cells in this group
            term: The Boolean term this group represents
            is_essential: Whether this is an essential prime implicant
            color: The color to use for this group
        """
        self.cells = cells
        self.term = term
        self.is_essential = is_essential
        
        # Generate a deterministic color if none provided
        if color is None:
            # Simple hash of the term to get a deterministic color
            hashed = sum(ord(c) for c in term) % 1000
            r = (hashed * 13) % 200 + 55  # Avoid too dark or too light
            g = (hashed * 17) % 200 + 55
            b = (hashed * 19) % 200 + 55
            self.color = QColor(r, g, b, 100)  # Semi-transparent
        else:
            self.color = color


class KarnaughMapWidget(QWidget):
    """
    Widget to display and interact with Karnaugh maps.
    
    Features:
    - Visualize truth table data as a Karnaugh map
    - Highlight prime implicants and essential prime implicants
    - Show simplified Boolean expressions
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # State variables
        self.variables = []
        self.minterms = []
        self.dont_cares = []
        self.k_map = None
        self.groupings = []
        self.cells = []  # 2D grid of KarnaughCellWidget instances
        
        # Setup UI
        self._build_ui()
        
    def _build_ui(self):
        """Set up the widget's UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("Karnaugh Map")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        main_layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Karnaugh maps visually represent Boolean functions to simplify expressions. "
            "Prime implicants are shown as groups of adjacent cells."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(description)
        
        # Options panel
        options_group = QGroupBox("Display Options")
        options_layout = QHBoxLayout()
        
        # Option to show/hide essential prime implicants
        self.show_essential_cb = QCheckBox("Highlight Essential Prime Implicants")
        self.show_essential_cb.setChecked(True)
        self.show_essential_cb.toggled.connect(self.update_display)
        options_layout.addWidget(self.show_essential_cb)
        
        # Option to show all prime implicants
        self.show_all_pi_cb = QCheckBox("Show All Prime Implicants")
        self.show_all_pi_cb.setChecked(True)
        self.show_all_pi_cb.toggled.connect(self.update_display)
        options_layout.addWidget(self.show_all_pi_cb)
        
        options_layout.addStretch()
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # K-map display
        map_container = QFrame()
        map_container.setFrameShape(QFrame.Shape.StyledPanel)
        map_container.setFrameShadow(QFrame.Shadow.Raised)
        map_layout = QVBoxLayout(map_container)
        
        # Grid for the K-map cells
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(2)
        map_layout.addLayout(self.grid_layout)
        
        # Scroll area for K-map (useful for larger maps with 4+ variables)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(map_container)
        main_layout.addWidget(scroll_area, 3)  # Give it more stretch
        
        # Results panel
        results_group = QGroupBox("Simplified Expressions")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group, 1)  # Give it less stretch
        
        # Initially there's no map, so create a placeholder
        self._create_placeholder()
        
    def _create_placeholder(self):
        """Create a placeholder when no map is available."""
        # Clear the grid layout
        self._clear_grid()
        
        # Add a placeholder label
        placeholder = QLabel("No map available. Generate a truth table first.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("font-size: 14px; color: #888888;")
        self.grid_layout.addWidget(placeholder, 0, 0)
        
        # Clear the results text
        self.results_text.clear()
        self.results_text.setHtml(
            "<p style='color: #888888; text-align: center;'>"
            "Generate a truth table to see simplified expressions."
            "</p>"
        )
        
    def _clear_grid(self):
        """Clear the grid layout."""
        # Remove all widgets from the grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Reset cells tracking
        self.cells = []
                
    def update_from_truth_table(self, variable_names, minterms, dont_cares=None):
        """
        Update the Karnaugh map from truth table data.
        
        Args:
            variable_names: List of variable names
            minterms: List of indices where the function is 1
            dont_cares: Optional list of indices where the function doesn't matter
        """
        self.variables = variable_names
        self.minterms = minterms
        self.dont_cares = dont_cares or []
        
        # Check if we have an appropriate number of variables
        num_vars = len(variable_names)
        if not 2 <= num_vars <= 5:
            self._create_placeholder()
            self.results_text.setHtml(
                f"<p style='color: #888888; text-align: center;'>"
                f"Karnaugh maps support 2 to 5 variables. Found {num_vars} variables."
                f"</p>"
            )
            return
            
        try:
            # Create the K-map
            self.k_map = ls.KarnaughMap(variable_names, minterms, self.dont_cares)
            
            # Compute groupings
            self.groupings = self.k_map.compute_groupings()
            
            # Update the display
            self._build_kmap_grid()
            self.update_display()
            
            # Show simplified expressions
            self._update_results()
            
        except Exception as e:
            self._create_placeholder()
            self.results_text.setHtml(
                f"<p style='color: #FF0000; text-align: center;'>"
                f"Error creating Karnaugh map: {str(e)}"
                f"</p>"
            )
    
    def _build_kmap_grid(self):
        """Build the Karnaugh map grid UI."""
        # Clear existing cells
        self.cells = []
        
        # Clear existing widgets from the grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # K-map grid dimensions depend on the number of variables
        if len(self.variables) == 2:
            rows, cols = 2, 2
        elif len(self.variables) == 3:
            rows, cols = 2, 4
        elif len(self.variables) == 4:
            rows, cols = 4, 4
        else:  # 5 variables would be a special case
            rows, cols = 4, 8
            
        # Row and column headers
        row_headers = []
        col_headers = []
        
        if len(self.variables) == 2:
            # 2 variables: p on rows, q on columns
            row_var = self.variables[0]
            col_var = self.variables[1]
            row_headers = [f"{row_var}=0", f"{row_var}=1"]
            col_headers = [f"{col_var}=0", f"{col_var}=1"]
        elif len(self.variables) == 3:
            # 3 variables: p on rows, q,r on columns (following Gray code)
            row_var = self.variables[0]
            col_vars = [self.variables[1], self.variables[2]]
            
            row_headers = [f"{row_var}=0", f"{row_var}=1"]
            col_headers = [
                f"{col_vars[0]},{col_vars[1]}=00", 
                f"{col_vars[0]},{col_vars[1]}=01", 
                f"{col_vars[0]},{col_vars[1]}=11", 
                f"{col_vars[0]},{col_vars[1]}=10"
            ]
        elif len(self.variables) == 4:
            # 4 variables: p,q on rows, r,s on columns (following Gray code)
            row_vars = [self.variables[0], self.variables[1]]
            col_vars = [self.variables[2], self.variables[3]]
            
            row_headers = [
                f"{row_vars[0]},{row_vars[1]}=00", 
                f"{row_vars[0]},{row_vars[1]}=01", 
                f"{row_vars[0]},{row_vars[1]}=11", 
                f"{row_vars[0]},{row_vars[1]}=10"
            ]
            col_headers = [
                f"{col_vars[0]},{col_vars[1]}=00", 
                f"{col_vars[0]},{col_vars[1]}=01", 
                f"{col_vars[0]},{col_vars[1]}=11", 
                f"{col_vars[0]},{col_vars[1]}=10"
            ]
        else:  # 5 variables
            # 5 variables: p,q on rows, r,s,t on columns
            row_vars = [self.variables[0], self.variables[1]]
            col_vars = [self.variables[2], self.variables[3], self.variables[4]]
            
            row_headers = [
                f"{row_vars[0]},{row_vars[1]}=00", 
                f"{row_vars[0]},{row_vars[1]}=01", 
                f"{row_vars[0]},{row_vars[1]}=11", 
                f"{row_vars[0]},{row_vars[1]}=10"
            ]
            # Complex column headers for 5 variables - 8 columns
            # We won't fully implement this case now
            
        # Grid layout for K-map
        # Add row headers (vertical)
        for i, header in enumerate(row_headers):
            label = QLabel(header)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet("padding: 5px; font-weight: bold;")
            self.grid_layout.addWidget(label, i+1, 0)
            
        # Add column headers (horizontal)
        for j, header in enumerate(col_headers):
            label = QLabel(header)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("padding: 5px; font-weight: bold;")
            self.grid_layout.addWidget(label, 0, j+1)
            
        # Create empty K-map grid
        for i in range(rows):
            cell_row = []
            for j in range(cols):
                # Get the actual minterm index for this cell
                idx = self._coords_to_index(i, j)
                
                # Determine the cell value
                if idx in self.minterms:
                    value = 1
                elif idx in self.dont_cares:
                    value = 'X'
                else:
                    value = 0
                    
                # Create the cell widget
                cell = KarnaughCellWidget(value, i, j)
                cell.clicked.connect(self._cell_clicked)
                self.grid_layout.addWidget(cell, i+1, j+1)
                cell_row.append(cell)
                
            self.cells.append(cell_row)
            
        # Add empty corner
        corner = QLabel("")
        self.grid_layout.addWidget(corner, 0, 0)
        
        # Set stretch factors to make the grid expand properly
        for i in range(rows + 2):
            self.grid_layout.setRowStretch(i, 1)
        for j in range(cols + 2):
            self.grid_layout.setColumnStretch(j, 1)
        
    @staticmethod
    def gray_code_bits(n, bits):
        """Convert a number to Gray code with specified number of bits."""
        # Binary to Gray code conversion
        gray = n ^ (n >> 1)
        # Convert to binary representation with specified bits
        return [(gray >> i) & 1 for i in range(bits - 1, -1, -1)]
        
    def _cell_clicked(self, row, col):
        """Handle click on a K-map cell."""
        # Get the cell's minterm index
        idx = self._coords_to_index(row, col)
        
        # Find which groups (prime implicants) this cell belongs to
        groups = []
        for i, (cells, term) in enumerate(self.groupings):
            if (row, col) in cells:
                is_essential = any(pi in self.k_map.essential_prime_implicants for pi in [term])
                groups.append((i, term, is_essential))
                
        # Show information about the cell and its groups
        html = f"<h3>Cell ({row}, {col})</h3>"
        html += f"<p>Minterm index: {idx}</p>"
        
        # Fix the escaped apostrophe in the f-string
        value_text = "1" if idx in self.minterms else "0" if idx not in self.dont_cares else "X (Don't Care)"
        html += f"<p>Value: {value_text}</p>"
        
        if groups:
            html += "<h4>Prime Implicants:</h4><ul>"
            for group_id, term, is_essential in groups:
                html += f"<li>{term} {'(Essential)' if is_essential else ''}</li>"
            html += "</ul>"
        else:
            html += "<p>Not covered by any prime implicant.</p>"
            
        self.results_text.setHtml(html)
                
    def _coords_to_index(self, row, col):
        """Convert K-map grid coordinates to minterm index."""
        if len(self.variables) == 2:
            # For 2 variables: row is p, col is q
            return (row << 1) | col
        elif len(self.variables) == 3:
            # For 3 variables: row is p, cols are q,r in Gray code order
            # Convert col (0-3) to q,r bits using Gray code
            if col == 0:   # 00
                qr_bits = 0
            elif col == 1: # 01
                qr_bits = 1
            elif col == 2: # 11
                qr_bits = 3
            else:          # 10
                qr_bits = 2
                
            # Combine p with q,r
            return (row << 2) | qr_bits
        elif len(self.variables) == 4:
            # For 4 variables: rows are p,q in Gray code, cols are r,s in Gray code
            # Convert row (0-3) to p,q bits
            if row == 0:   # 00
                pq_bits = 0
            elif row == 1: # 01
                pq_bits = 1
            elif row == 2: # 11
                pq_bits = 3
            else:          # 10
                pq_bits = 2
                
            # Convert col (0-3) to r,s bits
            if col == 0:   # 00
                rs_bits = 0
            elif col == 1: # 01
                rs_bits = 1
            elif col == 2: # 11
                rs_bits = 3
            else:          # 10
                rs_bits = 2
                
            # Combine p,q with r,s
            return (pq_bits << 2) | rs_bits
        else:  # 5 variables
            is_top_half = (idx >> 4) & 1 == 0
            return (row << 3) | col | ((row // 2) << 4)
        
    def update_display(self):
        """Update the K-map display based on current options."""
        if not self.k_map or not self.cells:
            return
            
        # Clear all group assignments
        for row in self.cells:
            for cell in row:
                if cell:
                    cell.clear_groups()
        
        # Get options
        show_essential = self.show_essential_cb.isChecked()
        show_all = self.show_all_pi_cb.isChecked()
        
        # Create mapping of prime implicants to groups
        pi_to_groups = {}
        
        # Get the prime implicants and essential prime implicants
        prime_implicants = self.k_map.prime_implicants
        essential_prime_implicants = self.k_map.essential_prime_implicants
        
        # Debug output
        print(f"Displaying K-map - Prime implicants: {prime_implicants}")
        print(f"Essential prime implicants: {essential_prime_implicants}")
        
        # Assign cells to groups
        for i, (cell_coords, term) in enumerate(self.groupings):
            # Determine if this is an essential prime implicant
            is_essential = False
            
            # Extract the pattern parts from the term
            term_parts = term.split(' & ')
            pattern = []
            
            for var in self.variables:
                if var in term_parts:
                    pattern.append('1')
                elif f"~{var}" in term_parts:
                    pattern.append('0')
                else:
                    pattern.append('-')
            
            pattern_str = ''.join(pattern)
            
            # Check if this pattern corresponds to an essential prime implicant
            for pi in essential_prime_implicants:
                is_match = True
                for i, bit in enumerate(pi):
                    if bit != '-' and pattern[i] != '-' and bit != pattern[i]:
                        is_match = False
                        break
                if is_match:
                    is_essential = True
                    break
            
            # Skip if we're only showing essentials and this isn't essential
            if not show_all and not is_essential:
                continue
                
            # Skip if we're not showing essentials and this is essential
            if not show_essential and is_essential:
                continue
                
            # Add the group to each cell
            for r, c in cell_coords:
                if 0 <= r < len(self.cells) and 0 <= c < len(self.cells[0]):
                    cell = self.cells[r][c]
                    if cell:
                        cell.add_group(i, is_essential)
        
    def _update_results(self):
        """Update the results text with simplified expressions."""
        if not self.k_map:
            return
            
        # Get the simplified expression
        simplified = self.k_map.get_simplified_expression()
        
        # Format the expression for display
        # Replace Boolean operators with symbols for display
        display_expr = simplified
        display_expr = display_expr.replace(" & ", " ∧ ")
        display_expr = display_expr.replace(" | ", " ∨ ")
        display_expr = display_expr.replace("~", "¬")
        
        # Generate the HTML content
        html = "<h3>Simplified Boolean Expression:</h3>"
        html += f"<p style='font-size: 16px; margin: 10px 0;'>{display_expr}</p>"
        
        # Add information about prime implicants
        html += "<h3>Prime Implicants:</h3>"
        html += "<ul>"
        
        # Create a set of essential prime implicant strings for easy checking
        essential_pis = set(self.k_map.essential_prime_implicants)
        
        # List the prime implicants with their terms
        for pi in self.k_map.prime_implicants:
            # Generate term expression
            term_parts = []
            for i, bit in enumerate(pi):
                if bit == '0':
                    term_parts.append(f"¬{self.variables[i]}")
                elif bit == '1':
                    term_parts.append(f"{self.variables[i]}")
                    
            term = " ∧ ".join(term_parts) if term_parts else "1"
            
            # Check if this is an essential prime implicant
            is_essential = pi in essential_pis
            
            # Add to the list with appropriate styling
            if is_essential:
                html += f"<li><b style='color: #FF00FF;'>{term} (Essential)</b></li>"
            else:
                html += f"<li>{term}</li>"
                
        html += "</ul>"
        
        # Explain what prime implicants are
        html += """
        <h3>What are Prime Implicants?</h3>
        <p>A prime implicant is a product term (AND of literals) that implies the function and cannot be reduced further.</p>
        <p>Essential prime implicants are those that cover minterms not covered by any other prime implicant.</p>
        <p>The minimal expression is formed by ORing all essential prime implicants plus any needed non-essential ones.</p>
        """
        
        # Set the HTML content
        self.results_text.setHtml(html)


# Example usage
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    widget = KarnaughMapWidget()
    
    # Example data
    variables = ['A', 'B', 'C', 'D']
    minterms = [0, 2, 5, 7, 8, 10, 13, 15]
    dont_cares = [11]
    
    widget.update_from_truth_table(variables, minterms, dont_cares)
    
    widget.setWindowTitle("Karnaugh Map Demonstration")
    widget.resize(800, 600)
    widget.show()
    
    sys.exit(app.exec()) 