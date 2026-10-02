"""
Smart Classroom Attention Analyzer
Main entry point for the application.
Supports both Cloud-Ready Web Dashboard and Desktop GUI modes.
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Smart Classroom Attention Analyzer")
    parser.add_argument(
        "--mode",
        choices=["web", "desktop", "global"],
        default="web",
        help="Run mode: 'web' (Local Web Dashboard, default), 'global' (Public Tunnel for remote students on any network), or 'desktop' (CustomTkinter GUI)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the web dashboard (default: 8000)"
    )

    args, unknown = parser.parse_known_args()

    # Allow shortcuts: --gui, --desktop, --global, --tunnel
    if "--gui" in sys.argv or "--desktop" in sys.argv:
        args.mode = "desktop"
    elif "--global" in sys.argv or "--tunnel" in sys.argv:
        args.mode = "global"

    if args.mode == "global":
        print("Starting Smart Classroom Attention Analyzer (Global Public Any-Network Mode)...")
        from run_global import run_global
        run_global()
    elif args.mode == "desktop":
        print("Starting Smart Classroom Attention Analyzer (Desktop GUI Mode)...")
        try:
            from dashboard import run_dashboard
            run_dashboard()
        except ImportError as e:
            print(f"Error starting desktop GUI: {e}")
            print("Switching to Web Dashboard mode instead...")
            from web_app import main as run_web
            run_web()
    else:
        print("Starting Smart Classroom Attention Analyzer (Local Web Dashboard)...")
        from web_app import main as run_web
        run_web()

if __name__ == "__main__":
    main()
