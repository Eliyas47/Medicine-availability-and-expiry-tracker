# Frontend Page & Component Plan
## Medicine Availability & Expiry Tracker

---

## 1. Design System

### Color Palette
```
Primary:    #0d9488  (teal-600)   — brand, CTAs, active nav
Secondary:  #0f766e  (teal-700)   — hover states
Accent:     #f59e0b  (amber-500)  — warnings, expiry alerts
Danger:     #ef4444  (red-500)    — errors, expired, delete
Success:    #22c55e  (green-500)  — in-stock, success states
Warning:    #f97316  (orange-500) — low stock
Neutral:    #f8fafc → #0f172a    — slate scale for text/bg
```

### Typography
- Font: Inter (Google Fonts)
- Headings: font-semibold, slate-900
- Body: font-normal, slate-700
- Code/mono: font-mono, slate-600

### Component Library
Base components from `shadcn/ui` (Radix UI primitives + Tailwind):
- Button (primary, secondary, ghost, destructive, outline)
- Input, Textarea, Select, Checkbox, Switch, RadioGroup
- Dialog / AlertDialog (confirmation modals)
- Popover, Tooltip
- Badge (status chips)
- Card
- Table (with sortable headers)
- Tabs
- Sheet (side panel / drawer)
- Toast (via react-hot-toast)
- Skeleton (loading placeholders)
- Progress bar

---

## 2. Layout Components

### `PublicLayout`
- Top navigation bar: Logo, nav links (Home, Search, Login)
- Footer: contact, license, Ethiopian context

### `DashboardLayout`
- Sidebar (collapsible on mobile):
  - Pharmacy logo / name
  - Navigation: Overview, Inventory, Batches, Movements, Expiry, Alerts, Reports
  - Admin section: Medicines, Users, Settings, Audit Logs (conditional on role)
- Top bar: breadcrumb, notification bell (badge count), user menu (profile, logout)
- Main content area with responsive padding

---

## 3. Page Inventory

### 3.1 Public Pages

#### `PublicLandingPage` (`/`)
- Hero section: headline, subheadline, CTA to search
- Features grid (3–4 key benefits)
- How it works (3-step flow)
- Participating pharmacies preview
- Footer

#### `AvailabilitySearchPage` (`/search`)
- Search bar (medicine name, city filter, region filter)
- Results list: `PharmacyAvailabilityCard` per result
  - Pharmacy name, address, phone
  - Medicine name, strength, form
  - Usable quantity badge
  - Last confirmed timestamp + stale warning if applicable
  - Prescription required badge
- Empty state, loading skeleton, error state

### 3.2 Auth Pages

#### `LoginPage` (`/auth/login`)
- Email + password form
- Validation feedback
- "Forgot password?" link (placeholder v1)
- Link to register

#### `RegisterPage` (`/auth/register`)
- Full name, email, phone, password, password confirm
- Role selector (pharmacy_admin / inventory_staff only; system_admin created by admin)
- Submit → on success, redirect to login with success toast

### 3.3 Dashboard Pages (all require auth)

#### `DashboardOverviewPage` (`/dashboard/overview`)
**Widgets (real API data):**
- Stats row: Total Medicines, Active Batches, Low Stock, Expired
- Expiry timeline: This Week / This Month / Within Window / Already Expired
- Chart: Stock by Category (pie or donut)
- Chart: Stock Movements (last 30 days, bar chart)
- Table: Recent Movements (last 10)
- Table: Low Stock Items (top 5)

#### `InventoryPage` (`/dashboard/inventory`)
- Per-medicine summary for this pharmacy
- Columns: Medicine, Category, Form, Usable Qty, Batches, Status, Last Updated
- Filterable by category, status, search
- Click row → expand or navigate to batch list for that medicine
- Export CSV button

#### `BatchListPage` (`/dashboard/batches`)
- Filterable, sortable data table
- Columns: Batch #, Medicine, Quantity, Received, Expiry, Days Left, Status, Supplier, Actions
- Status badge with color coding
- Add Batch button → `BatchFormPage`
- Inline quick-dispense action

#### `BatchFormPage` (`/dashboard/batches/new`, `/dashboard/batches/{id}/edit`)
- Form: Medicine (searchable select), Batch Number, Quantity, Received Date, Expiry Date, Supplier, Unit Cost, Notes
- Validation: expiry date must be future, quantity > 0
- On success: records a `received` movement automatically

#### `MovementsPage` (`/dashboard/movements`)
- Filterable timeline / table
- Filters: medicine, movement type, date range
- Columns: Date, Medicine, Batch, Type, Quantity, Reference, Performed By, Status
- Pending corrections flagged; Approve button for admins
- Record Movement button → `MovementFormModal`
- Export CSV

