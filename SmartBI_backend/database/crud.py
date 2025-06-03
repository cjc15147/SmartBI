from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from . import models
import logging

logger = logging.getLogger(__name__)

def create_user(db: Session, user_data: dict):
    try:
        db_user = models.User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Successfully created user with account: {user_data.get('userAccount')}")
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while creating user: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error while creating user: {str(e)}")
        raise

def get_user_by_account(db: Session, user_account: str):
    try:
        return db.query(models.User).filter(
            models.User.userAccount == user_account,
            models.User.isDelete == 0
        ).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error while querying user by account: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while querying user by account: {str(e)}")
        raise

def get_users(db: Session, skip: int = 0, limit: int = 100):
    try:
        return db.query(models.User).filter(
            models.User.isDelete == 0
        ).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error while querying users list: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while querying users list: {str(e)}")
        raise

def update_user_password(db: Session, user_id: int, new_password: str):
    try:
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if db_user:
            db_user.userPassword = new_password
            db.commit()
            logger.info(f"Successfully updated password for user ID: {user_id}")
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while updating user password: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error while updating user password: {str(e)}")
        raise 