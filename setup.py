from setuptools import setup

from auquanToolbox.version import __version__


setup(name='auquanToolbox',
      version=__version__,
      description='The Auquan Toolbox for trading system development',
      url='http://auquan.com/',
      author='Auquan',
      author_email='info@auquan.com',
      license='MIT',
      packages=['auquanToolbox'],
      scripts=['TradingStrategyTemplate.py', 'MeanReversion.py', 'BollingerBand.py'],
      include_package_data = True,

      install_requires=[
        'pandas',
        'numpy',
        'matplotlib',
      ],

      zip_safe=False,
     )