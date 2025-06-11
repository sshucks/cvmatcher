from sqlalchemy import Table, Column, Integer, BLOB, String, ForeignKey, UniqueConstraint, BOOLEAN, \
    ForeignKeyConstraint, Float
from sqlalchemy.orm import declarative_base, relationship, backref
from sqlalchemy.engine import Engine

import app

Base = declarative_base()

from sqlite3 import Connection as SQLite3Connection

class CachedCVs(Base):
    """Model class for caching a CV. 
    
    Attributes:
        cv_hash (str): hash of CV file
        path (str): location of CV file
        
    Constraints:
        path (str): location of CV file has to be unique
    """
    
    # define table name
    __tablename__ = 'cached_cvs'
    
    # define columns
    cv_hash = Column(String, primary_key=True)
    path = Column(String, nullable=False)
    
    # define constraints
    __table_args__ = (
        UniqueConstraint('path', name="unique_path")
    )
    
    # define string representation of object
    def __repr__(self):
        return f"CachedCV: cv_hash='{self.cv_hash}', path='{self.path}'"

class Requirement_CV_Matching(Base):
    """Model class for caching matching of requirement file and CV. 
    
    Attributes:
        id (int): unique identifier
        requirement_hash (str): hash of requirements file
        cv_hash (str): hash of CV file
        raw_education_score (float): raw (without weight applied) score of education
        raw_work_experience_score (float): raw (without weight applied) score of work experience
        raw_professional_skills_score (float): raw (without weight applied) score of professional skills
        raw_personal_skills_score (float): raw (without weight applied) score of personal skills
        
    Constraints:
        requirement_hash (str) & cv_hash (str): both combinations combined have to be unique
    """
    
    # define table name
    __tablename__ = 'requirement_cv_matching'
    
    # define columns
    id = Column(Integer, primary_key=True)
    requirement_hash = Column(String, nullable=False)
    cv_hash = Column(String, nullable=False)
    raw_education_score = Column(Float, nullable=False)
    raw_work_experience_score = Column(Float, nullable=False)
    raw_professional_skills_score = Column(Float, nullable=False)
    raw_personal_skills_score = Column(Float, nullable=Float)
    
    # define constraints
    __table_args__ = (
        UniqueConstraint('requirement_hash', 'cv_hash', name='unique_requirment_cv_matching'),
    )
    
    # define string representation of object
    def __repr__(self):
        return f"Requirement_CV_Matching: id={self.id}, requirement_hash='{self.requirement_hash}', cv_hash='{self.cv_hash}', raw_education_score={self.raw_education_score}, raw_work_experience_score={self.raw_work_experience_score}, raw_professional_skills_score={self.raw_professional_skills_score}, raw_personal_skills_score={self.raw_personal_skills_score}"
    