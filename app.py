import streamlit as st
try:
    import sympy as sp
    from sympy.parsing.latex import parse_latex
except ImportError:
    st.error("SymPy is not installed. Please install it using 'pip install sympy' or add 'sympy>=1.12' to your requirements.txt.")
    st.stop()
try:
    import pyperclip
except ImportError:
    st.warning("pyperclip is not installed. Clipboard copy will rely on browser-based fallback. Install with 'pip install pyperclip'.")
import json
import uuid

# Initialize session state
if "formula" not in st.session_state:
    st.session_state.formula = ""
if "copied" not in st.session_state:
    st.session_state.copied = False
if "compute_result" not in st.session_state:
    st.session_state.compute_result = None
if "compute_error" not in st.session_state:
    st.session_state.compute_error = ""
if "debug_message" not in st.session_state:
    st.session_state.debug_message = ""
if "compute_mode" not in st.session_state:
    st.session_state.compute_mode = "Simplify"

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
        ("d/dx", "\\frac{d}{dx} "),
        ("∂", "\\partial "),
        ("lim", "\\lim_{{ \\to }} "),
    ],
    "Sums & Products": [
        ("∑", "\\sum_{{}}^{{}} "),
        ("∏", "\\prod_{{}}^{{}} "),
    ],
    "Logs & Trig": [
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
        ("θ", "\\theta "),
        ("π", "\\pi "),
        ("σ", "\\sigma "),
        ("Δ", "\\Delta "),
        ("λ", "\\lambda "),
    ],
    "Relations & Symbols": [
        ("≠", "\\neq "),
        ("≈", "\\approx "),
        ("≤", "\\leq "),
        ("≥", "\\geq "),
        ("∈", "\\in "),
        ("∞", "\\infty "),
        ("∀", "\\forall "),
        ("∃", "\\exists "),
        ("→", "\\rightarrow "),
    ],
    "Matrices": [
        ("2×2 matrix", "\\begin{{matrix}} a & b \\\\ c & d \\end{{matrix}}"),
        ("3×3 matrix", "\\begin{{matrix}} a & b & c \\\\ d & e & f \\\\ g & h & i \\end{{matrix}}"),
        ("pmatrix", "\\begin{{pmatrix}}  &  \\\\  &  \\end{{pmatrix}}"),
    ],
}

st.title("LaTeX Formula Builder")

st.write("""
Type or use buttons to build your LaTeX formula. The preview below shows the rendered result.
Structures like ^{{}}, \\frac{{}}{{}} have placeholders ({{}}). Click inside {{}} to edit.
**Important**: Computation fails for complex LaTeX (e.g., \\sum, \\prod, matrices, nested fractions like \\\\frac{{ \\\\frac{{a}}{{b}} }}{{c}}).
Use simple expressions (e.g., \\int x^2 dx, \\frac{1}{x}) for computation.
For matrices, use symbolic variables and compute manually in SymPy (e.g., `sp.Matrix([[1,2],[3,4]])`).
**Note**: If buttons don't update the text area, click slowly or type directly.
""")

# Debug message for button clicks
if st.session_state.debug_message:
    st.info(st.session_state.debug_message)

# Display buttons grouped by categories
for cat_name, sym_list in categories.items():
    with st.expander(cat_name, expanded=True):
        num_cols = min(4, len(sym_list))  # Compact layout
        cols = st.columns(num_cols)
        for i, (label, latex) in enumerate(sym_list):
            with cols[i % num_cols]:
                if st.button(label, key=f"{cat_name}_{label}_{uuid.uuid4()}"):
                    st.session_state.formula += latex
                    st.session_state.compute_result = None
                    st.session_state.compute_error = ""
                    st.session_state.debug_message = f"Added: {latex}"
                    # Auto-focus first placeholder
                    if "{{}}" in latex:
                        st.markdown(
                            """
                            <script>
                            setTimeout(() => {
                                var textarea = document.querySelector('textarea[data-testid="stTextArea"] textarea');
                                if (textarea) {
                                    textarea.focus();
                                    var pos = textarea.value.lastIndexOf('{{}}');
                                    if (pos !== -1) {
                                        textarea.setSelectionRange(pos + 1, pos + 2);
                                    }
                                }
                            }, 100);
                            </script>
                            """,
                            unsafe_allow_html=True
                        )

# Editable text area for LaTeX input
def on_formula_change():
    st.session_state.compute_result = None
    st.session_state.compute_error = ""
    st.session_state.debug_message = ""

formula_input = st.text_area(
    "LaTeX Formula (type or use buttons)",
    value=st.session_state.formula,
    height=100,
    key="formula_input",
    on_change=on_formula_change
)
st.session_state.formula = formula_input

# Preview box (rendered LaTeX)
st.subheader("Preview (Rendered Formula)")
if not st.session_state.formula.strip():
    st.write("Enter a formula above to see the rendered preview.")
else:
    try:
        st.latex(f"$$ {st.session_state.formula} $$")
        st.session_state.compute_error = ""
    except Exception as e:
        st.error(f"Error rendering LaTeX: {str(e)}. Ensure braces are balanced and avoid complex structures (e.g., nested fractions like \\\\frac{{ \\\\frac{{a}}{{b}} }}{{c}}).")

# Computation section
st.subheader("Compute Answer (Optional)")
st.write("""
Enter a computable expression (e.g., \\frac{1}{x}, \\int x^2 dx).
**Limitations**: SymPy cannot parse \\sum, \\prod, matrices, or nested fractions.
Use 'Simplify' for symbolic results or 'Evaluate Numerically' for decimals (if variables are defined).
""")
st.selectbox(
    "Computation Mode",
    ["Simplify", "Evaluate Numerically"],
    key="compute_mode"
)

# Variable substitution
with st.expander("Define Variables (Optional)"):
    st.write("Enter values for variables (e.g., x=2, y=3) for numerical evaluation.")
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
        st.session_state.compute_error = f"Computation failed: {str(e)}. Use simple expressions like \\int x^2 dx or \\frac{1}{x}."
        st.session_state.compute_result = None

if st.session_state.compute_result:
    st.latex(f"$$ {st.session_state.compute_result} $$")
    st.write("Computed result (LaTeX):", st.session_state.compute_result)
if st.session_state.compute_error:
    st.error(st.session_state.compute_error)

# Copy section
st.subheader("Copy to Word")
st.write("Copy the LaTeX code below. In Word, press Alt + =, paste, and press Enter.")
if st.button("Copy LaTeX"):
    try:
        pyperclip.copy(st.session_state.formula)
        st.session_state.copied = True
    except Exception as e:
        st.session_state.copied = False
        st.error(f"Copy failed: {str(e)}. Use the manual copy option below.")

if st.session_state.copied:
    st.success("Copied to clipboard!", icon="✅")
    st.markdown(
        """
        <script>
        setTimeout(() => {
            var success = document.querySelector('div[role="alert"]');
            if (success) success.remove();
        }, 2000);
        </script>
        """,
        unsafe_allow_html=True
    )

# Fallback copy
with st.expander("Manual Copy"):
    st.text_area("Copy this text:", value=st.session_state.formula, key="manual_copy", height=80)
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
    st.session_state.debug_message = ""
    st.experimental_rerun()
