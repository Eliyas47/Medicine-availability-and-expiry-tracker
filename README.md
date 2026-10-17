# 💊 Medicine Availability & Expiry Tracker

**A healthcare inventory management platform designed to help pharmacies track medicine availability, monitor expiration dates, and reduce avoidable medicine waste.**

The Medicine Availability & Expiry Tracker is a web-based application designed to help pharmacies manage medicine stock more efficiently. It enables pharmacy staff to monitor available medicines, receive low-stock and expiry alerts, and maintain more accurate inventory records.

The project aims to improve medicine inventory visibility and help patients find pharmacies that have a medicine in stock, based on availability information confirmed by participating pharmacies.

## 🎯 Problem Statement

Pharmacies may face challenges such as:

- Difficulty tracking medicine quantities and expiration dates.
- Medicines expiring before they are sold or used.
- Stock shortages that are not identified early enough.
- Time wasted checking inventory manually.
- Patients visiting multiple pharmacies to find a specific medicine.

This project aims to address these challenges through a centralized, easy-to-use inventory management system.

## ✨ Key Features

### 🏥 Pharmacy Inventory Management
- Add, update, and remove medicine records.
- Store medicine names, categories, batch numbers, quantities, and expiry dates.
- Track stock movements, including incoming and outgoing medicines.
- Search and filter medicines by name, category, or availability.

### ⏰ Expiry Date Monitoring
- Identify medicines approaching their expiration dates.
- Display expired medicines separately from usable stock.
- Generate expiry alerts based on configurable time periods.
- Track medicine batches independently.

### 📦 Low-Stock Alerts
- Configure minimum stock levels for each medicine.
- Notify pharmacy staff when stock falls below the threshold.
- Identify frequently out-of-stock medicines.
- Help staff plan restocking activities.

### 🔎 Medicine Availability Search
- Allow users to search for a medicine by name.
- Display participating pharmacies reporting that the medicine is available.
- Show the last time each pharmacy confirmed its stock information.
- Provide pharmacy contact information for availability confirmation.

*Public availability information is only as reliable as the pharmacy's latest stock update. A listing does not guarantee that the medicine remains available.*

### 📊 Reports and Analytics
- Current inventory summary.
- Low-stock and expired-medicine reports.
- Medicines approaching expiry.
- Stock movement history.
- Exportable inventory reports.

### 🔐 Security and Access Control
- Secure user authentication.
- Role-based access for administrators and pharmacy staff.
- Pharmacy-specific inventory access.
- Audit logs for important stock changes.

## 🛠️ Proposed Technology Stack

| Component | Technology |
|---|---|
| Backend | Django REST Framework |
| Frontend | React.js |
| Programming languages | Python, JavaScript |
| Database | PostgreSQL |
| API communication | REST API |
| Authentication | JWT or secure session authentication |
| Version control | Git and GitHub |
| Testing | Pytest or Django testing tools |
| Deployment | A suitable cloud or VPS provider |

The stack can be adjusted depending on implementation requirements.

## 🏗️ System Architecture

The application follows a client-server architecture:

1. **Frontend:** Provides interfaces for pharmacy staff and medicine searches.
2. **Backend API:** Handles authentication, inventory operations, alerts, and reporting.
3. **Database:** Stores pharmacies, medicine records, batches, stock movements, and users.
4. **Alert service:** Identifies low-stock and approaching-expiry conditions.
5. **Public search interface:** Displays recently confirmed availability information from participating pharmacies.

## 🗃️ Core Data Models

The proposed database includes:

- **User:** Account details, roles, and authentication information.
- **Pharmacy:** Pharmacy name, location, contact information, and status.
- **Medicine:** Generic name, brand name where applicable, category, and relevant medicine details.
- **MedicineBatch:** Batch number, expiry date, and quantity associated with a specific batch.
- **StockMovement:** Records stock received, dispensed, adjusted, or removed.
- **Alert:** Low-stock and expiry notifications.
- **AuditLog:** Records important inventory changes and the responsible user.

Medicine quantities should be tracked by batch so that one expired batch is not incorrectly treated as equivalent to all other stock of the same medicine.

## 🚀 Getting Started

These instructions describe the intended local development setup. They will become fully applicable once the application source code is implemented.

### Prerequisites

Install the following tools:

- Python 3.11 or a compatible version.
- Node.js and npm.
- PostgreSQL.
- Git.

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/medicine-availability-tracker.git
cd medicine-availability-tracker
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Set up the backend

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install backend dependencies after creating the backend's `requirements.txt`:

```bash
pip install -r requirements.txt
```

Once the Django project has been created, configure the database and environment variables, then run:

```bash
python manage.py migrate
python manage.py runserver
```

### 3. Set up the frontend

After creating the React application:

```bash
cd frontend
npm install
npm run dev
```

Configure API URLs and database credentials through environment variables. Do not commit passwords, secret keys, or other credentials to GitHub.

## 🗺️ Development Roadmap

- [ ] Initialize the Django REST Framework backend.
- [ ] Design the PostgreSQL database schema.
- [ ] Implement authentication and role-based permissions.
- [ ] Develop pharmacy and medicine management APIs.
- [ ] Implement batch-level stock tracking.
- [ ] Add expiry and low-stock alerts.
- [ ] Build the React inventory dashboard.
- [ ] Develop public medicine availability search.
- [ ] Add reports and audit logging.
- [ ] Write automated tests.
- [ ] Deploy a working demonstration.
- [ ] Validate the application with participating pharmacies.

## 🧪 Testing Strategy

The project should include tests for:

- Authentication and pharmacy-specific permissions.
- Stock increases, decreases, and adjustments.
- Expiry alerts and expired-stock handling.
- Low-stock thresholds.
- Duplicate or invalid batch records.
- Medicine availability search.
- Audit logging and API validation.

## 🌍 Expected Impact

The project aims to:

- Reduce avoidable medicine waste caused by missed expiry dates.
- Help pharmacy staff maintain more accurate stock records.
- Improve visibility into medicine availability.
- Reduce unnecessary trips when searching for medicines.
- Support more informed inventory and restocking decisions.

These are intended outcomes, not yet measured results. Their effectiveness should be evaluated through pilot testing with real pharmacies.

## 🔒 Important Scope and Safety Considerations

- The system is an inventory and availability tool, not a medical diagnosis or prescribing platform.
- Expired medicines must be clearly flagged and excluded from available stock.
- Availability listings should show when stock was last confirmed.
- The system should not claim that a medicine is approved, authentic, or safe solely because it appears in the database.
- Real-world deployment should follow applicable Ethiopian pharmacy, medicine-handling, data-protection, and regulatory requirements.

## 🤝 Contributing

Contributions are welcome. You can help improve the project through bug reports, feature suggestions, documentation, testing, and pull requests.

1. Fork the repository.
2. Create a feature branch.
3. Make and test your changes.
4. Submit a pull request describing the improvement.

## 👨‍💻 Author

**Eliyas Siyum**

Software Engineer | Backend Development | AI Enthusiast

- GitHub: [@Eliyas47](https://github.com/Eliyas47)

## 📄 License

Choose and add an appropriate open-source license before publishing the project for reuse.

---

**Building technology for practical healthcare challenges in Ethiopia.**
