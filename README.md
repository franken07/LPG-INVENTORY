#  LPG Manager & Inventory System

A robust, professional desktop application built with Python, **PySide6 (Qt for Python)**, and **SQLAlchemy** designed specifically for LPG trading businesses. It streamlines daily operations including cylinder stock tracking, customer debt/credit monitoring, satellite house mapping, automated SMS collection reminders, and comprehensive financial reporting.

---

##  Key Features

* **📦 Real-Time Inventory & Stock Control**
  * Track **Full**, **Empty**, **Damaged (Quarantined)**, and **Customer-Held** cylinders independently for each LPG brand (e.g., Regasco, SPI).
  * Enforce strict validation to prevent negative stock levels.
  * Initial stock declaration wizards and dedicated incoming purchase / restocking logs.
* **⇄ Customer Transactions & Credit Tracking**
  * Support for multiple transaction types: **Gas Exchange**, **Borrowed Tank**, and **Permanent Cylinder Sale**.
  * Instant auto-fill and search completers for returning customers.
  * Color-coded balance badges (**Soft Red** for unpaid/credit balances, **Soft Green** for fully paid accounts) to spot receivables instantly across all tables.
* **🛰️ Satellite Rooftop & House Mapping**
  * Integrated **Leaflet.js** map viewer using Esri World Imagery Satellite tiles.
  * Pin customer houses or rooftops directly within the app so delivery drivers can easily locate them via Google Maps links.
* **🔔 Overdue Accounts & Instant SMS Reminders**
  * Automatically categorize outstanding customer credit by aging buckets (<30 days, 30–60 days, 60+ days overdue).
  * One-click **"Copy SMS Reminder"** button that generates polite, localized Tagalog collection messages directly to your clipboard.
* **⚠️ Returns & Damaged Tank Management**
  * Quarantine damaged or rusted tanks, track supplier reissuance, record delivery driver names, and automatically return replacement stock back to active inventory.
* **📊 Periodic Financial Reports & Excel Export**
  * Dynamic weekly or monthly financial breakdowns tracking Gross Revenue, Operating Expenses (fuel, vehicle maintenance, miscellaneous cash outs), Net Profit, and Accounts Receivable (AR).
  * One-click **Export to Excel (.xls)** generating clean, styled presentation workbooks.
* **♿ Accessible UI & Global Font Scaling**
  * Clean modern dark sidebar layout paired with responsive light content cards.
  * Quick font-size adjustment toolbar (`A-`, `Normal`, `Large`, `Extra Large`) built right into the header for maximum readability.

---

## 🛠️ Tech Stack

* **Language:** Python 3.10+
* **GUI Framework:** PySide6 (Qt)
* **Database & ORM:** SQLite via SQLAlchemy
* **Mapping/UI Components:** QtWebEngineWidgets & Leaflet.js

---

## ⚙️ Installation & Setup

### 1. Prerequisites
Ensure you have **Python 3.10 or newer** installed on your computer.

### 2. Clone or Download the Repository
```bash
git clone [https://github.com/YourUsername/LPG-INVENTORY.git](https://github.com/YourUsername/LPG-INVENTORY.git)
cd LPG-INVENTORY
