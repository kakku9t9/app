import streamlit as st
import replicate
import os
import pandas as pd
from datetime import datetime

# ==========================================
# 🔑 API KEY UPDATED
# ==========================================
# The new key you provided has been added.
os.environ["REPLICATE_API_TOKEN"] =  st.secrets["REPLICATE_API_TOKEN"]

# ==========================================
# ⚙️ APP CONFIGURATION
# ==========================================
st.set_page_config(page_title="Seedream 4 Studio", layout="wide", page_icon="⚡")

# Initialize Session State
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = ""

# --- Helper: AI Prompt Enhancer ---
def enhance_prompt(user_input):
    try:
        system_prompt = "You are an expert prompt engineer for Seedream 4. Expand the user's short prompt into a highly detailed, cinematic description. Include lighting, camera angles, and textures. Return ONLY the enhanced prompt text."
        output = replicate.run(
            "meta/meta-llama-3-70b-instruct",
            input={
                "system_prompt": system_prompt,
                "prompt": f"Enhance this prompt: {user_input}",
                "max_new_tokens": 150, "temperature": 0.7
            }
        )
        return "".join(output).strip()
    except Exception as e:
        st.error(f"Enhancement failed: {e}")
        return user_input

# --- Helper: Save to History ---
def save_to_history(mode, prompt, model, res, url):
    history_file = "generation_history.csv"
    new_data = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Mode": mode, "Prompt": prompt, "Model": model,
        "Resolution": res, "Image_URL": url
    }
    df = pd.DataFrame([new_data])
    if not os.path.isfile(history_file):
        df.to_csv(history_file, index=False)
    else:
        df.to_csv(history_file, mode='a', header=False, index=False)

# ==========================================
# 🎛️ SIDEBAR SETTINGS
# ==========================================
with st.sidebar:
    st.title("⚙️ Settings")
    st.success("API Token: Loaded ✅")
    
    model_version = st.selectbox("Model Version", ["bytedance/seedream-4", "bytedance/seedream-4.5"])
    st.divider()
    
    mode = st.radio("Mode", ["Text-to-Image", "Image-to-Image (Edit)"])
    size = st.selectbox("Resolution", ["1K", "2K", "4K"], index=0)
    aspect_ratio = st.selectbox("Aspect Ratio", ["1:1", "16:9", "9:16", "3:2", "2:3"])
    num_outputs = st.slider("Number of Variations", 1, 4, 1)
    
    if st.button("🗑️ Clear All History"):
        if os.path.exists("generation_history.csv"):
            os.remove("generation_history.csv")
            st.rerun()

# ==========================================
# 🖥️ MAIN INTERFACE
# ==========================================
tab1, tab2 = st.tabs(["🎨 Studio", "🖼️ Gallery"])

with tab1:
    st.title("⚡ Seedream 4 Creative Studio")
    with st.container(border=True):
        st.subheader("📝 Write Your Prompt")
        style = st.selectbox("Apply Style Preset", ["None", "Cinematic", "Cyberpunk", "Oil Painting", "Anime", "Hyper-Realistic", "3D Render"])
        user_prompt = st.text_area("What do you want to see?", value=st.session_state.current_prompt, placeholder="e.g. A futuristic samurai...", height=150)
        if st.button("✨ Auto-Enhance Prompt"):
            if user_prompt:
                with st.spinner("AI is rewriting your prompt..."):
                    st.session_state.current_prompt = enhance_prompt(user_prompt)
                    st.rerun()
            else:
                st.warning("Type a short idea first!")
    
    if mode == "Image-to-Image (Edit)":
        uploaded_file = st.file_uploader("Upload Base Image", type=["jpg", "png"])
        strength = st.slider("Prompt Strength", 0.1, 1.0, 0.6)
        if uploaded_file: st.image(uploaded_file, "Original Image", width=200)

    final_prompt = f"{user_prompt}, {style} style, high detail" if style != "None" else user_prompt
    
    if st.button("🚀 Generate Magic", use_container_width=True):
        if not user_prompt:
            st.warning("Please enter a prompt.")
        else:
            try:
                input_params = {"prompt": final_prompt, "size": size, "aspect_ratio": aspect_ratio, "max_images": num_outputs}
                if mode == "Image-to-Image (Edit)" and uploaded_file:
                    input_params.update({"image": uploaded_file, "prompt_strength": strength})
                
                with st.spinner("Seedream is dreaming..."):
                    output = replicate.run(model_version, input=input_params)
                
                st.divider()
                st.subheader("✨ Generated Results")
                cols = st.columns(num_outputs)
                for i, img_url in enumerate(output):
                    with cols[i]:
                        st.image(img_url, use_column_width=True)
                        st.download_button(f"Download #{i+1}", img_url, file_name=f"seedream_{i}.png")
                        save_to_history(mode, user_prompt, model_version, size, img_url)
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.title("🖼️ Your Creation Gallery")
    if os.path.exists("generation_history.csv"):
        history_df = pd.read_csv("generation_history.csv").iloc[::-1]
        grid_cols = 4
        rows = -(-len(history_df) // grid_cols) # Ceiling division
        for r in range(rows):
            cols = st.columns(grid_cols)
            for c in range(grid_cols):
                idx = r * grid_cols + c
                if idx < len(history_df):
                    row = history_df.iloc[idx]
                    with cols[c]:
                        st.image(row['Image_URL'], use_column_width=True)
                        st.caption(f"**Prompt:** {row['Prompt'][:50]}...")
                        if st.button(f"Reuse Prompt #{len(history_df)-idx}", key=f"btn_{idx}"):
                            st.session_state.current_prompt = row['Prompt']
                            st.success("Prompt sent to Studio!")
    else:
        st.info("No images in gallery yet.")

st.markdown("---")
st.caption("Seedream 4 Studio | Ready to Run")



