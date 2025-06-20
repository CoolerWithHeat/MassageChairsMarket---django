# MassageChairsMarket.com – Backend API ⚙️

This is the Django backend powering [https://MassageChairsMarket.com], a full-featured e-commerce platform for massage chairs. Built with **Django**, **Django REST Framework**, and **Django Channels**, this backend handles everything from checkout logic to admin content management and real-time customer analytics.

---

## ⚙️ Tech Stack

- **Django + DRF** – Core API framework
- **Django Channels (WebSockets)** – Real-time customer tracking
- **AWS S3** – File & media storage
- **Stripe API** – Secure payment processing
---

## 🔌 Core Functionalities

- 🛒 Full CRUD API for products, brands, discounts, and orders
- 💳 Secure Stripe Checkout session initiation and webhook handling
- 📦 Admin-only product management, pricing, shipping, and contact controls
- 🔍 Algolia reindexing endpoint (used by frontend separately)
- 📊 Real-time customer session analytics over WebSocket
- 🧾 Customer inquiries, FAQs, and reviews system
- 🔐 Admin authentication and verification endpoints

---

## 🔗 Highlighted API Endpoints

Here are some key endpoints used directly by the frontend:

| Endpoint | Description |
|----------|-------------|
| `POST /serverdestination/VerifyCart/` | Accepts product IDs and returns valid cart items |
| `GET /serverdestination/GetProduct/<int:product_ID>/` | Returns product detail |
| `GET /serverdestination/GetReview/<int:product_id>/` | Returns product reviews |
| `POST /serverdestination/initiate_checkout/` | Creates Stripe Checkout session |
| `GET /serverdestination/FindProduct/` | Search integration entry |
| `GET /serverdestination/HomePageData/` | Fetches data for homepage |
| `POST /serverdestination/RecordInquiry/` | Records a customer question |
| `POST /serverdestination/RegisterCustomer/` | Registers a customer prior to checkout |
| `GET /serverdestination/customer_orders/` | Gets a customer's past orders |
| `GET /serverdestination/order_details/<order_number>/` | Gets order details |

> ℹ️ There are **many more endpoints** supporting admin-side features, FAQs, reviews, contact info, shipping updates, and real-time promotional logic. See the full `urls.py` for complete routing.

---

## 📡 WebSocket Integration

- `WS /serverdestination/analytics/`  
  Used to track:
  - Page visits
  - Session durations
  - Product views
  - Cart activity

WebSocket events are stored in real-time and used for analytics, recommendations, and engagement strategies.

---

## 💳 Stripe Checkout

- `POST /serverdestination/initiate_checkout/`  
  Initiates a Stripe Checkout session with product and user data

- `POST /serverdestination/payment/`  
  General Stripe interaction endpoint

---

## 🧩 Deployment Notes

- ASGI server (Daphne)
- All static and media content stored on **AWS S3**

---

## 👤 Author

**Mansur Davlatov**  
GitHub: [@CoolerWithHeat](https://github.com/CoolerWithHeat)  
