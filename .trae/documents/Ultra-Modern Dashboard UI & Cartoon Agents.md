# Ultra-Modern Dashboard UI & Cartoon Agents Plan

This plan aims to transform the dashboard into a futuristic "Cyberpunk/Glassmorphism" interface with animated cartoon agents visualizing the system's thinking process.

## 1. UI Overhaul (Custom CSS)
We will inject extensive CSS into `dashboard/app.py` to:
- **Dark Mode**: Deep blue/black background with neon accents (Green, Pink, Cyan).
- **Glassmorphism**: Semi-transparent cards with blur effects for metrics and logs.
- **Typography**: Use modern sans-serif fonts (Roboto/Inter) and glowing text effects.
- **Hide Streamlit Elements**: Remove the standard header/footer and hamburger menu for a clean "App" feel.

## 2. Animated Agents (Lottie)
We will integrate `streamlit-lottie` to display cartoon animations corresponding to agent states.
- **Library**: Add `streamlit-lottie` to `dashboard/requirements.txt`.
- **Assets**: Use public Lottie JSON URLs (from LottieFiles/GitHub) for:
    - `ANALYZE`: Robot Scanning/Thinking.
    - `PLAN`: Robot Blueprint/Writing.
    - `EXECUTE`: Robot Coding/Typing.
    - `VALIDATE`: Robot Checking/Success.
    - `FAIL`: Robot Error/Broken.
    - *Fallback*: If URLs fail (CORS/Network), use CSS-animated emojis as a robust backup.

## 3. Layout Redesign ("Live Agents" Page)
The "Live Agents" page will be reimagined:
- **Top**: "Mission Control" Status Bar (Active Task ID, Uptime).
- **Split Screen**:
    - **Left (The Stage)**: Large Lottie animation of the current agent state + "Thinking..." text.
    - **Center (The Flow)**: The Graphviz chart (styled with dark colors).
    - **Right (The Terminal)**: A scrolling "Matrix-style" log of audit events.

## 4. Implementation Steps
1.  **Dependencies**: Add `streamlit-lottie` to `dashboard/requirements.txt`.
2.  **Code Update**:
    - Import `streamlit_lottie`.
    - Create a `load_css()` function with the new styles.
    - Create a `get_agent_animation(state)` function.
    - Refactor `show_live_agents()` to use the new layout.
3.  **Build**: Rebuild the dashboard container.

## 5. Verification
- Launch the dashboard.
- Verify the "Dark/Neon" theme is applied.
- Start a task and watch the robot animation change as the task progresses through Analyze -> Plan -> Execute.
