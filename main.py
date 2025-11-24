from console_cli import main_menu
from db import init_schema

if __name__ == "__main__":
    init_schema()
    main_menu()