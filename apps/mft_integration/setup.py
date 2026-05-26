from setuptools import setup, find_packages

setup(
    name='mft_integration',
    version='0.0.1',
    description='MFT Platform License Management for ERPNext',
    author='Hephzibah Technologies',
    author_email='support@hephzibahtech.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=['frappe'],
)