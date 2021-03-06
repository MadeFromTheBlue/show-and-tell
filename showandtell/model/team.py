#! /usr/bin/env python3

"""
Team Model
"""

from showandtell.db import Base
from showandtell.model.association_tables import person_team_xref

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class Team(Base):

    def __init__(self, name, website=None):
        self.name = name
        self.website = website

    def info_dict(self):
        return {
            'team_id': self.team_id,
            'name': self.name,
            'website': self.website,
        }

    __tablename__ = 'teams'

    # Fields
    team_id = Column(Integer, autoincrement=True, primary_key=True)
    profile_pic_id = Column(Integer, ForeignKey('assets.asset_id'))
    name = Column(String, nullable=False)
    website = Column(String)

    # Relationships
    profile_pic = relationship('Asset', back_populates='team')
    members = relationship(
        'Person', secondary=person_team_xref, back_populates='teams')
    projects = relationship('Project', back_populates='team')
