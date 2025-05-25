from setuptools import find_packages,setup

setup(
    name = 'mcqGenerator',
    versioin = '0.0.1',
    author = 'Liroshin',
    author_email='liroshin1541@gmail.com',
    install_requires=["openai","langchain","streamlit","python-dotenv","PyPDF2"],
    packages=find_packages()
)