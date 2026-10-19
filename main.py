import sys
import csv
import webbrowser
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

from sqlalchemy import (
    create_engine, String, Integer, DateTime, ForeignKey,
    CheckConstraint, select, text
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, sessionmaker
)

from PySide6.QtCore import Qt, QDate, QUrl
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QInputDialog, QHeaderView, QFrame, QStackedWidget,
    QLineEdit, QAbstractItemView, QDialog, QFormLayout,
    QDialogButtonBox, QComboBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QFileDialog, QCompleter
)
from PySide6.QtWebEngineWidgets import QWebEngineView


# =========================================================
# DATABASE — USE THE EXISTING DATABASE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "lpgmanager.db"

engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    connect_args={"check_same_thread": False}
)

Session = sessionmaker(
    bind=engine,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    capacity_kg: Mapped[int] = mapped_column(Integer, default=11)
    selling_price_centavos: Mapped[int] = mapped_column(
        Integer, default=100000
    )
    active: Mapped[int] = mapped_column(Integer, default=1)


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), unique=True
    )
    full_qty: Mapped[int] = mapped_column(Integer, default=0)
    empty_qty: Mapped[int] = mapped_column(Integer, default=0)
    damaged_qty: Mapped[int] = mapped_column(Integer, default=0)
    customer_qty: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )

    __table_args__ = (
        CheckConstraint("full_qty >= 0"),
        CheckConstraint("empty_qty >= 0"),
        CheckConstraint("damaged_qty >= 0"),
        CheckConstraint("customer_qty >= 0"),
    )


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )
    movement_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
    movement_type: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(String, default="")


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String)
    invoice_no: Mapped[str] = mapped_column(String, default="")
    invoice_date: Mapped[datetime] = mapped_column(DateTime)
    received_date: Mapped[datetime] = mapped_column(DateTime)
    total_centavos: Mapped[int] = mapped_column(Integer)
    paid_centavos: Mapped[int] = mapped_column(Integer, default=0)


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id")
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )
    quantity: Mapped[int] = mapped_column(Integer)
    unit_cost_centavos: Mapped[int] = mapped_column(Integer)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    phone: Mapped[str] = mapped_column(String, default="")
    address: Mapped[str] = mapped_column(String, default="")
    map_link: Mapped[str] = mapped_column(String, default="")
    credit_limit_centavos: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Exchange(Base):
    __tablename__ = "exchanges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_no: Mapped[str] = mapped_column(String, default="")
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id")
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )
    transaction_type: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_selling_price_centavos: Mapped[int] = mapped_column(Integer)
    total_centavos: Mapped[int] = mapped_column(Integer)
    paid_centavos: Mapped[int] = mapped_column(Integer, default=0)
    payment_status: Mapped[str] = mapped_column(String, default="Unpaid")
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
    remarks: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="Active")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("exchanges.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    amount_centavos: Mapped[int] = mapped_column(Integer)
    payment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    remarks: Mapped[str] = mapped_column(String, default="")


class DamagedTank(Base):
    __tablename__ = "damaged_tanks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    remarks: Mapped[str] = mapped_column(String, default="")
    report_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    status: Mapped[str] = mapped_column(String, default="Quarantined")
    resolved_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    reissued_by: Mapped[str] = mapped_column(String, default="")


# =========================================================
# DATABASE INITIALIZATION & MIGRATION
# =========================================================

def initialize_database():
    Base.metadata.create_all(engine)

    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(damaged_tanks);")).fetchall()
        existing_cols = [row[1] for row in result]
        if existing_cols:
            if "reissued_by" not in existing_cols:
                try:
                    conn.execute(text("ALTER TABLE damaged_tanks ADD COLUMN reissued_by VARCHAR DEFAULT '';"))
                    conn.commit()
                except Exception:
                    pass

        cust_result = conn.execute(text("PRAGMA table_info(customers);")).fetchall()
        cust_cols = [row[1] for row in cust_result]
        if cust_cols:
            if "map_link" not in cust_cols:
                try:
                    conn.execute(text("ALTER TABLE customers ADD COLUMN map_link VARCHAR DEFAULT '';"))
                    conn.commit()
                except Exception:
                    pass

        exp_result = conn.execute(text("PRAGMA table_info(expenses);")).fetchall()
        exp_cols = [row[1] for row in exp_result]
        if exp_cols:
            if "remarks" not in exp_cols:
                try:
                    conn.execute(text("ALTER TABLE expenses ADD COLUMN remarks VARCHAR DEFAULT '';"))
                    conn.commit()
                except Exception:
                    pass
            if "description" not in exp_cols:
                try:
                    conn.execute(text("ALTER TABLE expenses ADD COLUMN description VARCHAR DEFAULT '';"))
                    conn.commit()
                except Exception:
                    pass

    with Session.begin() as session:
        for brand in ("Regasco", "SPI"):
            product = session.scalar(
                select(Product).where(Product.name == brand)
            )

            if product is None:
                product = Product(
                    name=brand, capacity_kg=11, selling_price_centavos=100000
                )
                session.add(product)
                session.flush()

            balance = session.scalar(
                select(InventoryBalance).where(
                    InventoryBalance.product_id == product.id
                )
            )

            if balance is None:
                session.add(
                    InventoryBalance(product_id=product.id)
                )


# =========================================================
# SATELLITE & STREET MAP PICKER DIALOG
# =========================================================

class MapPickerDialog(QDialog):
    def __init__(self, initial_link="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pin Customer House (Satellite & Street View)")
        self.resize(900, 680)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top_bar = QHBoxLayout()
        info_lbl = QLabel("💡 Switch to Satellite view to see actual rooftops and houses, then click to pin exact location.")
        info_lbl.setStyleSheet("font-weight: 700; color: #334155;")
        top_bar.addWidget(info_lbl)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view, 1)

        bottom_layout = QHBoxLayout()
        self.coord_label = QLabel("Selected: No location pinned yet")
        self.coord_label.setStyleSheet("font-weight: 800; color: #2563EB;")
        bottom_layout.addWidget(self.coord_label)
        bottom_layout.addStretch()

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        bottom_layout.addWidget(btn_box)
        layout.addLayout(bottom_layout)

        self.selected_link = ""
        
        # Default starting coords (Binmaley / Pangasinan area: 16.035, 120.345)
        lat, lon = 16.035, 120.345
        if initial_link and "q=" in initial_link:
            try:
                coords_part = initial_link.split("q=")[1].split("&")[0]
                parts = coords_part.split(",")
                lat, lon = float(parts[0]), float(parts[1])
                self.selected_link = initial_link
            except Exception:
                pass

        self.load_map_html(lat, lon)

    def load_map_html(self, lat, lon):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                html, body, #map {{ width: 100%; height: 100%; margin: 0; padding: 0; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var streetLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19,
                    attribution: '© OpenStreetMap'
                }});

                var satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                    maxZoom: 19,
                    attribution: 'Tiles © Esri — Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, swisstopo, and the GIS User Community'
                }});

                var map = L.map('map', {{
                    center: [{lat}, {lon}],
                    zoom: 16,
                    layers: [satelliteLayer]
                }});

                var baseMaps = {{
                    "Satellite Imagery": satelliteLayer,
                    "Street Map": streetLayer
                }};

                L.control.layers(baseMaps).addTo(map);

                var marker = L.marker([{lat}, {lon}], {{draggable: true}}).addTo(map);

                function updateCoords(lat, lng) {{
                    document.title = lat + "," + lng;
                }}

                map.on('click', function(e) {{
                    var lat = e.latlng.lat.toFixed(6);
                    var lng = e.latlng.lng.toFixed(6);
                    marker.setLatLng([lat, lng]);
                    updateCoords(lat, lng);
                }});

                marker.on('dragend', function(e) {{
                    var pos = marker.getLatLng();
                    var lat = pos.lat.toFixed(6);
                    var lng = pos.lng.toFixed(6);
                    updateCoords(lat, lng);
                }});
            </script>
        </body>
        </html>
        """
        self.web_view.setHtml(html_content, QUrl("https://localhost"))
        self.web_view.titleChanged.connect(self.on_title_changed)

    def on_title_changed(self, title):
        if "," in title:
            try:
                parts = title.split(",")
                lat, lon = parts[0].strip(), parts[1].strip()
                self.selected_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                self.coord_label.setText(f"Pinned: {lat}, {lon}")
            except Exception:
                pass


# =========================================================
# DYNAMIC ACCESSIBLE STYLESHEET GENERATOR
# =========================================================

def get_app_stylesheet(font_pt=13):
    title_pt = font_pt + 15
    card_val_pt = font_pt + 19
    brand_pt = font_pt + 9
    muted_pt = max(10, font_pt - 2)
    brand_sub_pt = max(9, font_pt - 3)
    card_title_pt = max(10, font_pt - 1)
    filter_pt = max(11, font_pt - 1)

    return """
