"""Allow running CLI as: python -m proofkit.cli"""
import warnings

# Suppress the RuntimeWarning about module import order
warnings.filterwarnings("ignore", message=".*found in sys.modules.*")

from .main import main

if __name__ == "__main__":
    main()
