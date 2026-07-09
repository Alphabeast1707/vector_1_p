#!/usr/bin/env python3
import os
import sys
import subprocess
import time

def print_banner(text):
    print("=" * 70)
    print(f" {text}")
    print("=" * 70)

def main():
    print_banner("VECTOR_1_P BUILD & CODEBASE VERIFIER")
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, 'backend')
    venv_python = os.path.join(backend_dir, 'venv', 'bin', 'python')
    venv_pytest = os.path.join(backend_dir, 'venv', 'bin', 'pytest')
    
    # 1. Check virtual environment symlink
    print("\n[Step 1/4] Checking virtual environment symlink...")
    if not os.path.exists(venv_python):
        print("❌ Error: Virtual environment python not found at " + venv_python)
        print("Please ensure the symlink is set up correctly.")
        sys.exit(1)
    
    # Get Python version
    py_version = subprocess.check_output([venv_python, '--version']).decode().strip()
    print(f"  ✓ Found active virtualenv environment: {venv_python}")
    print(f"  ✓ Virtualenv Python: {py_version}")
    
    # 2. Check dependencies
    print("\n[Step 2/4] Verifying critical scientific imports...")
    imports = ['torch', 'botorch', 'gpytorch', 'sklearn', 'pandas', 'numpy', 'scipy', 'fastapi']
    all_ok = True
    for imp in imports:
        try:
            subprocess.check_call([venv_python, '-c', f"import {imp}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  ✓ Import '{imp}' is available")
        except subprocess.CalledProcessError:
            print(f"  ❌ Error: Import '{imp}' failed!")
            all_ok = False
            
    if not all_ok:
        print("❌ Verification failed due to missing dependencies.")
        sys.exit(1)
        
    # 3. Execute Pytest suite
    print("\n[Step 3/4] Running pytest validation suite...")
    start_time = time.time()
    
    test_files = [
        'tests/test_v1_bo.py',
        'tests/test_v1_bo_botorch.py',
        'tests/test_v1_phase1_integration.py',
        'tests/test_v1_router.py',
        'tests/test_v2_scaleup.py'
    ]
    
    results = {}
    for tf in test_files:
        test_path = os.path.join(backend_dir, tf)
        print(f"  Running {tf:40s} ... ", end="", flush=True)
        t_start = time.time()
        
        # Set a 120 second timeout for the slower Bayesian optimization checks
        try:
            cmd = [venv_pytest, tf]
            env = os.environ.copy()
            env['PYTHONPATH'] = '.'
            proc = subprocess.run(
                cmd, 
                cwd=backend_dir, 
                env=env,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                timeout=120
            )
            elapsed = time.time() - t_start
            if proc.returncode == 0:
                print(f"PASS ({elapsed:.2f}s)")
                results[tf] = ("PASS", elapsed)
            else:
                print(f"FAIL ({elapsed:.2f}s)")
                results[tf] = ("FAIL", elapsed)
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
            results[tf] = ("TIMEOUT", 120.0)
            
    # 4. Print Summary Report
    print_banner("SUMMARY VERIFICATION REPORT")
    print(f"Total verification time: {time.time() - start_time:.2f}s\n")
    
    print(f"{'Test File':45s} | {'Status':8s} | {'Duration':8s}")
    print("-" * 70)
    
    all_passed = True
    for tf, (status, dur) in results.items():
        stat_str = f"[\033[92m{status}\033[0m]" if status == "PASS" else f"[\033[91m{status}\033[0m]"
        print(f"{tf:45s} | {stat_str:17s} | {dur:.2f}s")
        if status != "PASS":
            all_passed = False
            
    print("-" * 70)
    if all_passed:
        print("\033[92m✓ VERIFICATION STATUS: SUCCESSFUL & FULLY COMPLIANT!\033[0m")
        sys.exit(0)
    else:
        print("\033[91m❌ VERIFICATION STATUS: FAILED!\033[0m")
        sys.exit(1)

if __name__ == '__main__':
    main()
