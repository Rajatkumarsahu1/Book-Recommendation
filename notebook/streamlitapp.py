import streamlit as st
import numpy as np
from fuzzywuzzy import process
import pickle

# Load model and data
model = pickle.load(open('artifacts/model.pkl', 'rb'))
book_names = pickle.load(open('artifacts/book_names.pkl', 'rb'))
final_rating = pickle.load(open('artifacts/final_rating.pkl', 'rb'))
book_pivot = pickle.load(open('artifacts/book_pivot.pkl', 'rb'))

st.set_page_config(page_title="📚 Book Recommender Store", layout="wide")

# Initialize session state
if 'cart' not in st.session_state:
    st.session_state.cart = []

if 'selected_book' not in st.session_state:
    st.session_state.selected_book = None

st.title("📚 Book Recommender Store")

# --- Search box and dynamic suggestions ---
search_query = st.text_input("🔍 Type book title")

def get_suggestions(query, choices, limit=10, score_cutoff=40):
    if not query:
        return []
    results = process.extract(query, choices, limit=limit)
    filtered = [r[0] for r in results if r[1] >= score_cutoff]
    return filtered

suggestions = get_suggestions(search_query, book_names)

selected_book = None

if suggestions:
    selected_book = st.selectbox("Did you mean?", [""] + suggestions)
    if selected_book == "":
        selected_book = None
else:
    if search_query:
        st.write("❌ No suggestions found.")

if selected_book:
    st.success(f"✅ You selected: {selected_book}")
    st.session_state.selected_book = selected_book

    # Show book image & title
    try:
        idx = np.where(final_rating['title'] == selected_book)[0][0]
        img_url = final_rating.iloc[idx]['image_url']
    except:
        img_url = None

    cols = st.columns([1, 4])
    with cols[0]:
        if img_url:
            st.image(img_url, width=120, use_container_width=False)
    with cols[1]:
        st.markdown(f"### {selected_book}")

    if st.button(f"Add '{selected_book}' to cart"):
        if selected_book not in st.session_state.cart:
            st.session_state.cart.append(selected_book)
            st.success(f"'{selected_book}' added to cart!")
            st.rerun()
        else:
            st.warning(f"'{selected_book}' is already in your cart.")

# --- Cart Section ---
st.markdown("---")
st.header("🛒 Your Cart")

if st.session_state.cart:
    cart_cols = st.columns(3)
    for i, book in enumerate(st.session_state.cart):
        with cart_cols[i % 3]:
            st.markdown(f"**{book}**")
            # Show image
            try:
                idx = np.where(final_rating['title'] == book)[0][0]
                url = final_rating.iloc[idx]['image_url']
                st.image(url, width=100)
            except:
                st.write("No image")
            if st.button(f"Remove '{book}'", key=f"remove_{i}"):
                st.session_state.cart.remove(book)
                st.rerun()
else:
    st.write("Your cart is empty.")

# --- Recommendations for cart books ---
st.markdown("---")
st.header("🛍️ Users Also Bought (Recommendations)")

def recommend_books(book_name, n_recommend=3):
    try:
        book_id = np.where(book_pivot.index == book_name)[0][0]
        distances, suggestions = model.kneighbors(book_pivot.iloc[book_id, :].values.reshape(1, -1), n_neighbors=n_recommend+1)
        recs = []
        for idx in suggestions[0]:
            rec_book = book_pivot.index[idx]
            if rec_book != book_name:
                recs.append(rec_book)
        return recs
    except:
        return []

# Collect recommendations for all books in cart
recommendation_set = set()
for b in st.session_state.cart:
    recs = recommend_books(b, 3)
    recommendation_set.update(recs)

recommendation_list = list(recommendation_set)
recommendation_list = [b for b in recommendation_list if b not in st.session_state.cart]

if recommendation_list:
    rec_cols = st.columns(3)
    selected_for_cart = []

    for i, rec_book in enumerate(recommendation_list):
        with rec_cols[i % 3]:
            st.markdown(f"**{rec_book}**")
            try:
                idx = np.where(final_rating['title'] == rec_book)[0][0]
                rec_url = final_rating.iloc[idx]['image_url']
                st.image(rec_url, width=100)
            except:
                st.write("No image")

            if st.checkbox(f"Add '{rec_book}'", key=f"rec_add_{i}"):
                selected_for_cart.append(rec_book)

    if selected_for_cart:
        if st.button("Add selected recommended books to cart"):
            for book in selected_for_cart:
                if book not in st.session_state.cart:
                    st.session_state.cart.append(book)
            st.success("Selected recommended books added to cart!")
            st.rerun()

    # Combo add option
    if st.button(f"Add all {len(recommendation_list)} recommended books as combo for ${len(recommendation_list)}"):
        for book in recommendation_list:
            if book not in st.session_state.cart:
                st.session_state.cart.append(book)
        st.success("Combo added to cart!")
        st.rerun()
else:
    st.write("Add books to your cart to get recommendations.")

# --- Checkout ---
st.markdown("---")
st.header("💳 Checkout")

total_price = len(st.session_state.cart) * 1  # $1 per book

if st.session_state.cart:
    st.write(f"Total books in cart: {len(st.session_state.cart)}")
    st.write(f"Total price: ${total_price}")

    if st.button("Checkout"):
        st.success(f"Thank you for your purchase of {len(st.session_state.cart)} books! Total: ${total_price}")
        st.session_state.cart.clear()
        st.rerun()
else:
    st.write("Add some books to your cart to proceed to checkout.")
