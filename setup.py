import setuptools

with open('README.md', 'r') as fh:
	long_description = fh.read()

setuptools.setup(
	name='LIMP',
	version='6.1.0.dev1',
	author='Mahmoud Abduljawad',
	author_email='mahmoud@masaar.com',
	description='Rapid app development framework',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://github.com/masaar/limp',
	packages=['limp'],
	classifiers=[
		'Programming Language :: Python :: 3',
		'License :: OSI Approved :: LGPL-3.0 License',
		'Operating System :: OS Independent',
	],
	python_requires='>=3.8',
)
