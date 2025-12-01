#!/usr/bin/env python3
"""
Secret Key Generator for Flask Applications
Includes JWT secret key generation
"""

import secrets
import sys
import argparse

def generate_secret_key(length=32):
    """
    Generate a secure random secret key
    
    Args:
        length (int): Length of the key in bytes (default: 32)
    
    Returns:
        str: Hexadecimal secret key
    """
    if length < 16:
        print("⚠️  Warning: Secret key should be at least 16 bytes for security")
    
    return secrets.token_hex(length)

def generate_jwt_key(length=32):
    """
    Generate a secure random JWT secret key
    
    Args:
        length (int): Length of the key in bytes (default: 32)
    
    Returns:
        str: Hexadecimal JWT secret key
    """
    if length < 32:
        print("⚠️  Warning: JWT secret key should be at least 32 bytes for security")
    
    return secrets.token_hex(length)

def update_env_file(secret_key, jwt_key, env_file='.env'):
    """
    Update or create .env file with the secret keys
    
    Args:
        secret_key (str): The generated Flask secret key
        jwt_key (str): The generated JWT secret key
        env_file (str): Path to the .env file
    """
    try:
        # Read existing .env file if it exists
        lines = []
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"📁 Creating new {env_file} file")
        
        # Update or add SECRET_KEY and JWT_SECRET_KEY
        secret_key_line = f"SECRET_KEY={secret_key}\n"
        jwt_key_line = f"JWT_SECRET_KEY={jwt_key}\n"
        
        secret_key_found = False
        jwt_key_found = False
        updated_lines = []
        
        for line in lines:
            if line.startswith('SECRET_KEY='):
                updated_lines.append(secret_key_line)
                secret_key_found = True
            elif line.startswith('JWT_SECRET_KEY='):
                updated_lines.append(jwt_key_line)
                jwt_key_found = True
            else:
                updated_lines.append(line)
        
        if not secret_key_found:
            updated_lines.append(secret_key_line)
        if not jwt_key_found:
            updated_lines.append(jwt_key_line)
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Secret keys successfully written to {env_file}")
        
    except Exception as e:
        print(f"❌ Error updating {env_file}: {e}")

def generate_complete_env_file(secret_key, jwt_key, env_file='.env'):
    """
    Generate a complete .env file with all required variables
    
    Args:
        secret_key (str): Flask secret key
        jwt_key (str): JWT secret key
        env_file (str): Path to the .env file
    """
    env_content = f"""# Flask Configuration
SECRET_KEY={secret_key}
FLASK_ENV=development
DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///portfolio.db

# JWT Configuration
JWT_SECRET_KEY={jwt_key}

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Feature Flags
AI_CHAT_ENABLED=True
EMAIL_NOTIFICATIONS=True

# Security Settings
SESSION_PROTECTION=strong
PERMANENT_SESSION_LIFETIME=3600

# Rate Limiting
RATELIMIT_DEFAULT=200 per day
RATELIMIT_CONTACT=5 per minute

# Upload Settings
MAX_FILE_SIZE=16777216
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,pdf

# API Settings
API_RATE_LIMIT=100 per hour
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Complete {env_file} file generated successfully")
        print(f"📝 Remember to update email credentials and other settings")
    except Exception as e:
        print(f"❌ Error creating {env_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Generate secure Flask and JWT secret keys')
    parser.add_argument('--length', type=int, default=32, 
                       help='Length of the secret keys in bytes (default: 32)')
    parser.add_argument('--jwt-length', type=int, default=32,
                       help='Length of the JWT secret key in bytes (default: 32)')
    parser.add_argument('--update-env', action='store_true',
                       help='Automatically update .env file with the generated keys')
    parser.add_argument('--create-env', action='store_true',
                       help='Create a complete .env file with all required variables')
    parser.add_argument('--env-file', default='.env',
                       help='Path to .env file (default: .env)')
    parser.add_argument('--flask-only', action='store_true',
                       help='Generate only Flask secret key (no JWT)')
    parser.add_argument('--jwt-only', action='store_true',
                       help='Generate only JWT secret key')
    
    args = parser.parse_args()
    
    # Generate keys based on arguments
    flask_key = None
    jwt_key = None
    
    if not args.jwt_only:
        flask_key = generate_secret_key(args.length)
    
    if not args.flask_only:
        jwt_key = generate_jwt_key(args.jwt_length)
    
    print("\n" + "="*60)
    print("🔐 SECRET KEY GENERATOR")
    print("="*60)
    
    if flask_key:
        print(f"🔑 Flask Secret Key ({args.length} bytes):")
        print(f"   {flask_key}")
        print()
    
    if jwt_key:
        print(f"🔐 JWT Secret Key ({args.jwt_length} bytes):")
        print(f"   {jwt_key}")
        print()
    
    print("="*60)
    
    # Show usage examples
    print("\n📋 Usage in your Flask app:")
    if flask_key:
        print(f"SECRET_KEY = '{flask_key}'")
    if jwt_key:
        print(f"JWT_SECRET_KEY = '{jwt_key}'")
    
    # Update or create .env file
    if args.update_env and (flask_key or jwt_key):
        if flask_key and jwt_key:
            update_env_file(flask_key, jwt_key, args.env_file)
        elif flask_key:
            update_env_file(flask_key, "", args.env_file)
        elif jwt_key:
            update_env_file("", jwt_key, args.env_file)
    
    if args.create_env and flask_key and jwt_key:
        generate_complete_env_file(flask_key, jwt_key, args.env_file)
    
    print("\n⚠️  Important Security Notes:")
    print("• Keep these keys secret and never commit them to version control")
    print("• Use different keys for development and production environments")
    print("• Store keys in environment variables, not in source code")
    print("• Regenerate keys if you suspect they've been compromised")
    print("• JWT keys should be strong (32+ bytes) for production use")
    
    print("\n🚀 Quick Start Commands:")
    print("python generate.py --create-env                    # Create complete .env file")
    print("python generate.py --update-env                   # Update existing .env")
    print("python generate.py --flask-only --length=64       # 64-byte Flask key only")
    print("python generate.py --jwt-only --jwt-length=64     # 64-byte JWT key only")

if __name__ == "__main__":
    main()