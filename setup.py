import setuptools

with open('README.md', 'r') as f:
	long_description = f.read()

with open('requirements.txt', 'r') as f:
	requirements = f.readlines()

setuptools.setup(
	name='LIMP',
	version='6.1.0.dev1',
	author='Mahmoud Abduljawad',
	author_email='mahmoud@masaar.com',
	description='Rapid app development framework',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://github.com/masaar/limp',
	project_urls={
		'Docs: Github': 'https://github.com/masaar/limp-docs',
		'GitHub: issues': 'https://github.com/masaar/limp/issues',
		'GitHub: repo': 'https://github.com/masaar/limp',
	},
	packages=['limp', 'limp.packages', 'limp.packages.core'],
	classifiers=[
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.8',
		'Development Status :: 5 - Production/Stable',
		'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
		'Operating System :: OS Independent',
		'Topic :: Internet :: WWW/HTTP',
		'Framework :: AsyncIO',
	],
	python_requires='>=3.8',
	install_requires=requirements,
)
