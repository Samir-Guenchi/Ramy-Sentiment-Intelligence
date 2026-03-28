from setuptools import setup, find_packages

setup(
    name="ramy-sentiment",
    version="1.0.0",
    description="AI-Powered Arabic & Algerian Darja Sentiment Analysis for Ramy",
    author="Ramy AI Team",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "streamlit>=1.28.0",
        "plotly>=5.18.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "gpu": [
            "torch>=2.0.0",
            "transformers>=4.35.0",
        ],
        "full": [
            "torch>=2.0.0",
            "transformers>=4.35.0",
            "wordcloud>=1.9.0",
            "arabic-reshaper>=3.0.0",
            "python-bidi>=0.4.2",
            "matplotlib>=3.8.0",
            "camel-tools>=1.5.0",
            "loguru>=0.7.0",
        ],
    },
)
