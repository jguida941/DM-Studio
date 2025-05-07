"""
Boolean algebra simplification and Karnaugh map implementation.

This module provides tools for:
1. Simplifying Boolean expressions using the Quine-McCluskey algorithm
2. Generating Karnaugh maps from truth tables
3. Finding prime implicants and essential prime implicants
"""

import itertools
from typing import List, Dict, Set, Tuple, Optional


class Term:
    """Represents a minterm or product term in a Boolean expression."""
    
    def __init__(self, indices: List[int], variables: List[str], is_dont_care: bool = False):
        """
        Initialize a term with its indices and variable names.
        
        Args:
            indices: List of indices where this term evaluates to 1
            variables: List of variable names in the expression
            is_dont_care: Whether this term is a don't care term
        """
        self.indices = sorted(indices)
        self.variables = variables
        self.is_dont_care = is_dont_care
        self._binary_reps = self._compute_binary_representations()
        
    def _compute_binary_representations(self) -> List[str]:
        """Calculate binary representations for each index."""
        n_vars = len(self.variables)
        return [format(idx, f'0{n_vars}b') for idx in self.indices]
    
    def to_expression(self) -> str:
        """Convert the term to a Boolean expression string."""
        if not self.indices:
            return "0"  # Empty term is False
        if len(self.indices) == 2**len(self.variables):
            return "1"  # Term covering all possibilities is True
            
        # Get the first binary representation as a reference
        reference = self._binary_reps[0]
        
        # Find positions that are the same across all binary representations
        term_parts = []
        for i, bit in enumerate(reference):
            var_name = self.variables[i]
            all_same = all(rep[i] == bit for rep in self._binary_reps)
            
            if all_same:
                if bit == '0':
                    term_parts.append(f"~{var_name}")
                else:
                    term_parts.append(var_name)
        
        return " & ".join(term_parts) if term_parts else "1"
    
    def __str__(self) -> str:
        return f"Term({self.indices}, {self.to_expression()})"


