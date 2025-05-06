from database import Base, engine
import models  # make sure this import is present

Base.metadata.create_all(bind=engine)
