
import sys
from pathlib import Path
from datetime import datetime

from sqlalchemy import (
    create_engine, String, Integer, DateTime, ForeignKey,
    CheckConstraint, select
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QInputDialog, QHeaderView
)
from PySide6.QtCore import Qt


# Keep the database in the project folder for this initial version.
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{(BASE_DIR / 'lpgmanager.db').as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
Session = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    capacity_kg: Mapped[int] = mapped_column(Integer, default=11)
    selling_price_centavos: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[int] = mapped_column(Integer, default=1)


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"
    __table_args__ = (
        CheckConstraint("full_qty >= 0"),
        CheckConstraint("empty_qty >= 0"),
        CheckConstraint("damaged_qty >= 0"),
        CheckConstraint("customer_qty >= 0"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), unique=True
    )
    full_qty: Mapped[int] = mapped_column(Integer, default=0)
    empty_qty: Mapped[int] = mapped_column(Integer, default=0)
    damaged_qty: Mapped[int] = mapped_column(Integer, default=0)
    customer_qty: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str] = mapped_column(String(40), default="")
    address: Mapped[str] = mapped_column(String(250), default="")
    credit_limit_centavos: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )


class Exchange(Base):
    __tablename__ = "exchanges"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_no: Mapped[str] = mapped_column(String(40), unique=True)
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"), nullable=True
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
    total_centavos: Mapped[int] = mapped_column(Integer, default=0)
    paid_centavos: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="completed")


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String(150))
    invoice_no: Mapped[str] = mapped_column(String(80), default="")
    invoice_date: Mapped[datetime] = mapped_column(DateTime)
    received_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    total_centavos: Mapped[int] = mapped_column(Integer, default=0)
    paid_centavos: Mapped[int] = mapped_column(Integer, default=0)


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
    category: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(250), default="")
    amount_centavos: Mapped[int] = mapped_column(Integer)


class CylinderReturn(Base):
    __tablename__ = "cylinder_returns"

    id: Mapped[int] = mapped_column(primary_key=True)
    return_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(String(250))
    disposition: Mapped[str] = mapped_column(String(40), default="quarantine")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    movement_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
    movement_type: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(String(250), default="")


def initialize_database():
    Base.metadata.create_all(engine)

    with Session.begin() as session:
        for name in ("Regasco", "SPI"):
            product = session.scalar(
                select(Product).where(Product.name == name)
            )
            if product is None:
                product = Product(name=name, capacity_kg=11)
                session.add(product)
                session.flush()
                session.add(InventoryBalance(product_id=product.id))


class LPGManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LPG Manager - Inventory System")
        self.resize(1000, 650)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        title = QLabel("LPG INVENTORY MANAGER")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Regasco 11 kg  |  SPI 11 kg  |  Local Windows Database"
        )
        layout.addWidget(subtitle)

        self.summary = QLabel()
        self.summary.setStyleSheet(
            "font-size: 15px; padding: 12px; background: #eeeeee;"
        )
        layout.addWidget(self.summary)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Brand", "Full", "Empty", "Damaged", "With Customers"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self.table)

        buttons = QHBoxLayout()

        refresh = QPushButton("Refresh Inventory")
        refresh.clicked.connect(self.refresh_inventory)
        buttons.addWidget(refresh)

        opening = QPushButton("Set Opening Stock")
        opening.clicked.connect(self.set_opening_stock)
        buttons.addWidget(opening)

        close = QPushButton("Exit")
        close.clicked.connect(self.close)
        buttons.addWidget(close)

        layout.addLayout(buttons)

        note = QLabel(
            "Initial version: stock setup only. Exchange, credit, "
            "purchases and returns screens are not implemented yet."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        self.refresh_inventory()

    def refresh_inventory(self):
        with Session() as session:
            products = session.scalars(
                select(Product).order_by(Product.id)
            ).all()

            rows = []
            for product in products:
                stock = session.scalar(
                    select(InventoryBalance).where(
                        InventoryBalance.product_id == product.id
                    )
                )
                if stock is not None:
                    rows.append((product.name, stock))

        self.table.setRowCount(len(rows))

        total_full = total_empty = total_damaged = total_customers = 0

        for row_index, (name, stock) in enumerate(rows):
            values = [
                name, stock.full_qty, stock.empty_qty,
                stock.damaged_qty, stock.customer_qty
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )
                self.table.setItem(row_index, column, item)

            total_full += stock.full_qty
            total_empty += stock.empty_qty
            total_damaged += stock.damaged_qty
            total_customers += stock.customer_qty

        self.summary.setText(
            f"Full: {total_full}    Empty: {total_empty}    "
            f"Damaged: {total_damaged}    With customers: {total_customers}"
        )

    def set_opening_stock(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Select product",
                "Select Regasco or SPI in the table first."
            )
            return

        product_name = self.table.item(row, 0).text()

        with Session() as session:
            product = session.scalar(
                select(Product).where(Product.name == product_name)
            )
            stock = session.scalar(
                select(InventoryBalance).where(
                    InventoryBalance.product_id == product.id
                )
            )

            current = [
                stock.full_qty, stock.empty_qty,
                stock.damaged_qty, stock.customer_qty
            ]

        labels = [
            "Full cylinders", "Empty cylinders",
            "Damaged cylinders", "With customers"
        ]
        new_values = []

        for label, old_value in zip(labels, current):
            value, ok = QInputDialog.getInt(
                self, f"{product_name} - Opening Stock",
                f"{label} (current: {old_value}):",
                old_value, 0, 100000, 1
            )
            if not ok:
                return
            new_values.append(value)

        confirm = QMessageBox.question(
            self, "Confirm stock",
            f"Set opening quantities for {product_name}?\n\n"
            + "\n".join(
                f"{label}: {value}"
                for label, value in zip(labels, new_values)
            )
            + "\n\nThis replaces the current quantities."
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            with Session.begin() as session:
                stock = session.scalar(
                    select(InventoryBalance).where(
                        InventoryBalance.product_id == product.id
                    )
                )
                stock.full_qty = new_values[0]
                stock.empty_qty = new_values[1]
                stock.damaged_qty = new_values[2]
                stock.customer_qty = new_values[3]
                stock.updated_at = datetime.now()

                session.add(InventoryMovement(
                    product_id=product.id,
                    movement_type="opening_stock",
                    quantity=sum(new_values),
                    notes="Opening stock set from dashboard"
                ))

            self.refresh_inventory()
            QMessageBox.information(
                self, "Saved", "Opening stock saved successfully."
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Database error", str(exc)
            )


if __name__ == "__main__":
    initialize_database()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LPGManager()
    window.show()
    sys.exit(app.exec())
