

from setuptools import setup, find_packages

setup(
    name='mcqGenerator',
    version='0.0.1',  # ✅ fixed typo: 'versioin' → 'version'
    author='Liroshin',
    author_email='liroshin1541@gmail.com',
    install_requires=[
        "langchain>=0.1.17",
        "langchain-community>=0.0.21",
        "langchain-huggingface>=0.0.1",
        "huggingface_hub",
        "streamlit",
        "python-dotenv",
        "PyPDF2",
        "sentence-transformers"
    ],
    packages=find_packages()
)
