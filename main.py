"""Main module for running the Retail AI Shopping Assistant with conversational interface."""

import argparse
import logging
import sys
import os
import traceback
from typing import Tuple, List, Dict, Any, Optional

from colorama import init as colorama_init, Fore, Style

# Import agent normally, not as relative import
from agent import RetailAgent
import config


def setup_logging(level: int, log_file: str) -> None:
    """Set up logging configuration.
    
    Args:
        level: Logging level
        log_file: Path to log file
    """
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )


def display_welcome_message() -> None:
    """Display welcome message."""
    print("\n" + "=" * 80)
    print("Welcome to Retail AI Shopping Assistant!".center(80))
    print("=" * 80)
    print("This intelligent shopping assistant will help you find products, provide recommendations,")
    print("and guide you through your shopping experience.")
    print("Just chat naturally as you would with a real sales assistant.")
    print("Type 'exit' to quit.")
    print("=" * 80 + "\n")
def parse_input(user_input: str) -> Tuple[str, List[str]]:
    """Parse user input into command and arguments.
    
    Args:
        user_input: User input string
        
    Returns:
        Tuple of (command, arguments)
    """
    parts = user_input.strip().split()
    if not parts:
        return "help", []
    
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    return cmd, args


def main() -> None:
    """Main function."""
    # Initialize colorama for colored output
    colorama_init(autoreset=True)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Retail AI Shopping Assistant",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        default="retail_agent.log",
        help="Path to log file"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level, args.log_file)
    
    # Create and initialize agent
    agent = RetailAgent()
    
    # Configure logger based on debug mode
    if args.debug:
        agent.logger.setLevel(logging.DEBUG)
    
    try:
        # Display welcome message
        display_welcome_message()
        
        # Main loop for user interaction
        while True:
            try:
                # Get user input
                user_input = input(f"{Fore.GREEN}> {Style.RESET_ALL}")
                
                # Skip empty input
                if not user_input.strip():
                    continue
                
                # Check if the user wants to exit
                if user_input.lower() in ("exit", "quit", "q"):
                    print(f"{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
                    break
                
                # Handle login command explicitly for authentication
                if user_input.lower().startswith("login "):
                    parts = user_input.split(maxsplit=2)
                    if len(parts) >= 3:
                        username, password = parts[1], parts[2]
                        if args.debug:
                            print(f"DEBUG: Processing command: '{user_input}', cmd: 'login', parts: {[parts[0], username, password]}")
                        success, message = agent.login(username, password)
                        print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")
                        continue
                
                # Process as natural language
                if args.debug:
                    cmd, *parts = parse_input(user_input)
                    print(f"DEBUG: Processing command: '{user_input}', cmd: '{cmd}', parts: {parts}")
                
                # Process using conversational interface
                response = agent.process_chat_message(user_input)
                print(f"{Fore.CYAN}{response}{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Interrupted by user.{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}I'm sorry, I encountered an error. Please try again or use simpler language.{Style.RESET_ALL}")
                if args.debug:
                    traceback.print_exc()
    except Exception as e:
        print(f"{Fore.RED}Critical error: {str(e)}{Style.RESET_ALL}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Shutdown agent
        try:
            agent.shutdown()
        except Exception as e:
            print(f"{Fore.RED}Error during shutdown: {str(e)}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
