# DM-Studio: Truth Table & Karnaugh Map Educational Tool

A comprehensive educational tool for Boolean logic, truth tables, and Karnaugh maps, designed to help students understand digital logic concepts.

## Features

- **Interactive Truth Tables**: Generate truth tables for any Boolean expression
- **Variable Configuration**: Configure up to 8 variables with custom names
- **Multiple Expressions**: Add and evaluate multiple expressions simultaneously
- **Karnaugh Maps**: Visualize Boolean functions with Karnaugh maps
- **Prime Implicant Highlighting**: Identify and highlight prime implicants in Karnaugh maps
- **Educational Content**: Built-in tutorials on Boolean logic, truth tables, and logical equivalences
- **Customizable Display**: Choose between T/F or 1/0 notation, and standard/reversed row ordering
- **Export Options**: Export truth tables as CSV or copy to clipboard
- **Modern UI**: Sleek, customizable interface with dark mode support

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/jguida941/DM-Studio.git
   ```

2. Install the required dependencies:
   ```
   pip install -r dependencies.txt
   ```

3. Run the application:
   ```
   python Visual_Truth_Table.py
   ```

## Usage

1. **Set Variables**: Configure the number of variables and their names in the "Variables" panel
2. **Create Expressions**: Enter Boolean expressions in the "Expressions" panel
3. **Generate Truth Table**: Click "Generate" in the toolbar or let auto-generate create the table
4. **View Karnaugh Map**: Click the "Show Karnaugh Map" button to visualize the function
5. **Learn Concepts**: Explore the educational content in the "Learning Resources" panel

## Logical Operators

The application supports the following logical operators:

- `and` or `∧` - Logical AND
- `or` or `∨` - Logical OR
- `not` or `¬` - Logical NOT
- `→` - Implication
- `↔` - Equivalence (biconditional)
- `⊕` - Exclusive OR (XOR)

## Screenshots

(Screenshots will be added here)

## Requirements

- Python 3.8+
- PyQt6

## License

This project is licensed under the MIT License - see the LICENSE file for details. 