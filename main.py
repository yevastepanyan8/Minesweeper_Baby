"""
Main entry point for the Minesweeper Solver.

Demonstrates loading a board and running the solver step-by-step.
"""

import sys
from solver.board import Board
from solver.strategy import step, solve_step
from solver.utils import format_cells


def main():
    """Run the solver on a test board."""
    # Default test board
    if len(sys.argv) > 1:
        board_file = sys.argv[1]
    else:
        board_file = "tests/example_boards/small_5x5.txt"
    
    print("=" * 60)
    print("Minesweeper Solver - Person 1 Implementation")
    print("=" * 60)
    print(f"\nLoading board from: {board_file}\n")
    
    try:
        # Load board from file
        board = Board.load_from_file(board_file)
    except FileNotFoundError:
        print(f"Error: Board file '{board_file}' not found.")
        print("Creating a simple test board instead...\n")
        # Create a simple test board
        board = Board(5, 5, {(0, 0), (1, 2), (4, 4)})
        # Reveal a starting cell
        board.reveal(2, 2)
    
    # Initial state
    print("Initial Board State:")
    board.print_solver_view()
    
    # Solver loop
    max_iterations = 100
    iteration = 0
    
    print("Starting solver...\n")
    
    while not board.is_finished() and iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        
        # Get solver decision
        action, cells = step(board)
        
        if action == "none" or not cells:
            print("No moves available. Solver stuck.")
            break
        
        # Display decision
        print(f"Action: {action}")
        print(f"Cells: {format_cells(cells)}")
        
        # Apply action
        success = solve_step(board, action, cells)
        
        if not success:
            print("Warning: Action failed to apply.")
            break
        
        # Show updated board
        board.print_solver_view()
        
        # Check if finished
        if board.is_finished():
            print("\n✓ Game finished! All safe cells revealed.")
            break
    
    if iteration >= max_iterations:
        print(f"\nReached maximum iterations ({max_iterations}).")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("Final Statistics:")
    print("=" * 60)
    unknown = board.unknown_cells()
    flagged = sum(1 for i in range(board.rows) for j in range(board.cols) 
                  if board.is_flagged(i, j))
    revealed = board.revealed_cells()
    
    print(f"Revealed cells: {len(revealed)}")
    print(f"Flagged cells: {flagged}")
    print(f"Unknown cells: {len(unknown)}")
    print(f"Iterations: {iteration}")
    print()


if __name__ == "__main__":
    main()

