from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from flask import g
from greenlet import getcurrent as _get_ident
from sqlalchemy.dialects.postgresql import JSONB
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./database/nhl.db"

Base = declarative_base()


class DictMixIn:
    def to_dict(self):
        return {
            column.name: getattr(self, column.name)
            if not isinstance(
                getattr(self, column.name), (datetime.datetime, datetime.date)
            )
            else getattr(self, column.name).isoformat()
            for column in self.__table__.columns  # type: ignore not an error
        }


class Database:
    def init_no_app(self, restart=False):
        """Set up SQLAlchemy to work with Flask Application"""
        # connect database
        self.engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
        # create session factory
        self.sessionmaker = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        # set up scoped_session registry
        # #add ability to access scoped session registry (implicitly)
        self.session = self.init_scoped_session()
        if restart:
            Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def init_app(self, app):
        """Set up SQLAlchemy to work with Flask Application"""
        # connect database
        self.engine = create_engine(app.config["DATABASE"])
        # create session factory
        self.sessionmaker = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.session = self.init_scoped_session()
        # make sure db is initialize and up to date
        Base.metadata.create_all(bind=self.engine)

    def init_scoped_session(self):
        "Create empty scoped session registry upon app startup"
        return scoped_session(self.sessionmaker, scopefunc=_get_ident)

    def remove_session(self, error=None):
        """Removes the current Session object associated with
        the request"""
        self.session.remove()
        # this is necessary for teardown functions
        if error:
            # Log the error
            print("logging error", str(error))

    def start_session(self, error=None):
        # set up scoped_session registry
        # #add ability to access scoped session registry (implicitly)
        self.session = self.init_scoped_session()
