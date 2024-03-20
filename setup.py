from setuptools import setup, find_packages
import os

with open("requirements.txt", "r") as f:
    dependencies = f.readlines()

setup(
   name='Cathero Tools',
   version='1.0',
   description='A Collection Of Tools For Cathero Game Automation',
   author='Jamesong7822',
   author_email='weiong7822@gmail.com',
   packages=find_packages(),  #same as name
   install_requires=dependencies,
   dependencies="".join(["file:\\", os.path.join(os.getcwd(), "tesserocr-2.6.2-cp312-cp312-win_amd64.whl")]),
)