class QuineMcCluskey:
    """Implementation of the Quine-McCluskey algorithm for Boolean minimization."""
    
    def __init__(self, variables: List[str], minterms: List[int], dont_cares: List[int] = None):
        """
        Initialize the Quine-McCluskey algorithm.
        
        Args:
            variables: List of variable names
            minterms: List of indices where the function is 1
            dont_cares: List of indices where the function value doesn't matter
        """
        self.variables = variables
        self.minterms = sorted(minterms)
        self.dont_cares = sorted(dont_cares) if dont_cares else []
        self.num_vars = len(variables)
        
        # All terms that should be considered for minimization
        self.all_terms = sorted(self.minterms + self.dont_cares)
        
        # Will store prime implicants
        self.prime_implicants = []
        
    def _bin_rep(self, num: int) -> str:
        """Get binary representation of a number with proper padding."""
        return format(num, f'0{self.num_vars}b')
    
    def _can_combine(self, term1: str, term2: str) -> Optional[str]:
        """
        Check if two terms can be combined, differing in exactly one position.
        Returns the combined term with a dash (-) in the differing position, or None.
        """
        diff_count = 0
        result = list(term1)
        
        for i in range(len(term1)):
            if term1[i] != term2[i]:
                diff_count += 1
                result[i] = '-'
                
        return ''.join(result) if diff_count == 1 else None
        
    def find_prime_implicants(self) -> List[str]:
        """Find all prime implicants for the Boolean function."""
        # Initialize the first group with binary representations
        groups = [[self._bin_rep(t) for t in self.all_terms]]
        
        prime_implicants = []
        combined = True
        
        # Keep combining terms until no more combinations are possible
        while combined:
            combined = False
            next_group = []
            combined_terms = set()
            
            for terms in groups:
                for i, term1 in enumerate(terms):
                    for term2 in terms[i+1:]:
                        combined_term = self._can_combine(term1, term2)
                        if combined_term:
                            next_group.append(combined_term)
                            combined_terms.add(term1)
                            combined_terms.add(term2)
                            combined = True
                            
            # Terms that couldn't be combined are prime implicants
            for terms in groups:
                for term in terms:
                    if term not in combined_terms:
                        prime_implicants.append(term)
                        
            groups = [list(set(next_group))]
            
        self.prime_implicants = prime_implicants
        return prime_implicants
    
    def _get_term_coverage(self, term: str) -> List[int]:
        """Get all minterms covered by a prime implicant term."""
        dash_positions = [i for i, bit in enumerate(term) if bit == '-']
        fixed_part = ''.join(bit for bit in term if bit != '-')
        
        coverage = []
        # For each combination of values in dash positions
        for bits in itertools.product('01', repeat=len(dash_positions)):
            # Reconstruct the binary string
            binary = list(term)
            for i, bit in zip(dash_positions, bits):
                binary[i] = bit
            binary_str = ''.join(binary)
            
            # Convert to decimal and check if it's a minterm
            decimal = int(binary_str, 2)
            if decimal in self.all_terms:
                coverage.append(decimal)
                
        return coverage
    
    def find_essential_prime_implicants(self) -> List[str]:
        """Find the essential prime implicants."""
        if not self.prime_implicants:
            self.find_prime_implicants()
            
        # Create a map from minterms to covering prime implicants
        coverage = {m: [] for m in self.minterms}
        
        for pi in self.prime_implicants:
            for minterm in self._get_term_coverage(pi):
                if minterm in self.minterms:  # Ignore don't cares
                    coverage[minterm].append(pi)
        
        # Find essential prime implicants (those that uniquely cover a minterm)
        essential = []
        for minterm, pis in coverage.items():
            if len(pis) == 1:
                essential.append(pis[0])
                
        return list(set(essential))
    
    def minimize(self) -> str:
        """
        Minimize the Boolean function and return the simplified expression.
        Returns an expression in sum-of-products form.
        """
        essential_pis = self.find_essential_prime_implicants()
        
        # If essential PIs cover all minterms, we're done
        covered_minterms = set()
        for pi in essential_pis:
            covered_minterms.update(self._get_term_coverage(pi))
        
        uncovered = set(self.minterms) - covered_minterms
        selected_pis = set(essential_pis)
        
        # If there are uncovered minterms, select additional prime implicants greedily
        if uncovered:
            # Create a map of prime implicants to the minterms they cover
            pi_coverage = {}
            for pi in self.prime_implicants:
                if pi not in selected_pis:
                    coverage = [m for m in self._get_term_coverage(pi) if m in uncovered]
                    if coverage:
                        pi_coverage[pi] = coverage
            
            # Greedily select prime implicants that cover the most uncovered minterms
            while uncovered and pi_coverage:
                # Find the prime implicant that covers the most uncovered minterms
                best_pi = max(pi_coverage.items(), key=lambda x: len(x[1]))[0]
                selected_pis.add(best_pi)
                
                # Update the uncovered minterms
                for m in pi_coverage[best_pi]:
                    uncovered.discard(m)
                    
                # Remove the selected prime implicant
                del pi_coverage[best_pi]
                
                # Update coverage for remaining prime implicants
                for pi in list(pi_coverage.keys()):
                    pi_coverage[pi] = [m for m in pi_coverage[pi] if m in uncovered]
                    if not pi_coverage[pi]:
                        del pi_coverage[pi]
                
        # Convert the selected prime implicants to a Boolean expression
        terms = []
        for pi in selected_pis:
            term_parts = []
            for i, bit in enumerate(pi):
                if bit == '0':
                    term_parts.append(f"~{self.variables[i]}")
                elif bit == '1':
                    term_parts.append(self.variables[i])
            
            if term_parts:
                terms.append(" & ".join(term_parts))
            else:
                terms.append("1")  # This happens if all bits are dashes
                
        if not terms:
            return "0"  # No prime implicants means the function is always 0
            
        # Simplify further if possible
        if len(terms) == 1:
            return terms[0]  # Single term, no need for OR
            
        # Check if simplification to single variable is possible
        # For example, ~p | ~q == ~(p & q), but we want to return ~r if that's the only output
        # Special case: If all minterms are consecutive powers of 2
        # and form a complete subset, it's a single variable
        if len(self.minterms) == 1:
            if self.minterms[0] == 0:
                # All variables are 0, expression is ~var1 & ~var2 & ... & ~varn
                return " & ".join([f"~{var}" for var in self.variables])
                
        # Handle special case for don't care optimization where we have ~r
        if self.dont_cares and len(terms) == 1:
            # We found a single term solution with don't cares
            return terms[0]
            
        # Join terms with OR
        return " | ".join(terms)


