import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import date

# --- Company Branding ---
COMPANY_NAME = "PrepnPrime Gh"
COMPANY_PHONE = "0244680516"
DASHBOARD_TAGLINE = "Your Beauty Inventory Partner"

st.set_page_config(page_title=f"{COMPANY_NAME} Inventory Dashboard", layout="wide")
st.title(f"{COMPANY_NAME} Inventory Dashboard")
st.markdown(f"<span style='font-size:1.2em;color:#6366f1'><i>{DASHBOARD_TAGLINE}</i></span>", unsafe_allow_html=True)
st.markdown(f"📞 **Contact:** {COMPANY_PHONE}")

# --- Google Sheets public CSV export links ---
INVENTORY_CSV = "https://docs.google.com/spreadsheets/d/1aiukBw220yTYGQjvrb1C0Tc_AsYM4p8EwJ70CWf1vhU/export?format=csv&id=1aiukBw220yTYGQjvrb1C0Tc_AsYM4p8EwJ70CWf1vhU&gid=0"
CUSTOMERS_CSV = "https://docs.google.com/spreadsheets/d/1by2BJB3H40vlggY31TNM-FS7H5TO5z9rQHrDE6lXPX0/export?format=csv&id=1by2BJB3H40vlggY31TNM-FS7H5TO5z9rQHrDE6lXPX0&gid=0"
SALES_CSV = "https://docs.google.com/spreadsheets/d/15qSz8hweToyDIeulHBTUN5dVBNw6tZojC9CxupTgWRk/export?format=csv&id=15qSz8hweToyDIeulHBTUN5dVBNw6tZojC9CxupTgWRk&gid=0"

@st.cache_data(ttl=60)
def get_data(url):
    return pd.read_csv(url)

inventory = get_data(INVENTORY_CSV)
customers = get_data(CUSTOMERS_CSV)
sales = get_data(SALES_CSV)

tabs = st.tabs([
    "Dashboard",
    "Inventory List",
    "All Customers",
    "Receipt Generator",
    "Sales Report"
])

# --- Dashboard ---
with tabs[0]:
    st.header("Dashboard")
    st.metric("Total Products", len(inventory))
    st.metric("Low Stock (< 5)", (inventory['Quantity'] < 5).sum())
    st.metric("Total Customers", len(customers))
    st.metric("Total Sales (Receipts)", len(sales['Receipt No'].unique()) if not sales.empty else 0)
    st.subheader("Low Stock Products")
    st.dataframe(inventory[inventory['Quantity'] < 5])

with tabs[1]:
    st.header("Inventory List")
    search = st.text_input("Search by product, brand or category")
    
    # ---- Highlights/Notifications ----
    # 1. Most Purchased
    if 'Product Name' in sales.columns:
        sales_count = sales.groupby('Product Name')['Quantity'].sum().sort_values(ascending=False)
        most_purchased = sales_count.head(1)
        if not most_purchased.empty:
            st.success(f"🔥 **Best-seller:** {most_purchased.index[0]} (sold {int(most_purchased.values[0])} units)")
    # 2. Running out of stock
    running_low = inventory[inventory['Quantity'] < 5]
    if not running_low.empty:
        names = ', '.join(running_low['Product Name'].astype(str).tolist())
        st.warning(f"⚠️ **Running low:** {names}")
    # 3. Out of stock
    out_stock = inventory[inventory['Quantity'] <= 0]
    if not out_stock.empty:
        names = ', '.join(out_stock['Product Name'].astype(str).tolist())
        st.error(f"❌ **Out of stock:** {names}")

    # ---- Inventory Table ----
    if search:
        mask = inventory.apply(lambda row: search.lower() in str(row).lower(), axis=1)
        show_table = inventory[mask]
    else:
        show_table = inventory

    # Optional: highlight low stock rows (Streamlit native highlight)
    def highlight_low(val):
        color = ""
        try:
            if int(val) < 1:
                color = "background-color: #ffe0e0"  # Red tint for out of stock
            elif int(val) < 5:
                color = "background-color: #fff7d9"  # Yellow tint for low stock
        except Exception:
            pass
        return color

    if 'Quantity' in show_table.columns:
        st.dataframe(
            show_table.style.applymap(highlight_low, subset=['Quantity']),
            use_container_width=True
        )
    else:
        st.dataframe(show_table)