QWidget {{
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: {font_pt}pt;
    color: #090D16;
}}
QMainWindow, QWidget#central {{
    background-color: #F8FAFC;
}}
QDialog {{
    background-color: #FFFFFF;
    color: #0F172A;
}}
QFrame#sidebar {{
    background-color: #090D16;
    border: none;
}}
QLabel#brand {{
    color: #FFFFFF;
    font-size: {brand_pt}pt;
    font-weight: 800;
}}
QLabel#brand_subtitle {{
    color: #38BDF8;
    font-size: {brand_sub_pt}pt;
    font-weight: 700;
    letter-spacing: 1px;
}}
QPushButton#nav {{
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-radius: 10px;
    text-align: left;
    padding: 14px 18px;
    font-size: {font_pt}pt;
    font-weight: 700;
}}
QPushButton#nav:hover {{
    background-color: #1E293B;
    color: #F1F5F9;
}}
QPushButton#nav[selected="true"] {{
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 800;
}}
QLabel#page_title {{
    font-size: {title_pt}pt;
    font-weight: 800;
    color: #0F172A;
}}
QLabel#muted {{
    color: #475569;
    font-size: {muted_pt}pt;
    font-weight: 600;
}}
QFrame#card {{
    background-color: #FFFFFF;
    border: 2px solid #CBD5E1;
    border-radius: 14px;
}}
QLabel#card_title {{
    color: #1E293B;
    font-size: {card_title_pt}pt;
    font-weight: 800;
    text-transform: uppercase;
}}
QLabel#card_value {{
    color: #0F172A;
    font-size: {card_val_pt}pt;
    font-weight: 900;
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background: #FFFFFF;
    border: 2px solid #94A3B8;
    border-radius: 10px;
    padding: 10px 14px;
    min-height: 26px;
    font-size: {font_pt}pt;
    font-weight: 600;
    color: #0F172A;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QDateEdit:focus {{
    border: 2px solid #2563EB;
    background: #FFFFFF;
}}
QTableWidget {{
    background: #FFFFFF;
    alternate-background-color: #F1F5F9;
    border: 2px solid #CBD5E1;
    border-radius: 12px;
    gridline-color: #E2E8F0;
    outline: none;
    font-size: {font_pt}pt;
}}
QTableWidget::item {{
    padding: 10px;
    font-weight: 600;
    color: #0F172A;
}}
QTableWidget::item:selected {{
    background-color: #DBEAFE;
    color: #1E3A8A;
}}
QHeaderView::section {{
    background: #E2E8F0;
    color: #0F172A;
    padding: 14px 12px;
    border: none;
    border-bottom: 3px solid #94A3B8;
    font-size: {font_pt}pt;
    font-weight: 800;
}}
QPushButton#primary {{
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 12px 20px;
    font-size: {font_pt}pt;
    font-weight: 800;
}}
QPushButton#primary:hover {{
    background-color: #1D4ED8;
}}
QPushButton#secondary {{
    background-color: #FFFFFF;
    color: #0F172A;
    border: 2px solid #94A3B8;
    border-radius: 10px;
    padding: 11px 18px;
    font-size: {font_pt}pt;
    font-weight: 800;
}}
QPushButton#secondary:hover {{
    background-color: #F1F5F9;
    border-color: #64748B;
}}
QPushButton#filter_btn {{
    background-color: #F1F5F9;
    color: #334155;
    border: 2px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: {filter_pt}pt;
    font-weight: 700;
}}
QPushButton#filter_btn:hover {{
    background-color: #E2E8F0;
}}
QPushButton#filter_btn[active="true"] {{
    background-color: #2563EB;
    color: #FFFFFF;
    border-color: #1D4ED8;
}}
QDialogButtonBox QPushButton {{
    background-color: #E2E8F0;
    color: #0F172A;
    border: 2px solid #94A3B8;
    border-radius: 10px;
    padding: 10px 20px;
    font-size: {font_pt}pt;
    font-weight: 800;
}}
QDialogButtonBox QPushButton:hover {{
    background-color: #CBD5E1;
}}
""".format(
        font_pt=font_pt,
        title_pt=title_pt,
        card_val_pt=card_val_pt,
        brand_pt=brand_pt,
        brand_sub_pt=brand_sub_pt,
        muted_pt=muted_pt,
        card_title_pt=card_title_pt,
        filter_pt=filter_pt
    )


# =========================================================
# REUSABLE UI HELPERS
# =========================================================

def make_label(text, object_name=None):
    label = QLabel(text)
    if object_name:
        label.setObjectName(object_name)
    return label


def make_button(text, object_name="secondary"):
    button = QPushButton(text)
    button.setObjectName(object_name)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def make_card(title, accent, description):
    card = QFrame()
    card.setObjectName("card")
    card.setMinimumHeight(165)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(8)

    heading = QHBoxLayout()
    heading.addWidget(make_label(title, "card_title"))
    heading.addStretch()

    icon = make_label(accent)
    icon.setStyleSheet("font-size: 24pt;")
    heading.addWidget(icon)
    layout.addLayout(heading)

    value = make_label("0", "card_value")
    layout.addWidget(value)

    note = make_label(description, "muted")
    note.setWordWrap(True)
    layout.addWidget(note)
    layout.addStretch()

    return card, value


def style_table(table, default_row_height=56):
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.setWordWrap(False)
    table.setEditTriggers(
        QAbstractItemView.EditTrigger.NoEditTriggers
    )
    table.setSelectionBehavior(
        QAbstractItemView.SelectionBehavior.SelectRows
    )
    table.setSelectionMode(
        QAbstractItemView.SelectionMode.SingleSelection
    )
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(default_row_height)
    table.horizontalHeader().setSectionResizeMode(
        QHeaderView.ResizeMode.Stretch
    )


# =========================================================
# RECORD PAYMENT DIALOG
# =========================================================

class RecordPaymentDialog(QDialog):
    def __init__(self, customer_id, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setWindowTitle("Record Payment")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(16)

        self.amount_box = QDoubleSpinBox()
        self.amount_box.setRange(0.01, 1000000.00)
        self.amount_box.setDecimals(2)
        self.amount_box.setPrefix("₱ ")

        self.date_box = QDateEdit()
        self.date_box.setCalendarPopup(True)
        self.date_box.setDisplayFormat("dd MMM yyyy")
        self.date_box.setDate(QDate.currentDate())

        self.txn_combo = QComboBox()

        form.addRow("Target Transaction:", self.txn_combo)
        form.addRow("Payment Amount:", self.amount_box)
        form.addRow("Payment Date:", self.date_box)

        layout.addLayout(form)
        layout.addSpacing(16)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.load_unpaid_transactions()

    def load_unpaid_transactions(self):
        with Session() as session:
            exchanges = session.scalars(
                select(Exchange)
                .where(Exchange.customer_id == self.customer_id)
                .order_by(Exchange.transaction_date.desc())
            ).all()

            for ex in exchanges:
                balance_centavos = ex.total_centavos - ex.paid_centavos
                if balance_centavos > 0:
                    label_text = f"{ex.transaction_no or f'TXN-{ex.id:04d}'} — Bal: ₱{balance_centavos/100:,.2f} ({ex.transaction_date.strftime('%d %b %Y')})"
                    self.txn_combo.addItem(label_text, (ex.id, balance_centavos))

            if self.txn_combo.count() > 0:
                _, max_bal = self.txn_combo.currentData()
                self.amount_box.setValue(max_bal / 100)
                self.amount_box.setMaximum(max_bal / 100)

            self.txn_combo.currentIndexChanged.connect(self.on_txn_changed)

    def on_txn_changed(self, index):
        data = self.txn_combo.currentData()
        if data:
            _, max_bal = data
            self.amount_box.setValue(max_bal / 100)
            self.amount_box.setMaximum(max_bal / 100)


# =========================================================
# CUSTOMER PROFILE DIALOG
# =========================================================

class CustomerProfileDialog(QDialog):
    def __init__(self, customer_id, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setWindowTitle("Customer Profile & Account History")
        self.resize(1100, 750)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(18)

        self.info_frame = QFrame()
        self.info_frame.setObjectName("card")
        info_layout = QVBoxLayout(self.info_frame)
        info_layout.setContentsMargins(22, 20, 22, 20)
        info_layout.setSpacing(8)

        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-size: 22pt; font-weight: 900; color: #0F172A;")
        
        header_row = QHBoxLayout()
        self.details_label = QLabel()
        self.details_label.setStyleSheet("color: #1E293B; font-size: 13pt; font-weight: 700;")
        header_row.addWidget(self.details_label)
        header_row.addStretch()

        self.pin_map_button = make_button("🛰️ Satellite Pin / Update", "secondary")
        self.pin_map_button.clicked.connect(self.open_map_picker)
        header_row.addWidget(self.pin_map_button)

        self.map_button = make_button("🗺️ Open Map Location", "secondary")
        self.map_button.clicked.connect(self.open_customer_map)
        header_row.addWidget(self.map_button)

        self.pay_button = make_button("＋ Record Payment", "primary")
        self.pay_button.clicked.connect(self.open_record_payment_dialog)
        header_row.addWidget(self.pay_button)

        info_layout.addWidget(self.name_label)
        info_layout.addLayout(header_row)
        layout.addWidget(self.info_frame)

        layout.addWidget(make_label("Purchase / Transaction History", "card_title"))
        self.history_table = QTableWidget(0, 8)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Txn #", "Type", "Brand", "Qty", "Total", "Paid", "Balance"
        ])
        style_table(self.history_table)
        layout.addWidget(self.history_table, 1)

        layout.addWidget(make_label("Payment History Log (When Paid)", "card_title"))
        self.payments_table = QTableWidget(0, 4)
        self.payments_table.setHorizontalHeaderLabels([
            "Payment Date", "Target Txn #", "Amount Paid", "Status / Notes"
        ])
        style_table(self.payments_table)
        layout.addWidget(self.payments_table, 1)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)

        self.load_customer_data()

    def load_customer_data(self):
        with Session() as session:
            customer = session.get(Customer, self.customer_id)
            if not customer:
                return

            self.name_label.setText(customer.name)
            phone_text = customer.phone if customer.phone else "No phone provided"
            address_text = customer.address if customer.address else "No address provided"
            self.map_link = customer.map_link if customer.map_link else ""
            
            self.map_button.setEnabled(bool(self.map_link))

            exchanges = session.scalars(
                select(Exchange).where(Exchange.customer_id == customer.id)
            ).all()

            total_credit = sum((ex.total_centavos - ex.paid_centavos) for ex in exchanges) / 100

            self.details_label.setText(
                f"Phone: {phone_text}   |   Address: {address_text}   |   Outstanding Balance: ₱{total_credit:,.2f}"
            )

            self.pay_button.setEnabled(total_credit > 0)

            rows = session.execute(
                select(Exchange, Product)
                .join(Product, Exchange.product_id == Product.id)
                .where(Exchange.customer_id == customer.id)
                .order_by(Exchange.transaction_date.desc(), Exchange.id.desc())
            ).all()

            self.history_table.setRowCount(len(rows))
            for row_idx, (ex, prod) in enumerate(rows):
                total = ex.total_centavos / 100
                paid = ex.paid_centavos / 100
                balance = total - paid

                values = [
                    ex.transaction_date.strftime("%d %b %Y"),
                    ex.transaction_no or f"TXN-{ex.id:04d}",
                    ex.transaction_type,
                    prod.name,
                    ex.quantity,
                    f"₱{total:,.2f}",
                    f"₱{paid:,.2f}",
                    f"₱{balance:,.2f}"
                ]

                for col_idx, val in enumerate(values):
                    cell = QTableWidgetItem(str(val))
                    if col_idx in [4, 5, 6, 7]:
                        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.history_table.setItem(row_idx, col_idx, cell)

            payment_rows = session.execute(
                select(Payment, Exchange)
                .join(Exchange, Payment.exchange_id == Exchange.id)
                .where(Payment.customer_id == customer.id)
                .order_by(Payment.payment_date.desc(), Payment.id.desc())
            ).all()

            self.payments_table.setRowCount(len(payment_rows))
            for row_idx, (pay, ex) in enumerate(payment_rows):
                p_amount = pay.amount_centavos / 100
                p_values = [
                    pay.payment_date.strftime("%d %b %Y"),
                    ex.transaction_no or f"TXN-{ex.id:04d}",
                    f"₱{p_amount:,.2f}",
                    ex.payment_status
                ]

                for col_idx, val in enumerate(p_values):
                    cell = QTableWidgetItem(str(val))
                    if col_idx in [1, 2, 3]:
                        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.payments_table.setItem(row_idx, col_idx, cell)

    def open_map_picker(self):
        picker = MapPickerDialog(self.map_link, self)
        if picker.exec() == QDialog.DialogCode.Accepted and picker.selected_link:
            try:
                with Session.begin() as session:
                    cust = session.get(Customer, self.customer_id)
                    if cust:
                        cust.map_link = picker.selected_link
                self.load_customer_data()
                QMessageBox.information(self, "Success", "Customer rooftop/house satellite pin updated successfully!")
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Could not save map location:\n{exc}")

    def open_customer_map(self):
        if self.map_link:
            webbrowser.open(self.map_link)
        else:
            QMessageBox.warning(self, "No Map Link", "No map link or coordinates saved for this customer.")

    def open_record_payment_dialog(self):
        dialog = RecordPaymentDialog(self.customer_id, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.txn_combo.currentData()
        if not data:
            QMessageBox.warning(self, "Error", "No valid unpaid transaction selected.")
            return

        txn_id, _ = data
        payment_centavos = round(dialog.amount_box.value() * 100)
        payment_date = datetime.combine(
            dialog.date_box.date().toPython(),
            datetime.min.time()
        )

        try:
            with Session.begin() as session:
                ex = session.get(Exchange, txn_id)
                if not ex:
                    raise ValueError("Transaction not found.")

                ex.paid_centavos += payment_centavos
                if ex.paid_centavos >= ex.total_centavos:
                    ex.payment_status = "Paid"
                    ex.paid_centavos = ex.total_centavos
                else:
                    ex.payment_status = "Partial"

                new_payment = Payment(
                    exchange_id=txn_id,
                    customer_id=self.customer_id,
                    amount_centavos=payment_centavos,
                    payment_date=payment_date,
                    remarks="Credit payment installment"
                )
                session.add(new_payment)

            self.load_customer_data()
            QMessageBox.information(self, "Success", "Payment recorded with date and credit updated successfully!")

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not record payment:\n{exc}")


# =========================================================
# REPORT DAMAGE DIALOG
# =========================================================

class ReportDamageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Report Damaged Tank")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(16)

        self.brand_box = QComboBox()
        self.qty_box = QSpinBox()
        self.qty_box.setRange(1, 1000000)
        self.qty_box.setValue(1)

        self.date_box = QDateEdit()
        self.date_box.setCalendarPopup(True)
        self.date_box.setDisplayFormat("dd MMM yyyy")
        self.date_box.setDate(QDate.currentDate())

        self.remarks_box = QLineEdit()
        self.remarks_box.setPlaceholderText("e.g., Rusted body, broken valve, dented")

        form.addRow("LPG Brand:", self.brand_box)
        form.addRow("Quantity:", self.qty_box)
        form.addRow("Date Reported:", self.date_box)
        form.addRow("Damage Remarks:", self.remarks_box)

        layout.addLayout(form)
        layout.addSpacing(16)

        with Session() as session:
            products = session.scalars(
                select(Product).where(Product.active == 1).order_by(Product.name)
            ).all()
            for p in products:
                self.brand_box.addItem(p.name, p.id)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


# =========================================================
# SUPPLIER REISSUANCE DIALOG
# =========================================================

class SupplierReissueDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Supplier Reissuance Details")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(16)

        self.reissued_by_box = QLineEdit()
        self.reissued_by_box.setPlaceholderText("e.g., Supplier Agent Name / Delivery Driver")

        self.date_box = QDateEdit()
        self.date_box.setCalendarPopup(True)
        self.date_box.setDisplayFormat("dd MMM yyyy")
        self.date_box.setDate(QDate.currentDate())

        form.addRow("Reissued By (Supplier Rep):", self.reissued_by_box)
        form.addRow("Replacement Date:", self.date_box)

        layout.addLayout(form)
        layout.addSpacing(16)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


# =========================================================
# RECORD EXPENSE / MISC WITHDRAWAL DIALOG
# =========================================================

class RecordExpenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Business Expense / Vehicle Draw")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(16)

        self.category_box = QComboBox()
        self.category_box.addItems([
            "Vehicle Gas / Fuel",
            "Vehicle Maintenance & Repair",
            "Store Miscellaneous / Utility",
            "Owner Draw / Personal Cash Out"
        ])

        self.amount_box = QDoubleSpinBox()
        self.amount_box.setRange(0.01, 1000000.00)
        self.amount_box.setDecimals(2)
        self.amount_box.setPrefix("₱ ")
        self.amount_box.setValue(500.00)

        self.date_box = QDateEdit()
        self.date_box.setCalendarPopup(True)
        self.date_box.setDisplayFormat("dd MMM yyyy")
        self.date_box.setDate(QDate.currentDate())

        self.remarks_box = QLineEdit()
        self.remarks_box.setPlaceholderText("e.g., Delivery motorcycle fuel, oil change, tire repair")

        form.addRow("Expense Category:", self.category_box)
        form.addRow("Amount:", self.amount_box)
        form.addRow("Date:", self.date_box)
        form.addRow("Details / Notes:", self.remarks_box)

        layout.addLayout(form)
        layout.addSpacing(16)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


# =========================================================
# MAIN WINDOW
# =========================================================

class LPGManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_font_size = 13
        self.exchange_payment_filter = "All"
        self.exchange_date_mode = "Today"  # Default to Today

        self.setWindowTitle("LPG Manager — High-Visibility Accessible Edition")
        self.resize(1350, 820)
        self.setMinimumSize(1050, 720)

        self.nav_buttons = []
        self.placeholder_pages = {}

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)

        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 28, 18, 24)
        side.setSpacing(12)

        side.addWidget(make_label("🔥  LPG Manager", "brand"))
        side.addWidget(
            make_label("INVENTORY & BUSINESS", "brand_subtitle")
        )
        side.addSpacing(25)

        for name, icon in [
            ("Dashboard", "▦"),
            ("Inventory", "▤"),
            ("Exchanges", "⇄"),
            ("Customers & Credit", "♙"),
            ("Reminders & Debt", "🔔"),
            ("Purchases", "＋"),
            ("Returns & Damages", "⚠"),
            ("Reports", "▥"),
        ]:
            button = QPushButton(f"{icon}    {name}")
            button.setObjectName("nav")
            button.setProperty("selected", name == "Dashboard")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, page=name: self.navigate(page)
            )
            side.addWidget(button)
            self.nav_buttons.append((name, button))

        side.addStretch()
        side.addWidget(make_label("LOCAL DATABASE", "brand_subtitle"))
        side.addWidget(make_label("●  Running on this computer"))

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 28, 32, 26)
        content_layout.setSpacing(18)

        header = QHBoxLayout()
        title_area = QVBoxLayout()

        self.page_title = make_label("Dashboard", "page_title")
        self.page_subtitle = make_label(
            "Your LPG business at a glance.", "muted"
        )

        title_area.addWidget(self.page_title)
        title_area.addWidget(self.page_subtitle)
        header.addLayout(title_area)
        header.addStretch()

        font_toolbar = QHBoxLayout()
        font_toolbar.setSpacing(6)
        font_toolbar.addWidget(make_label("Font Size:", "muted"))

        for label_text, pt in [("A-", 11), ("Normal", 13), ("Large", 15), ("Extra Large", 17)]:
            btn = make_button(label_text, "secondary")
            btn.setFixedWidth(75 if label_text in ["Normal", "Large", "Extra Large"] else 45)
            btn.clicked.connect(lambda checked=False, size=pt: self.set_global_font_size(size))
            font_toolbar.addWidget(btn)

        header.addLayout(font_toolbar)
        header.addSpacing(15)

        self.date_label = make_label(
            datetime.now().strftime("%A, %d %B %Y")
        )
        self.date_label.setStyleSheet("color: #0F172A; font-weight: 800; font-size: 13pt;")
        header.addWidget(self.date_label)
        content_layout.addLayout(header)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)

        root.addWidget(sidebar)
        root.addWidget(content, 1)

        self.dashboard_page = self.build_dashboard()
        self.inventory_page = self.build_inventory_page()
        self.exchanges_page = self.build_exchanges_page()
        self.customers_page = self.build_customers_page()
        self.reminders_page = self.build_reminders_page()
        self.damages_page = self.build_damages_page()
        self.reports_page = self.build_reports_page()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.inventory_page)
        self.stack.addWidget(self.exchanges_page)
        self.stack.addWidget(self.customers_page)
        self.stack.addWidget(self.reminders_page)
        self.stack.addWidget(self.damages_page)
        self.stack.addWidget(self.reports_page)

        self.refresh_all()

    def set_global_font_size(self, pt):
        self.current_font_size = pt
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_app_stylesheet(pt))
        self.date_label.setStyleSheet(f"color: #0F172A; font-weight: 800; font-size: {pt}pt;")

    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

    def build_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        self.alert_banner = QFrame()
        self.alert_banner.setObjectName("card")
        self.alert_banner.setStyleSheet("background-color: #FEF2F2; border: 2px solid #FCA5A5; border-radius: 12px;")
        alert_layout = QHBoxLayout(self.alert_banner)
        alert_layout.setContentsMargins(18, 14, 18, 14)

        self.alert_label = QLabel("⚠️ System Alert: All stock levels are sufficient and no overdue payments detected.")
        self.alert_label.setStyleSheet("color: #991B1B; font-weight: 800; font-size: 12pt;")
        alert_layout.addWidget(self.alert_label)
        
        self.alert_banner.setVisible(False)
        layout.addWidget(self.alert_banner)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(18)

        card_specs = [
            ("Full Cylinders", "📦", "Ready for exchange"),
            ("Empty Cylinders", "↻", "Available for refill"),
            ("Damaged Cylinders", "⚠", "Quarantined stock"),
            ("With Customers", "♙", "Customer-held cylinders"),
        ]

        self.card_values = {}

        for title, icon, description in card_specs:
            card, value = make_card(title, icon, description)
            cards_row.addWidget(card)
            self.card_values[title] = value

        layout.addLayout(cards_row)

        section_header = QHBoxLayout()
        section_header.addWidget(make_label("Inventory Overview", "card_title"))
        section_header.addStretch()

        view_all = make_button("View Inventory  →", "secondary")
        view_all.clicked.connect(lambda: self.navigate("Inventory"))
        section_header.addWidget(view_all)
        layout.addLayout(section_header)

        self.dashboard_table = QTableWidget(0, 5)
        self.dashboard_table.setHorizontalHeaderLabels([
            "Brand", "Full", "Empty", "Damaged", "With Customers"
        ])
        style_table(self.dashboard_table)
        layout.addWidget(self.dashboard_table, 1)

        info = QFrame()
        info.setObjectName("card")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(22, 18, 22, 18)
        info_layout.addWidget(make_label("Quick Actions", "card_title"))

        action_row = QHBoxLayout()

        new_txn = make_button("＋  Customer Transaction", "primary")
        new_txn.clicked.connect(self.open_customer_transaction_dialog)

        opening_stock = make_button(
            "＋  Set Opening Stock", "secondary"
        )
        opening_stock.clicked.connect(self.set_opening_stock)

        new_stock = make_button("＋  New Stock / Buy", "secondary")
        new_stock.clicked.connect(self.open_new_stock_dialog)

        record_exp = make_button("💸  Record Expense / Gas", "secondary")
        record_exp.clicked.connect(self.open_record_expense_dialog)

        refresh = make_button("↻  Refresh Data", "secondary")
        refresh.clicked.connect(self.refresh_all)

        action_row.addWidget(new_txn)
        action_row.addWidget(opening_stock)
        action_row.addWidget(new_stock)
        action_row.addWidget(record_exp)
        action_row.addWidget(refresh)
        action_row.addStretch()

        info_layout.addLayout(action_row)
        layout.addWidget(info)

        return page

    # -----------------------------------------------------
    # INVENTORY PAGE
    # -----------------------------------------------------

    def build_inventory_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search LPG brand...")
        self.search_input.textChanged.connect(self.filter_inventory)
        toolbar.addWidget(self.search_input, 1)

        stock_button = make_button("＋  New Stock / Buy", "primary")
        stock_button.clicked.connect(self.open_new_stock_dialog)
        toolbar.addWidget(stock_button)

        opening_button = make_button(
            "Set Opening Stock", "secondary"
        )
        opening_button.clicked.connect(self.set_opening_stock)
        toolbar.addWidget(opening_button)

        refresh_button = make_button("↻ Refresh", "secondary")
        refresh_button.clicked.connect(self.refresh_all)
        toolbar.addWidget(refresh_button)

        layout.addLayout(toolbar)

        self.inventory_table = QTableWidget(0, 6)
        self.inventory_table.setHorizontalHeaderLabels([
            "Brand", "Capacity", "Full", "Empty",
            "Damaged", "With Customers"
        ])
        style_table(self.inventory_table)
        layout.addWidget(self.inventory_table, 1)

        layout.addWidget(
            make_label(
                "Opening stock is for the initial count only. "
                "Use New Stock / Buy for incoming purchases.",
                "muted"
            )
        )

        return page

    # -----------------------------------------------------
    # EXCHANGES PAGE
    # -----------------------------------------------------

    def build_exchanges_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # Top Bar: Search and New Transaction
        toolbar = QHBoxLayout()

        self.exchange_search_input = QLineEdit()
        self.exchange_search_input.setPlaceholderText(
            "Search customer name, brand, or transaction #..."
        )
        self.exchange_search_input.textChanged.connect(
            self.filter_exchanges
        )
        toolbar.addWidget(self.exchange_search_input, 1)

        self.exchange_type_filter = QComboBox()
        self.exchange_type_filter.addItems([
            "All Types", "Gas Exchange", "Borrowed Tank",
            "Permanent Cylinder Sale"
        ])
        self.exchange_type_filter.currentIndexChanged.connect(
            self.filter_exchanges
        )
        toolbar.addWidget(self.exchange_type_filter)

        new_txn_button = make_button(
            "＋  New Customer Transaction", "primary"
        )
        new_txn_button.clicked.connect(
            self.open_customer_transaction_dialog
        )
        toolbar.addWidget(new_txn_button)

        refresh_button = make_button("↻ Refresh", "secondary")
        refresh_button.clicked.connect(self.refresh_exchanges)
        toolbar.addWidget(refresh_button)

        layout.addLayout(toolbar)

        # Date & Payment Filter Bar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        filter_row.addWidget(make_label("Date View:", "muted"))

        self.filter_btn_today = make_button("📅 Today", "filter_btn")
        self.filter_btn_today.setProperty("active", True)
        self.filter_btn_today.clicked.connect(lambda: self.set_exchange_date_mode("Today"))
        filter_row.addWidget(self.filter_btn_today)

        self.filter_btn_specific = make_button("🗓️ Pick Date...", "filter_btn")
        self.filter_btn_specific.setProperty("active", False)
        self.filter_btn_specific.clicked.connect(lambda: self.set_exchange_date_mode("Specific"))
        filter_row.addWidget(self.filter_btn_specific)

        self.date_picker_box = QDateEdit()
        self.date_picker_box.setCalendarPopup(True)
        self.date_picker_box.setDisplayFormat("dd MMM yyyy")
        self.date_picker_box.setDate(QDate.currentDate())
        self.date_picker_box.setEnabled(False)
        self.date_picker_box.dateChanged.connect(self.filter_exchanges)
        filter_row.addWidget(self.date_picker_box)

        self.filter_btn_all_dates = make_button("📜 Show All History", "filter_btn")
        self.filter_btn_all_dates.setProperty("active", False)
        self.filter_btn_all_dates.clicked.connect(lambda: self.set_exchange_date_mode("All"))
        filter_row.addWidget(self.filter_btn_all_dates)

        filter_row.addSpacing(15)
        filter_row.addWidget(make_label("Payment:", "muted"))

        self.filter_btn_all_pay = make_button("All Pay", "filter_btn")
        self.filter_btn_all_pay.setProperty("active", True)
        self.filter_btn_all_pay.clicked.connect(lambda: self.set_exchange_payment_filter("All"))
        filter_row.addWidget(self.filter_btn_all_pay)

        self.filter_btn_unpaid = make_button("⚠️ Unpaid", "filter_btn")
        self.filter_btn_unpaid.setProperty("active", False)
        self.filter_btn_unpaid.clicked.connect(lambda: self.set_exchange_payment_filter("Unpaid"))
        filter_row.addWidget(self.filter_btn_unpaid)

        self.filter_btn_paid = make_button("✅ Paid", "filter_btn")
        self.filter_btn_paid.setProperty("active", False)
        self.filter_btn_paid.clicked.connect(lambda: self.set_exchange_payment_filter("Paid"))
        filter_row.addWidget(self.filter_btn_paid)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        self.exchanges_table = QTableWidget(0, 9)
        self.exchanges_table.setHorizontalHeaderLabels([
            "Date", "Txn #", "Customer", "Type", "Brand",
            "Qty", "Total", "Paid", "Balance"
        ])
        style_table(self.exchanges_table)
        layout.addWidget(self.exchanges_table, 1)

        return page

    def set_exchange_date_mode(self, mode):
        self.exchange_date_mode = mode
        self.date_picker_box.setEnabled(mode == "Specific")

        for btn, target in [(self.filter_btn_today, "Today"), (self.filter_btn_specific, "Specific"), (self.filter_btn_all_dates, "All")]:
            btn.setProperty("active", mode == target)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.filter_exchanges()

    def set_exchange_payment_filter(self, mode):
        self.exchange_payment_filter = mode
        for btn, target in [(self.filter_btn_all_pay, "All"), (self.filter_btn_unpaid, "Unpaid"), (self.filter_btn_paid, "Paid")]:
            btn.setProperty("active", mode == target)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.filter_exchanges()

    # -----------------------------------------------------
    # CUSTOMERS & CREDIT PAGE
    # -----------------------------------------------------

    def build_customers_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        toolbar = QHBoxLayout()

        self.customer_search_input = QLineEdit()
        self.customer_search_input.setPlaceholderText(
            "Search customer name, phone, or address..."
        )
        self.customer_search_input.textChanged.connect(
            self.filter_customers
        )
        toolbar.addWidget(self.customer_search_input, 1)

        refresh_button = make_button("↻ Refresh", "secondary")
        refresh_button.clicked.connect(self.refresh_customers)
        toolbar.addWidget(refresh_button)

        layout.addLayout(toolbar)

        self.customers_table = QTableWidget(0, 7)
        self.customers_table.setHorizontalHeaderLabels([
            "Customer Name", "Phone", "Address", "Map Pin", "Total Txns", "Balance", "Actions"
        ])
        style_table(self.customers_table)
        self.customers_table.cellDoubleClicked.connect(self.on_customer_double_clicked)
        layout.addWidget(self.customers_table, 1)

        layout.addWidget(
            make_label(
                "Double-click any customer row to view their complete purchase history, payment dates, and map location.",
                "muted"
            )
        )

        return page

    # -----------------------------------------------------
    # REMINDERS & DEBT PAGE
    # -----------------------------------------------------

    def build_reminders_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        toolbar = QHBoxLayout()
        toolbar.addWidget(make_label("Track overdue customer credit balances and copy instant SMS payment reminders."))
        toolbar.addStretch()

        refresh_btn = make_button("↻ Refresh Reminders", "secondary")
        refresh_btn.clicked.connect(self.refresh_reminders)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        self.rem_metrics_frame = QFrame()
        self.rem_metrics_frame.setObjectName("card")
        rem_metrics_layout = QHBoxLayout(self.rem_metrics_frame)
        rem_metrics_layout.setContentsMargins(24, 20, 24, 20)

        self.rem_total_debt = QLabel("₱0.00")
        self.rem_total_debt.setStyleSheet("font-size: 20pt; font-weight: 900; color: #EF4444;")
        self.rem_30_days = QLabel("₱0.00")
        self.rem_30_days.setStyleSheet("font-size: 20pt; font-weight: 900; color: #D97706;")
        self.rem_60_days = QLabel("₱0.00")
        self.rem_60_days.setStyleSheet("font-size: 20pt; font-weight: 900; color: #DC2626;")

        def make_rem_box(title, widget):
            box = QVBoxLayout()
            lbl = QLabel(title)
            lbl.setObjectName("card_title")
            box.addWidget(lbl)
            box.addWidget(widget)
            return box

        rem_metrics_layout.addLayout(make_rem_box("Total Outstanding Receivables", self.rem_total_debt))
        rem_metrics_layout.addStretch()
        rem_metrics_layout.addLayout(make_rem_box("30–60 Days Overdue", self.rem_30_days))
        rem_metrics_layout.addStretch()
        rem_metrics_layout.addLayout(make_rem_box("60+ Days Severely Overdue", self.rem_60_days))

        layout.addWidget(self.rem_metrics_frame)

        layout.addWidget(make_label("Overdue Accounts & SMS Reminder Generator", "card_title"))
        self.reminders_table = QTableWidget(0, 8)
        self.reminders_table.setHorizontalHeaderLabels([
            "Customer Name", "Phone", "Txn #", "Txn Date", "Age (Days)", "Balance", "Aging Status", "Action"
        ])
        style_table(self.reminders_table)
        self.reminders_table.cellClicked.connect(self.on_reminder_table_clicked)
        layout.addWidget(self.reminders_table, 1)

        layout.addWidget(
            make_label(
                "Tip: Click '📋 Copy SMS Reminder' on any row to instantly copy a friendly collection message to your clipboard.",
                "muted"
            )
        )

        return page

    # -----------------------------------------------------
    # RETURNS & DAMAGES PAGE
    # -----------------------------------------------------

    def build_damages_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        toolbar = QHBoxLayout()

        report_btn = make_button("＋  Report Damaged Tank", "primary")
        report_btn.clicked.connect(self.open_report_damage_dialog)
        toolbar.addWidget(report_btn)

        resolve_btn = make_button("✓  Mark Replaced by Supplier", "secondary")
        resolve_btn.clicked.connect(self.resolve_damaged_tank)
        toolbar.addWidget(resolve_btn)

        toolbar.addStretch()

        refresh_btn = make_button("↻ Refresh", "secondary")
        refresh_btn.clicked.connect(self.refresh_damages)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        self.damages_table = QTableWidget(0, 7)
        self.damages_table.setHorizontalHeaderLabels([
            "Report Date", "Brand", "Quantity", "Damage Remarks", "Status", "Reissued By", "Resolved Date"
        ])
        style_table(self.damages_table)
        layout.addWidget(self.damages_table, 1)

        layout.addWidget(
            make_label(
                "Review damaged cylinders, track who from the supplier reissued replacements, and monitor restocked inventory.",
                "muted"
            )
        )

        return page

    # -----------------------------------------------------
    # REPORTS PAGE
    # -----------------------------------------------------

    def build_reports_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        toolbar = QHBoxLayout()

        self.report_period_combo = QComboBox()
        self.report_period_combo.addItems(["Per Week", "Per Month"])
        self.report_period_combo.currentIndexChanged.connect(self.refresh_reports)
        toolbar.addWidget(self.report_period_combo)

        export_btn = make_button("📥  Export Report to Excel", "primary")
        export_btn.clicked.connect(self.export_report_to_excel)
        toolbar.addWidget(export_btn)

        toolbar.addStretch()

        refresh_btn = make_button("↻ Refresh Reports", "secondary")
        refresh_btn.clicked.connect(self.refresh_reports)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        self.metrics_frame = QFrame()
        self.metrics_frame.setObjectName("card")
        metrics_layout = QHBoxLayout(self.metrics_frame)
        metrics_layout.setContentsMargins(24, 20, 24, 20)

        self.rep_total_rev = QLabel("₱0.00")
        self.rep_total_rev.setStyleSheet("font-size: 20pt; font-weight: 900; color: #0F172A;")
        self.rep_total_cost = QLabel("₱0.00")
        self.rep_total_cost.setStyleSheet("font-size: 20pt; font-weight: 900; color: #0F172A;")
        self.rep_net_profit = QLabel("₱0.00")
        self.rep_net_profit.setStyleSheet("font-size: 20pt; font-weight: 900; color: #059669;")
        self.rep_unpaid_ar = QLabel("₱0.00")
        self.rep_unpaid_ar.setStyleSheet("font-size: 20pt; font-weight: 900; color: #EF4444;")

        def make_metric_box(title, widget):
            box = QVBoxLayout()
            lbl = QLabel(title)
            lbl.setObjectName("card_title")
            box.addWidget(lbl)
            box.addWidget(widget)
            return box

        metrics_layout.addLayout(make_metric_box("Total Sales Revenue", self.rep_total_rev))
        metrics_layout.addStretch()
        metrics_layout.addLayout(make_metric_box("Total Expenses & Costs", self.rep_total_cost))
        metrics_layout.addStretch()
        metrics_layout.addLayout(make_metric_box("Estimated Net Profit", self.rep_net_profit))
        metrics_layout.addStretch()
        metrics_layout.addLayout(make_metric_box("Uncollected Credit (AR)", self.rep_unpaid_ar))

        layout.addWidget(self.metrics_frame)

        layout.addWidget(make_label("Periodic Financial Summary", "card_title"))
        self.reports_table = QTableWidget(0, 6)
        self.reports_table.setHorizontalHeaderLabels([
            "Period", "Total Transactions", "Cylinders Sold", "Gross Revenue", "Total Expenses/Costs", "Net Profit"
        ])
        style_table(self.reports_table)
        layout.addWidget(self.reports_table, 1)

        layout.addWidget(make_label("Detailed Operating Expenses Breakdown", "card_title"))
        self.expenses_table = QTableWidget(0, 4)
        self.expenses_table.setHorizontalHeaderLabels([
            "Date", "Category", "Amount", "Remarks / Notes"
        ])
        style_table(self.expenses_table)
        layout.addWidget(self.expenses_table, 1)

        layout.addWidget(make_label("Brand & Product Sales Performance", "card_title"))
        self.brand_table = QTableWidget(0, 6)
        self.brand_table.setHorizontalHeaderLabels([
            "Brand", "Units Sold", "Total Revenue", "Estimated Cost", "Net Profit", "Margin %"
        ])
        style_table(self.brand_table)
        layout.addWidget(self.brand_table, 1)

        return page

    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------

    def navigate(self, page_name):
        for name, button in self.nav_buttons:
            button.setProperty("selected", name == page_name)
            button.style().unpolish(button)
            button.style().polish(button)

        self.page_title.setText(page_name)

        subtitles = {
            "Dashboard": "Your LPG business at a glance.",
            "Inventory": "Monitor full, empty and damaged cylinders.",
            "Exchanges": "Record and review customer transactions.",
            "Customers & Credit": "Manage customers and outstanding balances.",
            "Reminders & Debt": "Track overdue accounts and generate SMS payment reminders.",
            "Purchases": "Track supplier purchases and invoices.",
            "Returns & Damages": "Review damaged cylinders and returns.",
            "Reports": "Review business profits, sales, and financial reports.",
        }

        self.page_subtitle.setText(subtitles.get(page_name, ""))

        if page_name == "Dashboard":
            self.stack.setCurrentWidget(self.dashboard_page)
            self.refresh_all()
            return

        if page_name == "Inventory":
            self.stack.setCurrentWidget(self.inventory_page)
            self.refresh_all()
            return

        if page_name == "Exchanges":
            self.stack.setCurrentWidget(self.exchanges_page)
            self.refresh_exchanges()
            return

        if page_name == "Customers & Credit":
            self.stack.setCurrentWidget(self.customers_page)
            self.refresh_customers()
            return

        if page_name == "Reminders & Debt":
            self.stack.setCurrentWidget(self.reminders_page)
            self.refresh_reminders()
            return

        if page_name == "Returns & Damages":
            self.stack.setCurrentWidget(self.damages_page)
            self.refresh_damages()
            return

        if page_name == "Reports":
            self.stack.setCurrentWidget(self.reports_page)
            self.refresh_reports()
            return

        if page_name not in self.placeholder_pages:
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            placeholder_layout.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            placeholder_layout.setSpacing(14)

            icon = make_label("🚧")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet("font-size: 40pt;")

            message = make_label(
                f"{page_name} module is not implemented yet."
            )
            message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message.setStyleSheet(
                "font-size: 18pt; font-weight: 800;"
            )

            details = make_label(
                "This page is a placeholder. No transactions "
                "will be recorded here yet."
            )
            details.setAlignment(Qt.AlignmentFlag.AlignCenter)
            details.setWordWrap(True)
            details.setStyleSheet("color: #475569; font-weight: 600;")

            back_button = make_button(
                "←  Back to Dashboard", "primary"
            )
            back_button.clicked.connect(
                lambda: self.navigate("Dashboard")
            )

            placeholder_layout.addWidget(icon)
            placeholder_layout.addWidget(message)
            placeholder_layout.addWidget(details)
            placeholder_layout.addSpacing(10)
            placeholder_layout.addWidget(
                back_button,
                alignment=Qt.AlignmentFlag.AlignCenter
            )

            self.placeholder_pages[page_name] = placeholder
            self.stack.addWidget(placeholder)

        self.stack.setCurrentWidget(self.placeholder_pages[page_name])

    # -----------------------------------------------------
    # REFRESH DATA & ALERT BANNER
    # -----------------------------------------------------

    def refresh_all(self):
        with Session() as session:
            rows = session.execute(
                select(Product, InventoryBalance)
                .join(
                    InventoryBalance,
                    Product.id == InventoryBalance.product_id
                )
                .where(Product.active == 1)
                .order_by(Product.name)
            ).all()

            inventory = []
            low_stock_brands = []
            for product, balance in rows:
                if balance.full_qty <= 5:
                    low_stock_brands.append(f"{product.name} ({balance.full_qty} left)")
                inventory.append({
                    "name": product.name,
                    "capacity": product.capacity_kg,
                    "full": balance.full_qty,
                    "empty": balance.empty_qty,
                    "damaged": balance.damaged_qty,
                    "customer": balance.customer_qty,
                })

            unpaid_count = session.scalar(
                select(Exchange.id).where(Exchange.payment_status != "Paid").limit(1)
            )

        alerts = []
        if low_stock_brands:
            alerts.append(f"⚠️ Low Stock Warning: {', '.join(low_stock_brands)} at or below 5 tanks!")
        if unpaid_count is not None:
            alerts.append("🔔 Notice: You have pending uncollected customer credit accounts.")

        if alerts:
            self.alert_label.setText("   |   ".join(alerts))
            self.alert_banner.setVisible(True)
        else:
            self.alert_banner.setVisible(False)

        totals = {
            "Full Cylinders": sum(r["full"] for r in inventory),
            "Empty Cylinders": sum(r["empty"] for r in inventory),
            "Damaged Cylinders": sum(r["damaged"] for r in inventory),
            "With Customers": sum(r["customer"] for r in inventory),
        }

        for title, value_label in self.card_values.items():
            value_label.setText(f'{totals[title]:,}')

        self.dashboard_table.setRowCount(len(inventory))

        for row, item in enumerate(inventory):
            values = [
                item["name"], item["full"], item["empty"],
                item["damaged"], item["customer"]
            ]

            for col, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if col == 0:
                    cell.setFont(
                        QFont("Segoe UI", self.current_font_size, QFont.Weight.Bold)
                    )
                if col > 0:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.dashboard_table.setItem(row, col, cell)

        self.inventory_table.setRowCount(len(inventory))

        for row, item in enumerate(inventory):
            values = [
                item["name"],
                f"{item['capacity']} kg",
                item["full"],
                item["empty"],
                item["damaged"],
                item["customer"],
            ]

            for col, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if col == 0:
                    cell.setFont(
                        QFont("Segoe UI", self.current_font_size, QFont.Weight.Bold)
                    )
                if col > 1:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.inventory_table.setItem(row, col, cell)

        self.filter_inventory(
            self.search_input.text()
            if hasattr(self, "search_input") else ""
        )

    def refresh_exchanges(self):
        if not hasattr(self, "exchanges_table"):
            return

        with Session() as session:
            rows = session.execute(
                select(Exchange, Customer, Product)
                .join(Customer, Exchange.customer_id == Customer.id)
                .join(Product, Exchange.product_id == Product.id)
                .order_by(
                    Exchange.transaction_date.desc(),
                    Exchange.id.desc()
                )
            ).all()

            data = []
            for ex, cust, prod in rows:
                total = ex.total_centavos / 100
                paid = ex.paid_centavos / 100
                balance = total - paid
                txn_dt = ex.transaction_date.date() if isinstance(ex.transaction_date, datetime) else ex.transaction_date
                
                data.append({
                    "date": ex.transaction_date.strftime("%d %b %Y"),
                    "raw_date": txn_dt,
                    "txn_no": ex.transaction_no or f"TXN-{ex.id:04d}",
                    "customer": cust.name,
                    "type": ex.transaction_type,
                    "brand": prod.name,
                    "qty": ex.quantity,
                    "total": f"₱{total:,.2f}",
                    "paid": f"₱{paid:,.2f}",
                    "balance": f"₱{balance:,.2f}",
                    "raw_type": ex.transaction_type,
                    "payment_status": ex.payment_status,
                    "search_text": (
                        f"{cust.name} {prod.name} "
                        f"{ex.transaction_no or f'TXN-{ex.id:04d}'} "
                        f"{ex.transaction_type}"
                    ).casefold()
                })

        self.exchanges_data = data
        self.filter_exchanges()

    def refresh_customers(self):
        if not hasattr(self, "customers_table"):
            return

        with Session() as session:
            customers = session.scalars(
                select(Customer).order_by(Customer.name)
            ).all()

            data = []
            for cust in customers:
                exchanges = session.scalars(
                    select(Exchange).where(Exchange.customer_id == cust.id)
                ).all()

                txn_count = len(exchanges)
                total_credit = sum((ex.total_centavos - ex.paid_centavos) for ex in exchanges) / 100

                map_status = "📍 Pinned" if cust.map_link else "—"

                data.append({
                    "id": cust.id,
                    "name": cust.name,
                    "phone": cust.phone or "—",
                    "address": cust.address or "—",
                    "map_link": cust.map_link or "",
                    "map_status": map_status,
                    "txn_count": txn_count,
                    "balance": f"₱{total_credit:,.2f}",
                    "search_text": f"{cust.name} {cust.phone} {cust.address}".casefold()
                })

        self.customers_data = data
        self.filter_customers()

    def refresh_reminders(self):
        if not hasattr(self, "reminders_table"):
            return

        today = date.today()

        with Session() as session:
            rows = session.execute(
                select(Exchange, Customer)
                .join(Customer, Exchange.customer_id == Customer.id)
                .order_by(Exchange.transaction_date.asc())
            ).all()

            unpaid_items = []
            total_debt = 0
            bucket_30 = 0
            bucket_60 = 0

            for ex, cust in rows:
                balance_centavos = ex.total_centavos - ex.paid_centavos
                if balance_centavos > 0:
                    bal_float = balance_centavos / 100
                    total_debt += bal_float

                    txn_date = ex.transaction_date.date() if isinstance(ex.transaction_date, datetime) else ex.transaction_date
                    age_days = (today - txn_date).days

                    if age_days > 60:
                        status = "🔴 60+ Days Overdue"
                        bucket_60 += bal_float
                    elif age_days > 30:
                        status = "🟠 30–60 Days Overdue"
                        bucket_30 += bal_float
                    else:
                        status = "🟢 Current (< 30 Days)"

                    unpaid_items.append({
                        "customer": cust.name,
                        "phone": cust.phone or "No phone",
                        "txn_no": ex.transaction_no or f"TXN-{ex.id:04d}",
                        "date": txn_date.strftime("%d %b %Y"),
                        "age": age_days,
                        "balance": bal_float,
                        "status": status,
                        "raw_balance": bal_float
                    })

            self.reminders_table.setRowCount(len(unpaid_items))
            for row_idx, item in enumerate(unpaid_items):
                values = [
                    item["customer"],
                    item["phone"],
                    item["txn_no"],
                    item["date"],
                    f"{item['age']} days",
                    f"₱{item['balance']:,.2f}",
                    item["status"],
                    "📋 Copy SMS Reminder"
                ]

                for col_idx, val in enumerate(values):
                    cell = QTableWidgetItem(str(val))
                    if col_idx in [1, 2, 3, 4, 5, 6]:
                        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if col_idx == 7:
                        cell.setForeground(Qt.GlobalColor.blue)
                        cell.setFont(QFont("Segoe UI", self.current_font_size - 2, QFont.Weight.Bold))
                    self.reminders_table.setItem(row_idx, col_idx, cell)

            self.rem_total_debt.setText(f"₱{total_debt:,.2f}")
            self.rem_30_days.setText(f"₱{bucket_30:,.2f}")
            self.rem_60_days.setText(f"₱{bucket_60:,.2f}")

    def on_reminder_table_clicked(self, row, col):
        if col == 7:
            cust_name = self.reminders_table.item(row, 0).text()
            phone = self.reminders_table.item(row, 1).text()
            txn_no = self.reminders_table.item(row, 2).text()
            balance = self.reminders_table.item(row, 5).text()
            age = self.reminders_table.item(row, 4).text()

            sms_text = (
                f"Magandang araw po {cust_name}, paalala lamang po mula sa aming LPG store na kayo ay may remaining balance na "
                f"{balance} para sa transaction {txn_no} na umabot na po ng {age.split()[0]} araw. "
                f"Sana po ay inyong maayos o mapagbayaran ito sa lalong madaling panahon. Maraming salamat po!"
            )

            clipboard = QGuiApplication.clipboard()
            clipboard.setText(sms_text)

            QMessageBox.information(
                self, "SMS Template Copied",
                f"Collection SMS template copied to clipboard for {cust_name} ({phone})!\n\n"
                f"Message Preview:\n\"{sms_text}\""
            )

    def refresh_damages(self):
        if not hasattr(self, "damages_table"):
            return

        with Session() as session:
            rows = session.execute(
                select(DamagedTank, Product)
                .join(Product, DamagedTank.product_id == Product.id)
                .order_by(DamagedTank.report_date.desc(), DamagedTank.id.desc())
            ).all()

            self.damages_table.setRowCount(len(rows))
            for row_idx, (dmg, prod) in enumerate(rows):
                resolved_str = dmg.resolved_date.strftime("%d %b %Y") if dmg.resolved_date else "—"
                reissued_str = dmg.reissued_by if dmg.reissued_by else "—"
                values = [
                    dmg.report_date.strftime("%d %b %Y"),
                    prod.name,
                    dmg.quantity,
                    dmg.remarks or "—",
                    dmg.status,
                    reissued_str,
                    resolved_str
                ]

                for col_idx, val in enumerate(values):
                    cell = QTableWidgetItem(str(val))
                    if col_idx in [1, 2, 4, 5, 6]:
                        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    cell.setData(Qt.ItemDataRole.UserRole, dmg.id)
                    self.damages_table.setItem(row_idx, col_idx, cell)

    def refresh_reports(self):
        if not hasattr(self, "reports_table"):
            return

        period_type = self.report_period_combo.currentText()

        with Session() as session:
            exchanges = session.scalars(select(Exchange)).all()
            products = session.scalars(select(Product)).all()
            prod_map = {p.id: p.name for p in products}

            avg_costs = {}
            p_items = session.scalars(select(PurchaseItem)).all()
            prod_cost_sums = defaultdict(lambda: [0, 0])
            for pi in p_items:
                prod_cost_sums[pi.product_id][0] += pi.unit_cost_centavos * pi.quantity
                prod_cost_sums[pi.product_id][1] += pi.quantity
            
            for pid, (c_sum, q_sum) in prod_cost_sums.items():
                if q_sum > 0:
                    avg_costs[pid] = c_sum / q_sum

            grouped_data = defaultdict(lambda: {"txns": 0, "qty": 0, "rev_centavos": 0, "cost_centavos": 0})
            brand_data = defaultdict(lambda: {"qty": 0, "rev_centavos": 0, "cost_centavos": 0})

            total_ar_centavos = 0

            for ex in exchanges:
                dt = ex.transaction_date
                if period_type == "Per Week":
                    year, week, _ = dt.isocalendar()
                    period_key = f"Week {week}, {year}"
                else:
                    period_key = dt.strftime("%B %Y")

                unit_cost = avg_costs.get(ex.product_id, 80000)
                
                grouped_data[period_key]["txns"] += 1
                grouped_data[period_key]["qty"] += ex.quantity
                grouped_data[period_key]["rev_centavos"] += ex.total_centavos
                grouped_data[period_key]["cost_centavos"] += (unit_cost * ex.quantity)

                bname = prod_map.get(ex.product_id, "Unknown")
                brand_data[bname]["qty"] += ex.quantity
                brand_data[bname]["rev_centavos"] += ex.total_centavos
                brand_data[bname]["cost_centavos"] += (unit_cost * ex.quantity)

                total_ar_centavos += (ex.total_centavos - ex.paid_centavos)

            purchases = session.scalars(select(Purchase)).all()
            for pur in purchases:
                dt = pur.received_date
                if period_type == "Per Week":
                    year, week, _ = dt.isocalendar()
                    period_key = f"Week {week}, {year}"
                else:
                    period_key = pur.received_date.strftime("%B %Y")
                grouped_data[period_key]["cost_centavos"] += pur.total_centavos

            expenses_list = []
            try:
                expenses = session.execute(text("SELECT id, category, amount_centavos, expense_date, remarks FROM expenses ORDER BY expense_date DESC;")).fetchall()
                for exp_id, cat, amt_centavos, exp_date, rem in expenses:
                    if isinstance(exp_date, str):
                        exp_dt = datetime.fromisoformat(exp_date)
                    else:
                        exp_dt = exp_date

                    expenses_list.append({
                        "date": exp_dt.strftime("%d %b %Y"),
                        "category": cat,
                        "amount": amt_centavos / 100,
                        "remarks": rem or "—"
                    })

                    if period_type == "Per Week":
                        year, week, _ = exp_dt.isocalendar()
                        period_key = f"Week {week}, {year}"
                    else:
                        period_key = exp_dt.strftime("%B %Y")
                    grouped_data[period_key]["cost_centavos"] += amt_centavos
            except Exception:
                pass

            self.expenses_table.setRowCount(len(expenses_list))
            for row_idx, exp in enumerate(expenses_list):
                vals = [exp["date"], exp["category"], f"₱{exp['amount']:,.2f}", exp["remarks"]]
                for col_idx, val in enumerate(vals):
                    cell = QTableWidgetItem(str(val))
                    if col_idx in [0, 1, 2]:
                        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.expenses_table.setItem(row_idx, col_idx, cell)

            sorted_periods = sorted(grouped_data.keys(), reverse=True)

            self.reports_table.setRowCount(len(sorted_periods))
            grand_rev = 0
            grand_cost = 0

            for row_idx, period in enumerate(sorted_periods):
                d = grouped_data[period]
                rev = d["rev_centavos"] / 100
                cost = d["cost_centavos"] / 100
                profit = rev - cost

                grand_rev += d["rev_centavos"]
                grand_cost += d["cost_centavos"]

                values = [
                    period,
                    d["txns"],
                    d["qty"],
                    f"₱{rev:,.2f}",
                    f"₱{cost:,.2f}",
                    f"₱{profit:,.2f}"
                ]

                for col_idx, val in enumerate(values):
                    cell = QTableWidgetItem(str(val))
                    if col_idx == 0:
                        cell.setFont(QFont("Segoe UI", self.current_font_size, QFont.Weight.Bold))
                    if col_idx > 0:
                        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.reports_table.setItem(row_idx, col_idx, cell)

            self.brand_table.setRowCount(len(brand_data))
            for row_idx, (bname, bd) in enumerate(sorted(brand_data.items())):
                brev = bd["rev_centavos"] / 100
                bcost = bd["cost_centavos"] / 100
                bprofit = brev - bcost
                margin = (bprofit / brev * 100) if brev > 0 else 0.0

                bvalues = [
                    bname,
                    bd["qty"],
                    f"₱{brev:,.2f}",
                    f"₱{bcost:,.2f}",
                    f"₱{bprofit:,.2f}",
                    f"{margin:.1f}%"
                ]

                for col_idx, val in enumerate(bvalues):
                    cell = QTableWidgetItem(str(val))
                    if col_idx == 0:
                        cell.setFont(QFont("Segoe UI", self.current_font_size, QFont.Weight.Bold))
                    if col_idx > 0:
                        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.brand_table.setItem(row_idx, col_idx, cell)

            g_rev_f = grand_rev / 100
            g_cost_f = grand_cost / 100
            g_profit_f = g_rev_f - g_cost_f
            g_ar_f = total_ar_centavos / 100

            self.rep_total_rev.setText(f"₱{g_rev_f:,.2f}")
            self.rep_total_cost.setText(f"₱{g_cost_f:,.2f}")
            self.rep_net_profit.setText(f"₱{g_profit_f:,.2f}")
            self.rep_unpaid_ar.setText(f"₱{g_ar_f:,.2f}")

            if g_profit_f >= 0:
                self.rep_net_profit.setStyleSheet("font-size: 20pt; font-weight: 900; color: #059669;")
            else:
                self.rep_net_profit.setStyleSheet("font-size: 20pt; font-weight: 900; color: #EF4444;")

    def export_report_to_excel(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Financial Report Workbook", "", "Excel Workbook (*.xls)"
        )
        if not filename:
            return

        if not filename.endswith(".xls"):
            filename += ".xls"

        try:
            html = f"""
            <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
            <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 12pt; }}
                .title {{ font-size: 18pt; font-weight: bold; color: #0F172A; padding: 10px 0px; }}
                .subtitle {{ font-size: 10pt; color: #475569; padding-bottom: 15px; }}
                .section-header {{ font-size: 13pt; font-weight: bold; background-color: #0F172A; color: #FFFFFF; padding: 8px; text-align: left; }}
                .card-title {{ font-size: 9pt; font-weight: bold; color: #475569; background-color: #F8FAFC; }}
                .card-val {{ font-size: 14pt; font-weight: bold; color: #0F172A; background-color: #F8FAFC; }}
                .card-profit {{ font-size: 14pt; font-weight: bold; color: #059669; background-color: #F8FAFC; }}
                .card-ar {{ font-size: 14pt; font-weight: bold; color: #EF4444; background-color: #F8FAFC; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 25px; }}
                th {{ background-color: #2563EB; color: #FFFFFF; font-weight: bold; text-align: center; border: 1px solid #1D4ED8; padding: 8px; }}
                td {{ border: 1px solid #CBD5E1; padding: 8px; text-align: center; color: #0F172A; }}
                .bold-cell {{ font-weight: bold; background-color: #F8FAFC; }}
            </style>
            </head>
            <body>
                <div class="title">🔥 LPG MANAGER — FINANCIAL & BUSINESS REPORT</div>
                <div class="subtitle">Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')} | Breakdown Period: {self.report_period_combo.currentText()}</div>
                
                <table>
                    <tr>
                        <td class="card-title">TOTAL SALES REVENUE</td>
                        <td class="card-title">TOTAL EXPENSES & COSTS</td>
                        <td class="card-title">ESTIMATED NET PROFIT</td>
                        <td class="card-title">UNCOLLECTED CREDIT (AR)</td>
                    </tr>
                    <tr>
                        <td class="card-val">{self.rep_total_rev.text()}</td>
                        <td class="card-val">{self.rep_total_cost.text()}</td>
                        <td class="card-profit">{self.rep_net_profit.text()}</td>
                        <td class="card-ar">{self.rep_unpaid_ar.text()}</td>
                    </tr>
                </table>

                <br>
                <table>
                    <tr><td colspan="6" class="section-header">PERIODIC FINANCIAL BREAKDOWN ({self.report_period_combo.currentText().upper()})</td></tr>
                    <tr>
            """

            for col in range(self.reports_table.columnCount()):
                html += f"<th>{self.reports_table.horizontalHeaderItem(col).text()}</th>"
            html += "</tr>"

            for row in range(self.reports_table.rowCount()):
                html += "<tr>"
                for col in range(self.reports_table.columnCount()):
                    val = self.reports_table.item(row, col).text()
                    cls = "bold-cell" if col == 0 else ""
                    html += f"<td class='{cls}'>{val}</td>"
                html += "</tr>"

            html += """
                </table>
                <br>
                <table>
                    <tr><td colspan="4" class="section-header">OPERATING EXPENSES LOG (GAS, VEHICLE, MISC)</td></tr>
                    <tr>
            """

            for col in range(self.expenses_table.columnCount()):
                html += f"<th>{self.expenses_table.horizontalHeaderItem(col).text()}</th>"
            html += "</tr>"

            for row in range(self.expenses_table.rowCount()):
                html += "<tr>"
                for col in range(self.expenses_table.columnCount()):
                    val = self.expenses_table.item(row, col).text()
                    cls = "bold-cell" if col == 0 else ""
                    html += f"<td class='{cls}'>{val}</td>"
                html += "</tr>"

            html += """
                </table>
                <br>
                <table>
                    <tr><td colspan="6" class="section-header">BRAND & PRODUCT PERFORMANCE ANALYSIS</td></tr>
                    <tr>
            """

            for col in range(self.brand_table.columnCount()):
                html += f"<th>{self.brand_table.horizontalHeaderItem(col).text()}</th>"
            html += "</tr>"

            for row in range(self.brand_table.rowCount()):
                html += "<tr>"
                for col in range(self.brand_table.columnCount()):
                    val = self.brand_table.item(row, col).text()
                    cls = "bold-cell" if col == 0 else ""
                    html += f"<td class='{cls}'>{val}</td>"
                html += "</tr>"

            html += """
                </table>
            </body>
            </html>
            """

            with open(filename, mode='w', encoding='utf-8') as file:
                file.write(html)

            QMessageBox.information(
                self, "Export Successful",
                f"Styled professional presentation workbook saved successfully to:\n{filename}"
            )

        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", f"Could not export presentation report:\n{exc}")

    def filter_inventory(self, search_text):
        if not hasattr(self, "inventory_table"):
            return

        search_text = search_text.strip().casefold()

        for row in range(self.inventory_table.rowCount()):
            item = self.inventory_table.item(row, 0)
            brand = item.text().casefold() if item else ""
            self.inventory_table.setRowHidden(
                row, search_text not in brand
            )

    def filter_exchanges(self):
        if not hasattr(self, "exchanges_table") or not hasattr(
            self, "exchanges_data"
        ):
            return

        search_text = self.exchange_search_input.text().strip().casefold()
        type_filter = self.exchange_type_filter.currentText()
        payment_filter = self.exchange_payment_filter
        date_mode = self.exchange_date_mode

        today_date = date.today()
        target_picker_date = self.date_picker_box.date().toPython() if hasattr(self, "date_picker_box") else today_date

        filtered = []
        for item in self.exchanges_data:
            match_search = search_text in item["search_text"]
            match_type = (
                type_filter == "All Types"
                or item["raw_type"] == type_filter
            )
            
            match_payment = True
            if payment_filter == "Unpaid":
                match_payment = item["payment_status"] in ["Unpaid", "Partial"]
            elif payment_filter == "Paid":
                match_payment = item["payment_status"] == "Paid"

            match_date = True
            item_date = item["raw_date"]
            if date_mode == "Today":
                match_date = (item_date == today_date)
            elif date_mode == "Specific":
                match_date = (item_date == target_picker_date)
            elif date_mode == "All":
                match_date = True

            if match_search and match_type and match_payment and match_date:
                filtered.append(item)

        self.exchanges_table.setRowCount(len(filtered))
        for row, item in enumerate(filtered):
            values = [
                item["date"],
                item["txn_no"],
                item["customer"],
                item["type"],
                item["brand"],
                item["qty"],
                item["total"],
                item["paid"],
                item["balance"],
            ]
            for col, val in enumerate(values):
                cell = QTableWidgetItem(str(val))
                if col == 0 or col == 1:
                    cell.setFont(
                        QFont("Segoe UI", self.current_font_size - 2, QFont.Weight.Bold)
                    )
                if col in [4, 5, 6, 7, 8]:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.exchanges_table.setItem(row, col, cell)

    def filter_customers(self):
        if not hasattr(self, "customers_table") or not hasattr(
            self, "customers_data"
        ):
            return

        search_text = self.customer_search_input.text().strip().casefold()

        filtered = []
        for item in self.customers_data:
            if search_text in item["search_text"]:
                filtered.append(item)

        self.customers_table.setRowCount(len(filtered))
        for row, item in enumerate(filtered):
            values = [
                item["name"],
                item["phone"],
                item["address"],
                item["map_status"],
                str(item["txn_count"]),
                item["balance"],
                "View History →"
            ]
            for col, val in enumerate(values):
                cell = QTableWidgetItem(str(val))
                if col == 0:
                    cell.setFont(
                        QFont("Segoe UI", self.current_font_size, QFont.Weight.Bold)
                    )
                if col in [1, 2, 3, 4, 5, 6]:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 3 and item["map_link"]:
                    cell.setForeground(Qt.GlobalColor.blue)
                cell.setData(Qt.ItemDataRole.UserRole, item["id"])
                self.customers_table.setItem(row, col, cell)

    def on_customer_double_clicked(self, row, col):
        item = self.customers_table.item(row, 0)
        if item:
            cust_id = item.data(Qt.ItemDataRole.UserRole)
            if cust_id:
                dialog = CustomerProfileDialog(cust_id, self)
                dialog.exec()
                self.refresh_customers()
                self.refresh_exchanges()

    def open_report_damage_dialog(self):
        dialog = ReportDamageDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        product_id = dialog.brand_box.currentData()
        quantity = dialog.qty_box.value()
        remarks = dialog.remarks_box.text().strip()
        report_date = datetime.combine(
            dialog.date_box.date().toPython(),
            datetime.min.time()
        )

        if not product_id:
            QMessageBox.warning(self, "Error", "Please select a valid product.")
            return

        try:
            with Session.begin() as session:
                balance = session.scalar(
                    select(InventoryBalance).where(
                        InventoryBalance.product_id == product_id
                    )
                )
                if balance is None:
                    raise ValueError("Inventory balance not found.")

                if balance.full_qty < quantity:
                    raise ValueError(f"Insufficient full stock to report as damaged. Available full stock: {balance.full_qty}")

                balance.full_qty -= quantity
                balance.damaged_qty += quantity
                balance.updated_at = datetime.now()

                damage_record = DamagedTank(
                    product_id=product_id,
                    quantity=quantity,
                    remarks=remarks,
                    report_date=report_date,
                    status="Quarantined"
                )
                session.add(damage_record)

                session.add(
                    InventoryMovement(
                        product_id=product_id,
                        movement_date=report_date,
                        movement_type="damage_reported",
                        quantity=quantity,
                        notes=f"Reported damaged tanks (deducted from full stock): {remarks}"
                    )
                )

            self.refresh_all()
            self.refresh_damages()
            QMessageBox.information(self, "Success", "Damaged tanks reported, deducted from full stock, and quarantined!")

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not save damage report:\n{exc}")

    def resolve_damaged_tank(self):
        selected_row = self.damages_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Selection Required", "Please select a damaged tank row from the table first.")
            return

        item = self.damages_table.item(selected_row, 0)
        if not item:
            return

        dmg_id = item.data(Qt.ItemDataRole.UserRole)
        if not dmg_id:
            return

        with Session() as session:
            dmg = session.get(DamagedTank, dmg_id)
            if not dmg:
                QMessageBox.warning(self, "Error", "Damage record not found.")
                return

            if dmg.status == "Replaced by Supplier":
                QMessageBox.information(self, "Already Resolved", "This damage record has already been marked as replaced.")
                return

        dialog = SupplierReissueDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        reissued_by = dialog.reissued_by_box.text().strip()
        reissue_date = datetime.combine(
            dialog.date_box.date().toPython(),
            datetime.min.time()
        )

        if not reissued_by:
            QMessageBox.warning(self, "Missing Info", "Please specify who from the supplier reissued the replacement.")
            return

        try:
            with Session.begin() as session:
                dmg = session.get(DamagedTank, dmg_id)
                balance = session.scalar(
                    select(InventoryBalance).where(
                        InventoryBalance.product_id == dmg.product_id
                    )
                )
                if balance:
                    balance.damaged_qty = max(0, balance.damaged_qty - dmg.quantity)
                    balance.full_qty += dmg.quantity
                    balance.updated_at = datetime.now()

                dmg.status = "Replaced by Supplier"
                dmg.resolved_date = reissue_date
                dmg.reissued_by = reissued_by

                session.add(
                    InventoryMovement(
                        product_id=dmg.product_id,
                        movement_date=reissue_date,
                        movement_type="supplier_replacement",
                        quantity=dmg.quantity,
                        notes=f"Damaged tanks reissued by supplier ({reissued_by}) — added back to full stock"
                    )
                )

            self.refresh_all()
            self.refresh_damages()
            QMessageBox.information(self, "Success", f"Reissuance recorded successfully! Replaced by: {reissued_by}")

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not process replacement:\n{exc}")

    def open_record_expense_dialog(self):
        dialog = RecordExpenseDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        category = dialog.category_box.currentText()
        amount_centavos = round(dialog.amount_box.value() * 100)
        exp_date = datetime.combine(
            dialog.date_box.date().toPython(),
            datetime.min.time()
        )
        remarks = dialog.remarks_box.text().strip()

        try:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        CREATE TABLE IF NOT EXISTS expenses (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            category VARCHAR,
                            description VARCHAR,
                            amount_centavos INTEGER,
                            expense_date DATETIME,
                            remarks VARCHAR
                        );
                    """)
                )
                conn.execute(
                    text("""
                        INSERT INTO expenses (category, description, amount_centavos, expense_date, remarks)
                        VALUES (:cat, :desc, :amt, :dt, :rem);
                    """),
                    {
                        "cat": category,
                        "desc": category,
                        "amt": amount_centavos,
                        "dt": exp_date,
                        "rem": remarks
                    }
                )

            self.refresh_reports()
            QMessageBox.information(
                self, "Success",
                f"Expense recorded successfully!\n₱{amount_centavos/100:,.2f} deducted for '{category}'."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not record expense:\n{exc}")

    # -----------------------------------------------------
    # INITIAL STOCK DECLARATION
    # -----------------------------------------------------

    def set_opening_stock(self):
        with Session() as session:
            products = session.scalars(
                select(Product)
                .where(Product.active == 1)
                .order_by(Product.name)
            ).all()
            choices = [p.name for p in products]

        if not choices:
            QMessageBox.warning(
                self, "No products",
                "No active LPG products were found."
            )
            return

        brand, accepted = QInputDialog.getItem(
            self, "Opening Stock", "Select LPG brand:",
            choices, 0, False
        )

        if not accepted:
            return

        with Session() as session:
            product = session.scalar(
                select(Product).where(Product.name == brand)
            )
            if product is None:
                QMessageBox.warning(
                    self, "Product not found",
                    "The selected product could not be found."
                )
                return

            product_id = product.id

            balance = session.scalar(
                select(InventoryBalance).where(
                    InventoryBalance.product_id == product_id
                )
            )

            current = {
                "full_qty": balance.full_qty,
                "empty_qty": balance.empty_qty,
                "damaged_qty": balance.damaged_qty,
                "customer_qty": balance.customer_qty,
            }

            already_declared = session.scalar(
                select(InventoryMovement.id).where(
                    InventoryMovement.product_id == product_id,
                    InventoryMovement.movement_type.in_([
                        "opening_stock_declaration",
                        "opening_stock_adjustment",
                    ])
                ).limit(1)
            )

        if already_declared is not None:
            QMessageBox.warning(
                self,
                "Opening Stock Already Recorded",
                f"An opening-stock record already exists for {brand}.\n\n"
                "To avoid overwriting inventory, this action is blocked. "
                "Use New Stock / Buy for incoming cylinders."
            )
            return

        labels = [
            ("Full cylinders", "full_qty"),
            ("Empty cylinders", "empty_qty"),
            ("Damaged cylinders", "damaged_qty"),
            ("With customers", "customer_qty"),
        ]

        quantities = {}

        for label, field in labels:
            value, accepted = QInputDialog.getInt(
                self,
                "Opening Stock",
                f"{brand} — {label}:",
                current[field],
                0,
                1000000,
                1,
            )

            if not accepted:
                return

            quantities[field] = value

        confirm = QMessageBox.question(
            self,
            "Confirm Opening Stock",
            f"Declare initial stock for {brand}?\n\n"
            f"Full: {quantities['full_qty']}\n"
            f"Empty: {quantities['empty_qty']}\n"
            f"Damaged: {quantities['damaged_qty']}\n"
            f"With customers: {quantities['customer_qty']}\n\n"
            "This should be the initial physical count only.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            with Session.begin() as session:
                existing = session.scalar(
                    select(InventoryMovement.id).where(
                        InventoryMovement.product_id == product_id,
                        InventoryMovement.movement_type.in_([
                            "opening_stock_declaration",
                            "opening_stock_adjustment",
                        ])
                    ).limit(1)
                )

                if existing is not None:
                    raise ValueError(
                        "Opening stock has already been declared."
                    )

                balance = session.scalar(
                    select(InventoryBalance).where(
                        InventoryBalance.product_id == product_id
                    )
                )

                previous = {
                    "full": balance.full_qty,
                    "empty": balance.empty_qty,
                    "damaged": balance.damaged_qty,
                    "customer": balance.customer_qty,
                }

                for field, value in quantities.items():
                    setattr(balance, field, value)

                balance.updated_at = datetime.now()

                session.add(
                    InventoryMovement(
                        product_id=product_id,
                        movement_date=datetime.now(),
                        movement_type="opening_stock_declaration",
                        quantity=sum(quantities.values()),
                        notes=(
                            f"Initial stock declaration; "
                            f"previous={previous}; "
                            f"declared={quantities}"
                        ),
                    )
                )

            self.refresh_all()

            QMessageBox.information(
                self, "Saved",
                f"Initial stock for {brand} was saved."
            )

        except Exception as exc:
            QMessageBox.critical(
                self, "Database Error",
                f"Could not declare opening stock:\n{exc}"
            )

    # -----------------------------------------------------
    # NEW STOCK / BUY
    # -----------------------------------------------------

    def open_new_stock_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("New Stock / Buy")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(16)

        brand_box = QComboBox()

        quantity_box = QSpinBox()
        quantity_box.setRange(1, 1000000)
        quantity_box.setValue(1)

        price_box = QDoubleSpinBox()
        price_box.setRange(0.01, 1000000)
        price_box.setDecimals(2)
        price_box.setPrefix("₱ ")
        price_box.setValue(800.00)

        date_box = QDateEdit()
        date_box.setCalendarPopup(True)
        date_box.setDisplayFormat("dd MMM yyyy")
        date_box.setDate(QDate.currentDate())

        supplier_box = QLineEdit()
        supplier_box.setPlaceholderText("Supplier name")

        invoice_box = QLineEdit()
        invoice_box.setPlaceholderText("Optional invoice number")

        form.addRow("LPG brand:", brand_box)
        form.addRow("Quantity received:", quantity_box)
        form.addRow("Cost per cylinder:", price_box)
        form.addRow("Purchase date:", date_box)
        form.addRow("Supplier:", supplier_box)
        form.addRow("Invoice number:", invoice_box)

        layout.addLayout(form)

        total_label = QLabel()
        total_label.setStyleSheet(
            "font-size: 16pt; font-weight: 900; color: #2563EB;"
        )
        layout.addWidget(total_label)

        def update_total(*args):
            total = quantity_box.value() * price_box.value()
            total_label.setText(f"Total purchase: ₱{total:,.2f}")

        quantity_box.valueChanged.connect(update_total)
        price_box.valueChanged.connect(update_total)
        update_total()

        with Session() as session:
            products = session.scalars(
                select(Product)
                .where(Product.active == 1)
                .order_by(Product.name)
            ).all()

            for product in products:
                brand_box.addItem(product.name, product.id)

        if brand_box.count() == 0:
            QMessageBox.warning(
                self, "No products",
                "There are no active LPG products to purchase."
            )
            return

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        product_id = brand_box.currentData()
        quantity = quantity_box.value()
        unit_cost_centavos = round(price_box.value() * 100)
        total_centavos = quantity * unit_cost_centavos

        selected_date = datetime.combine(
            date_box.date().toPython(),
            datetime.min.time()
        )

        supplier = supplier_box.text().strip() or "Unspecified"
        invoice_no = invoice_box.text().strip()

        confirm = QMessageBox.question(
            self,
            "Confirm Purchase",
            f"Brand: {brand_box.currentText()}\n"
            f"Quantity: {quantity}\n"
            f"Cost per cylinder: "
            f"₱{unit_cost_centavos / 100:,.2f}\n"
            f"Total: ₱{total_centavos / 100:,.2f}\n"
            f"Supplier: {supplier}\n"
            f"Purchase date: {selected_date:%d %b %Y}\n\n"
            "Save this purchase and deduct cash from business funds?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            with Session.begin() as session:
                product = session.get(Product, product_id)

                if product is None or not product.active:
                    raise ValueError(
                        "The selected product is unavailable."
                    )

                balance = session.scalar(
                    select(InventoryBalance).where(
                        InventoryBalance.product_id == product_id
                    )
                )

                if balance is None:
                    raise ValueError(
                        "Inventory balance was not found."
                    )

                purchase = Purchase(
                    supplier_name=supplier,
                    invoice_no=invoice_no,
                    invoice_date=selected_date,
                    received_date=selected_date,
                    total_centavos=total_centavos,
                    paid_centavos=total_centavos,
                )

                session.add(purchase)
                session.flush()

                session.add(
                    PurchaseItem(
                        purchase_id=purchase.id,
                        product_id=product_id,
                        quantity=quantity,
                        unit_cost_centavos=unit_cost_centavos,
                    )
                )

                balance.full_qty += quantity
                balance.updated_at = datetime.now()

                session.add(
                    InventoryMovement(
                        product_id=product_id,
                        movement_date=selected_date,
                        movement_type="stock_purchase",
                        quantity=quantity,
                        notes=(
                            f"Purchase #{purchase.id}; "
                            f"supplier={supplier}; "
                            f"invoice={invoice_no}; "
                            f"unit_cost_centavos={unit_cost_centavos}; "
                            f"total_centavos={total_centavos}"
                        ),
                    )
                )

            self.refresh_all()

            QMessageBox.information(
                self,
                "Purchase Saved & Cash Deducted",
                f"Purchase #{purchase.id} saved successfully.\n\n"
                f"₱{total_centavos/100:,.2f} deducted from business funds.\n"
                f"{quantity} {brand_box.currentText()} cylinder(s) added to full stock."
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Purchase Error",
                "The purchase could not be saved.\n\n"
                f"{exc}\n\n"
                "Your purchase and stock changes were rolled back."
            )

    # -----------------------------------------------------
    # CUSTOMER TRANSACTION / EXCHANGES
    # -----------------------------------------------------

    def open_customer_transaction_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("New Customer Transaction")
        dialog.setMinimumWidth(540)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(16)

        type_box = QComboBox()
        type_box.addItems([
            "Gas Exchange", "Borrowed Tank", "Permanent Cylinder Sale"
        ])

        brand_box = QComboBox()

        qty_box = QSpinBox()
        qty_box.setRange(1, 1000000)
        qty_box.setValue(1)

        price_box = QDoubleSpinBox()
        price_box.setRange(0.01, 1000000)
        price_box.setDecimals(2)
        price_box.setPrefix("₱ ")
        price_box.setValue(1000.00)

        date_box = QDateEdit()
        date_box.setCalendarPopup(True)
        date_box.setDisplayFormat("dd MMM yyyy")
        date_box.setDate(QDate.currentDate())

        customer_name_box = QLineEdit()
        customer_name_box.setPlaceholderText("Customer full name")

        customer_phone_box = QLineEdit()
        customer_phone_box.setPlaceholderText("Optional phone number")

        customer_address_box = QLineEdit()
        customer_address_box.setPlaceholderText("Optional customer address")

        map_layout = QHBoxLayout()
        customer_map_box = QLineEdit()
        customer_map_box.setPlaceholderText("Click '🛰️ Satellite Pin' to view rooftops")
        
        pick_map_btn = make_button("🛰️ Satellite Pin", "secondary")
        
        def open_txn_map_picker():
            picker = MapPickerDialog(customer_map_box.text(), dialog)
            if picker.exec() == QDialog.DialogCode.Accepted and picker.selected_link:
                customer_map_box.setText(picker.selected_link)

        pick_map_btn.clicked.connect(open_txn_map_picker)
        map_layout.addWidget(customer_map_box, 1)
        map_layout.addWidget(pick_map_btn)

        with Session() as session:
            customers_db = session.scalars(
                select(Customer).order_by(Customer.name)
            ).all()

        customer_dict = {c.name: (c.phone or "", c.address or "", c.map_link or "") for c in customers_db}
        existing_customer_names = list(customer_dict.keys())

        customer_completer = QCompleter(existing_customer_names, customer_name_box)
        customer_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        customer_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        customer_name_box.setCompleter(customer_completer)

        def on_customer_selected(name):
            if name in customer_dict:
                phone, address, map_link = customer_dict[name]
                if phone:
                    customer_phone_box.setText(phone)
                if address:
                    customer_address_box.setText(address)
                if map_link:
                    customer_map_box.setText(map_link)

        customer_completer.activated.connect(on_customer_selected)
        customer_name_box.editingFinished.connect(lambda: on_customer_selected(customer_name_box.text().strip()))

        paid_box = QDoubleSpinBox()
        paid_box.setRange(0.00, 1000000)
        paid_box.setDecimals(2)
        paid_box.setPrefix("₱ ")
        paid_box.setValue(1000.00)

        remarks_box = QLineEdit()
        remarks_box.setPlaceholderText("Optional remarks or notes")

        form.addRow("Transaction type:", type_box)
        form.addRow("LPG brand:", brand_box)
        form.addRow("Quantity:", qty_box)
        form.addRow("Unit selling price:", price_box)
        form.addRow("Transaction date:", date_box)
        form.addRow("Customer name:", customer_name_box)
        form.addRow("Customer phone:", customer_phone_box)
        form.addRow("Customer address:", customer_address_box)
        form.addRow("Google Maps Pin:", map_layout)
        form.addRow("Amount paid:", paid_box)
        form.addRow("Remarks:", remarks_box)

        layout.addLayout(form)

        summary_label = QLabel()
        summary_label.setStyleSheet(
            "font-size: 13pt; font-weight: 800; color: #2563EB;"
        )
        layout.addWidget(summary_label)

        with Session() as session:
            products = session.scalars(
                select(Product)
                .where(Product.active == 1)
                .order_by(Product.name)
            ).all()
            for p in products:
                default_price = (
                    p.selling_price_centavos / 100
                    if p.selling_price_centavos > 0 else 1000.00
                )
                brand_box.addItem(p.name, (p.id, default_price))

        def on_brand_changed(index):
            data = brand_box.currentData()
            if data:
                _, default_price = data
                price_box.setValue(default_price)
                update_calculations()

        def update_calculations(*args):
            total = qty_box.value() * price_box.value()
            paid_box.setMaximum(total)
            if paid_box.value() > total:
                paid_box.setValue(total)
            balance = total - paid_box.value()
            summary_label.setText(
                f"Total: ₱{total:,.2f}  |  "
                f"Paid: ₱{paid_box.value():,.2f}  |  "
                f"Balance: ₱{balance:,.2f}"
            )

        brand_box.currentIndexChanged.connect(on_brand_changed)
        qty_box.valueChanged.connect(update_calculations)
        price_box.valueChanged.connect(update_calculations)
        paid_box.valueChanged.connect(update_calculations)

        if brand_box.count() > 0:
            on_brand_changed(0)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        txn_type = type_box.currentText()
        brand_data = brand_box.currentData()
        if not brand_data:
            QMessageBox.warning(self, "Error", "No product selected.")
            return

        product_id, _ = brand_data
        quantity = qty_box.value()
        unit_price_centavos = round(price_box.value() * 100)
        total_centavos = quantity * unit_price_centavos
        paid_centavos = round(paid_box.value() * 100)

        if paid_centavos > total_centavos:
            QMessageBox.warning(
                self, "Invalid Payment",
                "Amount paid cannot exceed total amount."
            )
            return

        selected_date = datetime.combine(
            date_box.date().toPython(),
            datetime.min.time()
        )
        cust_name = customer_name_box.text().strip()
        if not cust_name:
            QMessageBox.warning(
                self, "Missing Information",
                "Customer name is required."
            )
            return

        cust_phone = customer_phone_box.text().strip()
        cust_address = customer_address_box.text().strip()
        cust_map = customer_map_box.text().strip()
        remarks = remarks_box.text().strip()

        if paid_centavos >= total_centavos:
            payment_status = "Paid"
        elif paid_centavos > 0:
            payment_status = "Partial"
        else:
            payment_status = "Unpaid"

        try:
            with Session.begin() as session:
                balance = session.scalar(
                    select(InventoryBalance).where(
                        InventoryBalance.product_id == product_id
                    )
                )
                if balance is None or balance.full_qty < quantity:
                    available = balance.full_qty if balance else 0
                    raise ValueError(
                        f"Insufficient full stock. "
                        f"Available: {available}, requested: {quantity}."
                    )

                customer = session.scalar(
                    select(Customer).where(Customer.name.ilike(cust_name))
                )
                if customer is None:
                    customer = Customer(
                        name=cust_name,
                        phone=cust_phone,
                        address=cust_address,
                        map_link=cust_map,
                        credit_limit_centavos=0,
                        created_at=datetime.now()
                    )
                    session.add(customer)
                    session.flush()
                else:
                    if cust_phone and not customer.phone:
                        customer.phone = cust_phone
                    if cust_address and not customer.address:
                        customer.address = cust_address
                    if cust_map:
                        customer.map_link = cust_map

                exchange = Exchange(
                    customer_id=customer.id,
                    product_id=product_id,
                    transaction_type=txn_type,
                    quantity=quantity,
                    unit_selling_price_centavos=unit_price_centavos,
                    total_centavos=total_centavos,
                    paid_centavos=paid_centavos,
                    payment_status=payment_status,
                    transaction_date=selected_date,
                    remarks=remarks,
                    status="Active"
                )
                session.add(exchange)
                session.flush()

                exchange.transaction_no = f"TXN-{exchange.id:04d}"

                if paid_centavos > 0:
                    session.add(
                        Payment(
                            exchange_id=exchange.id,
                            customer_id=customer.id,
                            amount_centavos=paid_centavos,
                            payment_date=selected_date,
                            remarks="Initial payment upon transaction"
                        )
                    )

                balance.full_qty -= quantity
                movement_type = ""
                if txn_type == "Gas Exchange":
                    balance.empty_qty += quantity
                    movement_type = "customer_exchange"
                elif txn_type == "Borrowed Tank":
                    balance.customer_qty += quantity
                    movement_type = "borrowed_tank"
                elif txn_type == "Permanent Cylinder Sale":
                    movement_type = "permanent_sale"

                balance.updated_at = datetime.now()

                session.add(
                    InventoryMovement(
                        product_id=product_id,
                        movement_date=selected_date,
                        movement_type=movement_type,
                        quantity=quantity,
                        notes=(
                            f"Transaction {exchange.transaction_no} "
                            f"({txn_type}); Customer: {cust_name}; "
                            f"Qty: {quantity}; Total: ₱{total_centavos/100:,.2f}"
                        )
                    )
                )

            self.refresh_all()
            self.refresh_exchanges()
            self.refresh_customers()

            QMessageBox.information(
                self, "Success",
                f"Customer transaction {exchange.transaction_no} "
                "recorded successfully!"
            )

        except Exception as exc:
            QMessageBox.critical(
                self, "Transaction Error",
                f"Could not complete transaction:\n{exc}"
            )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":
    try:
        initialize_database()
    except Exception as exc:
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Database Initialization Error",
            f"The database could not be initialized:\n\n{exc}\n\n"
            "No database reset was attempted."
        )
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(get_app_stylesheet(13))

    window = LPGManager()
    window.show()

    sys.exit(app.exec())