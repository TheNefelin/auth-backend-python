# Modelos (SQLAlchemy 2.1 `Mapped`)

> Detalle de la sección **Modelos** de la skill `fastapi`: ejemplo de mapeo con SQLAlchemy sobre PostgreSQL. El diseño de esquema, tipos, índices, constraints y migraciones sigue la skill `sql`.

```python
# src/models/models.py
from datetime import datetime
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Category(Base):
  __tablename__ = "app_categories"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

  products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
  __tablename__ = "app_products"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  category_id: Mapped[int] = mapped_column(Integer, ForeignKey("app_categories.id"), nullable=False)
  name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
  slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
  price: Mapped[int] = mapped_column(Integer, nullable=False)  # en centavos, nunca float
  is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

  category: Mapped["Category"] = relationship(back_populates="products")
```

---

### Una sola Base declarativa

La `Base` vive en `src/core/database.py` (con la convención de nombres) y **`src/models/models.py` la importa**:

```python
from src.core.database import Base
```

**No declares otra `Base`** en `models/`, ni otra en `core/database.py` distinta a la que usan los modelos. Dos bases = dos registries: `Base.metadata.create_all()` sobre la equivocada no crea las tablas, y los tests que usan `Base.metadata` quedan desalineados. Si quieres convención de nombres, ponla en `core/database.Base`, no en un segundo declarativo.

### Consolidar a un único `models.py` sin tocar los call sites

Si migras de un modelo por archivo a un único `models.py` (recomendado: evita imports circulares), deja `src/models/__init__.py` como fachada que reexporta:

```python
# src/models/__init__.py
from .models import User, UserRole, UserStatus, AuthProvider, UserIdentity, UserSession, MFA, RecoveryCode
```

Los call sites (`from src.models import User`) **no cambian**, y la fachada importa todos los modelos, lo que los registra en `Base.metadata`. Sin la fachada, `from src.models import User` deja de funcionar y hay que tocar cada archivo.
