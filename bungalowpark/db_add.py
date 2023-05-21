

from bungalowpark import db
from bungalowpark.models import Tent

# Create a new tent object
tent1 = Tent(omschrijving="Tent 1", aantal_personen=4, prijs_per_dag=50.0)

# Add the tent object to the database session
db.session.add(tent1)

# Commit the changes to the database
db.session.commit()