# --- All Customers ---
with tabs[2]:
    st.header("All Customers")
    cust_search = st.text_input("Search by customer name, phone, or location")
    if cust_search:
        mask = customers.apply(lambda row: cust_search.lower() in str(row).lower(), axis=1)
        st.dataframe(customers[mask])
    else:
        st.dataframe(customers)

# --- Receipt Generator ---
def generate_receipt_pdf(customer, items, total, receipt_no, date_str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, COMPANY_NAME, ln=True, align="C")
    pdf.set_font("Arial", "I", 12)
    pdf.cell(200, 10, DASHBOARD_TAGLINE, ln=True, align="C")
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 8, f"Tel: {COMPANY_PHONE}", ln=True, align="C")
    pdf.set_font("Arial", "B", 13)
    pdf.cell(200, 10, "RECEIPT", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(8)
    pdf.cell(100, 8, f"Date: {date_str}", ln=True)
    pdf.cell(100, 8, f"Receipt No: {receipt_no}", ln=True)
    pdf.cell(100, 8, f"Customer: {customer}", ln=True)
    pdf.ln(8)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(70, 8, "Product", 1)
    pdf.cell(30, 8, "Qty", 1)
    pdf.cell(40, 8, "Price", 1)
    pdf.cell(40, 8, "Total", 1)
    pdf.ln()
    pdf.set_font("Arial", size=11)
    for item in items:
        pdf.cell(70, 8, str(item['product']), 1)
        pdf.cell(30, 8, str(item['qty']), 1)
        pdf.cell(40, 8, f"{item['price']:.2f}", 1)
        pdf.cell(40, 8, f"{item['total']:.2f}", 1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(140, 10, "Grand Total", 1)
    pdf.cell(40, 10, f"{total:.2f}", 1)
    return pdf.output(dest='S').encode('latin1')

with tabs[3]:
    st.header("Receipt Generator")
    customer_options = customers["Name"].drop_duplicates().tolist()
    inventory_options = inventory["Product Name"].drop_duplicates().tolist()

    if "pdf_bytes" not in st.session_state:
        st.session_state["pdf_bytes"] = None
        st.session_state["file_name"] = ""

    with st.form("receipt_form"):
        col1, col2 = st.columns(2)
        with col1:
            customer = st.selectbox("Select Customer", customer_options)
            receipt_no = st.text_input("Receipt No", f"REC-{date.today().strftime('%Y%m%d')}-001")
            date_str = st.date_input("Date", value=date.today())
        with col2:
            # Product search/filter
            product_search = st.text_input("Search Product (optional)", key="product_search")
            if product_search:
                filtered_options = [
                    p for p in inventory_options if product_search.lower() in p.lower()
                ]
            else:
                filtered_options = inventory_options

            product_selections = st.multiselect(
                "Select Products",
                options=filtered_options,
                key="product_selections"
            )

        items = []
        total = 0
        for prod in product_selections:
            prod_row = inventory[inventory['Product Name'] == prod]
            if not prod_row.empty:
                prod_row = prod_row.iloc[0]
                try:
                    max_qty = int(prod_row['Quantity'])
                    if max_qty < 1:
                        max_qty = 1
                except Exception:
                    max_qty = 1000
                qty = st.number_input(
                    f"Quantity for {prod}",
                    min_value=1,
                    max_value=max_qty,
                    step=1,
                    key=prod
                )
                try:
                    price = float(prod_row['Price'])
                except Exception:
                    price = 0.0
                subtotal = qty * price
                items.append({'product': prod, 'qty': qty, 'price': price, 'total': subtotal})
                total += subtotal

        # --- Cart preview table ---
        if items:
            st.write("### Preview Receipt Items")
            cart_df = pd.DataFrame(items)
            cart_df = cart_df.rename(columns={'product': 'Product', 'qty': 'Qty', 'price': 'Unit Price', 'total': 'Total'})
            st.dataframe(cart_df)
        st.write(f"**Grand Total:** GHS {total:.2f}")

        submitted = st.form_submit_button("Generate Receipt PDF")
        if submitted and customer and items:
            pdf_bytes = generate_receipt_pdf(customer, items, total, receipt_no, str(date_str))
            st.session_state["pdf_bytes"] = pdf_bytes
            st.session_state["file_name"] = f"{receipt_no}.pdf"
            st.session_state["customer"] = customer  # store for WhatsApp
            st.session_state["date_str"] = str(date_str)
            st.success("Receipt generated! Scroll down to download.")

    # OUTSIDE form: Download and WhatsApp button
    if st.session_state.get("pdf_bytes"):
        st.download_button(
            "Download Receipt",
            data=st.session_state["pdf_bytes"],
            file_name=st.session_state["file_name"],
            mime="application/pdf"
        )

        # WhatsApp share button with phone formatting
        def format_gh_number(num):
            # Remove all spaces and plus signs
            num = str(num).replace(" ", "").replace("+", "")
            if num.startswith("233") and len(num) == 12:
                return num
            elif num.startswith("0") and len(num) == 10:
                return "233" + num[1:]
            elif len(num) == 9:
                return "233" + num
            elif len(num) == 10:
                return "233" + num[-9:]
            else:
                return num

        customer = st.session_state.get("customer", "")
        phone_number = ""
        whatsapp_message = f"Hello {customer}, your receipt from {COMPANY_NAME} dated {st.session_state.get('date_str','')} is ready."

        customer_row = customers[customers["Name"] == customer]
        # Try 'Phone Number', then 'Phone'
        colnames = [c.lower() for c in customers.columns]
        phone_col = None
        if "phone number" in colnames:
            phone_col = customers.columns[colnames.index("phone number")]
        elif "phone" in colnames:
            phone_col = customers.columns[colnames.index("phone")]
        if not customer_row.empty and phone_col:
            raw_number = customer_row.iloc[0][phone_col]
            formatted_number = format_gh_number(raw_number)
            if formatted_number and formatted_number != "nan" and len(formatted_number) >= 12:
                wa_link = f"https://wa.me/{formatted_number}?text={whatsapp_message}"
                st.markdown(f"""
                <a href="{wa_link}" target="_blank" style="display:inline-block;padding:10px 20px;background-color:#25D366;color:white;border-radius:5px;text-decoration:none;font-weight:bold;">
                📲 Share via WhatsApp
                </a>
                """, unsafe_allow_html=True)
            else:
                st.info("No valid phone number found for this customer. Please add one to share via WhatsApp.")
        else:
            st.info("No phone number found for this customer. Please add one to share via WhatsApp.")


with tabs[4]:
    st.header("Daily Sales PDF Report")
    report_date = st.date_input("Select date for sales report", value=date.today())
    sales_for_day = sales[sales['Date'] == str(report_date)]
    st.write(f"Total sales records: {len(sales_for_day)}")
    st.dataframe(sales_for_day)
    
    if len(sales_for_day) > 0:
        if st.button("Generate Sales PDF Report"):
            pdf_bytes = generate_sales_pdf(sales_for_day, str(report_date))
            st.download_button(
                "Download Sales Report",
                data=pdf_bytes,
                file_name=f"Sales_Report_{report_date}.pdf",
                mime="application/pdf"
            )
    else:
        st.info("No sales found for this date.")

