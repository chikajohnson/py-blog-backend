"""Seed initial data

Revision ID: 002
Revises: 001
Create Date: 2026-05-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import bcrypt


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Seed users with hashed passwords (all passwords are "password123")
    password_hash = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()
    users_data = [
        ('b0ee0000-0000-0000-0000-000000000001', 'superadmin@pyflow.dev', password_hash, 'Super', 'Admin', 'super_admin'),
        ('b0ee0000-0000-0000-0000-000000000002', 'admin@pyflow.dev', password_hash, 'Admin', 'User', 'admin'),
        ('b0ee0000-0000-0000-0000-000000000003', 'editor@pyflow.dev', password_hash, 'Jane', 'Editor', 'editor'),
        ('b0ee0000-0000-0000-0000-000000000004', 'author@pyflow.dev', password_hash, 'John', 'Author', 'author'),
    ]

    op.bulk_insert(
        sa.table(
            'users',
            sa.column('id', postgresql.UUID),
            sa.column('email', sa.String),
            sa.column('password_hash', sa.String),
            sa.column('first_name', sa.String),
            sa.column('last_name', sa.String),
            sa.column('role', sa.String),
            sa.column('is_active', sa.Boolean),
            sa.column('email_verified', sa.Boolean),
        ),
        [
            {'id': u[0], 'email': u[1], 'password_hash': u[2], 'first_name': u[3], 'last_name': u[4], 'role': u[5], 'is_active': True, 'email_verified': True}
            for u in users_data
        ]
    )

    # Seed categories
    categories_data = [
        ('b0ee0001-0000-0000-0000-000000000001', 'Technology', 'technology', 'Latest in tech and software development', 'code', '#3B82F6', 1),
        ('b0ee0001-0000-0000-0000-000000000002', 'Design', 'design', 'UI/UX design trends and tutorials', 'palette', '#10B981', 2),
        ('b0ee0001-0000-0000-0000-000000000003', 'Business', 'business', 'Startup stories and business insights', 'briefcase', '#F59E0B', 3),
        ('b0ee0001-0000-0000-0000-000000000004', 'Lifestyle', 'lifestyle', 'Work-life balance and productivity', 'sun', '#8B5CF6', 4),
    ]

    op.bulk_insert(
        sa.table(
            'categories',
            sa.column('id', postgresql.UUID),
            sa.column('name', sa.String),
            sa.column('slug', sa.String),
            sa.column('description', sa.Text),
            sa.column('icon', sa.String),
            sa.column('color', sa.String),
            sa.column('sort_order', sa.Integer),
        ),
        [
            {'id': c[0], 'name': c[1], 'slug': c[2], 'description': c[3], 'icon': c[4], 'color': c[5], 'sort_order': c[6]}
            for c in categories_data
        ]
    )

    # Seed tags
    tags_data = [
        ('b0ee0002-0000-0000-0000-000000000001', 'Python', 'python', '#3776AB'),
        ('b0ee0002-0000-0000-0000-000000000002', 'JavaScript', 'javascript', '#F7DF1E'),
        ('b0ee0002-0000-0000-0000-000000000003', 'FastAPI', 'fastapi', '#009688'),
        ('b0ee0002-0000-0000-0000-000000000004', 'React', 'react', '#61DAFB'),
        ('b0ee0002-0000-0000-0000-000000000005', 'PostgreSQL', 'postgresql', '#4169E1'),
        ('b0ee0002-0000-0000-0000-000000000006', 'Docker', 'docker', '#2496ED'),
        ('b0ee0002-0000-0000-0000-000000000007', 'AWS', 'aws', '#FF9900'),
        ('b0ee0002-0000-0000-0000-000000000008', 'CSS', 'css', '#264DE4'),
        ('b0ee0002-0000-0000-0000-000000000009', 'TypeScript', 'typescript', '#3178C6'),
        ('b0ee0002-0000-0000-0000-000000000010', 'Node.js', 'nodejs', '#339933'),
        ('b0ee0002-0000-0000-0000-000000000011', 'Git', 'git', '#F05032'),
        ('b0ee0002-0000-0000-0000-000000000012', 'AI', 'ai', '#FF6F61'),
    ]

    op.bulk_insert(
        sa.table(
            'tags',
            sa.column('id', postgresql.UUID),
            sa.column('name', sa.String),
            sa.column('slug', sa.String),
            sa.column('color', sa.String),
        ),
        [
            {'id': t[0], 'name': t[1], 'slug': t[2], 'color': t[3]}
            for t in tags_data
        ]
    )

    # Seed settings
    settings_data = [
        ('site_name', {'value': 'PyFlow Blog'}),
        ('site_description', {'value': 'A modern blog platform built with FastAPI'}),
        ('posts_per_page', {'value': 10}),
        ('enable_newsletter', {'value': True}),
        ('enable_ai_chat', {'value': True}),
    ]

    op.bulk_insert(
        sa.table(
            'settings',
            sa.column('key', sa.String),
            sa.column('value', postgresql.JSONB),
        ),
        [
            {'key': s[0], 'value': s[1]}
            for s in settings_data
        ]
    )


def downgrade() -> None:
    op.execute("DELETE FROM settings WHERE key IN ('site_name', 'site_description', 'posts_per_page', 'enable_newsletter', 'enable_ai_chat')")
    op.execute("DELETE FROM tags WHERE id LIKE 'b0ee0002-%'")
    op.execute("DELETE FROM categories WHERE id LIKE 'b0ee0001-%'")
    op.execute("DELETE FROM users WHERE id LIKE 'b0ee0000-%'")
