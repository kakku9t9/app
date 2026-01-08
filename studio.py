import streamlit as st
import replicate
import os
import pandas as pd
from datetime import datetime

# --- AUTHENTICATION ---
os.environ["REPLICATE_API_TOKEN"] = "r8_MhToY6Jsj5F7NgsWc3WVnCHQGBGkzY63jmKHV"

# Page Config
st.set_page_config(page_title="Seedream 4 Studio", layout="wide", page_icon="⚡")

# Initialize Session State
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = ""

# --- Helper: AI Prompt Enhancer ---
def enhance_prompt(user_input):
    try:
        # Using Llama-3 to expand the prompt
        system_prompt = "You are an expert prompt engineer for Seedream 4 and Midjourney. Expand the user's short prompt into a highly detailed, cinematic, and artistic description. Include lighting, camera angles, and textures. Return ONLY the enhanced prompt text, no intro or outro."
        
        output = replicate.run(
            "meta/meta-llama-3-70b-instruct",
            input={
                "system_prompt": system_prompt,
                "prompt": f"Enhance this prompt: {user_input}",
                "max_new_tokens": 150,
                "temperature": 0.7
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
        "Mode": mode,
        "Prompt": prompt,
        "Model": model,
        "Resolution": res,
        "Image_URL": url
    }
    df = pd.DataFrame([new_data])
    if not os.path.isfile(history_file):
        df.to_csv(history_file, index=False)
    else:
        df.to_csv(history_file, mode='a', header=False, index=False)

# --- Sidebar: Configuration ---
with st.sidebar:
    st.title("⚙️ Settings")
    st.success("API Token: Active ✅")
    
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

# --- Main App Layout ---
tab1, tab2 = st.tabs(["🎨 Studio", "🖼️ Gallery"])

# --- TAB 1: STUDIO ---
with tab1:
    st.title("⚡ Seedream 4 Creative Studio")

    with st.container(border=True):
        st.subheader("📝 Write Your Prompt")
        
        # Style Presets
        style = st.selectbox("Apply Style Preset", 
                             ["None", "Cinematic", "Cyberpunk", "Oil Painting", "Anime", "Hyper-Realistic", "3D Render"])
        
        # Main Prompt Box
        user_prompt = st.text_area("What do you want to see?", 
                                   value=st.session_state.current_prompt, 
                                   placeholder="e.g. A futuristic samurai...",
                                   height=150)
        
        # --- NEW: AUTO-ENHANCE BUTTON ---
        if st.button("✨ Auto-Enhance Prompt", help="Uses AI to make your prompt more detailed"):
            if user_prompt:
                with st.spinner("AI is rewriting your prompt..."):
                    enhanced = enhance_prompt(user_prompt)
                    st.session_state.current_prompt = enhanced
                    st.rerun() # Refresh to show the new prompt in the box
            else:
                st.warning("Type a short idea first!")

    if mode == "Image-to-Image (Edit)":
        uploaded_file = st.file_uploader("Upload Base Image", type=["jpg", "png", "jpeg"])
        strength = st.slider("Prompt Strength", 0.1, 1.0, 0.6)
        if uploaded_file:
            st.image(uploaded_file, caption="Original Image", width=200)

    # Combine prompt with style
    final_prompt = user_prompt
    if style != "None":
        final_prompt = f"{user_prompt}, {style} style, high detail, masterpiece"

    if st.button("🚀 Generate Magic", use_container_width=True):
        if not user_prompt:
            st.warning("Please enter a prompt.")
        else:
            try:
                input_params = {
                    "prompt": final_prompt,
                    "size": size,
                    "aspect_ratio": aspect_ratio,
                    "max_images": num_outputs,
                    "sequential_image_generation": "auto" if num_outputs > 1 else "off"
                }
                
                if mode == "Image-to-Image (Edit)" and uploaded_file:
                    input_params["image"] = uploaded_file
                    input_params["prompt_strength"] = strength

                with st.spinner(f"Seedream is dreaming..."):
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

# --- TAB 2: GALLERY ---
with tab2:
    st.title("🖼️ Your Creation Gallery")
    if os.path.exists("generation_history.csv"):
        history_df = pd.read_csv("generation_history.csv").iloc[::-1]
        grid_cols = 4
        rows = len(history_df) // grid_cols + (1 if len(history_df) % grid_cols > 0 else 0)
        
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
                            st.success("Prompt sent! Go to Studio.")
    else:
        st.info("No images in gallery yet.")

st.markdown("---")
st.caption("Auto-Enhance enabled | Powered by Llama-3 & Seedream 4")
