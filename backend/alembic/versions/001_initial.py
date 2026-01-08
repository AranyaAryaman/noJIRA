"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Person
    op.create_table(
        'person',
        sa.Column('person_id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('nickname', sa.String(100), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_person_email', 'person', ['email'])

    # Team
    op.create_table(
        'team',
        sa.Column('team_id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('person.person_id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # TeamMember
    op.create_table(
        'team_member',
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('team.team_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('person_id', sa.Integer(), sa.ForeignKey('person.person_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role', sa.Enum('OWNER', 'MEMBER', name='teamrole'), nullable=False, server_default='MEMBER'),
    )

    # Project
    op.create_table(
        'project',
        sa.Column('project_id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('person.person_id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
    )

    # ProjectTeam
    op.create_table(
        'project_team',
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.project_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('team.team_id', ondelete='CASCADE'), primary_key=True),
    )

    # ProjectMember
    op.create_table(
        'project_member',
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.project_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('person_id', sa.Integer(), sa.ForeignKey('person.person_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role', sa.Enum('ADMIN', 'MEMBER', 'VIEWER', name='projectrole'), nullable=False, server_default='MEMBER'),
    )

    # Task
    op.create_table(
        'task',
        sa.Column('task_id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('project.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_task_id', sa.Integer(), sa.ForeignKey('task.task_id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assignee_id', sa.Integer(), sa.ForeignKey('person.person_id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.Enum('NOT_STARTED', 'PLANNING', 'DEVELOPMENT', 'TESTING', 'FINISHED', name='taskstatus'), nullable=False, server_default='NOT_STARTED'),
        sa.Column('severity', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('person.person_id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
    )

    # TaskTag
    op.create_table(
        'task_tag',
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('task.task_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag', sa.String(100), primary_key=True),
    )

    # TaskWatcher
    op.create_table(
        'task_watcher',
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('task.task_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('person_id', sa.Integer(), sa.ForeignKey('person.person_id', ondelete='CASCADE'), primary_key=True),
    )

    # TaskAttachment
    op.create_table(
        'task_attachment',
        sa.Column('attachment_id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('task.task_id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(100), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('person.person_id'), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Comment
    op.create_table(
        'comment',
        sa.Column('comment_id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('task.task_id', ondelete='CASCADE'), nullable=False),
        sa.Column('person_id', sa.Integer(), sa.ForeignKey('person.person_id'), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('is_system_comment', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
    )

    # CommentAttachment
    op.create_table(
        'comment_attachment',
        sa.Column('attachment_id', sa.Integer(), primary_key=True),
        sa.Column('comment_id', sa.Integer(), sa.ForeignKey('comment.comment_id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(100), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # TaskStatusHistory
    op.create_table(
        'task_status_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('task.task_id', ondelete='CASCADE'), nullable=False),
        sa.Column('old_status', sa.Enum('NOT_STARTED', 'PLANNING', 'DEVELOPMENT', 'TESTING', 'FINISHED', name='taskstatus', create_type=False), nullable=True),
        sa.Column('new_status', sa.Enum('NOT_STARTED', 'PLANNING', 'DEVELOPMENT', 'TESTING', 'FINISHED', name='taskstatus', create_type=False), nullable=False),
        sa.Column('changed_by', sa.Integer(), sa.ForeignKey('person.person_id'), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('task_status_history')
    op.drop_table('comment_attachment')
    op.drop_table('comment')
    op.drop_table('task_attachment')
    op.drop_table('task_watcher')
    op.drop_table('task_tag')
    op.drop_table('task')
    op.drop_table('project_member')
    op.drop_table('project_team')
    op.drop_table('project')
    op.drop_table('team_member')
    op.drop_table('team')
    op.drop_table('person')

    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS projectrole')
    op.execute('DROP TYPE IF EXISTS teamrole')
