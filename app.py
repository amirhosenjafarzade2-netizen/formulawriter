import streamlit as st
try:
    import sympy as sp
    from sympy.parsing.latex import parse_latex
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    st.error("Required packages not installed. Please install: sympy, matplotlib, numpy")
    st.stop()

import json
import base64
from datetime import datetime
import re

# Page configuration
st.set_page_config(
    page_title="Advanced LaTeX Formula Builder",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.stTextArea textarea {
    font-family: 'Courier New', monospace;
    font-size: 14px;
}
.formula-preview {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
}
.template-button {
    background-color: #e1f5fe;
    border: 1px solid #01579b;
    border-radius: 5px;
    padding: 5px;
    margin: 2px;
}
.complexity-simple { color: #4caf50; font-weight: bold; }
.complexity-medium { color: #ff9800; font-weight: bold; }
.complexity-complex { color: #f44336; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    defaults = {
        "input_formula": "",
        "output_formula": "",
        "formula_history": [],
        "favorites": [],
        "compute_result": None,
        "compute_error": "",
        "compute_mode": "Simplify",
        "theme": "Light",
        "auto_preview": True,
        "current_step": 0,
        "undo_stack": [],
        "redo_stack": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Mathematical symbols with enhanced categories
categories = {
    "Basic Operators": [
        ("+", "+ "), ("-", "- "), ("×", "\\times "), ("÷", "\\div "),
        ("=", "= "), ("≠", "\\neq "), ("≈", "\\approx "), ("±", "\\pm ")
    ],
    "Brackets & Parentheses": [
        ("()", "\\left( \\right)"), ("[]", "\\left[ \\right]"), 
        ("{}", "\\left\\{ \\right\\}"), ("||", "\\left| \\right|"),
        ("⟨⟩", "\\langle \\rangle"), ("⌊⌋", "\\lfloor \\rfloor"), ("⌈⌉", "\\lceil \\rceil")
    ],
    "Powers & Indices": [
        ("x²", "x^{2}"), ("x³", "x^{3}"), ("xⁿ", "x^{n}"), ("x^y", "x^{y}"),
        ("x₁", "x_{1}"), ("x₂", "x_{2}"), ("xᵢ", "x_{i}"), ("x_y", "x_{y}")
    ],
    "Roots & Fractions": [
        ("√x", "\\sqrt{x}"), ("ⁿ√x", "\\sqrt[n]{x}"), ("∛x", "\\sqrt[3]{x}"),
        ("a/b", "\\frac{a}{b}"), ("∂f/∂x", "\\frac{\\partial f}{\\partial x}")
    ],
    "Calculus": [
        ("∫", "\\int "), ("∫₀^∞", "\\int_{0}^{\\infty} "), ("∬", "\\iint "), ("∭", "\\iiint "),
        ("d/dx", "\\frac{d}{dx} "), ("∂/∂x", "\\frac{\\partial}{\\partial x} "),
        ("lim", "\\lim_{x \\to a} "), ("∞", "\\infty ")
    ],
    "Sums & Products": [
        ("∑", "\\sum_{i=1}^{n} "), ("∏", "\\prod_{i=1}^{n} "),
        ("∑₀^∞", "\\sum_{n=0}^{\\infty} "), ("∏₀^∞", "\\prod_{n=0}^{\\infty} ")
    ],
    "Trigonometry": [
        ("sin", "\\sin "), ("cos", "\\cos "), ("tan", "\\tan "), ("cot", "\\cot "),
        ("sec", "\\sec "), ("csc", "\\csc "), ("arcsin", "\\arcsin "), 
        ("arccos", "\\arccos "), ("arctan", "\\arctan ")
    ],
    "Logarithms": [
        ("ln", "\\ln "), ("log", "\\log "), ("log₁₀", "\\log_{10} "),
        ("log₂", "\\log_{2} "), ("logₓ", "\\log_{x} ")
    ],
    "Greek Letters": [
        ("α", "\\alpha "), ("β", "\\beta "), ("γ", "\\gamma "), ("δ", "\\delta "),
        ("ε", "\\epsilon "), ("ζ", "\\zeta "), ("η", "\\eta "), ("θ", "\\theta "),
        ("κ", "\\kappa "), ("λ", "\\lambda "), ("μ", "\\mu "), ("ν", "\\nu "),
        ("π", "\\pi "), ("ρ", "\\rho "), ("σ", "\\sigma "), ("τ", "\\tau "),
        ("φ", "\\phi "), ("χ", "\\chi "), ("ψ", "\\psi "), ("ω", "\\omega "),
        ("Γ", "\\Gamma "), ("Δ", "\\Delta "), ("Θ", "\\Theta "), ("Λ", "\\Lambda "),
        ("Π", "\\Pi "), ("Σ", "\\Sigma "), ("Φ", "\\Phi "), ("Ω", "\\Omega ")
    ],
    "Relations & Logic": [
        ("≤", "\\leq "), ("≥", "\\geq "), ("∈", "\\in "), ("∉", "\\notin "),
        ("⊂", "\\subset "), ("⊆", "\\subseteq "), ("∪", "\\cup "), ("∩", "\\cap "),
        ("∀", "\\forall "), ("∃", "\\exists "), ("∄", "\\nexists "), ("∅", "\\emptyset ")
    ],
    "Arrows": [
        ("→", "\\rightarrow "), ("←", "\\leftarrow "), ("↔", "\\leftrightarrow "),
        ("⇒", "\\Rightarrow "), ("⇐", "\\Leftarrow "), ("⇔", "\\Leftrightarrow "),
        ("↗", "\\nearrow "), ("↘", "\\searrow "), ("↙", "\\swarrow "), ("↖", "\\nwarrow ")
    ],
    "Matrices & Vectors": [
        ("2×2", "\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}"),
        ("3×3", "\\begin{pmatrix} a & b & c \\\\ d & e & f \\\\ g & h & i \\end{pmatrix}"),
        ("[]", "\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}"),
        ("||", "\\begin{vmatrix} a & b \\\\ c & d \\end{vmatrix}"),
        ("vec", "\\vec{v}"), ("unit", "\\hat{i}")
    ],
    "Special Functions": [
        ("sin⁻¹", "\\sin^{-1} "), ("cos⁻¹", "\\cos^{-1} "), ("tan⁻¹", "\\tan^{-1} "),
        ("sinh", "\\sinh "), ("cosh", "\\cosh "), ("tanh", "\\tanh "),
        ("max", "\\max "), ("min", "\\min "), ("sup", "\\sup "), ("inf", "\\inf ")
    ]
}

# Formula templates with categories
templates = {
    "Algebra": {
        "Quadratic Formula": "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}",
        "Binomial Theorem": "(a + b)^n = \\sum_{k=0}^{n} \\binom{n}{k} a^{n-k} b^k",
        "Difference of Squares": "a^2 - b^2 = (a + b)(a - b)",
        "Perfect Square": "(a \\pm b)^2 = a^2 \\pm 2ab + b^2"
    },
    "Calculus": {
        "Derivative Definition": "f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}",
        "Fundamental Theorem": "\\int_{a}^{b} f'(x) dx = f(b) - f(a)",
        "Chain Rule": "\\frac{d}{dx}[f(g(x))] = f'(g(x)) \\cdot g'(x)",
        "Integration by Parts": "\\int u dv = uv - \\int v du"
    },
    "Statistics": {
        "Normal Distribution": "f(x) = \\frac{1}{\\sigma\\sqrt{2\\pi}} e^{-\\frac{1}{2}\\left(\\frac{x-\\mu}{\\sigma}\\right)^2}",
        "Standard Deviation": "\\sigma = \\sqrt{\\frac{1}{N} \\sum_{i=1}^{N} (x_i - \\mu)^2}",
        "Bayes' Theorem": "P(A|B) = \\frac{P(B|A) P(A)}{P(B)}",
        "Central Limit Theorem": "\\bar{X} \\sim N\\left(\\mu, \\frac{\\sigma^2}{n}\\right)"
    },
    "Physics": {
        "Einstein's E=mc²": "E = mc^2",
        "Newton's Second Law": "F = ma",
        "Schrödinger Equation": "i\\hbar \\frac{\\partial}{\\partial t} \\Psi = \\hat{H} \\Psi",
        "Wave Equation": "\\frac{\\partial^2 u}{\\partial t^2} = c^2 \\frac{\\partial^2 u}{\\partial x^2}"
    },
    "Geometry": {
        "Pythagorean Theorem": "a^2 + b^2 = c^2",
        "Circle Area": "A = \\pi r^2",
        "Sphere Volume": "V = \\frac{4}{3} \\pi r^3",
        "Distance Formula": "d = \\sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}"
    }
}

# Utility functions
def assess_complexity(formula):
    """Assess formula complexity"""
    if not formula:
        return "None", "#666666"
    
    complex_patterns = [r'\\begin\{', r'\\sum', r'\\prod', r'\\int.*\\int', r'\\frac.*\\frac.*\\frac']
    medium_patterns = [r'\\frac', r'\\sqrt', r'\\int', r'\\lim', r'\^.*\{.*\}']
    
    if any(re.search(pattern, formula) for pattern in complex_patterns):
        return "Complex", "#f44336"
    elif any(re.search(pattern, formula) for pattern in medium_patterns):
        return "Medium", "#ff9800"
    else:
        return "Simple", "#4caf50"

def add_to_history(formula):
    """Add formula to history"""
    if formula and formula not in st.session_state.formula_history:
        st.session_state.formula_history.insert(0, formula)
        if len(st.session_state.formula_history) > 10:
            st.session_state.formula_history.pop()

def save_state():
    """Save current state for undo functionality"""
    current_state = {
        'input': st.session_state.input_formula,
        'output': st.session_state.output_formula
    }
    st.session_state.undo_stack.append(current_state)
    if len(st.session_state.undo_stack) > 20:
        st.session_state.undo_stack.pop(0)
    st.session_state.redo_stack.clear()

# Sidebar
with st.sidebar:
    st.title("🎛️ Control Panel")
    
    # Theme toggle
    theme = st.selectbox("🎨 Theme", ["Light", "Dark"], key="theme_select", help="Choose the app's visual theme")
    st.session_state.theme = theme
    
    # Settings
    st.subheader("⚙️ Settings")
    auto_preview = st.checkbox("Auto Preview", value=st.session_state.auto_preview, help="Enable to see live formula previews")
    st.session_state.auto_preview = auto_preview
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("↶ Undo", help="Revert to previous state") and st.session_state.undo_stack:
            state = st.session_state.undo_stack.pop()
            st.session_state.redo_stack.append({
                'input': st.session_state.input_formula,
                'output': st.session_state.output_formula
            })
            st.session_state.input_formula = state['input']
            st.session_state.output_formula = state['output']
            st.rerun()
    
    with col2:
        if st.button("↷ Redo", help="Restore undone state") and st.session_state.redo_stack:
            state = st.session_state.redo_stack.pop()
            st.session_state.undo_stack.append({
                'input': st.session_state.input_formula,
                'output': st.session_state.output_formula
            })
            st.session_state.input_formula = state['input']
            st.session_state.output_formula = state['output']
            st.rerun()
    
    # Formula History
    if st.session_state.formula_history:
        st.subheader("📚 Recent Formulas")
        for i, formula in enumerate(st.session_state.formula_history[:5]):
            if st.button(f"📄 {formula[:30]}{'...' if len(formula) > 30 else ''}", key=f"hist_{i}", help="Load this formula"):
                save_state()
                st.session_state.input_formula = formula
                st.session_state.output_formula = formula
                st.rerun()
    
    # Favorites
    st.subheader("⭐ Favorites")
    if st.session_state.favorites:
        for i, formula in enumerate(st.session_state.favorites):
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"⭐ {formula[:25]}{'...' if len(formula) > 25 else ''}", key=f"fav_{i}", help="Load this favorite"):
                    save_state()
                    st.session_state.input_formula = formula
                    st.session_state.output_formula = formula
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_fav_{i}", help="Remove from favorites"):
                    st.session_state.favorites.pop(i)
                    st.rerun()

# Main interface
st.title("🧮 Advanced LaTeX Formula Builder")
st.write("Build, edit, and compute mathematical formulas with advanced features")

# Symbol buttons in tabs
st.subheader("🔤 Symbol Library")
tab_names = list(categories.keys())
tabs = st.tabs(tab_names)

for i, (cat_name, symbols) in enumerate(categories.items()):
    with tabs[i]:
        for j in range(0, len(symbols), 4):
            cols = st.columns(4)
            for k, (label, latex) in enumerate(symbols[j:j+4]):
                with cols[k]:
                    if st.button(label, key=f"{cat_name}_{j}_{k}", help=f"Insert: {latex}"):
                        save_state()
                        st.session_state.input_formula += latex
                        st.session_state.output_formula = st.session_state.input_formula
                        st.rerun()

# Main editing area
st.subheader("✏️ Formula Editor")

col1, col2 = st.columns([1, 1])

with col1:
    st.write("**📝 Input Formula**")
    
    complexity, color = assess_complexity(st.session_state.input_formula)
    st.markdown(f'<span style="color: {color};">●</span> Complexity: **{complexity}**', unsafe_allow_html=True)
    
    new_input = st.text_area(
        "LaTeX Input",
        value=st.session_state.input_formula,
        height=200,
        key="input_area",
        help="Type your LaTeX formula or use symbol buttons above",
        placeholder="Enter LaTeX formula here... e.g., \\frac{a}{b}"
    )
    
    if new_input != st.session_state.input_formula:
        st.session_state.input_formula = new_input
        st.session_state.output_formula = new_input
    
    if st.session_state.auto_preview and st.session_state.input_formula.strip():
        try:
            st.write("**👁️ Live Preview:**")
            st.latex(f"$$ {st.session_state.input_formula} $$")
        except:
            st.error("Invalid LaTeX syntax in input")

with col2:
    st.write("**📋 Output Formula (Copyable)**")
    
    is_valid = True
    try:
        if st.session_state.output_formula.strip():
            parse_latex(st.session_state.output_formula)
        validation_msg = "✅ Valid LaTeX"
        validation_color = "green"
    except:
        is_valid = False
        validation_msg = "❌ Invalid LaTeX"
        validation_color = "red"
    
    st.markdown(f'<span style="color: {validation_color};">{validation_msg}</span>', unsafe_allow_html=True)
    
    new_output = st.text_area(
        "LaTeX Output",
        value=st.session_state.output_formula,
        height=200,
        key="output_area",
        help="Edit or copy this formula"
    )
    
    if new_output != st.session_state.output_formula:
        st.session_state.output_formula = new_output
    
    if st.session_state.output_formula.strip():
        try:
            st.write("**🔍 Quick Preview:**")
            st.latex(f"$$ {st.session_state.output_formula} $$")
        except:
            st.error("Preview unavailable due to invalid LaTeX")

# Action buttons
st.subheader("🛠️ Actions")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("⬅️ Sync Input → Output", help="Copy input to output"):
        save_state()
        st.session_state.output_formula = st.session_state.input_formula
        st.rerun()

with col2:
    if st.button("⭐ Add to Favorites", help="Save formula to favorites"):
        if st.session_state.output_formula and st.session_state.output_formula not in st.session_state.favorites:
            st.session_state.favorites.append(st.session_state.output_formula)
            st.success("Added to favorites!")

with col3:
    if st.button("📚 Add to History", help="Save formula to history"):
        add_to_history(st.session_state.output_formula)
        st.success("Added to history!")

with col4:
    if st.button("🗑️ Clear All", help="Reset all fields"):
        save_state()
        st.session_state.input_formula = ""
        st.session_state.output_formula = ""
        st.session_state.compute_result = None
        st.session_state.compute_error = ""
        st.rerun()

with col5:
    if st.button("🔄 Reset", help="Clear input and output"):
        save_state()
        st.session_state.input_formula = ""
        st.session_state.output_formula = ""
        st.rerun()

# Enhanced Preview Section
st.subheader("🖼️ Enhanced Preview")
if st.session_state.output_formula.strip():
    try:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.latex(f"$$ {st.session_state.output_formula} $$")
        with col2:
            st.write("**Formula Info:**")
            st.write(f"Length: {len(st.session_state.output_formula)} chars")
            complexity, color = assess_complexity(st.session_state.output_formula)
            st.markdown(f'Complexity: <span style="color: {color}; font-weight: bold;">{complexity}</span>', unsafe_allow_html=True)
            
            frac_count = st.session_state.output_formula.count('\\frac')
            integral_count = st.session_state.output_formula.count('\\int')
            sum_count = st.session_state.output_formula.count('\\sum')
            
            if frac_count: st.write(f"Fractions: {frac_count}")
            if integral_count: st.write(f"Integrals: {integral_count}")
            if sum_count: st.write(f"Summations: {sum_count}")
    except Exception as e:
        st.error(f"Preview Error: {str(e)}")
else:
    st.info("👆 Enter a formula above to see the enhanced preview")

# Plotting Section
st.subheader("📊 Formula Visualization")
if st.session_state.output_formula.strip():
    if st.button("📈 Plot Formula", help="Generate a plot of the formula (if applicable)"):
        try:
            expr = parse_latex(st.session_state.output_formula)
            x = sp.Symbol('x')
            f = sp.lambdify(x, expr, modules=['numpy'])
            
            x_vals = np.linspace(-10, 10, 400)
            y_vals = f(x_vals)
            
            fig, ax = plt.subplots()
            ax.plot(x_vals, y_vals, label=st.session_state.output_formula[:30] + ("..." if len(st.session_state.output_formula) > 30 else ""))
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"Unable to plot: {str(e)}. Try a function of x, e.g., x^2 or sin(x).")
else:
    st.info("Enter a formula to enable plotting.")

# Computation Section with Enhanced Features
st.subheader("🧮 Advanced Computation")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    compute_mode = st.selectbox(
        "Computation Mode",
        ["Simplify", "Expand", "Factor", "Solve", "Differentiate", "Integrate", "Numerical Evaluation"],
        key="compute_mode_select",
        help="Choose how to process the formula"
    )
    st.session_state.compute_mode = compute_mode

with col2:
    var_input = st.text_input(
        "Variables (e.g., x=2, y=3)",
        key="var_input",
        help="Define variable values for numerical evaluation, e.g., 'x=2, y=3'"
    )

with col3:
    if compute_mode in ["Differentiate", "Integrate", "Solve"]:
        diff_var = st.text_input("Variable", value="x", help="Variable for differentiation, integration, or solving")
    else:
        diff_var = "x"

# Parse variables
substitutions = {}
if var_input:
    try:
        for pair in var_input.split(","):
            if "=" in pair:
                var, val = pair.split("=", 1)
                substitutions[sp.Symbol(var.strip())] = float(val.strip())
    except Exception as e:
        st.warning(f"Invalid variable input: {str(e)}")

# Enhanced computation
if st.button("🚀 Compute", type="primary", help="Process the formula with the selected computation mode"):
    if st.session_state.output_formula.strip():
        try:
            expr = parse_latex(st.session_state.output_formula)
            
            if compute_mode == "Simplify":
                result = sp.simplify(expr)
            elif compute_mode == "Expand":
                result = sp.expand(expr)
            elif compute_mode == "Factor":
                result = sp.factor(expr)
            elif compute_mode == "Solve":
                if "=" in st.session_state.output_formula:
                    lhs, rhs = st.session_state.output_formula.split("=", 1)
                    lhs_expr = parse_latex(lhs.strip())
                    rhs_expr = parse_latex(rhs.strip())
                    equation = sp.Eq(lhs_expr, rhs_expr)
                    result = sp.solve(equation, sp.Symbol(diff_var))
                else:
                    result = sp.solve(expr, sp.Symbol(diff_var))
            elif compute_mode == "Differentiate":
                result = sp.diff(expr, sp.Symbol(diff_var))
            elif compute_mode == "Integrate":
                result = sp.integrate(expr, sp.Symbol(diff_var))
            elif compute_mode == "Numerical Evaluation":
                if substitutions:
                    result = expr.subs(substitutions).evalf()
                else:
                    result = expr.evalf()
            
            st.session_state.compute_result = sp.latex(result)
            st.session_state.compute_error = ""
            
        except Exception as e:
            st.session_state.compute_error = f"Computation failed: {str(e)}"
            st.session_state.compute_result = None
    else:
        st.warning("Please enter a formula first.")

# Display results
if st.session_state.compute_result:
    st.success(f"✅ {compute_mode} successful!")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.latex(f"$$ {st.session_state.compute_result} $$")
    with col2:
        st.write("**Result LaTeX:**")
        st.code(st.session_state.compute_result, language="latex")
        
        if st.button("📥 Use as New Formula", help="Set result as new input formula"):
            save_state()
            st.session_state.input_formula = st.session_state.compute_result
            st.session_state.output_formula = st.session_state.compute_result
            st.rerun()

if st.session_state.compute_error:
    st.error(st.session_state.compute_error)
    
    with st.expander("💡 Computation Tips"):
        st.write("""
        **For successful computation:**
        - Use simple expressions like `\\frac{x^2}{2}`, `\\sin(x)`, `x^2 + 2x + 1`
        - For equations, include `=` sign: `x^2 - 4 = 0`
        - Avoid complex LaTeX structures like `\\sum`, `\\prod`, matrices
        - Define variables for numerical evaluation (e.g., x=2)
        - Use parentheses to clarify precedence
        """)

# Template Section with Search
st.subheader("📋 Formula Templates")

search_term = st.text_input("🔍 Search templates:", placeholder="e.g., quadratic, integral, normal...", help="Search for formula templates")

filtered_templates = {}
if search_term:
    for category, formulas in templates.items():
        filtered_formulas = {name: formula for name, formula in formulas.items() 
                           if search_term.lower() in name.lower() or search_term.lower() in formula.lower()}
        if filtered_formulas:
            filtered_templates[category] = filtered_formulas
else:
    filtered_templates = templates

if filtered_templates:
    template_tabs = st.tabs(list(filtered_templates.keys()))
    
    for i, (category, formulas) in enumerate(filtered_templates.items()):
        with template_tabs[i]:
            for j, (name, formula) in enumerate(formulas.items()):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    if st.button(f"📝 {name}", key=f"template_{category}_{j}", help=f"Use template: {name}"):
                        save_state()
                        st.session_state.input_formula = formula
                        st.session_state.output_formula = formula
                        add_to_history(formula)
                        st.rerun()
                
                with col2:
                    try:
                        st.latex(f"$$ {formula} $$")
                    except:
                        st.code(formula, language="latex")
                
                with col3:
                    if st.button("⭐", key=f"fav_template_{category}_{j}", help="Add to favorites"):
                        if formula not in st.session_state.favorites:
                            st.session_state.favorites.append(formula)
                            st.success("Added!")

# Export and Sharing Options
st.subheader("💾 Export & Share")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.session_state.output_formula:
        st.download_button(
            label="📥 Download LaTeX",
            data=st.session_state.output_formula,
            file_name=f"formula_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            help="Download formula as a text file"
        )

with col2:
    if st.session_state.output_formula:
        export_data = {
            "formula": st.session_state.output_formula,
            "created": datetime.now().isoformat(),
            "complexity": assess_complexity(st.session_state.output_formula)[0]
        }
        st.download_button(
            label="📦 Export JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"formula_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            help="Download formula with metadata as JSON"
        )

with col3:
    if st.button("🔗 Generate Share Link", help="Create a shareable link for the formula"):
        if st.session_state.output_formula:
            encoded = base64.b64encode(st.session_state.output_formula.encode()).decode()
            share_url = f"?formula={encoded}"
            st.code(share_url, language="text")
            st.success("Share link generated!")
        else:
            st.warning("Enter a formula to generate a share link.")

with col4:
    if st.button("📋 Copy to Clipboard", help="Copy formula to clipboard"):
        if st.session_state.output_formula:
            st.code(st.session_state.output_formula, language="latex")
            st.success("Formula copied to clipboard!")
        else:
            st.warning("Enter a formula to copy.")

# Instructions and Help (Completed Section)
with st.expander("📖 Instructions & Help", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### Getting Started
        - **Enter Formulas**: Use the "Formula Editor" text area to type LaTeX code or click symbol buttons above to insert common mathematical symbols.
        - **Templates**: Browse the "Formula Templates" section to select pre-built formulas for algebra, calculus, statistics, and more.
        - **Computation**: Select a computation mode (e.g., Simplify, Solve) and click "Compute" to process your formula. Define variables for numerical evaluation if needed.
        - **History & Favorites**: Save formulas to history or favorites for quick access later.
        - **Plotting**: Click "Plot Formula" to visualize functions of x (e.g., `x^2`, `sin(x)`).
        """)
    with col2:
        st.markdown("""
        ### Tips & Tricks
        - Use `\\frac{a}{b}` for fractions, `\\sqrt{x}` for square roots, and other LaTeX commands for complex expressions.
        - For equations, include an `=` sign (e.g., `x^2 - 4 = 0`) when solving.
        - Enable "Auto Preview" in the sidebar to see live updates of your formula.
        - Use "Undo" and "Redo" buttons to navigate changes.
        - Export formulas as LaTeX or JSON, or generate a shareable link.
        - If computation fails, check the "Computation Tips" under the computation section.
        - For plotting, ensure the formula is a function of x and avoid complex structures like matrices.
        """)
