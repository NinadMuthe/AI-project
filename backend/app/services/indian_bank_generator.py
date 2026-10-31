# backend/app/services/indian_bank_generator.py
"""
Generates realistic Indian banking data for a salaried professional.
Seeded by user_id so each user gets distinct, realistic financial history.
Covers 140+ days (4-5 months) ending today, with ~150-250 transactions,
including 4-6 marked anomalies and realistic Indian spending rhythms.
"""
import random
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

INDIAN_BANKS = [
    ("HDFC Bank", "HDFC Regular Savings A/C", "50100"),
    ("ICICI Bank", "ICICI Privilege Savings A/C", "10450"),
    ("State Bank of India", "SBI Classic Savings A/C", "30890"),
    ("Axis Bank", "Axis Liberty Savings A/C", "91201"),
    ("Kotak Mahindra Bank", "Kotak 811 Edge Savings A/C", "41500"),
]

EMPLOYERS = [
    "INFOSYS TECHNOLOGIES LTD",
    "TATA CONSULTANCY SERVICES",
    "WIPRO ENTERPRISES",
    "TECH MAHINDRA LTD",
    "RAZORPAY SOFTWARE PVT",
    "SWIGGY TECH LABS",
    "FLIPKART INTERNET PVT",
]

def map_indian_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["salary", "cashback", "refund", "upi received", "dividend"]):
        return "Income"
    if any(k in t for k in ["rent", "landlord", "flat rent", "house rent"]):
        return "Rent"
    if any(k in t for k in ["zerodha", "sip", "mutual fund", "groww", "investment", "uti mf"]):
        return "Investments"
    if any(k in t for k in ["netflix", "spotify", "hotstar", "youtube", "cult.fit", "gym"]):
        return "Subscriptions"
    if any(k in t for k in ["bescom", "tatapower", "electricity", "jio", "airtel", "broadband", "water bill", "indraprastha gas", "cylinder"]):
        return "Bills & Utilities"
    if any(k in t for k in ["swiggy", "zomato", "cafe", "chai", "coffee", "restaurant", "canteen", "darshini", "bhojanalaya", "dhaba", "barbeque"]):
        return "Food & Dining"
    if any(k in t for k in ["blinkit", "zepto", "bigbasket", "dmart", "kirana", "vegetable", "milk", "mother dairy", "nature basket"]):
        return "Groceries"
    if any(k in t for k in ["uber", "ola", "rapido", "metro", "petrol", "fuel", "hpcl", "bpcl", "irctc", "redbus", "auto fare"]):
        return "Transport"
    if any(k in t for k in ["amazon", "flipkart", "myntra", "croma", "reliance digital", "zara", "h&m", "decathlon", "ajio", "shopping"]):
        return "Shopping"
    if any(k in t for k in ["apollo", "1mg", "pharmacy", "doctor", "clinic", "lab", "hospital", "medplus", "netmeds"]):
        return "Health"
    if any(k in t for k in ["coursera", "udemy", "tuition", "books", "course", "education"]):
        return "Education"
    if any(k in t for k in ["pvr", "inox", "bookmyshow", "gaming", "amusement"]):
        return "Entertainment"
    return "Others"

def infer_payment_mode(text: str) -> str:
    t = text.upper()
    if "AUTO-DEBIT" in t or "NACH" in t or "ECS" in t:
        return "Auto-debit"
    if "CARD" in t or "POS" in t:
        return "Card"
    if "NET BANKING" in t or "NEFT" in t or "IMPS" in t or "SALARY" in t:
        return "Net Banking"
    if "CASH" in t:
        return "Cash"
    return "UPI"

