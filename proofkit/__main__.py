"""Allow running ProofKit as: python -m proofkit"""
import warnings

# Suppress the RuntimeWarning about module import order
warnings.filterwarnings("ignore", message=".*found in sys.modules.*")

from proofkit.cli.main import main

if __name__ == "__main__":
    main()
