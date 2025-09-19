import streamlit as st
import sympy as sp
from sympy.parsing.latex import parse_latex
import json
import pyperclip
import uuid
import time

# Initialize session state
if "formula" not in st.session_state:
    st.session_state.formula = ""
if "copied" not in st.session_state:
    st.session_state.copied = False
if "compute_result" not in st.session_state:
    st.session_state.compute_result = None
if "compute_error" not in st.session_state:
    st.session_state.compute_error = ""
if "compute_mode" not in st.session_state:
    st.session_state.compute_mode = "Simplify"
if "last_button_time" not in st.session_state:
    st.session_state.last_button_time = 0

# Define mathematical symbols grouped by categories
categories = {
    "Basic Operators": [
        ("+", "+ "),
        ("-", "- "),
        ("×", "\\times "),
        ("÷", "\\div "),
        ("=", "= "),
        ("(", "\\left( "),
        (")", "\\right) "),
        ("[", "\\left[ "),
        ("]", "\\right] "),
        ("{", "\\left\\{ "),
        ("}", "\\right\\} "),
    ],
    "Superscript/Subscript": [
        ("^", "^{{}}"),
        ("²", "^{2}"),
        ("³", "^{3}"),
        ("_", "_{{}}"),
    ],
    "Roots & Fractions": [
        ("√", "\\sqrt{{}}"),
        ("ⁿ√", "\\sqrt[{}]{{}}"),
        ("frac", "\\frac{{}}{{}}"),
    ],
    "Calculus": [
        ("∫", "\\int "),
        ("∫ dx", "\\int dx "),
        ("∬", "\\iint "),
        ("∮", "\\oint "),
        ("d/dx", "\\frac{d}{dx} "),
        ("∂", "\\partial "),
        ("lim", "\\lim_{{ \\to }} "),
    ],
    "Sums & Products": [
        ("∑", "\\sum_{{}}^{{}} "),
        ("∏", "\\prod_{{}}^{{}} "),
    ],
    "Logs & Trig": [
        ("log", "\\log_{{}} "),
        ("ln", "\\ln "),
        ("sin", "\\sin "),
        ("cos", "\\cos "),
        ("tan", "\\tan "),
        ("arcsin", "\\arcsin "),
        ("arccos", "\\arccos "),
        ("arctan", "\\arctan "),
    ],
    "Greek Letters": [
        ("α", "\\alpha "),
        ("β", "\\beta "),
        ("γ", "\\gamma "),
        ("δ", "\\delta "),
        ("Δ", "\\Delta "),
        ("θ", "\\theta "),
        ("φ", "\\phi "),
        ("π", "\\pi "),
        ("σ", "\\sigma "),
        ("μ", "\\mu "),
        ("λ", "\\lambda "),
        ("ω", "\\omega "),
        ("ψ", "\\psi "),
        ("ξ", "\\xi "),
    ],
    "Relations & Symbols": [
        ("≠", "\\neq "),
        ("≈", "\\approx "),
        ("<", "< "),
        (">", "> "),
        ("≤", "\\leq "),
        ("≥", "\\geq "),
        ("∈", "\\in "),
        ("∀", "\\forall "),
        ("∃", "\\exists "),
        ("∞", "\\infty "),
        ("∪", "\\cup "),
        ("∩", "\\cap "),
        ("→", "\\rightarrow "),
        ("⇒", "\\Rightarrow "),
        ("∧", "\\land "),
        ("∨", "\\lor "),
        ("⇒", "\\implies "),
    ],
    "Matrices": [
        ("2×2 matrix", "\\begin{{matrix}} a & b \\\\ c & d \\end{{matrix}}"),
        ("3×3 matrix", "\\begin{{matrix}} a & b & c \\\\ d & e & f \\\\ g & h & i \\end{{matrix}}"),
        ("pmatrix", "\\begin{{pmatrix}}  &  \\\\  &  \\end{{pmatrix}}"),
    ],
}

st.title("Mathematical Formula Builder for Word")

st.write("""
Build your formula using buttons below. Structures like ^{{}}, \\frac{{}}{{}} have placeholders ({{}}).
Click inside {{}} to edit. Preview updates as you type.
**Important**: SymPy computation cannot handle complex LaTeX like \\sum, \\prod, matrices, multi-line expressions, or nested fractions (e.g., \\frac{\\frac{a}{b}}{c}).
Use simple expressions (e.g., \\int x^2 dx, \\frac{1}{x}) for computation.
For matrices, use symbolic variables (e.g., a, b, c) and compute manually in SymPy code.
""")

# Display buttons grouped by categories
for cat_name, sym_list in categories.items():
    with st.expander(cat_name, expanded=True):
        num_cols = min(6, len(sym_list))  # Dynamic columns
        cols = st.columns(num_cols)
        for i, (label, latex) in enumerate(sym_list):
            with cols[i % num_cols]:
                button_key = f"{cat_name}_{label}_{uuid.uuid4()}"
                if st.button(label, key=button_key):
                    current_time = time.time()
                    if current_time - st.session_state.last_button_time > 0.5:  # Debounce
                        st.session_state.formula += latex
                        st.session_state.last_button_time = current_time
                        # Auto-focus and select first placeholder with retry
                        st.markdown(
                            f"""
                            <script>
                            function focusPlaceholder() {{
                                var textarea = document.querySelector('textarea[data-testid="stTextArea"] textarea');
                                if (textarea) {{
                                    textarea.focus();
                                    var pos = textarea.value.lastIndexOf('{{}}');
                                    if (pos !== -1) {{
                                        textarea.setSelectionRange(pos + 1, pos + 2);
                                    }}
                                }} else {{
                                    setTimeout(focusPlaceholder, 200);
                                }}
                            }}
                            setTimeout(focusPlaceholder, 100);
                            </script>
                            """,
                            unsafe_allow_html=True
                        )

