import os
import sys

def check_setup():
    """Check if all required files and directories exist"""
    
    # Get the parent directory (go up from test/ to project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}")
    
    required_files = [
        'app.py',
        'models.py',
        'config.py',
        'services/__init__.py',
        'services/billing_service.py',
        'services/pdf_service.py',
        'services/printer_service.py',
        'templates/index.html',
        'templates/bill.html',
        'static/logo.png'  # Add logo.png to required files
    ]
    
    required_dirs = [
        'templates',
        'services',
        'static',
        'instance'
    ]
    
    print("🔍 Checking setup...")
    
    # Check directories
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Directory: {directory}")
        else:
            print(f"❌ Missing directory: {directory}")
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
    
    # Check files
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ File: {file_path}")
        else:
            print(f"❌ Missing file: {file_path}")
            missing_files.append(file_path)
    
    # Create __init__.py files
    init_files = ['services/__init__.py']
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# Service module\n')
            print(f"✅ Created: {init_file}")
    
    # Check for logo.png specifically
    if 'static/logo.png' in missing_files:
        print("\n⚠️  IMPORTANT: Place your logo.png file in the static/ directory")
        print("   📸 The logo will be displayed in the invoice header")
        print("   📸 If logo.png is missing, a camera emoji will be shown as fallback")
        
        # Create a placeholder text file with instructions
        logo_instructions = """
LOGO INSTRUCTIONS:
==================

1. Place your company logo file as 'logo.png' in this directory
2. Recommended size: 200x200 pixels or square format
3. Supported formats: PNG (recommended), JPG, JPEG
4. The logo will be displayed as a circular image in the invoice header

If no logo.png is found, a camera emoji (📸) will be shown as fallback.
"""
        with open('static/LOGO_INSTRUCTIONS.txt', 'w') as f:
            f.write(logo_instructions)
        print(f"✅ Created: static/LOGO_INSTRUCTIONS.txt")
    
    print("\n🎯 Setup check complete!")
    
    if missing_files:
        print(f"\n⚠️  Missing {len(missing_files)} files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nCreate these files before running the app.")
    else:
        print("\n🚀 All files present! Ready to run: python app.py")

if __name__ == "__main__":
    check_setup()