class KarnaughMap:
    """Class for generating and manipulating Karnaugh maps."""
    
    def __init__(self, variables: List[str], minterms: List[int], dont_cares: List[int] = None):
        """
        Initialize a Karnaugh map.
        
        Args:
            variables: List of variable names (2 to 5 variables supported)
            minterms: List of indices where the function is 1
            dont_cares: List of indices where the function value doesn't matter
        """
        self.variables = variables
        self.minterms = sorted(minterms)
        self.dont_cares = sorted(dont_cares) if dont_cares else []
        self.num_vars = len(variables)
        
        if not 2 <= self.num_vars <= 5:
            raise ValueError("Karnaugh maps support 2 to 5 variables")
            
        # Create the K-map grid
        self.grid = self._create_grid()
        
        # Compute optimal groupings using Quine-McCluskey
        self.qm = QuineMcCluskey(variables, minterms, dont_cares)
        self.prime_implicants = []
        self.essential_prime_implicants = []
        
    def _create_grid(self) -> List[List[int]]:
        """Create the Karnaugh map grid with appropriate Gray code ordering."""
        # Determine grid dimensions based on number of variables
        if self.num_vars == 2:
            rows, cols = 2, 2
        elif self.num_vars == 3:
            rows, cols = 2, 4
        elif self.num_vars == 4:
            rows, cols = 4, 4
        else:  # 5 variables
            rows, cols = 4, 8
            
        # Create Gray code sequences
        gray_rows = gray_code(rows)
        gray_cols = gray_code(cols)
        
        # Initialize grid with 0s (False)
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        
        # Fill in the 1s (True) and 'X's (don't cares)
        for r in range(rows):
            for c in range(cols):
                # Compute the minterm index from row and column
                if self.num_vars == 2:
                    idx = (gray_rows[r] << 1) | gray_cols[c]
                elif self.num_vars == 3:
                    idx = (gray_rows[r] << 2) | gray_cols[c]
                elif self.num_vars == 4:
                    idx = (gray_rows[r] << 2) | gray_cols[c]
                else:  # 5 variables
                    idx = (gray_rows[r] << 3) | gray_cols[c] | ((r // 2) << 4)
                
                if idx in self.minterms:
                    grid[r][c] = 1
                elif idx in self.dont_cares:
                    grid[r][c] = 'X'
        
        return grid
    
    def compute_groupings(self) -> List[Tuple[List[Tuple[int, int]], str, str]]:
        """
        Compute the prime implicant groupings on the Karnaugh map.
        
        Returns:
            List of tuples, each containing:
            - List of cell coordinates (row, col) in the group
            - The simplified term that this group represents
            - The prime implicant pattern string (e.g., '1-1')
        """
        # Use the Quine-McCluskey algorithm to find prime implicants
        self.prime_implicants = self.qm.find_prime_implicants()
        self.essential_prime_implicants = self.qm.find_essential_prime_implicants()
        
        # Debug the results
        print(f"Prime implicants: {self.prime_implicants}")
        print(f"Essential prime implicants: {self.essential_prime_implicants}")
        
        groupings = []
        for pi in self.prime_implicants:
            cells = []
            covered_indices = self.qm._get_term_coverage(pi)
            print(f"Prime implicant {pi} covers indices: {covered_indices}")
            
            for idx in covered_indices:
                # Convert index to grid coordinates
                row, col = self._index_to_coords(idx)
                cells.append((row, col))
            
            # Generate the term expression
            term_parts = []
            for i, bit in enumerate(pi):
                if bit == '0':
                    term_parts.append(f"~{self.variables[i]}")
                elif bit == '1':
                    term_parts.append(self.variables[i])
            
            term = " & ".join(term_parts) if term_parts else "1"
            groupings.append((cells, term, pi))
            
        return groupings
    
    def _index_to_coords(self, idx: int) -> Tuple[int, int]:
        """Convert a minterm index to Karnaugh map coordinates (row, col)."""
        # Implementation depends on the grid layout
        if self.num_vars == 2:
            return idx >> 1, idx & 1
        elif self.num_vars == 3:
            return idx >> 2, idx & 3
        elif self.num_vars == 4:
            return idx >> 2, idx & 3
        else:  # 5 variables
            is_top_half = (idx >> 4) & 1 == 0
            return (idx >> 3) % 4, idx & 7
        
    def get_simplified_expression(self) -> str:
        """Get the simplified Boolean expression from the map."""
        return self.qm.minimize()


def gray_code(n: int) -> List[int]:
    """Generate a Gray code sequence of given length."""
    if n <= 0:
        return []
        
    if n == 1:
        return [0]
        
    # Generate Gray code recursively
    prev = gray_code(n // 2)
    reflected = prev[::-1]
    
    # Add 0 and 1 prefixes
    return prev + [p | (n//2) for p in reflected]
    

def generate_karnaugh_map_html(k_map: KarnaughMap) -> str:
    """
    Generate an HTML representation of a Karnaugh map with prime implicant groupings.
    
    Args:
        k_map: A KarnaughMap instance
        
    Returns:
        HTML string for displaying the Karnaugh map with highlighted groupings
    """
    # Get the grid and compute groupings
    grid = k_map.grid
    groupings = k_map.compute_groupings()
    essential_pis = set(k_map.essential_prime_implicants)
    
    rows = len(grid)
    cols = len(grid[0])
    
    html = ['<div class="karnaugh-map">']
    
    # Generate row and column headers
    col_headers = []
    row_headers = []
    
    if k_map.num_vars == 2:
        col_var, row_var = k_map.variables[1], k_map.variables[0]
        col_headers = [f"{col_var}=0", f"{col_var}=1"]
        row_headers = [f"{row_var}=0", f"{row_var}=1"]
    elif k_map.num_vars == 3:
        row_var = k_map.variables[0]
        col_vars = [k_map.variables[1], k_map.variables[2]]
        
        col_headers = [
            f"{col_vars[0]},{col_vars[1]}=00", 
            f"{col_vars[0]},{col_vars[1]}=01", 
            f"{col_vars[0]},{col_vars[1]}=11", 
            f"{col_vars[0]},{col_vars[1]}=10"
        ]
        row_headers = [f"{row_var}=0", f"{row_var}=1"]
    elif k_map.num_vars == 4:
        # 4 variables: p,q on rows, r,s on cols
        row_vars = [k_map.variables[0], k_map.variables[1]]
        col_vars = [k_map.variables[2], k_map.variables[3]]
        
        col_headers = [
            f"{col_vars[0]},{col_vars[1]}=00", 
            f"{col_vars[0]},{col_vars[1]}=01", 
            f"{col_vars[0]},{col_vars[1]}=11", 
            f"{col_vars[0]},{col_vars[1]}=10"
        ]
        row_headers = [
            f"{row_vars[0]},{row_vars[1]}=00", 
            f"{row_vars[0]},{row_vars[1]}=01", 
            f"{row_vars[0]},{row_vars[1]}=11", 
            f"{row_vars[0]},{row_vars[1]}=10"
        ]
    else:  # 5 variables
        # 5 variables: p,q on rows, r,s,t on cols
        row_vars = [k_map.variables[0], k_map.variables[1]]
        col_vars = [k_map.variables[2], k_map.variables[3], k_map.variables[4]]
        
        col_headers = [
            f"{col_vars[0]},{col_vars[1]},{col_vars[2]}=000", 
            f"{col_vars[0]},{col_vars[1]},{col_vars[2]}=001", 
            f"{col_vars[0]},{col_vars[1]},{col_vars[2]}=011", 
            f"{col_vars[0]},{col_vars[1]},{col_vars[2]}=010",
            f"{col_vars[0]},{col_vars[1]},{col_vars[2]}=110", 
            f"{col_vars[0]},{col_vars[1]},{col_vars[2]}=111", 
            f"{col_vars[0]},{col_vars[1]},{col_vars[2]}=101", 
            f"{col_vars[0]},{col_vars[1]},{col_vars[2]}=100"
        ]
        row_headers = [
            f"{row_vars[0]},{row_vars[1]}=00", 
            f"{row_vars[0]},{row_vars[1]}=01", 
            f"{row_vars[0]},{row_vars[1]}=11", 
            f"{row_vars[0]},{row_vars[1]}=10"
        ]
    
    # Generate HTML table
    html.append('<table class="k-map">')
    
    # Header row
    html.append('<tr><th></th>')
    for header in col_headers:
        html.append(f'<th>{header}</th>')
    html.append('</tr>')
    
    # Data rows
    for r in range(rows):
        html.append(f'<tr><th>{row_headers[r]}</th>')
        for c in range(cols):
            cell_value = grid[r][c]
            if cell_value == 'X':
                cell_class = 'dont-care'
                cell_text = 'X'
            else:
                cell_class = 'minterm' if cell_value == 1 else 'maxterm'
                cell_text = str(cell_value)
                
            # Calculate cell's group data to allow CSS highlighting
            group_data = []
            for i, (cells, term, pi_pattern) in enumerate(groupings):
                if (r, c) in cells:
                    is_essential = any(pi in essential_pis for pi in term)
                    group_type = 'essential' if is_essential else 'prime'
                    group_data.append(f'data-group-{i}="{group_type}"')
            
            group_attr = ' '.join(group_data)
            html.append(f'<td class="{cell_class}" {group_attr}>{cell_text}</td>')
        html.append('</tr>')
    
    html.append('</table>')
    
    # Generate legend
    html.append('<div class="legend">')
    html.append('<h4>Prime Implicants:</h4>')
    html.append('<ul>')
    for i, (_, term, pi_pattern) in enumerate(groupings):
        is_essential = any(pi in essential_pis for pi in term)
        legend_class = 'essential-pi' if is_essential else 'prime-implicant'
        html.append(f'<li class="{legend_class}" data-group-id="{i}">{term} {"(Essential)" if is_essential else ""}</li>')
    html.append('</ul>')
    
    # Add the simplified expression
    html.append('<div class="simplified">')
    html.append('<h4>Simplified Expression:</h4>')
    html.append(f'<p>{k_map.get_simplified_expression()}</p>')
    html.append('</div>')
    
    html.append('</div>')
    html.append('</div>')
    
    return '\n'.join(html)


# Example usage:
if __name__ == "__main__":
    # Example: f(A,B,C,D) = Σm(0,2,5,7,8,10,13,15)
    variables = ['A', 'B', 'C', 'D']
    minterms = [0, 2, 5, 7, 8, 10, 13, 15]
    dont_cares = []
    
    k_map = KarnaughMap(variables, minterms, dont_cares)
    html = generate_karnaugh_map_html(k_map)
    
    with open('karnaugh_map.html', 'w') as f:
        f.write(html)
    
    qm = QuineMcCluskey(variables, minterms, dont_cares)
    print(f"Prime implicants: {qm.find_prime_implicants()}")
    print(f"Essential prime implicants: {qm.find_essential_prime_implicants()}")
    print(f"Simplified expression: {qm.minimize()}") 