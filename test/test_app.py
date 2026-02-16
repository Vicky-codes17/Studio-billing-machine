#!/usr/bin/env python3
import sys
import os

def test_imports():
    """Test all imports"""
    print("🧪 Testing imports...")
    
    try:
        from flask import Flask
        print("✅ Flask imported")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        from models import db, Invoice, Item
        print("✅ Models imported")
    except ImportError as e:
        print(f"❌ Models import failed: {e}")
        return False
    
    try:
        from services.billing_service import save_invoice, get_invoice_stats
        print("✅ Services imported")
    except ImportError as e:
        print(f"❌ Services import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database creation"""
    print("\n🗄️ Testing database...")
    
    try:
        from app import app, db
        
        with app.app_context():
            db.create_all()
            print("✅ Database created successfully")
            return True
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False

def test_templates():
    """Test template files exist"""
    print("\n📄 Testing templates...")
    
    required_templates = [
        'templates/index.html',
        'templates/invoices_list.html',
        'templates/thermal_preview.html'
    ]
    
    missing = []
    for template in required_templates:
        if os.path.exists(template):
            print(f"✅ {template} exists")
        else:
            missing.append(template)
            print(f"❌ {template} missing")
    
    return len(missing) == 0

def main():
    print("🚀 Anand Digital Studio - App Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n💡 Fix import errors first")
        return False
    
    # Test database
    if not test_database():
        print("\n💡 Fix database errors first") 
        return False
    
    # Test templates
    if not test_templates():
        print("\n💡 Create missing templates first")
        return False
    
    print("\n✅ All tests passed! Starting app...")
    
    try:
        from app import app
        print("🌐 Starting server at http://127.0.0.1:5000")
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"❌ App startup failed: {e}")
        return False

if __name__ == "__main__":
    main()