def generate_indian_transactions(user_id: int) -> Dict[str, Any]:
    rng = random.Random(user_id * 777 + 101)
    bank_info = INDIAN_BANKS[user_id % len(INDIAN_BANKS)]
    employer = EMPLOYERS[user_id % len(EMPLOYERS)]

    # Persona salary and rent based on user
    base_salary = rng.choice([42000, 55000, 68000, 75000, 85000])
    base_rent = rng.choice([11000, 14500, 18000, 22000, 26000])
    sip_amount = rng.choice([2500, 5000, 7500, 10000])

    today = date.today()
    days_back = 145  # ~4.8 months of continuous history
    start_date = today - timedelta(days=days_back)

    transactions = []
    running_balance = 50000.0 + (user_id % 5) * 5000.0

    current_date = start_date
    tx_counter = 1

    # Placeholders for 5 specific anomalies to inject across the period
    anomaly_days = {
        days_back - 20: ("UPI/Croma Electronics/LED_TV", 48999.00, "Shopping", "Card", "₹48,999 is far above your usual Shopping spend of about ₹1,800"),
        days_back - 45: ("UPI/UnknownContact/LATE_NIGHT_TRANSFER", 18500.00, "Others", "UPI", "Unusual late-night transfer of ₹18,500 to an unverified recipient"),
        days_back - 70: ("UPI/Swiggy/DUPLICATE_ORDER_9918", 850.00, "Food & Dining", "UPI", "Possible duplicate charge of ₹850 detected within 2 minutes"),
        days_back - 95: ("UPI/BESCOM Electricity/SURCHARGE_BILL", 7850.00, "Bills & Utilities", "UPI", "Electricity bill of ₹7,850 is 4x higher than your 2-month average of ₹1,400"),
        days_back - 120: ("POS/Taj Gateway Weekend/DINNER", 14500.00, "Food & Dining", "Card", "Dining expense of ₹14,500 significantly exceeds usual dining range"),
    }

    month_tracker = set()

    while current_date <= today:
        day_str = current_date.isoformat()
        day_of_month = current_date.day
        weekday = current_date.weekday()  # 5=Sat, 6=Sun
        month_key = (current_date.year, current_date.month)

        # 1. Salary Credit on the 1st
        if day_of_month == 1:
            ref = 100000 + tx_counter
            desc = f"SALARY CREDIT/{employer}/REF{ref}"
            transactions.append({
                "amount": -float(base_salary),  # Plaid convention: negative = credit
                "display_amount": float(base_salary),
                "type": "income",
                "category": "Income",
                "merchant": employer.split()[0],
                "description": desc,
                "date": day_str,
                "payment_mode": "Net Banking",
                "is_anomaly": False,
                "anomaly_score": None,
                "anomaly_reason": None,
                "plaid_id": f"plaid_in_{user_id}_{tx_counter}",
            })
            running_balance += base_salary
            tx_counter += 1

        # 2. Rent on the 5th
        if day_of_month == 5:
            ref = 200000 + tx_counter
            desc = f"UPI/HouseRent/LANDLORD_{user_id}_REF{ref}"
            transactions.append({
                "amount": float(base_rent),
                "display_amount": float(base_rent),
                "type": "expense",
                "category": "Rent",
                "merchant": "Landlord",
                "description": desc,
                "date": day_str,
                "payment_mode": "UPI",
                "is_anomaly": False,
                "anomaly_score": None,
                "anomaly_reason": None,
                "plaid_id": f"plaid_in_{user_id}_{tx_counter}",
            })
            running_balance -= base_rent
            tx_counter += 1

        # 3. Monthly SIP Investment on the 10th
        if day_of_month == 10:
            desc = f"AUTO-DEBIT/ZERODHA COIN SIP/UTI NIFTY 50"
            transactions.append({
                "amount": float(sip_amount),
                "display_amount": float(sip_amount),
                "type": "expense",
                "category": "Investments",
                "merchant": "Zerodha",
                "description": desc,
                "date": day_str,
                "payment_mode": "Auto-debit",
                "is_anomaly": False,
                "anomaly_score": None,
                "anomaly_reason": None,
                "plaid_id": f"plaid_in_{user_id}_{tx_counter}",
            })
            running_balance -= sip_amount
            tx_counter += 1

        # 4. Utilities / Bills on 12th & 16th
        if day_of_month == 12:
            recharge = rng.choice([399.0, 699.0, 899.0, 999.0])
            desc = f"UPI/JioFiber Broadband/INV_{tx_counter}"
            transactions.append({
                "amount": recharge,
                "display_amount": recharge,
                "type": "expense",
                "category": "Bills & Utilities",
                "merchant": "Jio Fiber",
                "description": desc,
                "date": day_str,
                "payment_mode": "UPI",
                "is_anomaly": False,
                "anomaly_score": None,
                "anomaly_reason": None,
                "plaid_id": f"plaid_in_{user_id}_{tx_counter}",
            })
            running_balance -= recharge
            tx_counter += 1

        if day_of_month == 16 and (current_date.month % 2 == 0):
            elec = rng.choice([840.0, 1150.0, 1420.0, 1850.0])
            desc = f"UPI/Bescom Electricity Bill/RR_0921"
            transactions.append({
                "amount": elec,
                "display_amount": elec,
                "type": "expense",
                "category": "Bills & Utilities",
                "merchant": "BESCOM",
                "description": desc,
                "date": day_str,
                "payment_mode": "UPI",
                "is_anomaly": False,
                "anomaly_score": None,
                "anomaly_reason": None,
                "plaid_id": f"plaid_in_{user_id}_{tx_counter}",
            })
            running_balance -= elec
            tx_counter += 1

        # 5. Fixed monthly subscriptions on the 18th
        if day_of_month == 18:
            subs = [
                ("UPI/Netflix India/SUB_MTH", 499.0, "Netflix"),
                ("UPI/Spotify India/PREMIUM", 119.0, "Spotify"),
                ("AUTO-DEBIT/Cult.Fit Gym Membership", 1800.0, "Cult.Fit"),
            ]
            for s_desc, s_amt, s_mer in subs:
                transactions.append({
                    "amount": s_amt,
                    "display_amount": s_amt,
                    "type": "expense",
                    "category": "Subscriptions",
                    "merchant": s_mer,
                    "description": s_desc,
                    "date": day_str,
                    "payment_mode": "Auto-debit" if "AUTO-DEBIT" in s_desc else "UPI",
                    "is_anomaly": False,
                    "anomaly_score": None,
                    "anomaly_reason": None,
                    "plaid_id": f"plaid_in_{user_id}_{tx_counter}",
                })
                running_balance -= s_amt
                tx_counter += 1

        # 6. Check for injected anomaly
        day_offset = (current_date - start_date).days
        if day_offset in anomaly_days:
            a_desc, a_amt, a_cat, a_mode, a_reason = anomaly_days[day_offset]
            transactions.append({
                "amount": a_amt,
                "display_amount": a_amt,
                "type": "expense",
                "category": a_cat,
                "merchant": a_desc.split("/")[1] if "/" in a_desc else "Merchant",
                "description": a_desc,
                "date": day_str,
                "payment_mode": a_mode,
                "is_anomaly": True,
                "anomaly_score": 0.88,
                "anomaly_reason": a_reason,
                "plaid_id": f"plaid_in_{user_id}_{tx_counter}",
            })
            running_balance -= a_amt
            tx_counter += 1

        # 7. Occasional small credits (cashback, UPI from friend, refund)
        if rng.random() < 0.08:
            credit_type = rng.choice([
                ("UPI/GooglePay Cashback/ScratchCard", rng.choice([25.0, 50.0, 100.0, 150.0]), "Income"),
                ("UPI/Aakash Verma/SPLIT_DINNER", rng.choice([350.0, 620.0, 1200.0]), "Income"),
                ("REFUND/Amazon Pay Balance", rng.choice([199.0, 449.0, 899.0]), "Income"),
            ])
            transactions.append({
                "amount": -credit_type[1],
                "display_amount": credit_type[1],
                "type": "income",
                "category": "Income",
                "merchant": credit_type[0].split("/")[1] if "/" in credit_type[0] else "Refund",
                "description": credit_type[0],
                "date": day_str,
                "payment_mode": "UPI",
                "is_anomaly": False,
                "anomaly_score": None,
                "anomaly_reason": None,
                "plaid_id": f"plaid_in_{user_id}_{tx_counter}",
            })
            running_balance += credit_type[1]
            tx_counter += 1

        # 8. Daily life activity (35-40% of days have 2-5 transactions)
        prob = 0.40 if weekday >= 5 else 0.35
        # Month-end slightly tighter spending (days 24-28)
        if 24 <= day_of_month <= 28:
            prob *= 0.75

        if rng.random() < prob:
            num_txs = rng.choice([2, 3, 4] if weekday < 5 else [2, 3, 5])
            for _ in range(num_txs):
                choice = rng.choice(["food", "groceries", "transport", "shopping", "health"])
                if choice == "food":
                    if weekday >= 5 and rng.random() < 0.4:
                        # Weekend restaurant
                        amt = rng.choice([650.0, 890.0, 1250.0, 1850.0, 2400.0])
                        mer = rng.choice(["Toscano Italian", "Barbeque Nation", "Empire Restaurant", "Meghana Foods"])
                        desc = f"UPI/{mer}/DINNER_BILL"
                    else:
                        amt = rng.choice([40.0, 60.0, 120.0, 189.0, 249.0, 340.0, 480.0])
                        mer = rng.choice(["Swiggy", "Zomato", "Chai Point", "Starbucks Coffee", "Third Wave Coffee", "A2B Bhavan"])
                        desc = f"UPI/{mer}/ORD_{rng.randint(1000, 9999)}"
                    cat = "Food & Dining"
                    mode = "UPI"
                elif choice == "groceries":
                    if rng.random() < 0.4:
                        amt = rng.choice([650.0, 1280.0, 1850.0, 2490.0])
                        mer = rng.choice(["Blinkit", "Zepto", "BigBasket", "DMart Supermarket"])
                        desc = f"UPI/{mer}/GROC_ORDER"
                    else:
                        amt = rng.choice([35.0, 65.0, 95.0, 140.0])
                        mer = rng.choice(["Local Kirana Store", "Mother Dairy Milk", "Fresh Veggie Cart"])
                        desc = f"UPI/{mer}/DAILY_PURCHASE"
                    cat = "Groceries"
                    mode = "UPI"
                elif choice == "transport":
                    if rng.random() < 0.2:
                        amt = rng.choice([500.0, 1000.0, 1500.0, 2000.0])
                        mer = rng.choice(["HPCL Petrol Pump", "Indian Oil Station", "Shell Fuel Station"])
                        desc = f"POS/{mer}/FUEL"
                        mode = "Card"
                    else:
                        amt = rng.choice([45.0, 85.0, 140.0, 220.0, 360.0])
                        mer = rng.choice(["Uber India", "Ola Cabs", "Rapido Bike", "Namma Metro Card Recharge"])
                        desc = f"UPI/{mer}/RIDE_{rng.randint(100, 999)}"
                        mode = "UPI"
                    cat = "Transport"
                elif choice == "shopping":
                    amt = rng.choice([499.0, 899.0, 1299.0, 2499.0, 3499.0])
                    mer = rng.choice(["Amazon India", "Flipkart", "Myntra Fashion", "Decathlon Sports", "Ajio Fashion"])
                    desc = f"UPI/{mer}/ORDER_{rng.randint(10000, 99999)}"
                    cat = "Shopping"
                    mode = "UPI"
                else:  # health
                    amt = rng.choice([85.0, 190.0, 340.0, 680.0, 1250.0])
                    mer = rng.choice(["Apollo Pharmacy", "Tata 1mg", "Medplus Chemists", "Practo Consultation"])
                    desc = f"UPI/{mer}/MED_{rng.randint(100, 999)}"
                    cat = "Health"
                    mode = "UPI"

                transactions.append({
                    "amount": amt,
                    "display_amount": amt,
                    "type": "expense",
                    "category": cat,
                    "merchant": mer,
                    "description": desc,
                    "date": day_str,
                    "payment_mode": mode,
                    "is_anomaly": False,
                    "anomaly_score": None,
                    "anomaly_reason": None,
                    "plaid_id": f"plaid_in_{user_id}_{tx_counter}",
                })
                running_balance -= amt
                tx_counter += 1

        current_date += timedelta(days=1)

    return {
        "bank_name": bank_info[0],
        "account_name": bank_info[1],
        "account_number": f"{bank_info[2]}{rng.randint(1000000, 9999999)}",
        "current_balance": max(round(running_balance, 2), 15000.0),
        "transactions": transactions,
    }