# Editable text area with live update
def on_formula_change():
    st.session_state.compute_result = None
    st.session_state.compute_error = ""

formula_input = st.text_area(
    "LaTeX Formula (editable)",
    value=st.session_state.formula,
    height=150,
    key="formula_input",
    on_change=on_formula_change
)
st.session_state.formula = formula_input

# Preview the rendered formula
st.subheader("Preview")
try:
    if st.session_state.formula.strip():
        st.latex(f"$$ {st.session_state.formula} $$")
    st.session_state.compute_error = ""
except Exception as e:
    st.error(f"Error rendering LaTeX: {str(e)}. Ensure braces are balanced, commands are valid, and avoid complex multi-line or nested structures.")

# Computation section
st.subheader("Compute Answer (Optional)")
st.write("""
Enter a computable expression (e.g., \\frac{1}{x}, \\int x^2 dx).
**Limitations**: SymPy cannot parse \\sum_{{i=1}}^{{n}} i, \\prod, matrices, multi-line expressions, or nested fractions.
Use 'Simplify' for symbolic results or 'Evaluate Numerically' for decimals (if variables are defined).
For matrices, define symbolic variables (e.g., \\begin{{matrix}} a & b \\\\ c & d \\end{{matrix}}) and compute manually in SymPy.
Example: For \\begin{{matrix}} 1 & 2 \\\\ 3 & 4 \\end{{matrix}}, use SymPy code: `sp.Matrix([[1,2],[3,4]])`.
""")
st.session_state.compute_mode = st.selectbox(
    "Computation Mode",
    ["Simplify", "Evaluate Numerically"],
    index=["Simplify", "Evaluate Numerically"].index(st.session_state.compute_mode)
)

# Variable substitution for numerical evaluation
with st.expander("Define Variables (Optional for Numerical Evaluation)"):
    st.write("Enter values for variables (e.g., x=2, y=3) to substitute before computing.")
    var_input = st.text_input("Variables (e.g., x=2, y=3)", key="var_input")
    substitutions = {}
    if var_input:
        try:
            for pair in var_input.split(","):
                var, val = pair.split("=")
                substitutions[sp.Symbol(var.strip())] = float(val.strip())
        except Exception as e:
            st.warning(f"Invalid variable input: {str(e)}. Use format 'x=2, y=3'.")

if st.button("Compute"):
    try:
        expr = parse_latex(st.session_state.formula)
        if substitutions and st.session_state.compute_mode == "Evaluate Numerically":
            expr = expr.subs(substitutions)
        if isinstance(expr, (sp.Integral, sp.Derivative)):
            result = expr.doit()
        else:
            result = sp.simplify(expr) if st.session_state.compute_mode == "Simplify" else expr.evalf()
        st.session_state.compute_result = sp.latex(result)
        st.session_state.compute_error = ""
    except Exception as e:
        st.session_state.compute_error = f"Computation failed: {str(e)}. Use simple expressions like \\int x^2 dx or \\frac{1}{x}. Avoid \\sum, \\prod, matrices, or nested fractions."
        st.session_state.compute_result = None

if st.session_state.compute_result:
    st.latex(f"$$ {st.session_state.compute_result} $$")
    st.write("Computed result (LaTeX):", st.session_state.compute_result)
if st.session_state.compute_error:
    st.error(st.session_state.compute_error)

# Copy section
st.subheader("Copy to Word")
st.write("""
Copy the LaTeX code below. In Microsoft Word, press Alt + = to open the Equation Editor, paste, and press Enter.
Example: Paste '\\sqrt{x^{2} + y^{2}} = z' for \\(\\sqrt{x^2 + y^2} = z\\).
""")

if st.button("Copy LaTeX to Clipboard"):
    try:
        pyperclip.copy(st.session_state.formula)
        st.session_state.copied = True
    except Exception as e:
        st.session_state.copied = False
        st.error(f"Copy failed: {str(e)}. Use the manual copy option below.")

if st.session_state.copied:
    st.success("Copied to clipboard!", icon="✅")
    # Auto-clear feedback after 2 seconds with fallback selector
    st.markdown(
        """
        <script>
        setTimeout(() => {
            var success = document.querySelector('div[role="alert"]') || document.querySelector('div[data-testid="stNotification"]');
            if (success) success.remove();
        }, 2000);
        </script>
        """,
        unsafe_allow_html=True
    )

# Fallback copy mechanism
with st.expander("Manual Copy (if button fails)"):
    st.text_area("Copy this text:", value=st.session_state.formula, key="manual_copy", height=100)
    st.markdown(
        f"""
        <button onclick="navigator.clipboard.writeText({json.dumps(st.session_state.formula)}).then(() => alert('Copied!'));">
        Copy via Browser
        </button>
        """,
        unsafe_allow_html=True
    )

# Clear button
if st.button("Clear Formula"):
    st.session_state.formula = ""
    st.session_state.copied = False
    st.session_state.compute_result = None
    st.session_state.compute_error = ""
    st.experimental_rerun()

