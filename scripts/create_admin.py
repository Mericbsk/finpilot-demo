#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FinPilot Admin Management Script
=================================

Admin kullanıcı oluşturma ve yönetim aracı.

Kullanım:
    # Yeni admin oluştur
    python scripts/create_admin.py --email admin@finpilot.com --password SecurePass123!

    # Mevcut kullanıcıyı admin yap
    python scripts/create_admin.py --promote user@example.com

    # Admin listele
    python scripts/create_admin.py --list
"""
import argparse
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.core import AuthConfig, AuthManager, User, UserRole
from auth.database import Database, SessionRepository, UserRepository


def get_managers(db_path: str = "data/finpilot.db"):
    """Initialize database and managers."""
    db = Database(db_path)
    db.initialize()

    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    auth = AuthManager(
        config=AuthConfig(), user_repository=user_repo, session_repository=session_repo
    )

    return db, user_repo, auth


def create_admin(email: str, username: str, password: str, display_name: str = None):
    """Create a new admin user."""
    db, user_repo, auth = get_managers()

    # Check if user exists
    existing = user_repo.get_by_email(email)
    if existing:
        print(f"❌ Kullanıcı zaten mevcut: {email}")
        print(f"   Mevcut rol: {existing.role.value}")
        return False

    # Register user first
    try:
        session = auth.register(
            email=email, username=username, password=password, display_name=display_name or "Admin"
        )
        print(f"✅ Kullanıcı oluşturuldu: {email}")
    except Exception as e:
        print(f"❌ Kayıt hatası: {e}")
        return False

    # Now promote to admin
    user = user_repo.get_by_email(email)
    if user:
        user.role = UserRole.ADMIN
        user.is_verified = True  # Auto-verify admin
        user_repo.save(user)  # save() works as upsert
        print(f"✅ Admin rolü atandı: {email}")
        print(f"   Kullanıcı adı: {username}")
        print(f"   Görünen ad: {display_name or 'Admin'}")
        return True

    return False


def promote_to_admin(email: str):
    """Promote existing user to admin."""
    db, user_repo, auth = get_managers()

    user = user_repo.get_by_email(email)
    if not user:
        print(f"❌ Kullanıcı bulunamadı: {email}")
        return False

    if user.role == UserRole.ADMIN:
        print(f"ℹ️ Kullanıcı zaten admin: {email}")
        return True

    old_role = user.role.value
    user.role = UserRole.ADMIN
    user.is_verified = True
    user_repo.save(user)  # save() works as upsert

    print(f"✅ Admin rolü atandı: {email}")
    print(f"   Önceki rol: {old_role}")
    print("   Yeni rol: admin")
    return True


def demote_from_admin(email: str):
    """Demote admin to regular user."""
    db, user_repo, auth = get_managers()

    user = user_repo.get_by_email(email)
    if not user:
        print(f"❌ Kullanıcı bulunamadı: {email}")
        return False

    if user.role != UserRole.ADMIN:
        print(f"ℹ️ Kullanıcı zaten admin değil: {email}")
        return True

    user.role = UserRole.USER
    user_repo.save(user)  # save() works as upsert

    print(f"✅ Admin rolü kaldırıldı: {email}")
    print("   Yeni rol: user")
    return True


def list_admins():
    """List all admin users."""
    db, user_repo, auth = get_managers()

    # Get all users and filter admins
    with db.connection() as conn:
        cursor = conn.execute("SELECT * FROM users WHERE role = 'admin'")
        rows = cursor.fetchall()

    if not rows:
        print("ℹ️ Henüz admin kullanıcı yok.")
        print("\n   Oluşturmak için:")
        print(
            "   python scripts/create_admin.py --email admin@finpilot.com --password GucluSifre123!"
        )
        return

    print(f"\n📋 Admin Kullanıcılar ({len(rows)} adet):")
    print("-" * 60)

    for row in rows:
        print(f"  • {row['email']}")
        print(f"    Kullanıcı adı: {row['username']}")
        print(f"    Görünen ad: {row['display_name'] or '-'}")
        print(f"    Aktif: {'✅' if row['is_active'] else '❌'}")
        print(f"    Doğrulanmış: {'✅' if row['is_verified'] else '❌'}")
        print(f"    Kayıt tarihi: {row['created_at']}")
        print()


def list_all_users():
    """List all users with their roles."""
    db, user_repo, auth = get_managers()

    with db.connection() as conn:
        cursor = conn.execute(
            "SELECT email, username, role, is_active, created_at FROM users ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()

    if not rows:
        print("ℹ️ Henüz kullanıcı yok.")
        return

    print(f"\n📋 Tüm Kullanıcılar ({len(rows)} adet):")
    print("-" * 70)
    print(f"{'Email':<30} {'Kullanıcı Adı':<15} {'Rol':<10} {'Aktif':<6}")
    print("-" * 70)

    for row in rows:
        role_icon = "👑" if row["role"] == "admin" else "💎" if row["role"] == "premium" else "👤"
        active = "✅" if row["is_active"] else "❌"
        print(f"{row['email']:<30} {row['username']:<15} {role_icon} {row['role']:<7} {active}")


def main():
    parser = argparse.ArgumentParser(
        description="FinPilot Admin Yönetim Aracı",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # Yeni admin oluştur
  python scripts/create_admin.py --email admin@finpilot.com --password GucluSifre123!

  # Mevcut kullanıcıyı admin yap
  python scripts/create_admin.py --promote user@example.com

  # Admin listele
  python scripts/create_admin.py --list

  # Tüm kullanıcıları listele
  python scripts/create_admin.py --list-all
        """,
    )

    parser.add_argument("--email", "-e", help="Admin e-posta adresi")
    parser.add_argument("--username", "-u", help="Kullanıcı adı (varsayılan: email prefix)")
    parser.add_argument("--password", "-p", help="Şifre (en az 8 karakter)")
    parser.add_argument("--name", "-n", help="Görünen ad")
    parser.add_argument("--promote", metavar="EMAIL", help="Mevcut kullanıcıyı admin yap")
    parser.add_argument("--demote", metavar="EMAIL", help="Admin rolünü kaldır")
    parser.add_argument("--list", "-l", action="store_true", help="Admin kullanıcıları listele")
    parser.add_argument("--list-all", action="store_true", help="Tüm kullanıcıları listele")
    parser.add_argument("--db", default="data/finpilot.db", help="Veritabanı yolu")

    args = parser.parse_args()

    # List commands
    if args.list:
        list_admins()
        return

    if args.list_all:
        list_all_users()
        return

    # Promote command
    if args.promote:
        promote_to_admin(args.promote)
        return

    # Demote command
    if args.demote:
        demote_from_admin(args.demote)
        return

    # Create admin command
    if args.email and args.password:
        username = args.username or args.email.split("@")[0]
        create_admin(
            email=args.email, username=username, password=args.password, display_name=args.name
        )
        return

    # No valid command
    parser.print_help()
    print("\n⚠️ Gerekli parametreleri girin veya --help ile yardım alın.")


if __name__ == "__main__":
    main()