#### `MovementFormModal` (Dialog)
- Batch selector (filtered to pharmacy's batches)
- Type selector (sold/dispensed/adjustment/correction)
- Quantity, Reference, Notes
- Correction type triggers admin approval workflow

#### `ExpiryPage` (`/dashboard/expiry`)
- Tabs: Expiring Soon | Expired | All
- Table with days-until-expiry countdown, color-coded
- Bulk expired-removal action (creates `expired_removal` movements)
- Configurable warning window display

#### `AlertsPage` (`/dashboard/alerts`)
- Low Stock table: Medicine, Current Qty, Threshold, Shortfall, Recommendation
- Edit threshold inline or via modal
- Sort by severity

#### `ReportsPage` (`/dashboard/reports`)
- Tab per report type: Stock Summary | Expiring | Expired | Movements | Low Stock
- Date range picker, medicine/category filter
- Data table preview
- Export CSV / Print buttons

#### `PharmacyProfilePage` (`/dashboard/pharmacy`)
- Edit form for pharmacy details (admin only)
- Operating hours editor (per-day schedule)
- Staff list with add/remove controls (admin only)
- Expiry warning days + stale stock days config

#### `MedicineCatalogPage` (`/dashboard/medicines`) — admin
- All medicines table
- Add/Edit/Deactivate medicine
- Category management inline

#### `UsersPage` (`/dashboard/users`) — admin
- All users table
- Filter by role, is_active
- Add user, edit role, activate/deactivate

#### `AuditLogPage` (`/dashboard/audit`) — system_admin
- Filterable audit log table
- Columns: Timestamp, User, Action, Model, Object, Changes (expandable), IP

#### `SettingsPage` (`/dashboard/settings`) — system_admin
- System config: expiry warning days, stale stock days, low stock default threshold
- Save with confirmation

#### `UserProfilePage` (`/profile`)
- View/edit own profile
- Change password section

---

## 4. Reusable Components

### Data Display
- `DataTable` — sortable, filterable, paginated table with column config
- `StatusBadge` — batch status color-coded chip
- `StockQtyBadge` — green/orange/red quantity chip
- `ExpiryCountdown` — days remaining with color warning
- `StaleWarning` — inline warning when last_confirmed_at is old
- `EmptyState` — icon + message for empty table/search
- `LoadingSkeleton` — table row skeletons

### Forms
- `SearchInput` — debounced search with clear button
- `DateRangePicker` — start/end date selector
- `MedicineSelect` — async searchable select backed by `/api/medicines/`
- `BatchSelect` — async select backed by `/api/batches/`

### Charts (Recharts)
- `CategoryPieChart` — stock distribution by category
- `MovementsBarChart` — daily movements over time
- `ExpiryTimelineChart` — expiry countdown buckets

### Feedback
- `ConfirmDialog` — reusable "Are you sure?" dialog
- `FormErrorAlert` — inline validation error display
- `PageHeader` — title + subtitle + optional action button
- `Breadcrumb` — route-based breadcrumb

---

## 5. State & Data Fetching

```typescript
// Example TanStack Query usage
const { data, isLoading, error } = useQuery({
  queryKey: ['batches', pharmacyId, filters],
  queryFn: () => batchService.getBatches({ pharmacyId, ...filters }),
  staleTime: 1000 * 60 * 2, // 2 min
})

const mutation = useMutation({
  mutationFn: batchService.createBatch,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['batches'] })
    toast.success('Batch added successfully')
  },
  onError: (err) => {
    toast.error(getApiErrorMessage(err))
  }
})
```

---

## 6. Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| xs | < 640px | Single column; sidebar collapses to bottom nav |
| sm | 640px | |
| md | 768px | Two-column forms |
| lg | 1024px | Sidebar visible; main content full |
| xl | 1280px | Wider tables, charts side by side |

---

## 7. Loading & Error States

Every data-fetching page must handle:
1. **Loading** — skeleton placeholders matching content shape
2. **Empty** — `EmptyState` component with contextual message and action
3. **Error** — error card with message and retry button
4. **Success** — data rendered; mutations show toast

---

## 8. Accessibility Requirements

- All interactive elements have visible focus rings
- Color alone never conveys status (use icons + text alongside color)
- Form fields have associated `<label>` elements
- Tables have `<th scope="col">` headers
- Dialogs trap focus and support Escape key
- Status badges include screen-reader text
- Chart data has accessible fallback table
