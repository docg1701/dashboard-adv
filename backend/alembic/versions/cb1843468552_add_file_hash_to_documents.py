# Copyright 2025 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from alembic import op
import sqlalchemy as sa


# add_file_hash_to_documents
#
# Revision ID: cb1843468552
# Revises: 0001
# Create Date: 2025-07-02 18:51:13.706028

# revision identifiers, used by Alembic.
revision = 'cb1843468552'
down_revision = '0001'


def upgrade():
    # This migration is now a no-op because the file_hash column is
    # already created in the 0001_create_initial_schema.py migration.
    pass


def downgrade():
    # The downgrade logic is also a no-op for the same reason.
    pass