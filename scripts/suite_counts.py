"""Thin CLI so the standing probe and a human can run the same check."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from claimgate.suitecounts import main
raise SystemExit(main())
